import os
import logging
import typesense
from bs4 import BeautifulSoup
import chardet
from flask import Flask, render_template, request
import logging

COLLECTIONS = ['GB', 'BE', 'MX']
MODEL = "ts/paraphrase-multilingual-mpnet-base-v2"
DELETE_CREATE_COLLECTIONS = True

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HTMLSearchEngine:
    def __init__(self, 
                 typesense_host='localhost', 
                 typesense_port=8108):
        """
        Initialize Typesense client and embedding model
        """
        self.client = typesense.Client({
            'nodes': [{
                'host': typesense_host,
                'port': typesense_port,
                'protocol': 'http'
            }],
            'api_key': 'xyz',
            'connection_timeout_seconds': 10
        })
    
        self.collections = COLLECTIONS
    
        self._is_indexing = False

    def create_collection(self, collection_name: str):
        """
        Create Typesense collection schema for a specific collection
        """
        collection_schema = {
            'name': collection_name,
            'fields': [
                {'name': 'document_id', 'type': 'string'},
                {'name': 'filename', 'type': 'string'},
                {'name': 'path', 'type': 'string'},
                {'name': 'text', 'type': 'string'},
                {
                    "name": "embedding",
                    "type": "float[]",
                    "embed": {
                        "from": [
                            "text"
                        ],
                        "model_config": {
                            "model_name": MODEL
                        }
                    }
                },
                {'name': 'text_length', 'type': 'int32'}
            ],
            'default_sorting_field': 'text_length'
        }
        
        try:
            existing_collections = self.client.collections.retrieve()
            existing_collection_names = [collection['name'] for collection in existing_collections]
            
            if collection_name in existing_collection_names:
                logger.info(f"Collection {collection_name} already exists. Skipping creation.")
                return
            
            self.client.collections.create(collection_schema)
            logger.info(f"Collection {collection_name} created successfully")
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise

    def detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                return result['encoding'] or 'utf-8'
        except Exception as e:
            logger.error(f"Encoding detection error for {file_path}: {e}")
            return 'utf-8'

    def extract_text_from_file(self, file_path: str) -> str:
        """
        Extract readable text from file
        """
        try:
            encoding = self.detect_encoding(file_path)
            
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            return soup.get_text(separator=' ', strip=True)
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return ""

    def index_documents(self, documents_path: str, collection_name: str):
        """
        Index all files in the given directory and its subdirectories for a specific collection
        """
        self.create_collection(collection_name)
        
        indexed_count = 0
        
        self._is_indexing = True
        
        for root, dirs, files in os.walk(os.path.join(documents_path, collection_name)):
            for filename in files:
                full_path = os.path.join(root, filename)
                
                text = self.extract_text_from_file(full_path)
                
                if not text.strip():
                    continue
                
                try:
                    document = {
                        'document_id': full_path,
                        'filename': filename,
                        'path': full_path,
                        'text': text,
                        'text_length': len(text)
                    }
                    
                    self.client.collections[collection_name].documents.create(document)
                    indexed_count += 1
                    logger.info(f"Indexed: {full_path}")
                except Exception as e:
                    logger.error(f"Error indexing {full_path}: {e}")
        
        self._is_indexing = False
        
        logger.info(f"Indexing complete for {collection_name}. Total documents indexed: {indexed_count}")

    def multi_search(self, query: str, 
                  collection_name: str, 
                  max_hits: int = 10):
        """
        Perform multi search on a specific collection with exact text matching and vector search
        """
        if not query.strip():
            raise ValueError("Query parameter cannot be empty.")
    
        
        common_params = {
            'collection': collection_name,
            'max_hits': max_hits
        }

        # Prepare multi_search requests with multiple search strategies
        multi_search_requests = {
            'searches': [
                {  # Exact phrase match
                    'q': f'"{query}"',
                    'query_by': 'text',
                    'query_weight': 1.0,
                    'exact_match': 1
                },
                {  # Vector search
                    'q': query,
                    'query_by': 'embedding',
                    "exclude_fields": "embedding"
                }
            ]
        }

        try:
            results = self.client.multi_search.perform(multi_search_requests, common_params)
            
            hit_dict = {}
            
            # Process exact phrase matches first
            for hit in results['results'][0]['hits']:
                doc_id = hit['document']['document_id']
                hit_dict[doc_id] = {
                    'document': hit['document'],
                    'text_match_score': hit['text_match'],
                    'vector_match_score': float('inf')
                }
            
            for hit in results['results'][1]['hits']:
                doc_id = hit['document']['document_id']
                vector_score = hit['vector_distance']
                
                if doc_id in hit_dict:
                    hit_dict[doc_id]['vector_match_score'] = vector_score
                else:
                    hit_dict[doc_id] = {
                        'document': hit['document'],
                        'text_match_score': 0,
                        'vector_match_score': vector_score
                    }
            
            # Convert to sorted list: first by text_match_score, then by vector_match_score
            merged_hits = sorted(
                hit_dict.values(), 
                key=lambda x: (x['text_match_score'], x['vector_match_score']),
                reverse=True
            )[:max_hits]
            
            return merged_hits
        
        except Exception as e:
            logger.error(f"Multi-search error: {e}")
            raise

    def search_all_collections(self, query: str, max_hits: int = 10, exceptName: str = ""):
        """
        Search across all collections
        """
        all_results = []
        
        for collection in self.collections:
            if(collection == exceptName):
                continue
            try:
                collection_results = self.multi_search(query, collection)
                all_results.extend(collection_results)
            except Exception as e:
                logger.error(f"Error searching collection {collection}: {e}")
        
        return sorted(
            all_results, 
            key=lambda x: (x['text_match_score'], x['vector_match_score']),
            reverse=True
        )[:max_hits]

def create_app(search_engine):
    """
    Create and configure Flask application
    """
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        """
        Render the main search page with collection options
        """
        return render_template('index.html', collections=search_engine.collections)
    
    @app.route('/search', methods=['POST'])
    def search():
        """
        Perform search based on user input
        """
        try:
            query = request.form.get('query', '').strip()
            collection_choice = request.form.get('collection', 'all')
            
            if collection_choice == 'all':
                results = search_engine.search_all_collections(query)
            else:
                results = search_engine.multi_search(query, collection_choice)
                results = results[:8]
                all_results = search_engine.search_all_collections(query, exceptName=collection_choice)
                results = results + all_results[:2]
            
            formatted_results = []
            for result in results:
                path_parts = result['document']['path'].split('/')
                collection = path_parts[-2]
                filename = path_parts[-1]
                
                bitrefill_url = f"https://www.bitrefill.com/{collection}/en/gift-cards/{filename}"
                
                # Try to read the original document
                original_doc_path = result['document']['path'].replace('bitrefill_keywords', 'bitrefill_parsed')
                try:
                    with open(original_doc_path, 'r', encoding='utf-8') as f:
                        original_text = f.read()[:600]
                except Exception as e:
                    logger.error(f"Could not read original document: {e}")
                    original_text = result['document']['text'][:600]
                
                formatted_results.append({
                    'collection': collection,
                    'filename': filename,
                    'url': bitrefill_url,
                    'text_match_score': result['text_match_score'],
                    'vector_match_score': result['vector_match_score'],
                    'snippet': result['document']['text'][:600],
                    'original_snippet': original_text
                })
            
            return render_template('results.html', 
                                results=formatted_results, 
                                query=query, 
                                collection=collection_choice)
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return render_template('error.html', error=str(e))
        
    return app

def initialize_search_engine(base_documents_path='./bitrefill_keywords'):
    """
    Separate function to initialize the search engine and index documents
    Returns initialized search engine instance
    """
    search_engine = HTMLSearchEngine()
    
    if(DELETE_CREATE_COLLECTIONS):
        try:
            existing_collections = search_engine.client.collections.retrieve()
            for collection in existing_collections:
                collection_name = collection['name']
                if collection_name in search_engine.collections:
                    print(f"Deleting collection: {collection_name}")
                    search_engine.client.collections[collection_name].delete()
            
            print("Existing collections have been deleted.")
        except Exception as e:
            print(f"Error deleting collections: {e}")
        
        for collection in search_engine.collections:
            search_engine.index_documents(base_documents_path, collection)
        
        logger.info("Indexing complete. Ready for search queries.")
    
    return search_engine



def main():
    base_documents_path = os.environ.get('DOCUMENTS_PATH', './bitrefill_keywords')
    
    search_engine = initialize_search_engine(base_documents_path)
    
    app = create_app(search_engine)
    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()