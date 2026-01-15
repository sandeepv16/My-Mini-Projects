CREATE TABLE IF NOT EXISTS parsed_table_data (
    id INTEGER,
    document_name VARCHAR(255),
    table_number INTEGER,
    row_number INTEGER,
    column_number INTEGER,
    cell_content TEXT,
    extracted_date VARCHAR(255)
);