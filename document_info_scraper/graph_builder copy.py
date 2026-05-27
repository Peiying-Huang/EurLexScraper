import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from document_info_scaper import DocumentInfoScraper
import threading
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s") 
# set different mode to show the logs: DEBUG → INFO → WARNING → ERROR → CRITICAL 

class GraphBuilder:
    def __init__(self, attributes_list, G, document, delay_time_asynchronous_gb):
        self.attributes_list = attributes_list
        self.delay_time_asynchronous = delay_time_asynchronous_gb
        self.document = document

        self.logger = logging.getLogger(__name__)
        self.G = nx.DiGraph()
        self.failed_urls = []

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

    def log_failure(self, url, error, stage="unknown"):
        """Log failed URLs with structured metadata."""

        self.logger.error("[%s] %s -> %s: %s", stage, url, type(error).__name__, error)
        
        self.failed_urls.append(url)
    

    def fetch_all_links(self, url, modifiedby=True):
        """log the failure if the loading is not sucessful and get the links from the modifiedby table"""
        try:
            scraper = DocumentInfoScraper(url, self.delay_time_asynchronous)

            if modifiedby:
                _, by_links = scraper.extract_modifiedby_data()

                scraper.close()

                return by_links
            else:
                _, s_links = scraper.extract_modifies_data()
                
                scraper.close()
                
                return s_links
                

        except Exception as e:
            self.log_failure(
                url=url,
                error=e,
                stage="fetch_all_links"
            )
            return []
        
    def fetch_selected_links(self, url, modifiedby=True, **filter_kwargs):
        """Fetch selected links with internal error capture."""
        try:
            if modifiedby:
                page = Modifiedby(url,self.delay_time_asynchronous)
                _, selected_links1 = page.subselect_modifiedby(**filter_kwargs)
                return selected_links1
            else:
                page = Modifies(url,self.delay_time_asynchronous)
                _, selected_links2 = page.subselect_modifies(**filter_kwargs)
                return selected_links2
            
        except Exception as e:
            self.log_failure(
                url=url,
                error=e,
                stage="fetch_selected_links"
            )
            return []
                  

class Modifiedby(GraphBuilder):
    def __init__(self, url, delay_time_asynchronous_max=0.01):
        # Step 1: scrape data
        scraper = DocumentInfoScraper(url, delay_time_asynchronous_max)
        attrs, links = scraper.extract_modifiedby_data()
        document = scraper.get_document_num()
        delay_time_asynchronous_gb = delay_time_asynchronous_max

        # Step 2: initialize parent
        super().__init__(attributes_list=attrs, G=None, document=document, delay_time_asynchronous_gb = delay_time_asynchronous_gb)

        # Step 3: child-specific attributes
        self.first_url = url
        self.attrs = attrs
        self.modifiedby_links = links
        self.scraper = scraper


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
                page_operations = {
                    executor.submit(self.fetch_all_links, url): url
                    for url in batch
                }

                for page in as_completed(page_operations):
                    try:
                        sub_links = page.result()
                    except Exception:
                        continue

                    sub_urls = [sub_link for sub_link in sub_links if sub_link not in visited]
                    queue.extend(sub_urls)

                    pbar.update(1)

        pbar.close()

        num_of_urls = len(all_urls) 
        self.logger.info("Total URLs collected: %s", num_of_urls)

        return all_urls


    def generate_full_graph(self, urls, visualize = False, progress = False):

        """Generate a full graph from all connected documents"""
        
        all_links = urls

        if self.G is None:
            self.G = nx.DiGraph()

        cache = {}
    
        lock = threading.Lock()

        def get_data(link):
            with lock:
                if link not in cache:
                    cache[link] = Modifiedby(link, self.delay_time_asynchronous)
                obj = cache[link]

            return obj.create_graph()

        with ThreadPoolExecutor(max_workers=10) as executor:
            page_operations = [executor.submit(get_data, link) for link in all_links]

            for page in tqdm(as_completed(page_operations), total=len(page_operations), desc="Building graph"):
                G_sub = page.result()

                if progress:
                    num_of_nodes = len(G_sub)
                    self.logger.info("The number of nodes of graph: %s", num_of_nodes)

                if G_sub is not None and len(G_sub.nodes) > 0:
                    self.G = nx.compose(self.G, G_sub)
        
        if visualize:
            if len(self.G.nodes) > 0:
                self.visualize_graph()

        return self.G

    def subselect_modifiedby(self, relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]):
        """
        Enter any values in the 'relation', 'act', 'comment', 'subdivision', 'from', 'to'.
        Returns rows matching ALL entered filter values.
        """

        filters = {
            'Relation': relations,
            'Act': acts,
            'Comment': comments,
            'Subdivision concerned': subdivisions,
            'From': froms,
            'To': tos,
        }

        # Keep track of original indices so we can sync the links list
        indexed_result = list(enumerate(self.attrs)) # -->[(index, metadata of one row), ..]

        for question,answer  in filters.items():
            if answer: # if the values in the filter is not empty
                indexed_result = [(i, row_dict) for i, row_dict in indexed_result if row_dict[question] in answer] # row_dict[question]: the value of the 'question' in the row dict

        # Unzip indices and metadata rows
        if indexed_result:
            matched_indices, matched_metadata = zip(*indexed_result)
        else:
            matched_indices, matched_metadata = [], []

        self.attrs = list(matched_metadata) # re-initialized???
        selected_links = [self.modifiedby_links[i] for i in matched_indices] # re-initialized???
        
        return self.attrs, selected_links
    
    def collect_selected_urls(self, max_workers=10, **filter_kwargs):
        """
        add **filter_kwargs (relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]) to subselect what you want;
        set max_workers to open the number of websites at the same moment
        
        """
        visited = set()
        queue = deque([self.first_url])
        all_selected_urls = []

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
                        all_selected_urls.append(url)

                if not batch:
                    continue

                # submit all jobs in parallel
                page_operations = {
                    executor.submit(self.fetch_selected_links, url,**filter_kwargs): url
                    for url in batch
                }

                for page in as_completed(page_operations):
                    try:
                        links = page.result()
                    except Exception:
                        continue

                    sub_links = [link for link in links if link not in visited]
                    queue.extend(sub_links)

                    pbar.update(1)

        pbar.close()

        num_of_urls = len(all_selected_urls) 
        self.logger.info("Total URLs collected: %s", num_of_urls)

        return all_selected_urls

    
class Modifies(GraphBuilder):
    def __init__(self, url,delay_time_asynchronous_max=1):
        # Step 1: scrape data
        scraper = DocumentInfoScraper(url,delay_time_asynchronous_max)
        attrs, links = scraper.extract_modifies_data()
        document = scraper.get_document_num()
        delay_time_asynchronous_gb = delay_time_asynchronous_max

        # Step 2: initialize parent
        super().__init__(attributes_list=attrs, G=None, document=document, delay_time_asynchronous_gb = delay_time_asynchronous_gb)

        # Step 3: child-specific attributes
        self.first_url = url
        self.attrs = attrs
        self.modifies_links = links
        self.scraper = scraper
       

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
                batch = [] #batch stores the links when it open multiple websites

                while queue and len(batch) < max_workers:
                    url = queue.popleft()

                    if url not in visited:
                        visited.add(url)
                        batch.append(url)
                        all_urls.append(url)

                if not batch:
                    continue

                # submit all jobs in parallel
                page_operations = {
                    executor.submit(self.fetch_all_links, url, modifiedby = False): url
                    for url in batch
                }
                
                for page in as_completed(page_operations):
                    try:
                        sub_links = page.result()
                    except Exception:
                        
                        continue

                    sub_urls = [sub_link for sub_link in sub_links if sub_link not in visited]
                    queue.extend(sub_urls)

                    pbar.update(1)

        pbar.close()

        num_of_urls = len(all_urls) 
        self.logger.info("Total URLs collected: %s", num_of_urls)
        return all_urls
        
    def generate_full_graph(self, urls, max_workers=10, visualize = False, progress = True):

        """Generate a full graph from all connected documents"""
        
        all_links = urls

        if self.G is None:
            self.G = nx.DiGraph()

        cache = {}
    
        lock = threading.Lock()

        def get_data(link):
            with lock:
                if link not in cache:
                    cache[link] = Modifiedby(link, self.delay_time_asynchronous)
                obj = cache[link]

            return obj.create_graph()
       
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            page_operations = [executor.submit(self.get_data, link) for link in all_links]

            for page in tqdm(as_completed(page_operations), total=len(page_operations), desc="Building graph"):
                G_sub = page.result()

                if progress:
                    num_of_nodes = len(G_sub)
                    self.logger.info("The number of nodes of graph: %s", num_of_nodes)

                if G_sub is not None and len(G_sub.nodes) > 0:
                    self.G = nx.compose(self.G, G_sub)
        
        if visualize:
            if len(self.G.nodes) > 0:
                self.visualize_graph()

        return self.G


    def subselect_modifies(self, relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]):
        """
        Enter any values in the 'relation', 'act', 'comment', 'subdivision', 'from', 'to'.
        Returns rows (metadata + links) matching ALL entered filter values.
        """
        filters = {
            'Relation': relations,
            'Act': acts,
            'Comment': comments,
            'Subdivision concerned': subdivisions,
            'From': froms,
            'To': tos,
        }

        # Keep track of original indices so we can sync the links list
        indexed_result = list(enumerate(self.attrs))

        for question,answer  in filters.items():
            if answer: # if the values in the filter is not empty
                indexed_result = [(i, row_dict) for i, row_dict in indexed_result if row_dict[question] in answer] # row_dict[question]: the value of the 'question' in the row dict
       
        # Unzip indices and metadata rows
        if indexed_result:
            matched_indices, matched_metadata = zip(*indexed_result)
        else:
            matched_indices, matched_metadata = [], []

        self.attrs = list(matched_metadata)
        selected_links = [self.modifiedby_links[i] for i in matched_indices] # re-initialized???
        
        return self.attrs, selected_links
    
    def collect_selected_urls(self, max_workers=10, **filter_kwargs):
        """
        add **filter_kwargs (relations=[], acts=[], comments=[], subdivisions=[], froms=[], tos=[]) to subselect what you want;
        set max_workers to open the number of websites at the same moment
        
        """
        visited = set()
        queue = deque([self.first_url])
        all_selected_urls = []

        pbar = tqdm(desc="Crawling URLs") #show the much time to excute the code

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
                        all_selected_urls.append(url)

                if not batch:
                    continue

                # submit all jobs in parallel
                page_operations = {
                    executor.submit(self.fetch_selected_links, url, modifiedby= False,**filter_kwargs): url
                    for url in batch
                }

                for page in as_completed(page_operations):
                    try:
                        links = page.result()
                    except Exception:
                        continue

                    sub_links = [link for link in links if link not in visited] #sublinks from the kid website of the first url
                    queue.extend(sub_links)

                    pbar.update(1)

        pbar.close()

        num_of_urls = len(all_selected_urls) 
        self.logger.info("Total URLs collected: %s", num_of_urls)
        
        return all_selected_urls

    
