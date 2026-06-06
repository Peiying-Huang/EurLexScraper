from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json

class NationalTransScraper:
    def __init__(self, url, delay_time_asynchronous_max=0.01):
        self.url = url
        self.base_url = "https://eur-lex.europa.eu/legal-content/EN"
        parts = self.url.split('/TXT/')
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"This is not a correct input url: {self.url}, please give url like: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631")
        self.uri_identifier = self.url.split('/TXT/')[1]
        self.failed_urls = []
        
        # ---- Initialize driver ONCE ----
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(options=options)
        
        self.delay_time_asynchronous_max = delay_time_asynchronous_max
        self.exist = self.side_bar_check()
        self.soup = self.get_soup()

    # ---- Clean shutdown ----
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()


    def _load_page(self, url, expected_tag = 'VMIMore nonTransform', max_attempts=5, base_delay=2):
        """load a page, if the loading process is not sucessful. Try 5 times"""
        for attempt in range(max_attempts):
            try:
                self.driver.get(url)
            
                loading = WebDriverWait(self.driver, self.delay_time_asynchronous_max).until(EC.presence_of_element_located((By.CLASS_NAME, expected_tag)))
                #wait for a MAXIUM amount of waiting time until it finds the class in any tag. Raise an error when it doesn't work

                source = self.driver.page_source #Get the source of the last loaded page--> get the dish on the table
                soup = BeautifulSoup(source, "html.parser")
                return soup

            except (WebDriverException, ValueError) as e:
                if attempt == max_attempts - 1:
                    self.failed_urls.append({
                        "url": url,
                        "error": str(e)
                    })
                    raise ValueError("Try 5 attempt, but the website doesn't return intended content. Try to increase delay time.")
                else:
                    #print(f'{url}:Try {attempt+1} attempt') #--> can be used to debug
                    delay = base_delay * (2 ** attempt) # fixed time to wait
                    time.sleep(delay)  
          
    
    def side_bar_check(self):
        """
        check if the 'National transposition' exists on the left side bar of the document info page.
        returns: self.exist (True/False)
        """
        def has_nim(soup):
            side_bar = soup.find('nav', {"id": "AffixSidebar"})
            
            if side_bar:
                names = [a.get_text().strip() for a in side_bar.find_all('a')]
                if 'National transposition' in names:
                    self.exist = True
                    return self.exist
            else:
                self.exist = False
                raise ValueError("The National Transposition page doesn't exist.")
        
        txt_soup = self._load_page(self.url, expected_tag = "MenuList")

        if not txt_soup:
            self.exist = False
            raise ValueError("The National Transposition page doesn't exist.")
        else:
            self.exist = has_nim(txt_soup)
            return self.exist


    def get_soup(self):
        """
        check if the nim website exist, make the nim website and get soup
        """
        if not self.exist:
            raise ValueError("The National Transposition page doesn't exist.")

        nim_url = f'{self.base_url}/NIM/{self.uri_identifier}'

        self.soup = self._load_page(nim_url, expected_tag="panel-title")
        return self.soup

    def extract_country_data(self):
        """"
        store the content under the titles from the document information link in dictionary
        returns: two lists
        country_names ['Belgium', 'Bulgaria', 'Czechia', 'Denmark', 'Germany', 'Estonia', 'Ireland', 'Greece' ...]
        country_values [{'Transposition deadline(s)': '', 'Number of measures': ''},{},{}, ...]
        """
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
    
    def extract_measures_values(self):
        """
        extract all the documents within each country
        return: a list of lists of documenst
        [[documents from country1],[documents from country2],[documents from country3],...]
        """
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

                text = measure.get_text()
                has_official_pub = 'Official publication:' in text
                split_key = 'Official publication:' if has_official_pub else 'Number:'
        
                content = text.split(split_key)[1]
                elements = [e.strip().strip(':;').lower().strip() for e in content.split('\n') if e.strip() and e.strip() not in (':', ';')]
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
        
        return json.loads(json_meta)

    
