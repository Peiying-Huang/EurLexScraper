import networkx as nx
import matplotlib.pyplot as plt
from document_info_scaper import DocumentInfoScraper
import spacy
import re

class GraphBuilder:
    def __init__(self, url):
        self.scraper = DocumentInfoScraper(url)
        self.modified = self.scraper.extract_modified_table()
        self.document = self.scraper.get_document_num()
    
    
    def graph_data(self):
        """ 
        extract graph data from the "Modified By" table.
        return: 
        attributes_list:[{Relation':'','Act':'','Comment':'','Subdivision concerned':'','From':'','To':''},....]
        node_list:[32023R2631R(01), 2023R2631R(02),...]
        edge_attri_list:[{'relation':'modifies', 'weight':'1.0'},{'relation':'modifies', 'weight':'1.0'},....]
        """
        data = self.modified
        if not data:
            return #Exit
        
        attributes_list =[] #[{Relation':'','Act':'','Comment':'','Subdivision concerned':'','From':'','To':''},....]
        for row in data.find_all('tr'):
            tds = row.find_all('td')
            attribute_dict = {}
            attri_keys = ['Relation', 'Act', 'Comment', 'Subdivision concerned', 'From','To']
            attri_values = []
            for td in tds:
                td_text = td.get_text().strip()
                attri_values.append(td_text)
            for attri_key, attri_value in zip(attri_keys,attri_values):
                attribute_dict[attri_key] = attri_value
            attributes_list.append(attribute_dict)

        node_list = [] #[32023R2631R(01), 2023R2631R(02),...]
        for act in attributes_list:
            node_label = act['Act']
            node_list.append(node_label)

        edge_attri_list = [] #[{'relation':'modifies', 'weight':'1.0'},{'relation':'modifies', 'weight':'1.0'},....]
        for relation in attributes_list:
            relation_dict = {}
            relation_dict['relation'] = relation['Relation']
            relation_dict['weight'] = 1.0
            edge_attri_list.append(relation_dict)
        return attributes_list,node_list, edge_attri_list
    
    def create_graph(self):
        """
        create a graph based on attributes_list,node_list, edge_attri_list
        return a graph
        """
        is_valid = self.graph_data()
        if not is_valid:
            return # Exit
        
        attributes_list,node_list, edge_attri_list = is_valid
        G = nx.DiGraph()
        G.add_node(self.document)
        form_node_list = zip(node_list,attributes_list)
        G.add_nodes_from(form_node_list)
        targets = node_list
        sources = [self.document for i in range(0,len(targets))]
        edges = [(u, v, r) for u, v, r in zip(sources, targets, edge_attri_list)]
        G.add_edges_from(edges)
        return G

    def find_links(self):
        """
        store all links inside the "Modified by" table in a list named 'links'
        return: a list of links
        """
        
        is_valid = self.modified
        if not is_valid:
            return # Exit
        
        links =[]
        for a in is_valid.find_all('a'):
            uri_identifier = a.get("href", "").split('./../../../legal-content/EN/AUTO/')[1]
            base_url = 'https://eur-lex.europa.eu/legal-content/EN/TXT/'
            link = f'{base_url}{uri_identifier}'
            links.append(link)
        return links
    
