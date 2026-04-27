from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json

class NationalTransScraper:
    def __init__(self, url):
        self.url = url
        self.base_url = "https://eur-lex.europa.eu/legal-content/EN"
        parts = self.url.split('/TXT/')
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"This is not a correct input url: {self.url}, please give url like: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631")
        self.uri_identifier = self.url.split('/TXT/')[1]
        self.exist = None
        self.nim_url = None
        self.soup = None

    def side_bar_check(self):
        """
        check if the 'National transposition' exists on the left side bar of the document info page.
        returns: self.exist (True/False)
        """
        
        url = self.url
        options = Options()# create an option instance 
        options.add_argument("--headless") # running in headless mode
        driver = webdriver.Chrome(options=options)
        
        driver.get(url)
        time.sleep(5)
        html = driver.page_source # gets the source of the current page
        
        info_soup = BeautifulSoup(html,"html.parser")
        side_bar = info_soup.find('nav',{"id":"AffixSidebar"})
        if side_bar is not None: 
            a_tags = side_bar.find_all('a')
            side_bar_names = [a_tag.get_text().strip() for a_tag in a_tags]
            if 'National transposition' in side_bar_names:
                self.exist = True
                return self.exist
            else:
                self.exist = False
                return self.exist
        else:
            self.exist = False
            return self.exist
              
    
    def get_soup(self):
        """"
        parse the content of a url 
        returns: the content of the website
        """
        self.exist
        if self.exist:
            self.base_url
            self.uri_identifier
            self.nim_url = f'{self.base_url}/NIM/{self.uri_identifier}'
        else:
            raise ValueError("The National Transposition page doesn't exist.")
        
        url = self.nim_url
        options = Options()# create an option instance 
        options.add_argument("--headless") # running in headless mode
        driver = webdriver.Chrome(options=options)#starts a new ChromeDriver instance.

        try:
            driver.get(url)
            time.sleep(5)
            html = driver.page_source # gets the source of the current page
            self.soup = BeautifulSoup(html,"html.parser")
            return self.soup

        except WebDriverException:
            self.soup = None
            return  # exit the function when this error is raised

        finally:
            driver.quit()
            
    #def check_national_trans(self):
        #"""
        #check whether the page contains a warning message, which indicates
        #that the national transposition is unavailable or invalid.
        
        #Raises valueError:
        #If a warning message is found on the page.The error message will contain the warning text.
        #"""

        #soup = self.soup

        #warning = soup.find('div', class_="alert alert-warning")

        #if warning:
            #warning_message = warning.get_text(strip=True)
            #raise ValueError(warning_message)
        #else:
            #print('The national transpositions page is found.')
        

    def extract_country_data(self):
        """"
        store the content under the titles from the document information link in dictionary
        returns: two lists
        country_names ['Belgium', 'Bulgaria', 'Czechia', 'Denmark', 'Germany', 'Estonia', 'Ireland', 'Greece' ...]
        country_values [{'Transposition deadline(s)': '', 'Number of measures': ''},{},{}, ...]
        """
        #self.side_bar_check()
        #self.get_soup()
        soup = self.soup
        
        countries = soup.find_all('div', class_= 'col-sm-12 ntmRow')
        country_names = []
        country_values = []
        for country in countries:
            country_name = country.find('span', class_="VMIMore nonTransform").get_text()
            country_names.append(country_name)

            country_value = {}
            country_value['transposition_deadline(s)'] = country.find('div', class_="col-sm-4 hidden-xs").get_text()
            country_value['number_of_measures'] = country.find('p', class_="ViewMoreInfo ntmMore collapsed countryToggle noNimsBtn").get_text().split('\n')[1]
            country_values.append(country_value)
        return country_names, country_values

    def collect_text_url(self, measure):
        """
        collect the English HTML document URL.
        return:
            str: the full URL
        """
        en_text_a = measure.find('a', {'id': 'titleLink'}, href=True)
        href = en_text_a.get('href').split('./../../..')[1]
        link = f'https://eur-lex.europa.eu{href}'
        return link
    
    def extract_measures_values(self):
        """
        extract all the documents within eacg countriy
        return: a list of lists of documenst
        [[documents from country1],[documents from country2],[documents from country3],...]
        """
        #self.side_bar_check()
        #self.get_soup()
        soup = self.soup
        
        measures_list = []
        country_measures = soup.find_all('div',  class_='panel panel-default PagePanel eurlexPanel child-row')
        for country_measure in country_measures:
            country_measures_list = []
            measures = country_measure.find_all('li')

            i =0
            for measure in measures:
                i = i+1
                measure_dict = {}
                link_title = measure.find('a').get_text()
                after = measure.get_text().split('Official publication:')[1]
                elements = [e.strip().strip(':;').lower().strip() for e in after.split('\n') if e.strip() and e.strip() not in (':', ';')]
                mea_keys = elements[1::2]
                mea_keys = [mea_key.replace(" ", "_") for mea_key in mea_keys]
                mea_values = elements[2::2]

                measure_dict['document_id'] = i
                measure_dict['document_name'] = link_title
                measure_dict['document_link'] = self.collect_text_url(measure)
                measure_dict['official_pubilication'] = elements[0]
                for mea_key, mea_value in zip(mea_keys, mea_values):
                    measure_dict[mea_key] = mea_value
                country_measures_list.append(measure_dict)
            measures_list.append(country_measures_list)
        return measures_list


    def build_json_metadata(self):
        """"
        create a dictionary for the metadata
        return: a json file of metadata
        """
        self.side_bar_check()
        self.get_soup()
        country_names, country_data = self.extract_country_data()
        country_measures = self.extract_measures_values()


        dict_meta = {}

        for i in range(len(country_names)):
            subdict = {}
            country_name = country_names[i]
            country_value = country_data[i]

            subdict['summary'] = country_value
            subdict['measures'] = country_measures[i]

            dict_meta[country_name] = subdict
            
        json_meta = json.dumps(dict_meta)
        return json_meta

    
