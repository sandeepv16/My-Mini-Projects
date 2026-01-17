"""
CSV to MySQL and Metadata to PostgreSQL Data Pipeline DAG

This DAG orchestrates the following workflow:
1. Detect CSV files in the input directory
2. Read and validate CSV data
3. Load data into MySQL database
4. Extract and store metadata in PostgreSQL
5. Archive processed files

Can be triggered manually or scheduled automatically.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
import os
import sys
import logging
import shutil
from pathlib import Path

# Add utils to Python path
sys.path.insert(0, '/opt/airflow/utils')

from data_processor import (
    read_csv_file,
    extract_column_metadata,
    extract_data_quality_metrics,
    prepare_dataframe_for_mysql,
    get_mysql_table_schema
)
from db_connectors import MySQLConnector, PostgreSQLConnector

# Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'mysql'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'data_db'),
    'user': os.getenv('MYSQL_USER', 'data_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'data_pass')
}

POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_METADATA_HOST', 'postgres-metadata'),
    'port': int(os.getenv('POSTGRES_METADATA_PORT', 5432)),
    'database': os.getenv('POSTGRES_METADATA_DATABASE', 'metadata_db'),
    'user': os.getenv('POSTGRES_METADATA_USER', 'metadata_user'),
    'password': os.getenv('POSTGRES_METADATA_PASSWORD', 'metadata_pass')
}

INPUT_DIR = '/opt/airflow/data/input'
ARCHIVE_DIR = '/opt/airflow/data/archive'
TARGET_TABLE = 'sales_data'

logger = logging.getLogger(__name__)


def scan_for_csv_files(**context):
    """
    Scan input directory for CSV files
    """
    logger.info(f"Scanning directory: {INPUT_DIR}")
    
    csv_files = []
    if os.path.exists(INPUT_DIR):
        for file in os.listdir(INPUT_DIR):
            if file.endswith('.csv'):
                file_path = os.path.join(INPUT_DIR, file)
                csv_files.append(file_path)
    
    logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")
    
    if not csv_files:
        logger.warning("No CSV files found in input directory")
        return None
    
    # For this example, process the first file
    # In production, you might want to process all files or use dynamic task mapping
    selected_file = csv_files[0]
    context['task_instance'].xcom_push(key='csv_file_path', value=selected_file)
    
    return selected_file


def read_and_validate_csv(**context):
    """
    Read CSV file and perform basic validation
    """
    file_path = context['task_instance'].xcom_pull(key='csv_file_path')
    
    if not file_path:
        raise ValueError("No CSV file path found in XCom")
    
    logger.info(f"Reading CSV file: {file_path}")
    
    # Read CSV and get metadata
    df, metadata = read_csv_file(file_path)
    
    # Validate data
    if len(df) == 0:
        raise ValueError("CSV file is empty")
    
    logger.info(f"Validation successful. Rows: {len(df)}, Columns: {len(df.columns)}")
    
    # Store metadata in XCom
    metadata['target_table'] = TARGET_TABLE
    context['task_instance'].xcom_push(key='file_metadata', value=metadata)
    context['task_instance'].xcom_push(key='dataframe_shape', value={'rows': len(df), 'cols': len(df.columns)})
    
    return True


def load_data_to_mysql(**context):
    """
    Load CSV data into MySQL database
    """
    file_path = context['task_instance'].xcom_pull(key='csv_file_path')
    
    logger.info(f"Loading data from {file_path} into MySQL")
    
    # Read CSV
    df, _ = read_csv_file(file_path)
    
    # Prepare DataFrame for MySQL
    df_clean = prepare_dataframe_for_mysql(df)
    
    # Initialize MySQL connector
    mysql_conn = MySQLConnector(**MYSQL_CONFIG)
    
    # Create table schema
    create_statement = get_mysql_table_schema(df_clean, TARGET_TABLE)
    logger.info(f"Creating table with schema:\n{create_statement}")
    mysql_conn.create_table(create_statement)
    
    # Insert data
    rows_inserted = mysql_conn.insert_dataframe(df_clean, TARGET_TABLE, batch_size=1000)
    
    logger.info(f"Successfully loaded {rows_inserted} rows into MySQL table: {TARGET_TABLE}")
    
    context['task_instance'].xcom_push(key='rows_inserted', value=rows_inserted)
    
    return rows_inserted


def extract_and_store_metadata(**context):
    """
    Extract metadata and store in PostgreSQL
    """
    file_path = context['task_instance'].xcom_pull(key='csv_file_path')
    file_metadata = context['task_instance'].xcom_pull(key='file_metadata')
    
    logger.info(f"Extracting metadata from {file_path}")
    
    # Read CSV
    df, _ = read_csv_file(file_path)
    df_clean = prepare_dataframe_for_mysql(df)
    
    # Initialize PostgreSQL connector
    postgres_conn = PostgreSQLConnector(**POSTGRES_CONFIG)
    
    try:
        # Insert file metadata
        file_metadata_id = postgres_conn.insert_file_metadata(file_metadata)
        logger.info(f"Inserted file metadata with ID: {file_metadata_id}")
        
        # Extract and insert column metadata
        column_metadata = extract_column_metadata(df_clean)
        postgres_conn.insert_column_metadata(file_metadata_id, column_metadata)
        logger.info(f"Inserted {len(column_metadata)} column metadata records")
        
        # Extract and insert data quality metrics
        quality_metrics = extract_data_quality_metrics(df_clean)
        postgres_conn.insert_data_quality_metrics(file_metadata_id, quality_metrics)
        logger.info(f"Inserted {len(quality_metrics)} data quality metrics")
        
        # Update status to completed
        postgres_conn.update_metadata_status(file_metadata_id, 'completed')
        
        context['task_instance'].xcom_push(key='metadata_id', value=file_metadata_id)
        
        return file_metadata_id
        
    except Exception as e:
        logger.error(f"Error storing metadata: {str(e)}")
        # Update status to failed
        if 'file_metadata_id' in locals():
            postgres_conn.update_metadata_status(file_metadata_id, 'failed', str(e))
        raise


def archive_processed_file(**context):
    """
    Move processed CSV file to archive directory
    """
    file_path = context['task_instance'].xcom_pull(key='csv_file_path')
    
    if not file_path or not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return False
    
    # Create archive directory if it doesn't exist
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    # Generate archive filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]
    archive_file_name = f"{name_without_ext}_{timestamp}.csv"
    archive_path = os.path.join(ARCHIVE_DIR, archive_file_name)
    
    # Move file to archive
    shutil.move(file_path, archive_path)
    
    logger.info(f"Archived file: {file_path} -> {archive_path}")
    
    return archive_path


def log_pipeline_summary(**context):
    """
    Log summary of the pipeline execution
    """
    file_path = context['task_instance'].xcom_pull(key='csv_file_path')
    rows_inserted = context['task_instance'].xcom_pull(key='rows_inserted')
    metadata_id = context['task_instance'].xcom_pull(key='metadata_id')
    
    summary = f"""
    ========================================
    DATA PIPELINE EXECUTION SUMMARY
    ========================================
    File Processed: {file_path}
    Rows Inserted to MySQL: {rows_inserted}
    Metadata ID in PostgreSQL: {metadata_id}
    Target Table: {TARGET_TABLE}
    Execution Time: {datetime.now()}
    ========================================
    """
    
    logger.info(summary)
    print(summary)
    
    return summary


# Default arguments for the DAG
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': days_ago(1),
}

# Define the DAG
dag = DAG(
    'csv_to_mysql_with_metadata',
    default_args=default_args,
    description='Ingest CSV data into MySQL and store metadata in PostgreSQL',
    schedule_interval='@daily',  # Runs daily automatically, can also be triggered manually
    catchup=False,
    tags=['data-ingestion', 'csv', 'mysql', 'postgresql', 'metadata'],
)

# Define tasks
start = EmptyOperator(
    task_id='start',
    dag=dag,
)

scan_files = PythonOperator(
    task_id='scan_for_csv_files',
    python_callable=scan_for_csv_files,
    provide_context=True,
    dag=dag,
)

validate_csv = PythonOperator(
    task_id='read_and_validate_csv',
    python_callable=read_and_validate_csv,
    provide_context=True,
    dag=dag,
)

load_mysql = PythonOperator(
    task_id='load_data_to_mysql',
    python_callable=load_data_to_mysql,
    provide_context=True,
    dag=dag,
)

store_metadata = PythonOperator(
    task_id='extract_and_store_metadata',
    python_callable=extract_and_store_metadata,
    provide_context=True,
    dag=dag,
)

archive_file = PythonOperator(
    task_id='archive_processed_file',
    python_callable=archive_processed_file,
    provide_context=True,
    dag=dag,
)

log_summary = PythonOperator(
    task_id='log_pipeline_summary',
    python_callable=log_pipeline_summary,
    provide_context=True,
    dag=dag,
)

end = EmptyOperator(
    task_id='end',
    dag=dag,
)

# Define task dependencies
start >> scan_files >> validate_csv >> [load_mysql, store_metadata]
load_mysql >> archive_file
store_metadata >> archive_file
archive_file >> log_summary >> end
