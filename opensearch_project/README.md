# E-Commerce Product Search with OpenSearch

A production-grade Python application that demonstrates the implementation of OpenSearch for an e-commerce product catalog.

This project serves as a comprehensive example of building a scalable search system for e-commerce applications. It functions as a REST API-powered service that enables powerful product search capabilities, utilizing OpenSearch as the underlying search engine. Data flows from various sources—such as JSON files or direct API inputs—through a structured ingestion pipeline where products are validated, transformed, and indexed into OpenSearch. When search requests are made, the system processes queries with fuzzy matching, filters, and pagination, retrieving relevant results from the indexed data and returning them to clients in a structured JSON format, ensuring fast and accurate product discovery for e-commerce platforms.

## Features

- **Powerful Search Capabilities**:
    - Full-text search with relevance scoring
    - Fuzzy text search to handle typos
    - Price range filtering
    - Category and brand filters
    - Sorting and pagination

- **Data Management**:
    - Bulk data ingestion
    - Sample data generation
    - OpenSearch index configuration

- **Production-Ready Architecture**:
    - Containerized with Docker
    - Environment-based configuration
    - Logging
    - REST API

## Project Structure
e-commerce-search/ ├── app/ # Application code ├── data/ # Sample data and mappings ├── scripts/ # Utility scripts ├── tests/ # Unit tests ├── docker-compose.yml # Docker setup ├── Dockerfile # Python app container ├── .env.example # Environment variables template ├── requirements.txt # Dependencies ├── main.py # Application entry point └── README.md # Documentation

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)

### Running with Docker Compose

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/e-commerce-search.git
   cd e-commerce-search
   ```

2. Create environment file:
   ```
   cp .env.example .env
   ```

3. Start the services:
   ```
   docker-compose up -d
   ```

4. Generate sample data:
   ```
   docker-compose exec app python scripts/generate_data.py
   ```

5. Index the sample data:
   ```
   docker-compose exec app python scripts/index_data.py
   ```

6. Access the API at http://localhost:8000 and OpenSearch Dashboards at http://localhost:5601

### Using the Search CLI

Search for products with a query:
python scripts/search_cli.py "camera"

Search with filters:
python scripts/search_cli.py "shirt" --min-price 20 --max-price 50 --category "Clothing" --brand "Nike"

### API Endpoints

For interactive API testing, visit the [FastAPI Documentation](http://localhost:8000/docs).

#### GET /
Returns API information.

**Example:**
```bash
curl http://localhost:8000/
```

#### POST /search
Search for products with optional filters.

**Parameters:**
- `query` (string): Search term
- `min_price`, `max_price` (float): Price range
- `category`, `brand` (string): Filters
- `limit` (int): Max results (default: 10)

**Example - Basic Search:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "camera"}'
```

**Example - Search with Filters:**
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "shirt",
    "min_price": 20,
    "max_price": 50,
    "category": "Clothing",
    "limit": 5
  }'
```

#### POST /products
Create a single product.

**Example:**
```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "prod-001",
    "name": "Wireless Headphones",
    "description": "High-quality wireless headphones",
    "price": 99.99,
    "category": "Electronics",
    "brand": "AudioTech",
    "in_stock": true
  }'
```

#### POST /products/bulk
Create multiple products at once.

**Example:**
```bash
curl -X POST "http://localhost:8000/products/bulk" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "prod-002",
      "name": "Smart Watch",
      "description": "Fitness tracking smartwatch",
      "price": 199.99,
      "category": "Electronics",
      "brand": "TechFit",
      "in_stock": true
    },
    {
      "id": "prod-003",
      "name": "Running Shoes",
      "description": "Comfortable running shoes",
      "price": 79.99,
      "category": "Sports",
      "brand": "RunPro",
      "in_stock": true
    }
  ]'
```

#### POST /products/load-from-file
Load products from the data file (`data/product_data.json`).

**Example:**
```bash
curl -X POST "http://localhost:8000/products/load-from-file"
```

## Development

### Local Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python main.py
   ```

### Running Tests
pytest

## Architecture

The application follows a modular architecture:

- **Config Layer**: Environment-based configuration
- **Data Layer**: OpenSearch connection and index management
- **Model Layer**: Data models and validation
- **Service Layer**: Search and ingestion logic
- **API Layer**: REST endpoints

## License

MIT
Architecture Diagram
Here is the architecture diagram for the e-commerce search application:

┌─────────────────────────────────────────────────────────────────────┐
│                     E-Commerce Search System                         │
└───────────────────────────────┬─────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Docker Compose Stack                          │
│                                                                      │
│  ┌─────────────┐      ┌───────────────┐      ┌───────────────────┐  │
│  │  Python App │      │  OpenSearch   │      │    OpenSearch     │  │
│  │  Container  │◄────►│    Engine     │◄────►│    Dashboards     │  │
│  │             │      │               │      │                   │  │
│  └──────┬──────┘      └───────┬───────┘      └───────────────────┘  │
│         │                     │                                      │
│         ▼                     ▼                                      │
│  ┌─────────────┐      ┌───────────────┐                             │
│  │  App Volume │      │ OpenSearch    │                             │
│  │  (Code)     │      │ Volume (Data) │                             │
│  └─────────────┘      └───────────────┘                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       Python Application                             │
│                                                                      │
│  ┌─────────────┐      ┌───────────────┐      ┌───────────────────┐  │
│  │    API      │      │   Service     │      │      Models       │  │
│  │   Layer     │◄────►│    Layer      │◄────►│                   │  │
│  │ (FastAPI)   │      │               │      │                   │  │
│  └─────┬───────┘      └───────┬───────┘      └───────────────────┘  │
│        │                      │                                      │
│        ▼                      ▼                                      │
│  ┌─────────────┐      ┌───────────────┐      ┌───────────────────┐  │
│  │  REST API   │      │  Search &     │      │  OpenSearch       │  │
│  │  Endpoints  │      │  Ingestion    │      │  Connection       │  │
│  │             │      │  Logic        │      │                   │  │
│  └─────────────┘      └───────────────┘      └───────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       Data Flow Pipeline                             │
│                                                                      │
│  ┌─────────────┐      ┌───────────────┐      ┌───────────────────┐  │
│  │  Generate   │      │   Index       │      │   Search          │  │
│  │  Sample     │─────►│   Data        │─────►│   Query           │  │
│  │  Data       │      │   Pipeline    │      │   Pipeline        │  │
│  └─────────────┘      └───────────────┘      └───────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
Component Descriptions
1.	Docker Infrastructure:
      o	Python App Container: Hosts the FastAPI application
      o	OpenSearch Engine: Search database for storing and querying product data
      o	OpenSearch Dashboards: Web UI for OpenSearch monitoring and management
2.	Python Application:
      o	API Layer: FastAPI-based REST interface for search and data operations
      o	Service Layer: Business logic for search and data ingestion
      o	Models Layer: Data definitions and validation using Pydantic
      o	Connection Layer: OpenSearch client management and configuration
3.	Data Flow Pipeline:
      o	Data Generation: Creates sample product data
      o	Data Ingestion: Indexes data into OpenSearch
      o	Search Processing: Handles search requests with fuzzy matching and filtering
      Key Features Explained
1.	Fuzzy Search Handling:
      o	The fuzziness: "AUTO" parameter in search queries allows the system to handle typos by finding close matches
      o	Example: Searching for "camra" will match products with "camera"
2.	Price Range Filtering:
      o	The search API accepts min_price and max_price parameters
      o	These are translated into OpenSearch range queries on the price field
3.	Modular Architecture:
      o	Each component has a single responsibility
      o	Environment-based configuration separates config from code
      o	Docker setup allows for isolated, consistent deployment
4.	Data Ingestion Pipeline:
      o	Data can be generated using the sample generator
      o	Bulk indexing optimizes ingestion of large datasets
      o	JSON-based data format for easy exchange
      How to Use
      This application demonstrates a production-grade implementation of OpenSearch for e-commerce search. The key components to explore are:
1.	The search functionality in app/searcher.py which shows how to implement fuzzy search and filters
2.	The data ingestion pipeline in app/ingestor.py
3.	The REST API in app/api.py
      You can extend this project by:
1.	Adding more search features (faceted search, more filters)
2.	Implementing user authentication
3.	Adding real-time analytics on search patterns
4.	Integrating with actual e-commerce platforms
