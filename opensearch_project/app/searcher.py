import logging
from opensearchpy import OpenSearch
from app.config import INDEX_NAME
from app.models import SearchRequest, SearchResponse, Product
import math

logger = logging.getLogger(__name__)

def search_products(client: OpenSearch, request: SearchRequest) -> SearchResponse:
    """
    Search for products with support for:
    - Text search with fuzzy matching (handles typos)
    - Price range filtering
    - Category and brand filtering
    - Pagination
    - Sorting
    """
    try:
        # Build query
        query_parts = []

        # Text search with fuzzy matching
        if request.query:
            query_parts.append({
                "multi_match": {
                    "query": request.query,
                    "fields": ["name^3", "description"],  # Boost name matches
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            })
        else:
            # If no query provided, match all documents
            query_parts.append({"match_all": {}})

        # Prepare filters
        filters = []

        # Price range filter
        price_range = {"range": {"price": {}}}
        if request.min_price is not None:
            price_range["range"]["price"]["gte"] = request.min_price
        if request.max_price is not None and request.max_price != float('inf'):
            price_range["range"]["price"]["lte"] = request.max_price

        filters.append(price_range)

        # Category filter
        if request.category:
            filters.append({"term": {"category": request.category}})

        # Brand filter
        if request.brand:
            filters.append({"term": {"brand": request.brand}})

        # Calculate pagination
        from_value = (request.page - 1) * request.size

        # Build sort options
        sort_options = []
        if request.sort_by:
            field, direction = request.sort_by.split(':') if ':' in request.sort_by else (request.sort_by, 'asc')
            sort_options.append({field: {"order": direction}})

        # Construct the complete query
        body = {
            "query": {
                "bool": {
                    "must": query_parts,
                    "filter": filters
                }
            },
            "from": from_value,
            "size": request.size
        }

        if sort_options:
            body["sort"] = sort_options

        # Execute search
        logger.debug(f"Executing search query: {body}")
        response = client.search(index=INDEX_NAME, body=body)

        # Parse results
        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]
        took = response["took"]

        # Convert to Product objects
        products = []
        for hit in hits:
            source = hit["_source"]
            products.append(Product(**source))

        # Calculate total pages
        total_pages = math.ceil(total / request.size) if total > 0 else 0

        return SearchResponse(
            total=total,
            took_ms=took,
            products=products,
            page=request.page,
            size=request.size,
            total_pages=total_pages
        )

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise

def advanced_search(client, index, term, min_p, max_p):
    """Legacy search function for backward compatibility"""
    query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "name": {
                                "query": term,
                                "fuzziness": "AUTO",
                                "operator": "or"
                            }
                        }
                    }
                ],
                "filter": [
                    {"range": {"price": {"gte": min_p, "lte": max_p}}}
                ]
            }
        }
    }
    return client.search(index=index, body=query)
