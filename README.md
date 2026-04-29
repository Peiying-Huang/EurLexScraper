# EurLexScraper
Extract the content from the EUR-Lex websites. Each legal document's website (e.g. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631) has a left side bar with a possible combination of  'Text', 'Document Information', 'Procedure', 'Document Summary', and 'National Transposition'.
<img width="286" height="524" alt="Screenshot 2026-04-29 at 11 14 12" src="https://github.com/user-attachments/assets/7ceb7783-9d3e-4af6-8b7a-0438edd99a98" />

### DocumentInfoScraper
1. The DocumentInfoScraper extracts the data from the Document Information page.<b>\
   ->**The codes to initialize the extraction:**\
      scraper = DocumentInfoScraper(url)\
      data = scraper.build_json_metadata()\
   ->**This is an example structure of the website:**\
    {'Dates': [{'Date of document':}, {'Date of effectN':},...,{'Date of signature:'}, {'Deadline:'}, {'Date of end of validity':}],\
     'Miscellaneous information':[{'Author': }, {'Responsible body':  }, {'Form':}, {'Additional information': }],\
     'Procedure':[{'Procedure number':  }, {'Link':  }],\
     'Relationship between documents':[{'Treaty':},  {'Legal basis':}, {'Proposal': }, {'Link': }, \
   {'Internal procedures based on this legislative basic act':}, {'Modified by':}, {'Subsequent related instruments':}, {'Instruments cited':}],\
     'Classification':[ {'EUROVOC descriptor':},  {'Subject matter':}, {'Directory code':}]} \
   If the text is a hyperlink, the text and the link will be stored as a dictionary. **Note: in the value of the key 'Relationship between documents', the value of 'Internal procedures based on this legislative basic act' is not complete.**\

**Some of the websites only contain parts of the sections, e.g., {'Dates': , 'Miscellaneous information': , 'Procedure': }. If the website doesn't exist, the code returns an empty dictionary {}.**
