import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.connection import create_client, create_index_if_not_exists
from app.ingestor import load_products_from_file, bulk_index_products
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Script to load product data from a file and index it in OpenSearch"""
    parser = argparse.ArgumentParser(description='Index product data from a JSON file')
    parser.add_argument('--file', type=str, default='data/product_data.json', help='Path to product data JSON file')
    parser.add_argument('--recreate-index', action='store_true', help='Recreate the index before indexing')

    args = parser.parse_args()

    try:
        # Connect to OpenSearch
        client = create_client()

        # Create index if it doesn't exist
        create_index_if_not_exists(client)

        # If requested, delete and recreate the index
        if args.recreate_index:
            from app.config import INDEX_NAME
            if client.indices.exists(index=INDEX_NAME):
                logger.info(f"Deleting existing index '{INDEX_NAME}'")
                client.indices.delete(index=INDEX_NAME)
            create_index_if_not_exists(client)

        # Load products from file
        products = load_products_from_file(args.file)

        if not products:
            logger.error(f"No products found in file: {args.file}")
            sys.exit(1)

        # Bulk index the products
        result = bulk_index_products(client, products)

        if result["success"]:
            logger.info(f"Successfully indexed {result['indexed']} products")
        else:
            logger.warning(f"Indexed {result['indexed']} products, but {result['failed']} failed")

    except Exception as e:
        logger.error(f"Error indexing products: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
