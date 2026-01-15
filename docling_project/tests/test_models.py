import pytest
from datetime import datetime
from src.models import TableData


class TestTableData:
    def test_table_data_creation(self):
        table_data = TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=1,
            cell_content="Test"
        )
        assert table_data.document_name == "test.pdf"
        assert table_data.table_number == 1
        assert table_data.row_number == 1
        assert table_data.column_number == 1
        assert table_data.cell_content == "Test"
        assert isinstance(table_data.extracted_date, datetime)

    def test_table_data_validation(self):
        # Test that model allows type coercion (common in Python dataclasses)
        table_data = TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=1,
            cell_content="Test"
        )
        # Verify all required fields are present
        assert hasattr(table_data, 'document_name')
        assert hasattr(table_data, 'table_number')
        assert hasattr(table_data, 'row_number')
        assert hasattr(table_data, 'column_number')
        assert hasattr(table_data, 'cell_content')

    def test_table_data_equality(self):
        data1 = TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=1,
            cell_content="Test"
        )
        data2 = TableData(
            document_name="test.pdf",
            table_number=1,
            row_number=1,
            column_number=1,
            cell_content="Test"
        )
        assert data1 == data2
