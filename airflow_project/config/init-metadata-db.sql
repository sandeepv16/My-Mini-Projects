-- PostgreSQL Metadata Initialization Script
-- Create metadata tables to track data ingestion

CREATE TABLE IF NOT EXISTS file_metadata (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes BIGINT,
    row_count INTEGER,
    column_count INTEGER,
    columns_info JSONB,
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ingestion_status VARCHAR(50),
    target_table VARCHAR(255),
    error_message TEXT,
    processing_duration_seconds DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS column_metadata (
    id SERIAL PRIMARY KEY,
    file_metadata_id INTEGER REFERENCES file_metadata(id),
    column_name VARCHAR(255) NOT NULL,
    column_type VARCHAR(100),
    null_count INTEGER,
    unique_count INTEGER,
    min_value TEXT,
    max_value TEXT,
    sample_values JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id SERIAL PRIMARY KEY,
    file_metadata_id INTEGER REFERENCES file_metadata(id),
    metric_name VARCHAR(255) NOT NULL,
    metric_value TEXT,
    metric_type VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_file_name ON file_metadata(file_name);
CREATE INDEX idx_ingestion_timestamp ON file_metadata(ingestion_timestamp);
CREATE INDEX idx_ingestion_status ON file_metadata(ingestion_status);
CREATE INDEX idx_file_metadata_id ON column_metadata(file_metadata_id);
