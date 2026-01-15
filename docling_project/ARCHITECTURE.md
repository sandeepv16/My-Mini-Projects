# Architecture Overview

## Project Structure

This PDF parsing application is built with a modular architecture designed for processing PDF documents and extracting tabular data. The system uses Docling for document conversion and PostgreSQL for data persistence.

## Core Components

### 1. Application Entry Point (`main.py`)
- **Purpose**: Orchestrates the PDF processing workflow
- **Responsibilities**:
  - Scans the `input_pdfs/` directory for PDF files
  - Initializes database connections
  - Processes each PDF through the parser
  - Stores extracted data in the database

### 2. Configuration Layer (`config/config.py`)
- **Purpose**: Centralizes all configuration settings
- **Features**:
  - Environment variable loading via `python-dotenv`
  - Database connection parameters
  - Input directory configuration
  - Support for different deployment environments

### 3. Parser Module (`src/parser/pdf_parser.py`)
- **Purpose**: Handles PDF document processing and table extraction
- **Key Features**:
  - Uses Docling's `DocumentConverter` for robust PDF parsing
  - Extracts tabular data from PDF documents
  - Handles metadata extraction (creation dates, document info)
  - Normalizes date formats across different PDF sources
  - Maps PDF table structures to database-compatible format

### 4. Data Models (`src/models/table_data.py`)
- **Purpose**: Defines data structures for parsed table information
- **Structure**: Uses Python dataclass for type safety and simplicity
- **Fields**:
  - `document_name`: Source PDF filename
  - `table_number`: Sequential table identifier within document
  - `row_number`: Row position within table
  - `column_number`: Column position within row
  - `cell_content`: Extracted text content
  - `extracted_date`: Normalized date information

### 5. Database Operations (`src/database/db_operations.py`)
- **Purpose**: Manages all database interactions
- **Features**:
  - PostgreSQL connectivity via `psycopg2`
  - Batch insert operations for performance
  - Connection management and error handling
  - Data validation and type conversion

## Data Flow

```
PDF Files → Parser → TableData Objects → Database → PostgreSQL
     ↓         ↓             ↓            ↓          ↓
input_pdfs/  Docling     Data Models   Batch Ops   parsed_table_data
```

1. **Input**: PDF files placed in `input_pdfs/` directory
2. **Processing**: Docling converts PDFs and extracts table structures
3. **Transformation**: Raw table data converted to `TableData` objects
4. **Storage**: Data inserted into PostgreSQL database in batches
5. **Output**: Structured tabular data available for querying

## Database Schema

```sql
CREATE TABLE parsed_table_data (
    id INTEGER,
    document_name VARCHAR(255),
    table_number INTEGER,
    row_number INTEGER,
    column_number INTEGER,
    cell_content TEXT,
    extracted_date VARCHAR(255)
);
```

## Deployment Architecture

### Docker Compose Setup
- **Database Service**: PostgreSQL 15 with persistent volumes
- **Application Service**: Python application container
- **Test Service**: Isolated testing environment

### Container Dependencies
- Application waits for database health check before starting
- Shared volumes for code and data persistence
- Network isolation between services

## Testing Strategy

### Test Structure (`tests/`)
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow validation
- **Database Tests**: Data persistence and retrieval
- **Parser Tests**: PDF processing accuracy

### Test Execution
- Docker-based test environment
- Coverage reporting with `pytest-cov`
- Marker-based test categorization

## Key Design Decisions

### 1. Modular Architecture
- Separation of concerns across different modules
- Easy testing and maintenance
- Clear interfaces between components

### 2. Docker Containerization
- Consistent deployment across environments
- Isolated dependencies and runtime
- Simplified scaling and orchestration

### 3. Database Choice (PostgreSQL)
- ACID compliance for data integrity
- Rich data types and indexing capabilities
- Excellent performance for analytical queries

### 4. Docling Integration
- Modern document processing library
- Handles complex PDF layouts and formats
- Active development and community support

### 5. Batch Processing
- Efficient database operations
- Reduced connection overhead
- Better performance for large datasets

## Performance Considerations

- **Lazy Loading**: DocumentConverter initialized only when needed
- **Batch Inserts**: Multiple records inserted in single operations
- **Connection Pooling**: Efficient database connection management
- **Memory Management**: Processing one PDF at a time

## Extensibility

The architecture supports easy extension through:
- Additional parser formats (beyond PDF)
- New data models for different content types
- Multiple database backends
- REST API endpoints for web integration
- Asynchronous processing for high-volume scenarios