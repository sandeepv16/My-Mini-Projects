import json
import logging
from typing import List, Dict, Any
import os
from opensearchpy import OpenSearch, helpers
from app.models import Product
from app.config import INDEX_NAME

logger = logging.getLogger(__name__)

def bulk_index_products(client: OpenSearch, products: List[Product]) -> Dict[str, Any]:
    """Bulk index multiple products into OpenSearch"""
    try:
        actions = []
        for product in products:
            product_dict = product.to_dict()
            action = {
                "_index": INDEX_NAME,
                "_id": product_dict["id"],
                "_source": product_dict
            }
            actions.append(action)

        if not actions:
            logger.warning("No products to index")
            return {"success": True, "indexed": 0, "failed": 0}

        # Perform bulk indexing
        success, failed = helpers.bulk(client, actions, stats_only=True)
        logger.info(f"Indexed {success} products, failed: {failed}")

        return {
            "success": failed == 0,
            "indexed": success,
            "failed": failed
        }

    except Exception as e:
        logger.error(f"Bulk indexing error: {str(e)}")
        raise

def index_product(client: OpenSearch, product: Product) -> Dict[str, Any]:
    """Index a single product into OpenSearch"""
    try:
        product_dict = product.to_dict()
        response = client.index(
            index=INDEX_NAME,
            id=product_dict["id"],
            body=product_dict,
            refresh=True  # Make document immediately available for search
        )

        logger.info(f"Indexed product {product.id} with result: {response['result']}")
        return {"success": True, "product_id": product.id, "result": response["result"]}

    except Exception as e:
        logger.error(f"Indexing error for product {product.id}: {str(e)}")
        raise

def load_products_from_file(filename: str = 'data/product_data.json') -> List[Product]:
    """Load products from a JSON file"""
    try:
        if not os.path.exists(filename):
            logger.warning(f"Product data file not found: {filename}")
            return []

        with open(filename, 'r') as f:
            product_dicts = json.load(f)

        products = [Product(**p) for p in product_dicts]
        logger.info(f"Loaded {len(products)} products from {filename}")
        return products

    except Exception as e:
        logger.error(f"Error loading products from file: {str(e)}")
        raise
