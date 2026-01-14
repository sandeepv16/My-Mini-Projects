import argparse
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.connection import create_client
from app.models import SearchRequest
from app.searcher import search_products
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Command-line interface for searching products"""
    parser = argparse.ArgumentParser(description='Search products in OpenSearch')
    parser.add_argument('query', type=str, nargs='?', default="", help='Search query')
    parser.add_argument('--min-price', type=float, default=0.0, help='Minimum price filter')
    parser.add_argument('--max-price', type=float, default=float('inf'), help='Maximum price filter')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--brand', type=str, help='Filter by brand')
    parser.add_argument('--sort-by', type=str, help='Sort by field (e.g., "price:asc", "name:desc")')
    parser.add_argument('--page', type=int, default=1, help='Page number')
    parser.add_argument('--size', type=int, default=10, help='Results per page')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')

    args = parser.parse_args()

    # Create search request from CLI arguments
    request = SearchRequest(
        query=args.query,
        min_price=args.min_price,
        max_price=args.max_price,
        category=args.category,
        brand=args.brand,
        sort_by=args.sort_by,
        page=args.page,
        size=args.size
    )

    try:
        # Connect to OpenSearch
        client = create_client()

        # Execute search
        response = search_products(client, request)

        if args.json:
            # Output as JSON
            print(json.dumps(response.dict(), indent=2))
        else:
            # Pretty print results
            print(f"\nFound {response.total} products (page {response.page} of {response.total_pages})")
            print(f"Search took {response.took_ms}ms\n")

            for i, product in enumerate(response.products, 1):
                print(f"{i}. {product.name}")
                print(f"   Price: ${product.price:.2f}")
                print(f"   Brand: {product.brand}")
                print(f"   Category: {product.category}")
                print(f"   {'In stock' if product.in_stock else 'Out of stock'}")
                print()

            # Show pagination info
            if response.total_pages > 1:
                print(f"Page {response.page} of {response.total_pages}")

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
