# Architecture Overview

## High-Level Architecture

This is a production-grade e-commerce product search application built with Python and OpenSearch. The system is designed to provide powerful search capabilities for product catalogs with features like full-text search, fuzzy matching, filtering, and pagination.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │   FastAPI App   │    │   OpenSearch    │
│                 │◄──►│                 │◄──►│                 │
│ - REST API      │    │ - Search API    │    │ - Full-text     │
│ - JSON Requests │    │ - Data Ingestion│    │   Search        │
│ - Results       │    │ - Product Mgmt  │    │ - Fuzzy Search  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Data Sources  │
                       │                 │
                       │ - JSON Files    │
                       │ - API Endpoints │
                       └─────────────────┘
```

## Components

### 1. FastAPI Application (`app/`)
The core web application built with FastAPI, providing REST API endpoints for search and data management.

#### Key Modules:
- **`api.py`**: Defines REST API endpoints
  - `POST /search`: Product search with filters
  - `POST /products`: Single product indexing
  - `POST /products/bulk`: Bulk product indexing
  - `POST /products/load-from-file`: Load products from JSON file

- **`connection.py`**: OpenSearch client management
  - Creates and configures OpenSearch client
  - Handles index creation with mappings
  - Connection health checks

- **`searcher.py`**: Search logic implementation
  - Builds complex OpenSearch queries
  - Supports text search with fuzzy matching
  - Implements filtering (price, category, brand)
  - Handles pagination and sorting

- **`ingestor.py`**: Data ingestion functionality
  - Single and bulk product indexing
  - Data validation and transformation
  - Error handling for indexing operations

- **`models.py`**: Data models and schemas
  - Pydantic models for request/response validation
  - Product data structure definitions

- **`config.py`**: Configuration management
  - Environment-based settings
  - OpenSearch connection parameters

### 2. OpenSearch Cluster
The search engine backend providing:
- Full-text search with relevance scoring
- Fuzzy text search for typo tolerance
- Structured data storage with mappings
- Real-time indexing and search

### 3. Data Layer (`data/`)
- **`mappings.json`**: OpenSearch index mappings defining field types and analyzers
- **`product_data.json`**: Sample product data for testing and demonstration

### 4. Scripts (`scripts/`)
Utility scripts for development and operations:
- **`generate_data.py`**: Generate sample product data
- **`index_data.py`**: Bulk index data into OpenSearch
- **`search_cli.py`**: Command-line search interface

### 5. Testing (`tests/`)
Unit tests for core functionality:
- Connection testing
- Data ingestion validation
- Search functionality verification

## Data Flow

### Product Indexing Flow:
1. Product data received via API or loaded from file
2. Data validated using Pydantic models
3. Products transformed to OpenSearch documents
4. Bulk indexing performed with error handling
5. Index refreshed for immediate search availability

### Search Flow:
1. Search request received with query and filters
2. Query built with multi-match for text search
3. Filters applied (price range, category, brand)
4. Pagination and sorting parameters added
5. OpenSearch query executed
6. Results formatted and returned as JSON

## Deployment Architecture

The application is containerized using Docker for consistent deployment:

```
┌─────────────────────────────────────┐
│           Docker Compose            │
├─────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐     │
│ │OpenSearch   │ │Dashboards   │     │
│ │Port: 9200   │ │Port: 5601   │     │
│ └─────────────┘ └─────────────┘     │
│                                     │
│ ┌─────────────┐                     │
│ │Search App   │                     │
│ │Port: 8000   │                     │
│ └─────────────┘                     │
└─────────────────────────────────────┘
```

### Services:
- **OpenSearch**: Search engine (single-node for development)
- **OpenSearch Dashboards**: Web UI for data exploration
- **Search App**: Python FastAPI application

## Technology Stack

- **Backend**: Python 3.8+, FastAPI
- **Search Engine**: OpenSearch 2.6.0
- **Containerization**: Docker, Docker Compose
- **Data Validation**: Pydantic
- **HTTP Client**: OpenSearch Python client
- **Testing**: pytest

## Security Considerations

- Environment-based configuration
- Input validation with Pydantic models
- OpenSearch security plugin disabled for development
- Container isolation with Docker

## Scalability

- OpenSearch supports horizontal scaling
- FastAPI is asynchronous and performant
- Bulk operations for efficient data ingestion
- Pagination for large result sets

## Monitoring and Logging

- Structured logging with Python logging module
- OpenSearch cluster health monitoring
- Error handling and reporting in API responses
- Docker container logs for debugging</content>
<parameter name="filePath">c:\Users\ADMIN\SV_Practice_06102024\Self_Learning\MyProjects\opensearch_project\ARCHITECTURE.md