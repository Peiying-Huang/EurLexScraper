from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json

class DocumentSumScraper:
    def __init__(self, url, delay_time_asynchronous_max= 0.1):
        self.url = url
        self.base_url = "https://eur-lex.europa.eu/legal-content/EN"
        parts = self.url.split('/TXT/') # raise value error if the url is not correct format
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"This is not correct input url: {self.url}, please give a url like: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631")
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

    def _load_page(self, url, expected_tag = "NMetadata", max_attempts=5, base_delay=2):
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
        check if the 'Document summary' exists on the left side bar of the document info page.
        returns: self.exist (True/False)
        """
        def has_sum(soup):
            side_bar = soup.find('nav', {"id": "AffixSidebar"})

            if side_bar:
                names = [a.get_text().strip() for a in side_bar.find_all('a')]
                if 'Document summary' in names:
                    self.exist = True
                    return self.exist
            else:
                self.exist = False
                raise ValueError("The Document Summary page doesn't exist.")

        
        txt_soup = self._load_page(self.url, expected_tag = "MenuList")

        if not txt_soup:
            self.exist = False
            raise ValueError("The Document Summary page doesn't exist.")
        else:
            self.exist = has_sum(txt_soup)
            return self.exist

    def get_soup(self):
        """"
        parse the content of a url 
        returns: the content of the website
        """
        if not self.exist:
            raise ValueError("The Document Summary page doesn't exist.")

        sum_url = f'{self.base_url}/LSU/{self.uri_identifier}'
    
        self.soup = self._load_page(sum_url, expected_tag = "NMetadata")
        
        return self.soup
    
    def extract_keys(self):
        """
        extract all the titles in the document summary websites and raise an error when the brower extracted the data from the document information page
        return: a list of keys -> ['Dates',  'Classifications', 'Summarised and linked documents', 'Miscellaneous information'](this can be changed if there are other titles contains html tag "dl" with class_="NMetadata".
        """
        list_keys = []
        document_sum_titles = ['Title and reference','Dates', 'Classifications', 'Summarised and linked documents', 'Miscellaneous information']

        for block in self.soup.find_all("div", class_="panel panel-default PagePanel"):
            for btn in block.select('button[data-toggle="collapse"]'):
                key = btn.get_text(strip=True)
                if key in document_sum_titles:
                    list_keys.append(key)
        return list_keys

    def create_dict_links(self, a_block):
        """"
        create dictionary for each links from the metedata
        para: blocks of a element
        returns: a dictionary of the link, like this {text:href}
        """
        dict_a = {}
        for a in a_block:
            href = a.get("href", "").replace("./../../../", "https://eur-lex.europa.eu/")
            text = a.get_text(strip=True).replace("\uf002", "") # get rid of '\uf002' in the retrieved text
            dict_a[text] = href
        return dict_a

    def extract_values(self):
        """"
        store the content under the titles from the document information link in dictionary
        returns: a list of dictionary in each blocks ->['Dates block', 'Miscellaneous information block', 'Procedure block', 'Relationship between documents block']
        """
        list_values = []
        
        first_value_block = self.soup.find("div", { "id" :"PP1Contents" })
        first_value = first_value_block.find('p').get_text()
        if first_value:
            list_values.append(first_value)

        dl_blocks = self.soup.find_all("dl", class_="NMetadata")
        if dl_blocks:
            for value_block in dl_blocks:
                dts = value_block.find_all("dt")
                dds = value_block.find_all("dd")

                values = []
                for dt, dd in zip(dts, dds):
                    key = dt.get_text(strip=True).rstrip(":").strip()
                    a_block = dd.find_all("a", href=True)
                    dict_text = {}
                    if a_block:
                        dict_text[key] = self.create_dict_links(a_block)
                        values.append(dict_text)
                    else:
                        dict_text = {}
                        content = dd.get_text(strip=True)
                        dict_text[key] = content
                        values.append(dict_text)
                list_values.append(values)
        return list_values

    def collect_text_url(self):
        """
        Collect and returns the English HTML document URL.
        Return:
            str: The full URL if found and valid, otherwise an error message.
        """

        en_text_a = self.soup.find('a', {'id': 'format_language_table_HTML_EN'}, href=True)

        if en_text_a is None:
            return "English HTML link is not found on the document summary page."

        href = en_text_a.get('href')

        if not href or "/legal-content/EN/TXT/HTML/?" not in href or "uri=LEGISSUM:" not in href:
            return f"Invalid or unexpected href format: {href}"

        return urljoin("https://eur-lex.europa.eu", href)
    
    def build_json_metadata(self):
        """"
        create a dictionary for the metadata
        return: a json file of metadata
        """
        
        list_keys = self.extract_keys()
        list_values = self.extract_values()
        dict_meta = {}
        
        for i in range(len(list_keys)):
            key = list_keys[i]
            value = list_values[i]
            dict_meta[key] = value
        dict_meta['Summary document url'] = self.collect_text_url()
        json_meta = json.dumps(dict_meta)
        return json.loads(json_meta)
     
