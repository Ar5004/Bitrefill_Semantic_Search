#### Dependencies:
- Ollama
- Typesense-server

#### Python dependencies:
- bs4
- chardet
- flask
- typesense

#### Instructions 
`selenium_scraper` scraps Bitrefill's website, yielding data in `bitrefill_scraped`.  
`parse_data` takes this data and extracts the initial dataset for further processing on each document (in the example only the description), yielding `bitrefill_parsed`  
`keywords_extractor` takes this data, uses `llama3.2` to extract keywords, yielding `bitrefill_keywords`
`search_app` then takes this data, add it into typeserve collections with auto-embedding, has search functions that use exact match + vectorm matched using `paraphrase-multilingual-mpnet-base-v2` then run a flask server for the UI  

> [!NOTE]
> Because of caching mechanism when deleting a Collection the system will take few minutes to allow a new collection to be created using the same name
> When the embeds don't change, run with DELETE_CREATE_COLLECTIONS = True to avoid this inconvenience
