import logging
from opensearchpy import OpenSearch
from app.config import OPENSEARCH_CONFIG, INDEX_NAME

logger = logging.getLogger(__name__)

def create_client():
    """Create and return an OpenSearch client"""
    try:
        client = OpenSearch(
            hosts=[{
                'host': OPENSEARCH_CONFIG['host'],
                'port': OPENSEARCH_CONFIG['port']
            }],
            http_auth=(OPENSEARCH_CONFIG['username'], OPENSEARCH_CONFIG['password'])
            if OPENSEARCH_CONFIG['username'] else None,
            use_ssl=OPENSEARCH_CONFIG['use_ssl'],
            verify_certs=OPENSEARCH_CONFIG['verify_certs'],
            ssl_show_warn=False
        )

        # Test connection
        health = client.cluster.health()
        logger.info(f"Connected to OpenSearch cluster: {health['cluster_name']}")
        logger.info(f"Cluster health status: {health['status']}")

        return client
    except Exception as e:
        logger.error(f"Failed to connect to OpenSearch: {str(e)}")
        raise

def create_index_if_not_exists(client, index_name=INDEX_NAME, mapping_file='data/mappings.json'):
    """Create the search index if it doesn't already exist"""
    try:
        import json
        import os

        if client.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' already exists")
            return False

        # Load mapping from file
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r') as f:
                mapping = json.load(f)
        else:
            # Default mapping if file doesn't exist
            mapping = {
                "mappings": {
                    "properties": {
                        "id": {"type": "keyword"},
                        "name": {"type": "text", "analyzer": "standard"},
                        "description": {"type": "text", "analyzer": "standard"},
                        "price": {"type": "float"},
                        "category": {"type": "keyword"},
                        "brand": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "in_stock": {"type": "boolean"}
                    }
                },
                "settings": {
                    "index": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    }
                }
            }

        # Create index with mapping
        client.indices.create(index=index_name, body=mapping)
        logger.info(f"Created index '{index_name}' with mapping")
        return True

    except Exception as e:
        logger.error(f"Failed to create index: {str(e)}")
        raise
