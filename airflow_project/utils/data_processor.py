"""
Utility functions for data processing and metadata extraction
"""
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
import logging

logger = logging.getLogger(__name__)


def read_csv_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read CSV file and extract basic metadata
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Tuple of (DataFrame, metadata_dict)
    """
    try:
        start_time = datetime.now()
        
        # Read CSV with pandas
        df = pd.read_csv(file_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Get file size
        import os
        file_size = os.path.getsize(file_path)
        
        # Extract basic metadata
        metadata = {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'file_size_bytes': file_size,
            'row_count': len(df),
            'column_count': len(df.columns),
            'processing_duration_seconds': processing_time,
            'ingestion_status': 'success'
        }
        
        logger.info(f"Successfully read CSV file: {file_path}")
        logger.info(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        
        return df, metadata
        
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {str(e)}")
        raise


def extract_column_metadata(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract detailed metadata for each column in the DataFrame
    
    Args:
        df: pandas DataFrame
        
    Returns:
        List of column metadata dictionaries
    """
    column_metadata_list = []
    
    for column in df.columns:
        try:
            col_data = df[column]
            
            # Determine column type
            col_type = str(col_data.dtype)
            
            # Calculate statistics
            null_count = int(col_data.isna().sum())
            unique_count = int(col_data.nunique())
            
            # Get min/max for numeric and date columns
            min_value = None
            max_value = None
            
            if pd.api.types.is_numeric_dtype(col_data):
                min_value = str(col_data.min()) if not col_data.isna().all() else None
                max_value = str(col_data.max()) if not col_data.isna().all() else None
            elif pd.api.types.is_datetime64_any_dtype(col_data):
                min_value = str(col_data.min()) if not col_data.isna().all() else None
                max_value = str(col_data.max()) if not col_data.isna().all() else None
            
            # Get sample values (first 5 unique non-null values)
            sample_values = col_data.dropna().unique()[:5].tolist()
            # Convert to strings for JSON serialization
            sample_values = [str(val) for val in sample_values]
            
            column_metadata = {
                'column_name': column,
                'column_type': col_type,
                'null_count': null_count,
                'unique_count': unique_count,
                'min_value': min_value,
                'max_value': max_value,
                'sample_values': json.dumps(sample_values)
            }
            
            column_metadata_list.append(column_metadata)
            
        except Exception as e:
            logger.error(f"Error extracting metadata for column {column}: {str(e)}")
            continue
    
    return column_metadata_list


def extract_data_quality_metrics(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Extract data quality metrics from the DataFrame
    
    Args:
        df: pandas DataFrame
        
    Returns:
        List of data quality metric dictionaries
    """
    metrics = []
    
    # Overall completeness
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isna().sum().sum()
    completeness = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 0
    
    metrics.append({
        'metric_name': 'data_completeness_percentage',
        'metric_value': str(round(completeness, 2)),
        'metric_type': 'quality'
    })
    
    # Duplicate rows
    duplicate_count = df.duplicated().sum()
    metrics.append({
        'metric_name': 'duplicate_rows_count',
        'metric_value': str(duplicate_count),
        'metric_type': 'quality'
    })
    
    # Columns with nulls
    columns_with_nulls = (df.isna().sum() > 0).sum()
    metrics.append({
        'metric_name': 'columns_with_nulls',
        'metric_value': str(columns_with_nulls),
        'metric_type': 'quality'
    })
    
    # Memory usage
    memory_usage_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    metrics.append({
        'metric_name': 'memory_usage_mb',
        'metric_value': str(round(memory_usage_mb, 2)),
        'metric_type': 'performance'
    })
    
    return metrics


def prepare_dataframe_for_mysql(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for MySQL insertion
    Clean and transform data as needed
    
    Args:
        df: pandas DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df_clean = df.copy()
    
    # Replace NaN with None for proper NULL handling
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    # Convert column names to lowercase and replace spaces with underscores
    df_clean.columns = [col.lower().replace(' ', '_').replace('-', '_') 
                        for col in df_clean.columns]
    
    # Convert date columns
    for col in df_clean.columns:
        if 'date' in col.lower():
            try:
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            except:
                pass
    
    logger.info(f"Prepared DataFrame with {len(df_clean)} rows for MySQL")
    return df_clean


def get_mysql_table_schema(df: pd.DataFrame, table_name: str) -> str:
    """
    Generate MySQL CREATE TABLE statement from DataFrame schema
    
    Args:
        df: pandas DataFrame
        table_name: Name for the MySQL table
        
    Returns:
        CREATE TABLE SQL statement
    """
    type_mapping = {
        'int64': 'INT',
        'float64': 'DECIMAL(10, 2)',
        'object': 'VARCHAR(255)',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'DATETIME',
        'datetime64[ns, UTC]': 'DATETIME'
    }
    
    columns = []
    columns.append('id INT AUTO_INCREMENT PRIMARY KEY')
    
    for col_name, dtype in df.dtypes.items():
        mysql_type = type_mapping.get(str(dtype), 'TEXT')
        columns.append(f"`{col_name}` {mysql_type}")
    
    columns.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    columns_str = ',\n        '.join(columns)
    create_statement = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {columns_str}
    )
    """
    
    return create_statement
