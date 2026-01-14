# tests/test_searcher.py

import pytest
from unittest.mock import MagicMock
from app.searcher import search_products
from app.models import SearchRequest, Product, SearchResponse


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client"""
    client = MagicMock()
    client.search.return_value = {
        "hits": {
            "total": {"value": 5},
            "hits": [
                {
                    "_source": {
                        "id": "1",
                        "name": "Sample Product",
                        "description": "A sample product",
                        "price": 50.0,
                        "category": "Electronics",
                        "brand": "Sample Brand",
                        "in_stock": True,
                        "created_at": "2023-01-01T00:00:00"
                    }
                }
            ]
        },
        "took": 50
    }
    return client


def test_search_products(mock_opensearch_client):
    """Test search functionality"""
    search_request = SearchRequest(
        query="Sample",
        min_price=10.0,
        max_price=100.0,
        category="Electronics",
        brand="Sample Brand",
        page=1,
        size=10
    )

    response = search_products(mock_opensearch_client, search_request)

    assert isinstance(response, SearchResponse)
    assert response.total == 5
    assert len(response.products) == 1
    assert response.products[0].name == "Sample Product"
