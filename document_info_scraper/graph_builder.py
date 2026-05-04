import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from document_info_scaper import DocumentInfoScraper


class GraphBuilder:
    def __init__(self, attributes_list=None, G=None, document=None):
        self.attributes_list = attributes_list or []
        self.G = G if G is not None else nx.DiGraph()
        self.document = document 

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
    
    def visualize_graph(self):
        """
        Visualize the graph 
        """
        G = self.G
        pos = nx.spring_layout(G, seed=50)
        edge_labels = {(u, v): d["relation"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_nodes(G, pos, node_size=10)
        nx.draw_networkx_labels(G, pos, font_color="white", font_weight="bold")
        nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True,
                            arrowsize=20, connectionstyle="arc3,rad=0.1")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

        plt.title("Directed Graph with Attributes")
        plt.axis("off")
        plt.tight_layout()
        plt.show()


class Modifiedby(GraphBuilder):
    def __init__(self, url):
        # Step 1: scrape data
        scraper = DocumentInfoScraper(url)
        attrs, links = scraper.extract_modifiedby_data()
        document = scraper.get_document_num()

        # Step 2: initialize parent
        super().__init__(attributes_list=attrs, G=None, document=document)

        # Step 3: child-specific attributes
        self.first_url = url
        self.modifiedby_links = links
        self.scraper = scraper

    def subselect_modifiedby_attributes(self, relations=[], acts=[], comments=[], subdivisions= [], froms= [], tos= []):
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

    def get_links_only(self, url):
        """speed up the process of getting the links"""
        scraper = DocumentInfoScraper(url)
        _, links = scraper.extract_modifiedby_data()
        return links


    def collect_all_urls(self, max_workers=10):
        """
        Parallel BFS crawler (fast version)
        """

        visited = set()
        queue = deque([self.first_url])
        all_urls = []

        pbar = tqdm(desc="Crawling URLs")

        # thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            while queue:
                # batch URLs (important for speed)
                batch = []

                while queue and len(batch) < max_workers:
                    url = queue.popleft()

                    if url not in visited:
                        visited.add(url)
                        batch.append(url)
                        all_urls.append(url)

                if not batch:
                    continue

                # submit all jobs in parallel
                futures = {
                    executor.submit(self.get_links_only, url): url
                    for url in batch
                }

                for future in as_completed(futures):
                    try:
                        links = future.result()
                    except Exception:
                        continue

                    new_links = [link for link in links if link not in visited]
                    queue.extend(new_links)

                    pbar.update(1)

        pbar.close()

        print(f"\nTotal URLs collected: {len(all_urls)}")
        return all_urls

    def collect_all_urls(self):
        """
        collect all urls from the start url
        """
        
        visited = set()
        queue = deque([self.first_url]) # the BFS queue. Stores tuples of (url, layer). Starts with start_url at layer 0
        all_urls = []

        while queue:
            url = queue.popleft() # Remove the leftmost item from the queue and unpack the tuple into two variables — the URL and its layer number.

            if url in visited:
                continue # skip everything below, don't add to all_urls,  all_urls has no duplicates

            visited.add(url)
            all_urls.append(url) # only unique URLs reach here

            obj = Modifiedby(url)

            new_links = [link for link in obj.modifiedby_links if link not in visited]##change the code here if you need to reset the attributes

            queue.extend(new_links)

        print(f"\nTotal URLs collected: {len(all_urls)}")
        return all_urls

    
    def generate_full_graph(self):
        """Generate a full graph from all connected documents"""
        
        all_links = self.collect_all_urls()

        if self.G is None:
            self.G = nx.DiGraph()

        cache = {}

        def process(link):
            """Run process(link) in a separate thread"""
            if link not in cache:
                cache[link] = Modifiedby(link)
            obj = cache[link]
            return obj.create_graph()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process, link) for link in all_links]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Building graph"):
                G_sub = future.result()

                if G_sub is not None and len(G_sub.nodes) > 0:
                    self.G = nx.compose(self.G, G_sub)

        if len(self.G.nodes) > 0:
            self.visualize_graph()

        return self.G
    

    
class Modifies(GraphBuilder):
    def __init__(self, url):
        # Step 1: scrape data
        scraper = DocumentInfoScraper(url)
        attrs, links = scraper.extract_modifies_data()
        document = scraper.get_document_num()

        # Step 2: initialize parent
        super().__init__(attributes_list=attrs, G=None, document=document)

        # Step 3: child-specific attributes
        self.first_url = url
        self.modifies_links = links
        self.scraper = scraper

    def subselect_modifies_attributes(self, relations=None, acts=None, comments=None, subdivisions=None, froms=None, tos=None):
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
    

    def get_links_only(self, url):
        """speed up the process of getting the links"""
        scraper = DocumentInfoScraper(url)
        _, links = scraper.extract_modifies_data()
        return links


    def collect_all_urls(self, max_workers=10):
        """
        Parallel BFS crawler (fast version)
        """

        visited = set()
        queue = deque([self.first_url])
        all_urls = []

        pbar = tqdm(desc="Crawling URLs")

        # thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:

            while queue:
                # batch URLs (important for speed)
                batch = []

                while queue and len(batch) < max_workers:
                    url = queue.popleft()

                    if url not in visited:
                        visited.add(url)
                        batch.append(url)
                        all_urls.append(url)

                if not batch:
                    continue

                # submit all jobs in parallel
                futures = {
                    executor.submit(self.get_links_only, url): url
                    for url in batch
                }

                for future in as_completed(futures):
                    try:
                        links = future.result()
                    except Exception:
                        continue

                    new_links = [link for link in links if link not in visited]
                    queue.extend(new_links)

                    pbar.update(1)

        pbar.close()

        print(f"\nTotal URLs collected: {len(all_urls)}")
        return all_urls
        
    def generate_full_graph(self):
        """Generate a full graph from all connected documents"""
        
        all_links = self.collect_all_urls()

        if self.G is None:
            self.G = nx.DiGraph()

        cache = {}

        def process(link):
            """Run process(link) in a separate thread"""
            if link not in cache:
                cache[link] = Modifies(link)
            obj = cache[link]
            return obj.create_graph()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process, link) for link in all_links]

            for future in tqdm(as_completed(futures), total=len(futures), desc="Building graph"):
                G_sub = future.result()

                if G_sub is not None and len(G_sub.nodes) > 0:
                    self.G = nx.compose(self.G, G_sub)

        if len(self.G.nodes) > 0:
            self.visualize_graph()

        return self.G
    
    
    
    

