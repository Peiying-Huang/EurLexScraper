# EurLexScraper
Extract the content from the EUR-Lex websites. Each legal document's website (e.g. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R2631) has a left side bar with a possible combination of  'Text', 'Document Information', 'Procedure', 'Document Summary', and 'National Transposition'.
<img width="286" height="524" alt="Screenshot 2026-04-29 at 11 14 12" src="https://github.com/user-attachments/assets/7ceb7783-9d3e-4af6-8b7a-0438edd99a98" />

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
> The 

---

### 1.1 Build the `modifiedby` Full Graph

#### Initialize the Process

```python
from graph_builder import Modifiedby

mb = Modifiedby(url)

full_urls = mb.collect_all_urls()

graph = mb.generate_full_graph(full_urls)
```

---

### 1.2 Build the `modifies` Full Graph

#### Initialize the Process

```python
from graph_builder import Modifies

ms = Modifies(url)

full_urls = ms.collect_all_urls()

graph = ms.generate_full_graph(full_urls, visualize = True)
# visualize = True means to show the output of the G shown as the example
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

- `graph3_full_graph_Test.ipynb`

This method allows filtering the graph by a specific relation type.

---

### 2.1 Build a Selected `modifiedby` Graph
#### Select the relevent links from the arguments: 
```python
(relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]):
```python

#### Initialize the Process

```python
from graph_builder import Modifiedby

mb_selected = Modifiedby(url)

selected_urls = mb_selected.create_selected_urls(relations='Corrected by')

graph = mb_selected.generate_full_graph(selected_urls)
```

---

### 2.2 Build a Selected `modifies` Graph

#### Initialize the Process

```python
from graph_builder import Modifies
mb_selected = Modifies(url)
selected_urls = ms_selected.create_selected_urls(relations='Corrected by')
graph = ms_selected.generate_full_graph(selected_urls)
```

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

- If a value is a hyperlink, both the displayed text and the URL are stored as a dictionary.

- This applies to:
  
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

- The length of the measures should be the same as the number of measures.
   
   


















