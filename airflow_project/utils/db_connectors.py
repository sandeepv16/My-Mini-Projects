"""
Database utility functions for MySQL and PostgreSQL operations
"""
import mysql.connector
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class MySQLConnector:
    """MySQL database connector for data operations"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
    
    def get_connection(self):
        """Get MySQL connection"""
        return mysql.connector.connect(**self.config)
    
    def create_table(self, create_statement: str):
        """Execute CREATE TABLE statement"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(create_statement)
            conn.commit()
            logger.info("Table created successfully")
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, batch_size: int = 1000):
        """Insert DataFrame into MySQL table"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Prepare column names
            columns = ', '.join([f"`{col}`" for col in df.columns])
            placeholders = ', '.join(['%s'] * len(df.columns))
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            # Insert in batches
            total_rows = len(df)
            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]
                data = [tuple(row) for row in batch.values]
                cursor.executemany(insert_query, data)
                conn.commit()
                logger.info(f"Inserted batch {i//batch_size + 1}: {len(data)} rows")
            
            logger.info(f"Successfully inserted {total_rows} rows into {table_name}")
            return total_rows
            
        except Exception as e:
            logger.error(f"Error inserting data into MySQL: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str):
        """Execute a SQL query"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            logger.info("Query executed successfully")
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()


class PostgreSQLConnector:
    """PostgreSQL database connector for metadata operations"""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
    
    def get_connection(self):
        """Get PostgreSQL connection"""
        return psycopg2.connect(**self.config)
    
    def insert_file_metadata(self, metadata: Dict[str, Any]) -> int:
        """Insert file metadata and return the inserted ID"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO file_metadata 
            (file_name, file_path, file_size_bytes, row_count, column_count, 
             ingestion_status, target_table, processing_duration_seconds)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            cursor.execute(insert_query, (
                metadata.get('file_name'),
                metadata.get('file_path'),
                metadata.get('file_size_bytes'),
                metadata.get('row_count'),
                metadata.get('column_count'),
                metadata.get('ingestion_status'),
                metadata.get('target_table'),
                metadata.get('processing_duration_seconds')
            ))
            
            file_metadata_id = cursor.fetchone()[0]
            conn.commit()
            
            logger.info(f"Inserted file metadata with ID: {file_metadata_id}")
            return file_metadata_id
            
        except Exception as e:
            logger.error(f"Error inserting file metadata: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_column_metadata(self, file_metadata_id: int, column_metadata_list: List[Dict[str, Any]]):
        """Insert column metadata for a file"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO column_metadata 
            (file_metadata_id, column_name, column_type, null_count, 
             unique_count, min_value, max_value, sample_values)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for col_meta in column_metadata_list:
                cursor.execute(insert_query, (
                    file_metadata_id,
                    col_meta.get('column_name'),
                    col_meta.get('column_type'),
                    col_meta.get('null_count'),
                    col_meta.get('unique_count'),
                    col_meta.get('min_value'),
                    col_meta.get('max_value'),
                    col_meta.get('sample_values')
                ))
            
            conn.commit()
            logger.info(f"Inserted {len(column_metadata_list)} column metadata records")
            
        except Exception as e:
            logger.error(f"Error inserting column metadata: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def insert_data_quality_metrics(self, file_metadata_id: int, metrics: List[Dict[str, Any]]):
        """Insert data quality metrics"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO data_quality_metrics 
            (file_metadata_id, metric_name, metric_value, metric_type)
            VALUES (%s, %s, %s, %s)
            """
            
            for metric in metrics:
                cursor.execute(insert_query, (
                    file_metadata_id,
                    metric.get('metric_name'),
                    metric.get('metric_value'),
                    metric.get('metric_type')
                ))
            
            conn.commit()
            logger.info(f"Inserted {len(metrics)} data quality metrics")
            
        except Exception as e:
            logger.error(f"Error inserting data quality metrics: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    def update_metadata_status(self, file_metadata_id: int, status: str, error_message: str = None):
        """Update the status of file metadata"""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            update_query = """
            UPDATE file_metadata 
            SET ingestion_status = %s, error_message = %s
            WHERE id = %s
            """
            
            cursor.execute(update_query, (status, error_message, file_metadata_id))
            conn.commit()
            
            logger.info(f"Updated metadata status to: {status}")
            
        except Exception as e:
            logger.error(f"Error updating metadata status: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
