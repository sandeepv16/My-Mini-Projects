-- MySQL Initialization Script
-- Create the main data table for CSV data

USE data_db;

-- Sample table structure - will be created dynamically by the DAG
-- This is just a template for reference
CREATE TABLE IF NOT EXISTS sales_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id VARCHAR(50),
    customer_id VARCHAR(50),
    product_name VARCHAR(255),
    quantity INT,
    price DECIMAL(10, 2),
    transaction_date DATE,
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create an index for better query performance
CREATE INDEX idx_transaction_date ON sales_data(transaction_date);
CREATE INDEX idx_customer_id ON sales_data(customer_id);
