CREATE TABLE IF NOT EXISTS parsed_table_data (
    id SERIAL PRIMARY KEY,
    document_name VARCHAR(255) NOT NULL,
    table_number INTEGER,
    row_number INTEGER,
    column_number INTEGER,
    cell_content TEXT,
    extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);