# main.py

import logging
import os
import uvicorn
from app.config import APP_HOST, APP_PORT, LOGGING_LEVEL
from app.api import app as api_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Application entry point"""
    logger.info("Starting E-Commerce Product Search application")

    # Run in development mode
    uvicorn.run(
        "app.api:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=True if os.environ.get("ENV", "development") == "development" else False
    )

if __name__ == "__main__":
    main()
