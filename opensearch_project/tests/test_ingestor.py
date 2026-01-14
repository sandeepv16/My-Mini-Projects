# tests/test_ingestor.py

import pytest
import json
from unittest.mock import patch, MagicMock
from app.ingestor import load_products_from_file, index_product, bulk_index_products
from app.models import Product


@pytest.fixture
def sample_product():
    """Fixture for a sample product"""
    return Product(
        id="1",
        name="Test Product",
        description="A test product",
        price=99.99,
        category="Electronics",
        brand="Test Brand",
        in_stock=True
    )


def test_load_products_from_file(monkeypatch):
    """Test loading products from a JSON file"""
    sample_data = [
        {
            "id": "1",
            "name": "Test Product",
            "description": "A test product",
            "price": 99.99,
            "category": "Electronics",
            "brand": "Test Brand",
            "in_stock": True,
            "created_at": "2023-01-01T00:00:00"
        }
    ]

    with patch("builtins.open", new_callable=MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(sample_data)
        products = load_products_from_file("mock.json")
        assert len(products) == 1
        assert products[0].name == "Test Product"


def test_index_product(sample_product):
    """Test indexing a single product"""
    mock_client = MagicMock()
    mock_client.index.return_value = {"result": "created"}

    result = index_product(mock_client, sample_product)
    assert result["success"]
    assert result["product_id"] == sample_product.id


def test_bulk_index_products(sample_product):
    """Test bulk indexing of products"""
    mock_client = MagicMock()
    mock_client.helpers.bulk.return_value = (1, 0)  # (success, failed)

    products = [sample_product]
    result = bulk_index_products(mock_client, products)
    assert result["success"]
    assert result["indexed"] == 1
    assert result["failed"] == 0
