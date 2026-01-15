# PDF Parser Project

This project is a robust document processing application designed to automatically extract and structure tabular data from PDF documents. Built with Docling for advanced PDF parsing capabilities, it transforms unstructured PDF content into structured, queryable data stored in a PostgreSQL database. The system functions as a batch processor that scans input directories for PDF files, intelligently extracts table structures using modern document AI, normalizes the data into a consistent format, and persists it for downstream analysis and reporting. Data flows seamlessly from PDF input through Docling's document conversion pipeline, where tables are identified and extracted; then through data transformation where content is normalized and structured into database-compatible records; finally into PostgreSQL storage where it becomes available for querying, export, and integration with other business systems.

pdf_parser_project/
├── docker/
│   ├── app/
│   │   └── Dockerfile
│   └── db/
│       └── init-db.sh
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
├── config/
│   └── config.py
├── scripts/
│   └── create_tables.sql
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── db_operations.py
│   ├── parser/
│   │   ├── __init__.py
│   │   └── pdf_parser.py
│   └── models/
│       ├── __init__.py
│       └── table_data.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_parser.py
│   └── test_db_operations.py
├── input_pdfs/
│   └── .gitkeep
└── main.py

### Setup and Running Instructions:
Shell Script
cp .env.example .env

docker-compose up --build / docker compose up -d
or
docker-compose build --no-cache

if fails 
docker system prune -a 
repeat above build command 
This clears up other project networks and shards 

docker-compose exec app pytest

To check postgres data
# Direct query execution:
docker-compose exec db psql -U postgres -d pdf_parser_db -c "SELECT * FROM parsed_table_data LIMIT 5;"


if container didnt start
1. First, start just the database:
   docker-compose up db -d
2. Wait a few seconds for the health check to pass, then start the app:
   docker-compose up app -d
3. Or to start everything at once:
   docker-compose up -d
4. View container status:
   docker-compose ps
5. View logs:
   docker-compose logs
6. For specific service logs:
   docker-compose logs db    # Database logs
   docker-compose logs app   # Application logs

1. Force rebuild everything:
   docker-compose down -v
   docker-compose build --no-cache
   docker-compose up -d
2. Check if PostgreSQL is accessible:
   docker-compose exec db psql -U postgres -c "\l"
3. Verify the network is created:
   docker network ls | grep pdf_parser_network
4. 
To run the tests:
1)Run all tests:
docker-compose run test
2)Run specific test file
docker-compose run test pytest tests/test_parser.py
3)1. Run tests with specific marker:
docker-compose run test pytest -m integration
4)1. Run tests with coverage:
docker-compose run test pytest --cov=src tests/


Errors
target test: failed to solve: failed to prepare extraction snapshot "extract-82642955-4RH1 sha256:e411e191d13593041108b2cc127d4b35173b3e881c8eaa2d6a47894618520d93": parent snapshot sha256:7002e8394ccd2e3649d21842aa47494b32760c2114d5393df80fd946ec5d7069 does not exist: not found

This error typically occurs when there's an issue with Docker's build cache or when image layers become inconsistent. Let's fix this with the following steps:

1. First, let's clean up Docker completely:
# Stop all containers
docker-compose down

# Remove all containers
docker rm -f $(docker ps -aq)

# Remove all images
docker rmi -f $(docker images -aq)

# Clean up system
docker system prune -af --volumes

2. Now rebuild the project:
   docker-compose build --no-cache
   docker-compose up -d

3. If the error persists, try this alternative approach:
# Reset Docker daemon
docker system prune -af
docker builder prune -af

# Restart Docker service
# On Windows: Restart Docker Desktop
# On Linux: sudo systemctl restart docker

# Then rebuild
docker-compose build --no-cache

The error you're seeing suggests that Docker can't find a parent layer it expects to exist. This usually happens when:
1. The Docker cache becomes corrupted
2. There's a network issue while pulling base images
3. Docker daemon has encountered synchronization issues

If the above steps don't resolve the issue, please try:
1. Make sure you have a stable internet connection
2. Verify that Docker Desktop (if you're using Windows) is running properly
