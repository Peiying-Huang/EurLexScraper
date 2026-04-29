from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import json

class DocumentSumScraper:
    def __init__(self, url):
        self.url = url
        self.base_url = "https://eur-lex.europa.eu/legal-content/EN"
        parts = self.url.split('/TXT/') # raise value error if the url is not correct format
        if len(parts) < 2 or not parts[1]:
            raise ValueError(f"This is not correct input url: {self.url}, please give a url like: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631")
        self.uri_identifier = self.url.split('/TXT/')[1]
        self.info_url =  f'{self.base_url}/LSU/{self.uri_identifier}'
        self.soup = None
    
    def get_soup(self):
        """"
        parse the content of a url
        returns: soup object
        """
        url = self.info_url
        options = Options()# create an option instance 
        options.add_argument("--headless") # running in headless mode
        driver = webdriver.Chrome(options=options)#starts a new ChromeDriver instance.
        driver.get(url)
        time.sleep(5)  # wait for JS to load

        # Get full rendered HTML
        html = driver.page_source # gets the source of the current page
        driver.quit()
        self.soup = BeautifulSoup(html,"html.parser")

    def check_document_sum(self):
        """
        check whether the page contains a warning message, which indicates
        that the document summary is unavailable or invalid.
        
        Raises valueError:
        If a warning message is found on the page.The error message will contain the warning text.
        """

        soup = self.soup

        warning = soup.find('div', class_="alert alert-warning")

        if warning:
            warning_message = warning.get_text(strip=True)
            raise ValueError(warning_message)
            
    
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
        self.get_soup()
        self.check_document_sum()
        list_keys = self.extract_keys()
        list_values = self.extract_values()
        dict_meta = {}
        
        for i in range(len(list_keys)):
            key = list_keys[i]
            value = list_values[i]
            dict_meta[key] = value
        dict_meta['Summary document url'] = self.collect_text_url()
        json_meta = json.dumps(dict_meta)
        return json_meta
     
