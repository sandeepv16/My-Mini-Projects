import os
import sys
import pytest
import tempfile
from pathlib import Path

# Add parent directory to Python path so src can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.db_operations import DatabaseOperations
from src.models import TableData


@pytest.fixture
def sample_pdf_content():
    # This is a minimal PDF content for testing
    return b"""
    %PDF-1.4
    % Sample PDF with table for testing
    """


@pytest.fixture
def temp_pdf_file(sample_pdf_content):
    # Create a temporary PDF file for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(sample_pdf_content)
        tmp.flush()
        yield tmp.name
    # Cleanup after test
    os.unlink(tmp.name)


@pytest.fixture
def db_ops():
    # Initialize database connection for testing
    db = DatabaseOperations()
    yield db
    # Cleanup after tests
    db.disconnect()


@pytest.fixture
def sample_table_data():
    return [
        TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=1,
            cell_content="Test Content"
        ),
        TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=2,
            cell_content="More Content"
        )
    ]
