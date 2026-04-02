import networkx as nx
import matplotlib.pyplot as plt
from document_info_scaper import DocumentInfoScraper
import spacy
import re

class GraphBuilder:
    def __init__(self, url):
        self.scraper = DocumentInfoScraper(url)
        self.modifiedby_attributes_list, self.modifiedby_links = self.scraper.extract_modifiedby_data()
        self.modifies_attributes_list, self.modifies_links = self.scraper.extract_modifies_data()
        self.document = self.scraper.get_document_num()
        self.attributes_list = []
    
  
    def subselect_modifiedby_attributes(self, relations=None, acts=None, comments=None, subdivisions=None, froms=None, tos=None):
        """
        enter any values in the 'relation', 'act', 'comment', 'subdivision', 'from', 'to',
        return rows with the entered values
        """
        
        result = self.modifiedby_attributes_list

        if relations:
            result = [x for x in result if x['Relation'] in relations]
        if acts:
            result = [x for x in result if x['Act'] in acts]
        if comments:
            result = [x for x in result if x['Comment'] in comments]
        if subdivisions:
            result = [x for x in result if x['Subdivision concerned'] in subdivisions]
        if froms:
            result = [x for x in result if x['From'] in froms]
        if tos:
            result = [x for x in result if x['To'] in tos]

        self.attributes_list = result
        return self.attributes_list
            
    def subselect_modifies_attributes(self, relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]):
        """
        enter any values in the 'relation', 'act', 'comment', 'subdivision', 'from', 'to',
        return rows with the entered values
        """
        result = self.modifies_attributes_list

        if relations:
            result = [x for x in result if x['Relation'] in relations]
        if acts:
            result = [x for x in result if x['Act'] in acts]
        if comments:
            result = [x for x in result if x['Comment'] in comments]
        if subdivisions:
            result = [x for x in result if x['Subdivision concerned'] in subdivisions]
        if froms:
            result = [x for x in result if x['From'] in froms]
        if tos:
            result = [x for x in result if x['To'] in tos]

        self.attributes_list = result
        return self.attributes_list
            
    
    def graph_data(self):
        """ 
        extract graph data from the "Modified By" table.
        return: 
        node_list:[32023R2631R(01), 2023R2631R(02),...]
        edge_attri_list:[{'relation':'modifies', 'weight':'1.0'},{'relation':'modifies', 'weight':'1.0'},....]
        """
        
        node_list = [] #[32023R2631R(01), 2023R2631R(02),...]
        for act in self.attributes_list:
            node_label = act['Act']
            node_list.append(node_label)

        edge_attri_list = [] #[{'relation':'modifies', 'weight':'1.0'},{'relation':'modifies', 'weight':'1.0'},....]
        for relation in self.attributes_list:
            relation_dict = {}
            relation_dict['relation'] = relation['Relation']
            relation_dict['weight'] = 1.0
            edge_attri_list.append(relation_dict)
            
        return node_list, edge_attri_list

    
    def create_graph(self):
        """
        create a graph based on attributes_list,node_list, edge_attri_list
        return a graph
        """
        is_valid = self.graph_data()
        if not is_valid:
            return # Exit
        
        attributes_list = self.attributes_list
        node_list, edge_attri_list = is_valid
        G = nx.DiGraph()
        G.add_node(self.document)
        form_node_list = zip(node_list,attributes_list)
        G.add_nodes_from(form_node_list)
        targets = node_list
        sources = [self.document for i in range(0,len(targets))]
        edges = [(u, v, r) for u, v, r in zip(sources, targets, edge_attri_list)]
        G.add_edges_from(edges)
        return G


