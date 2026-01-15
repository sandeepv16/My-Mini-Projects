import psycopg2
from psycopg2.extras import execute_batch
from config.config import DB_CONFIG
from src.models.table_data import TableData


class DatabaseOperations:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"Error connecting to database: {e}")
            raise

    def disconnect(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def insert_table_data(self, table_data_list: list[TableData]):
        try:
            self.connect()
            insert_query = """
                INSERT INTO parsed_table_data 
                (id, document_name, table_number, row_number, column_number, cell_content, extracted_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            data_tuples = []
            for idx, data in enumerate(table_data_list, 1):
                # Helper to safely convert values to int or None
                def _safe_int(value):
                    if value is None:
                        return None
                    # allow numeric types through
                    if isinstance(value, int):
                        return value
                    s = str(value).strip()
                    if s == "":
                        return None
                    try:
                        return int(s)
                    except Exception:
                        return None

                # Typecast to match database schema, using None for missing/invalid integers
                data_tuples.append((
                    int(idx),  # id: INTEGER (auto-increment)
                    str(data.document_name) if data.document_name else "",  # document_name: VARCHAR(255)
                    _safe_int(data.table_number),  # table_number: INTEGER or NULL
                    _safe_int(data.row_number),  # row_number: INTEGER or NULL
                    _safe_int(data.column_number),  # column_number: INTEGER or NULL
                    str(data.cell_content) if data.cell_content else "",  # cell_content: TEXT
                    str(data.extracted_date) if data.extracted_date else ""  # extracted_date: VARCHAR(255)
                ))

            execute_batch(self.cursor, insert_query, data_tuples)
            self.conn.commit()
            print(f"Successfully inserted {len(data_tuples)} rows into database")
        except Exception as e:
            print(f"Error inserting data: {e}")
            self.conn.rollback()
            raise
        finally:
            self.disconnect()

    def document_already_processed(self, document_name: str) -> bool:
        """Return True if the source filename has been recorded in `processed_files`.

        Uses a lightweight `processed_files` table to track which input files
        have been processed by `main.py` (prevents duplicate processing when the
        script runs multiple times or the container restarts).
        """
        try:
            # ensure tracking table exists
            self._ensure_processed_table()
            self.connect()
            query = "SELECT EXISTS(SELECT 1 FROM processed_files WHERE filename = %s)"
            self.cursor.execute(query, (document_name,))
            exists = self.cursor.fetchone()[0]
            return bool(exists)
        except Exception as e:
            print(f"Error checking document processed state: {e}")
            return False
        finally:
            self.disconnect()

    def mark_document_processed(self, document_name: str):
        """Record that `document_name` has been processed."""
        try:
            self._ensure_processed_table()
            self.connect()
            insert = "INSERT INTO processed_files (filename) VALUES (%s) ON CONFLICT (filename) DO NOTHING"
            self.cursor.execute(insert, (document_name,))
            self.conn.commit()
        except Exception as e:
            print(f"Error marking document processed: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
        finally:
            self.disconnect()

    def _ensure_processed_table(self):
        try:
            self.connect()
            create = """
            CREATE TABLE IF NOT EXISTS processed_files (
                filename VARCHAR(512) PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT NOW()
            )
            """
            self.cursor.execute(create)
            self.conn.commit()
        except Exception as e:
            print(f"Error creating processed_files table: {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
        finally:
            self.disconnect()
