# Quickstart Guide

Get the PDF parsing application up and running in minutes.

## Prerequisites

- **Docker & Docker Compose**: [Install Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Git**: For cloning the repository (optional)

## Quick Setup

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd docling_project
```

### 2. Environment Setup

Copy the environment template:

```bash
cp .env.example .env
```

### 3. Launch with Docker

Build and start all services:

```bash
docker-compose up --build
```

Or run in detached mode:

```bash
docker-compose up -d --build
```

## Verify Installation

### Check Container Status

```bash
docker-compose ps
```

You should see:
- `docling_project-db-1` (PostgreSQL database)
- `docling_project-app-1` (Python application)

### View Logs

```bash
docker-compose logs
```

## Basic Usage

### 1. Add PDF Files

Place PDF files in the `input_pdfs/` directory:

```bash
# Example: Copy a PDF to the input directory
cp your-document.pdf input_pdfs/
```

### 2. Process PDFs

The application automatically processes PDFs on startup. To manually trigger processing:

```bash
# Restart the app container
docker-compose restart app
```

### 3. Check Processed Data

Query the database directly:

```bash
docker-compose exec db psql -U postgres -d pdf_parser_db -c "SELECT * FROM parsed_table_data LIMIT 5;"
```

### 4. Export Data to CSV

Export all parsed data to CSV file:

```bash
# Export to CSV using PostgreSQL COPY command
docker-compose exec db psql -U postgres -d pdf_parser_db -c "\COPY parsed_table_data TO '/tmp/parsed_table_data_export.csv' WITH CSV HEADER;"

# Copy the exported file to host machine
docker cp $(docker-compose ps -q db):/tmp/parsed_table_data_export.csv ./parsed_table_data_export.csv

# View the exported CSV
head -10 parsed_table_data_export.csv
```

For filtered exports:

```bash
# Export data from specific document
docker-compose exec db psql -U postgres -d pdf_parser_db -c "\COPY (SELECT * FROM parsed_table_data WHERE document_name = 'your-document.pdf') TO '/tmp/filtered_export.csv' WITH CSV HEADER;"

# Export only table data (exclude metadata columns)
docker-compose exec db psql -U postgres -d pdf_parser_db -c "\COPY (SELECT table_number, row_number, column_number, cell_content FROM parsed_table_data ORDER BY table_number, row_number, column_number) TO '/tmp/table_data_only.csv' WITH CSV HEADER;"
```

## Running Tests

Execute the test suite:

```bash
# Run all tests
docker-compose run test

# Run specific test file
docker-compose run test pytest tests/test_parser.py

# Run with coverage
docker-compose run test pytest --cov=src tests/
```

## Development Mode

### Local Development (without Docker)

1. **Install Dependencies**:

```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**:

```bash
export DB_HOST=localhost
export DB_NAME=pdf_parser_db
export DB_USER=postgres
export DB_PASSWORD=postgres
export DB_PORT=5432
```

3. **Start Database**:

```bash
docker-compose up db -d
```

4. **Run Application**:

```bash
python main.py
```

## Troubleshooting

### Common Issues

**Database Connection Failed**:
```bash
# Check database health
docker-compose logs db

# Restart database
docker-compose restart db
```

**Build Failures**:
```bash
# Clean rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

**Permission Issues**:
```bash
# Fix file permissions
chmod +x docker/db/init-db.sh
```

### Useful Commands

```bash
# Stop all services
docker-compose down

# View real-time logs
docker-compose logs -f app

# Access database shell
docker-compose exec db psql -U postgres -d pdf_parser_db

# Access application shell
docker-compose exec app bash
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design details
- Explore the `tests/` directory for examples
- Customize configuration in `config/config.py`

## Support

If you encounter issues:
1. Check the [README.md](README.md) troubleshooting section
2. Review Docker and PostgreSQL logs
3. Ensure all prerequisites are installed
4. Verify file permissions and network connectivity