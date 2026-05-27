# EurLexScraper
Extract the content from the EUR-Lex websites. Each legal document's website (e.g. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0882) has a left side bar with a possible combination of  'Text', 'Document Information', 'Procedure', 'Document Summary', and 'National Transposition'.


<img width="339" height="458" alt="Screenshot 2026-05-27 at 17 50 23" src="https://github.com/user-attachments/assets/ad467efa-1d70-423d-a515-4be6f420f564" />

## `DocumentInfoScraper`

### 1. Extracting Data from the Document Information Page

The `DocumentInfoScraper` extracts structured data from the **Document Information** page.

A test notebook is available:

- `document_info_scraper_Test.ipynb`

---

### Initialize the Extraction

```python
scraper = DocumentInfoScraper(url)
data = scraper.build_json_metadata()
```

---

### Example Website Structure

```python
{
    'Dates': [
        {'Date of document':},
        {'Date of effect':},
        ...,
        {'Date of signature:':},
        {'Deadline:':},
        {'Date of end of validity':}
    ],

    'Miscellaneous information': [
        {'Author':},
        {'Responsible body':},
        {'Form':},
        {'Additional information':}
    ],

    'Procedure': [
        {'Procedure number':},
        {'Link':}
    ],

    'Relationship between documents': [
        {'Treaty':},
        {'Legal basis':},
        {'Proposal':},
        {'Link':},
        {'Internal procedures based on this legislative basic act':},
        {'Modified by':},
        {'Subsequent related instruments':},
        {'Instruments cited':}
    ],

    'Classification': [
        {'EUROVOC descriptor':},
        {'Subject matter':},
        {'Directory code':}
    ]
}
```

---

### Notes

- If a value is a hyperlink, both the displayed text and the URL are stored as a dictionary.

- The following field is currently incomplete due to multiple repeated key names:

```python
'Relationship between documents': [{'Internal procedures based on this legislative basic act':{one key value pair}}]
```

- Some websites may only contain part of the sections, for example:

```python
{
    'Dates':,
    'Miscellaneous information':,
    'Procedure':
}
```

- If the website does not exist, the scraper returns:

```python
{}
```

---

## 2. Extracting `Modified by` and `Modifies` Metadata

The `DocumentInfoScraper` can also extract links and metadata from the following sections:

- `Modified by`
- `Modifies`

A test notebook is available:

- `graph1_modifiedby_modifies_Test.ipynb`

---

### Initialize the Extraction

```python
scraper = DocumentInfoScraper(url1)
modifiedby = scraper.extract_modifiedby_data()
modifies = scraper.extract_modifies_data()
```

---

### Example Data Structure

```python
[
    {
        'Relation': '',
        'Act': '',
        'Comment': '',
        'Subdivision concerned': '',
        'From': '',
        'To': ''
    },
    ...
],

[
    link1,
    link2,
    ...
]
```

# `Graphbuilder`

## 1. Create a Fully Connected Graph from the Main Link

Implementation details can be found in:

- A test notebook is available:

- `graph2_full_graph_Test.ipynb`

> **Important**
>
> Choose **either**:
>
> - the `modifiedby` table using the `Modifiedby` class, **or**
> - the `modifies` table using the `Modifies` class.
>
> Otherwise, the scraper will continue scraping all related links indefinitely and may never terminate.
>
> If the number of scraped sites does not match the final output, rerun the code. Some websites may become overloaded after multiple simultaneous requests.
> Error messages will show up if the code opens the websites unsuccessfully:
> - find the failed URLs through `print(mb.failed_urls)`

---

### 1.1 Build the `modifiedby` Full Graph

#### Initialize the Process

```python
from graph_builder import Modifiedby
url = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631"
mb = Modifiedby(url, delay_time_asynchronous_max=4)
# delay_time_asynchronous_max is used to set the initial maximum waiting time for opening one/ multiple websites; the default is 0.01

full_urls = mb.collect_all_urls()

graph = mb.generate_full_graph(full_urls, visualize = True, progress = True)
# visualize is used to display the graph from the networkx library (visualize = True).
# progress is used to display the progress of building the graph per link (progress = True).
```
---

### Example Output

- The blue nodes represent the document numbers.

<img width="824" height="680" alt="Screenshot 2026-05-27 at 18 00 20" src="https://github.com/user-attachments/assets/75ca58c2-ac3e-481e-9b0f-820485916236" />

---
### 1.2 Build the `modifies` Full Graph

#### Initialize the Process

```python
from graph_builder import Modifies
ms = Modifies(url, delay_time_asynchronous_max=4)
# delay_time_asynchronous_max is used to set the initial maximum waiting time for opening one/ multiple websites;the default is 0.01

full_urls = ms.collect_all_urls()

graph = ms.generate_full_graph(full_urls, visualize = True, progress = True)
# visualize = True means to show the output of the G shown as the example
# visualize is used to display the graph from the networkx library (visualize = True).
# progress is used to display the progress of building the graph per link (progress = True).
```

---

### Example Output

- The blue nodes represent the document numbers.

<img
    width="602"
    height="409"
    alt="Example Full Graph"
    src="https://github.com/user-attachments/assets/654cbcce-c8e4-4b4e-b506-01dd7dd145ac"
/>

---

## 2. Create a Selected Connected Graph from the Main Link

Implementation details can be found in:

- `graph2_full_graph_Test.ipynb`

This method allows filtering the graph by a specific relation type.

Select the relevant links from the arguments: 
```python
create_selected_urls(relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[])
```


### 2.1 Build a Selected `modifiedby` Graph

#### Initialize the Process

```python
from graph_builder import Modifiedby
mb2 = Modifiedby("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R2019", delay_time_asynchronous_max=5)
# delay_time_asynchronous_max is used to set the initial maximum waiting time for opening one/ multiple websites;the default is 0.01

selected_urls = mb2.collect_selected_urls(relations=['Repeal'])
# enter relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[] to select metadata

graph2 = mb2.generate_full_graph(selected_urls, visualize = True, progress = False, selected = True, relations=['Repeal'])
# visualize is used to display the graph from the networkx library (visualize = True).
# progress is used to display the progress of building the graph per link (progress = True).
# selected is used to filter the metadata that fulfills requirements (selected = True), else it returns unselected metadata 
# enter relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[] to select metadata
```

---
### Example Output

- The blue nodes represent the document numbers.
<img width="1373" height="673" alt="Screenshot 2026-05-27 at 18 22 50" src="https://github.com/user-attachments/assets/dc4cdd50-b05a-4d89-afcb-3ba0012a60ee" />

---


### 2.2 Build a Selected `modifies` Graph

#### Initialize the Process

```python
from graph_builder import Modifies
ms2 = Modifies("https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R2019", delay_time_asynchronous_max=5)
# delay_time_asynchronous_max is used to set the initial maximum waiting time for opening one/ multiple websites;the default is 0.01

selected_urls2 = ms2.collect_selected_urls(relations=['Repeal'])
# enter relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[] to select metadata

graph2 = ms2.generate_full_graph(selected_urls2, visualize = True, progress = False, selected = True, relations=['Repeal'])
# visualize is used to display the graph from the networkx library (visualize = True).
# progress is used to display the progress of building the graph per link (progress = True).
# selected is used to filter the metadata that fulfills requirements (selected = True), else it returns unselected metadata 
# enter relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[] to select metadata
```
---
### Example Output

- The blue nodes represent the document numbers.
<img width="1223" height="652" alt="Screenshot 2026-05-27 at 18 19 36" src="https://github.com/user-attachments/assets/b0c8a6a0-96e0-4624-bd8d-b3c7b9f91353" />

---

# `document_sum_scraper` Folders

## `DocumentSumScraper`

The `DocumentSumScraper` extracts structured data from the **Document Summary** page.

A test notebook is available:

- `document_sum_scraper_Test.ipynb`

---

## 1. Initialize the Extraction

```python
from document_sum_scraper import DocumentSumScraper

scraper = DocumentSumScraper(url)

data = scraper.build_json_metadata()
```

---

## 2. Example Website Structure

```python
{
    'Title and reference': string,

    'Dates': [
        dict1,
        dict2
    ],

    'Classifications': [
        dict1,
        dict2,
        ...
    ],

    'Summarised and linked documents': [
        dict1,
        dict2,
        ...
    ],

    'Miscellaneous information': [
        dict1,
        dict2,
        ...
    ],

    'Summary document url':
        'HTML link of the English summary text'
}
```

---

## Notes

- If a value is a hyperlink, both the displayed text and the URL are stored as a dictionary. This applies to:
  - `Summarised and linked documents`
  - `Miscellaneous information`

- Most document summary websites contain an HTML version of the summarized text.

- The scraper raises an error if the website does not exist.

- Some websites may only contain part of the available sections, for example:

```python
{
    'Title and reference':,
    'Dates':,
    'Miscellaneous information':
}
```



  
# `national_trans_scraper` Folder

## `NationalTransScraper`

The `NationalTransScraper` extracts metadata related to **National Transposition** information.

A test notebook is available:

- `national_trans_scraper_Test.ipynb`

---

## 1. Initialize the Extraction

```python
from national_trans_scraper import NationalTransScraper

scraper = NationalTransScraper(url1)

data = scraper.build_json_metadata()
```

---

## 2. Extraction Logic

The scraper first checks whether the **National Transposition** section exists in the left sidebar.

- If the section exists, the scraper automatically extracts the metadata.
- Otherwise, the scraper raises an error.

---

## 3. Example Data Structure

```python
{
    'Belgium': {
        'summary': {
            'transposition_deadline(s)': '05/07/2020',
            'number_of_measures': '30'
        },

        'measures': [
            {
                'document_id': 1,
                'document_name': '',
                'document_link': link,
                'official_publication': string,
                'number': '',
                'publication_date': '',
                'page': ''
            },

            {
                'document_id': 2,
                'document_name': '',
                'document_link': link,
                'official_publication': string
            },

            ...
        ]
    },

    'France': {
        'summary': {
            'transposition_deadline(s)': '05/07/2020',
            'number_of_measures': '30'
        },

        'measures': [
            {
                'document_id': 1,
                'document_name': '',
                'document_link': link,
                'official_publication': string,
                'number': '',
                'publication_date': '',
                'page': ''
            },

            {
                'document_id': 2,
                'document_name': '',
                'document_link': link,
                'official_publication': string
            },

            ...
        ]
    }
}
```

---

## Notes

The length of the measures should be the same as the number of measures.
   
   


















