# Quickstart Guide

This guide will get you up and running with the E-Commerce Product Search application in minutes.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (for cloning the repository)

## Step 1: Clone and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/e-commerce-search.git
   cd e-commerce-search
   ```

2. Start all services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

   This will start:
   - OpenSearch (search engine) on port 9200
   - OpenSearch Dashboards on port 5601
   - The Python application on port 8000

## Step 2: Load Sample Data

1. Generate sample product data:
   ```bash
   docker-compose exec app python scripts/generate_data.py
   ```

2. Index the data into OpenSearch:
   ```bash
   docker-compose exec app python scripts/index_data.py
   ```

## Step 3: Test the Application

### API Testing

- **FastAPI Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - Interactive Swagger UI to test all API endpoints
  - Try the search functionality immediately

- **Alternative API Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
  - ReDoc format for API documentation

### OpenSearch Dashboards

- **Data Visualization**: [http://localhost:5601](http://localhost:5601)
  - Explore indexed data
  - Create visualizations and dashboards
  - Monitor cluster health

### Command Line Testing

Test search via command line:
```bash
docker-compose exec app python scripts/search_cli.py "camera"
```

## Inserting Data via JSON

### Method 1: Single Product via API

Use the API to insert a single product:

```bash
curl -X POST "http://localhost:8000/products" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "prod-001",
    "name": "Wireless Bluetooth Headphones",
    "description": "High-quality wireless headphones with noise cancellation",
    "price": 99.99,
    "category": "Electronics",
    "brand": "AudioTech",
    "in_stock": true
  }'
```

### Method 2: Bulk Insert via API

Insert multiple products at once:

```bash
curl -X POST "http://localhost:8000/products/bulk" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "id": "prod-002",
      "name": "Smart Watch",
      "description": "Fitness tracking smartwatch with heart rate monitor",
      "price": 199.99,
      "category": "Electronics",
      "brand": "TechFit",
      "in_stock": true
    },
    {
      "id": "prod-003",
      "name": "Running Shoes",
      "description": "Comfortable running shoes for all terrains",
      "price": 79.99,
      "category": "Sports",
      "brand": "RunPro",
      "in_stock": true
    }
  ]'
```

### Method 3: Load from JSON File

1. Prepare a JSON file with product data (see `data/product_data.json` for format)

2. Load via API:
   ```bash
   curl -X POST "http://localhost:8000/products/load-from-file"
   ```

   Or use the script:
   ```bash
   docker-compose exec app python scripts/index_data.py
   ```

### JSON Data Format

Products should follow this structure:
```json
{
  "id": "unique-product-id",
  "name": "Product Name",
  "description": "Product description",
  "price": 99.99,
  "category": "Category Name",
  "brand": "Brand Name",
  "in_stock": true
}
```

## Testing Search Functionality

### Basic Search
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "camera"}'
```

### Search with Filters
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "shirt",
    "min_price": 20,
    "max_price": 50,
    "category": "Clothing",
    "brand": "Nike",
    "limit": 10
  }'
```

## Stopping the Application

To stop all services:
```bash
docker-compose down
```

To stop and remove volumes (including data):
```bash
docker-compose down -v
```

## Troubleshooting

- **Port conflicts**: Ensure ports 8000, 9200, and 5601 are available
- **Services not starting**: Check Docker logs with `docker-compose logs`
- **API not responding**: Wait for OpenSearch to fully initialize (may take 30-60 seconds)
- **Data not found**: Ensure sample data was generated and indexed successfully

## Next Steps

- Explore the [API Documentation](http://localhost:8000/docs) for all available endpoints
- Check out the [Architecture Guide](ARCHITECTURE.md) for system details
- View indexed data in [OpenSearch Dashboards](http://localhost:5601)
- Run tests: `docker-compose exec app pytest`</content>
<parameter name="filePath">c:\Users\ADMIN\SV_Practice_06102024\Self_Learning\MyProjects\opensearch_project\QUICKSTARTGUIDE.md