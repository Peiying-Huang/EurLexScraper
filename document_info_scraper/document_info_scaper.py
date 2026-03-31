from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import json

class DocumentInfoScraper:
    def __init__(self, url):
        self.url = url
        self.base_url = "https://eur-lex.europa.eu/legal-content/EN"
        parts = self.url.split('/TXT/')
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"This is not a correct input url: {self.url}, please give url like: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631")
        self.uri_identifier = self.url.split('/TXT/')[1]
        self.info_url =  f'{self.base_url}/ALL/{self.uri_identifier}'
        self.soup = None
   
    
    def get_soup(self):
        """"
        parse the content of a url 
        returns: the content of the website
        """
        url = self.info_url
        options = Options()# create an option instance 
        options.add_argument("--headless") # running in headless mode
        driver = webdriver.Chrome(options=options)#starts a new ChromeDriver instance.
        
        try:
            driver.get(url)
            time.sleep(5)
            html = driver.page_source # gets the source of the current page
            self.soup = BeautifulSoup(html,"html.parser")

        except WebDriverException:
            self.soup = None
            return  # exit the function when this error is raised

        finally:
            driver.quit()

    
    def extract_keys(self):
        """
        extract all the titles in the document info websites
        return: a list of keys ->['Dates', 'Miscellaneous information', 'Procedure', 'Relationship between documents', 'Classifications']
        """
        list_keys = []
        document_info_titles = ['Dates', 'Miscellaneous information', 'Procedure', 'Relationship between documents', 'Classifications']
        for block in self.soup.find_all("div", class_="panel panel-default PagePanel"):
            for btn in block.select('button[data-toggle="collapse"]'):
                key = btn.get_text(strip=True)
                if key in document_info_titles:
                    list_keys.append(key)
        return list_keys
    
    def create_dict_links(self, a_block):
        """"
        create dictionary for each links from the metedata
        para: blocks of a tag 
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

        value_blocks = self.soup.find_all("dl", class_="NMetadata")
        for value_block in value_blocks:
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
    
    def build_json_metadata(self):
        """"
        create a dictionary for the metadata
        return: a json file of metadata
        """
        self.get_soup()
        list_keys = self.extract_keys()
        list_values = self.extract_values()
        dict_meta = {}
        
        for i in range(len(list_keys)):
            key = list_keys[i]
            value = list_values[i]
            dict_meta[key] = value
        json_meta = json.dumps(dict_meta)
        return json_meta
    
    def get_document_num(self):
        """
        extract document number for making graphs
        """
        document_block = self.soup
        if document_block is not  None:
            document = document_block.find("p", class_ = "DocumentTitle pull-left")
            document_number = document.get_text().split()[1]
        return document_number

    def extract_modified_table(self):
        """
        extract the "modified by" table and return all the html tags if the table exist.
        Otherwise, return None.
        """
        self.get_soup()
        modified_table = self.soup.find("tbody")
        if modified_table:
            return modified_table
        else:
            return None

        

    
