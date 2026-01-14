# tests/test_connection.py

import pytest
from unittest.mock import patch, MagicMock
from app.connection import create_client, create_index_if_not_exists


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client"""
    client = MagicMock()
    client.indices.exists.side_effect = lambda index: False
    return client


def test_create_client_success():
    """Test successful OpenSearch client creation"""
    with patch("app.connection.OpenSearch") as mock_opensearch:
        mock_opensearch.return_value.cluster.health.return_value = {
            "cluster_name": "mock_cluster",
            "status": "green",
        }
        client = create_client()
        assert client is not None


def test_create_index_if_not_exists(mock_opensearch_client):
    """Test index creation when it doesn't exist"""
    with patch("app.connection.create_client", return_value=mock_opensearch_client):
        result = create_index_if_not_exists(mock_opensearch_client)
        assert result is True
        mock_opensearch_client.indices.create.assert_called_once()


def test_create_index_already_exists(mock_opensearch_client):
    """Test scenario where index already exists"""
    mock_opensearch_client.indices.exists.side_effect = lambda index: True
    with patch("app.connection.create_client", return_value=mock_opensearch_client):
        result = create_index_if_not_exists(mock_opensearch_client)
        assert not result
        mock_opensearch_client.indices.create.assert_not_called()
