import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenSearch configuration
OPENSEARCH_CONFIG = {
    "host": os.getenv("OPENSEARCH_HOST", "localhost"),
    "port": int(os.getenv("OPENSEARCH_PORT", 9200)),
    "use_ssl": os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true",
    "verify_certs": os.getenv("OPENSEARCH_VERIFY_CERTS", "false").lower() == "true",
    "username": os.getenv("OPENSEARCH_USERNAME", ""),
    "password": os.getenv("OPENSEARCH_PASSWORD", ""),
}

# Index configuration
INDEX_NAME = os.getenv("OPENSEARCH_INDEX_NAME", "products")

# App configuration
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
