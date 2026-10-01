from elasticsearch import AsyncElasticsearch
from app.config import settings

es_client = AsyncElasticsearch(settings.ELASTICSEARCH_URL)