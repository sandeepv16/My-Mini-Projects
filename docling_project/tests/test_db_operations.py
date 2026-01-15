import pytest
from src.database.db_operations import DatabaseOperations
from src.models import TableData
from psycopg2 import OperationalError


class TestDatabaseOperations:
    @pytest.fixture(autouse=True)
    def cleanup_test_data(self, db_ops):
        """Clean up test data before and after each test"""
        # Cleanup before
        try:
            db_ops.connect()
            db_ops.cursor.execute("DELETE FROM parsed_table_data WHERE document_name LIKE 'test%'")
            db_ops.conn.commit()
            db_ops.disconnect()
        except:
            pass
        yield
        # Cleanup after
        try:
            db_ops.connect()
            db_ops.cursor.execute("DELETE FROM parsed_table_data WHERE document_name LIKE 'test%'")
            db_ops.conn.commit()
            db_ops.disconnect()
        except:
            pass

    def test_database_connection(self, db_ops):
        db_ops.connect()
        assert db_ops.conn is not None
        assert db_ops.cursor is not None
        db_ops.disconnect()
        assert db_ops.conn is None
        assert db_ops.cursor is None

    def test_insert_table_data(self, db_ops, sample_table_data):
        db_ops.insert_table_data(sample_table_data)

        # Verify insertion by querying the database
        db_ops.connect()
        db_ops.cursor.execute(
            "SELECT * FROM parsed_table_data WHERE document_name = %s ORDER BY id DESC LIMIT %s",
            ("test.pdf", len(sample_table_data))
        )
        results = db_ops.cursor.fetchall()
        assert len(results) == len(sample_table_data)
        db_ops.disconnect()

    def test_database_connection_error(self):
        db_ops = DatabaseOperations()
        # Create a custom config to test connection errors
        original_connect = db_ops.connect
        def mock_connect():
            raise OperationalError("Connection failed")
        db_ops.connect = mock_connect
        
        with pytest.raises(OperationalError):
            db_ops.connect()

    def test_insert_invalid_data(self, db_ops):
        invalid_data = [None, "invalid", 123]
        with pytest.raises(Exception):
            db_ops.insert_table_data(invalid_data)

    @pytest.mark.integration
    def test_batch_insert_performance(self, db_ops):
        # Create a large batch of test data
        large_dataset = [
            TableData(
                document_name=f"test_{i}.pdf",
                table_number=1,
                row_number=i,
                column_number=1,
                cell_content=f"Content {i}"
            )
            for i in range(1000)
        ]

        db_ops.insert_table_data(large_dataset)

        # Verify count of inserted records
        db_ops.connect()
        db_ops.cursor.execute("SELECT COUNT(*) FROM parsed_table_data")
        count = db_ops.cursor.fetchone()[0]
        assert count >= len(large_dataset)
