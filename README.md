Dependencies:
- Ollama
- Typeserve-server

Python dependencies:
- bs4
- chardet
- flask
- typesense

Parsing folder is made to scrap and process Bitrefill, yielding data in bitrefill_scraped
keywords_extractor takes this data, uses llama3.2 to extract keywords, yielding bitrefill_keywords
search_app then takes this data, add it into typeserve collections with auto-embedding, has search functions that use exact match + vectorm matched using paraphrase-multilingual-mpnet-base-v2 then run a flask server for the UI
