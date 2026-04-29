# EurLexScraper
Extract the content from the EUR-Lex websites. Each legal document's website (e.g. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631) has a left side bar with a possible combination of  'Text', 'Document Information', 'Procedure', 'Document Summary', and 'National Transposition'.
<img width="286" height="524" alt="Screenshot 2026-04-29 at 11 14 12" src="https://github.com/user-attachments/assets/7ceb7783-9d3e-4af6-8b7a-0438edd99a98" />

## document_info_scraper folders
### DocumentInfoScraper
1. The DocumentInfoScraper extracts the data from the Document Information page. There is a testing file to test the code (document_info_scraper_Test.ipynb)\
   **->The codes to initialize the extraction:**\
    ```scraper = DocumentInfoScraper(url)```\
    ```data = scraper.build_json_metadata()```
   
   **->This is an example structure of the website:**\
   {'Dates': [{'Date of document':},{'Date of effect':},...,{'Date of signature:'}, {'Deadline:'}, {'Date of end of validity':}],\
     'Miscellaneous information':[{'Author': }, {'Responsible body':  }, {'Form':}, {'Additional information': }],\
     'Procedure':[{'Procedure number':  }, {'Link':  }],\
     'Relationship between documents':[{'Treaty':},  {'Legal basis':}, {'Proposal': }, {'Link': }, \
   {'Internal procedures based on this legislative basic act':}, {'Modified by':}, {'Subsequent related instruments':}, {'Instruments cited':}],\
     'Classification':[ {'EUROVOC descriptor':},  {'Subject matter':}, {'Directory code':}]} \
   If the text is a hyperlink, the text and the link will be stored as a dictionary. **Note: in the value of the key 'Relationship between documents', the value of 'Internal procedures based on this legislative basic act' is not complete.**\
   **Some of the websites only contain parts of the sections, e.g., {'Dates': , 'Miscellaneous information': , 'Procedure': }. If the website doesn't exist, the code returns an empty dictionary {}**.

2. The DocumentInfoScraper extracts the links and their metadata from the 'Modified by' and 'Modifies' from the Document Information page. There is a testing file for the code (graph1_modifiedby_modifies_Test.ipynb).\
   **->The codes to initialize the extraction:**\
      ```scraper = DocumentInfoScraper(url1)```\
      ```modifiedby = scraper.extract_modifiedby_data()```\
      ```modifies = scraper.extract_modifies_data()```\
   **->The example data structure for mo:**\
   [{Relation':'','Act':'','Comment':'','Subdivision concerned':'','From':'','To':''},....],\
   [link1, link2,....]

### Graphbuilder
1. Make one graph on the main link. There is a testing file for the code (graph2_generate_one_graph_Test.ipynb).:\
   **->The codes to initialize the building process of the modifiedby table:**\
   ```graph_data = GraphBuilder(url)```\
   #get the metadata from the modifiedby\
   ```modifiedby_data_list = graph_data.modifiedby_attributes_list```\ 
   #subselect_modifiedby_attributes(self, relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[])\
   ```set_to_modifiedby = graph_data.subselect_modifiedby_attributes()```\
   ```modifiedby_graph = graph_data.create_graph() # modifiedby graph```
   
   **->The codes to initialize the building process of the modifies table:**\
   ```graph_data = GraphBuilder(url)```\
   #get the metadata from the modifies\
   ```modifies_data_list = graph_data.modifies_attributes_list```\
   #subselect_modifies_attributes(self, relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[])\
   ```set_to_modifies = graph_data.subselect_modifies_attributes()```\
   ```modifies_graph = graph_data.create_graph()```

   **->example output:**\
   The blue dots are the document numbers.\
   <img width="576" height="390" alt="Screenshot 2026-04-29 at 12 06 20" src="https://github.com/user-attachments/assets/1228b823-6e9b-45ec-a4ea-a284768eceab" />
   
3. Make a connected graph of the main link. The details are seen in the graph3_full_graph_Test.ipynb):\
   **Choose either the modifiedby table or  the modifies table. Otherwise, the code will scrape all the links, and it never ends.**
   
   **->example output:**\
   The blue dots are the document numbers.\
   <img width="602" height="409" alt="Screenshot 2026-04-29 at 12 13 34" src="https://github.com/user-attachments/assets/654cbcce-c8e4-4b4e-b506-01dd7dd145ac" />


## document_sum_scraper folders
### DocumentSumScraper
The DocumentSumScraper extracts the data from the Document Summary page. There is a testing file to test the code (document_sum_scraper_Test.ipynb)\
   1. **->The codes to initialize the extraction:**\
      ```from document_sum_scaper import DocumentSumScraper```\
      ```scraper = DocumentSumScraper(url)```\
      ```data = scraper.build_json_metadata()```
   
   2. **->This is an example structure of the website:**\
      {'Title and reference': string, \
      'Dates':[dict1, dict2], \
      'Classifications':[dict1, dict2,...], \
      'Summarised and linked documents':[dict1, dict2,...] (if the text is a hyperlink, the text and the link will be stored as a dictionary),\
      'Miscellaneous information':[dict1, dict2,...] (if the text is a hyperlink, the text and the link will be stored as a dictionary as the value of dictN),\
      'Summary document url': a HTML link of English text  (most of the document summary websites contain a HTML form of the summarized text)}\
   **Note: The code raises an error when the website doesn't exist. Some of the websites only contain parts of the sections, e.g., {'Title and reference': , 'Dates': , 'Miscellaneous information': }.**.\


## national_trans_scraper folder
### NationalTransScraper
The NationalTransScraper extracts the following structure.There is a testing file to test the code (national_trans_scraper_Test.ipynb)
  1. **->The codes to initialize the extraction:**\
      ```from national_trans_scaper import NationalTransScraper```\
      ```scraper = NationalTransScraper(url1)```\
      ```data = scraper.build_json_metadata()```
     
     The code will first check if the 'National Transposition ' exists on the left sidebar.\
     If the result is True, the code will automatically extract the metadata. Otherwise, it raises an error.
  3. **->The data structure:<br/>**
    {'Belgium': {'summary': {'transposition_deadline(s)': '05/07/2020', 'number_of_measures': '30'}}, <br/>
    'measures':[{'document_id':1, 'document_name': , 'document_link':link, 'official_pubilication': string, 'number': , 'publication_date': '', 'page': },\
                {'document_id':2, 'document_name': , 'document_link':link, 'official_pubilication': string, ''}, .... ],
    'France': {'summary': {'transposition_deadline(s)': '05/07/2020', 'number_of_measures': '30'}}, \
    'measures':[{'document_id':1, 'document_name': , 'document_link':link, 'official_pubilication': string, 'number': , 'publication_date': '', 'page': },\
                {'document_id':2, 'document_name': , 'document_link':link, 'official_pubilication': string, ''}, .... ],}\
     **The length of the measures should be the same as the number of measures.**
  

   
   
   


















