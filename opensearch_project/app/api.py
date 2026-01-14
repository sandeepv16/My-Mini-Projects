from fastapi import FastAPI, HTTPException, Depends
from app.models import Product, SearchRequest, SearchResponse
from app.connection import create_client, create_index_if_not_exists
from app.searcher import search_products
from app.ingestor import index_product, bulk_index_products, load_products_from_file
import logging

logger = logging.getLogger(__name__)
app = FastAPI(title="E-Commerce Product Search API")

# OpenSearch client as a dependency
def get_client():
    client = create_client()
    create_index_if_not_exists(client)
    return client

@app.get("/")
def root():
    return {"message": "E-Commerce Product Search API"}

@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, client=Depends(get_client)):
    try:
        return search_products(client, request)
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/products", status_code=201)
def create_product(product: Product, client=Depends(get_client)):
    try:
        result = index_product(client, product)
        return result
    except Exception as e:
        logger.error(f"Failed to index product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to index product: {str(e)}")

@app.post("/products/bulk", status_code=201)
def create_products_bulk(products: list[Product], client=Depends(get_client)):
    try:
        result = bulk_index_products(client, products)
        return result
    except Exception as e:
        logger.error(f"Failed to bulk index products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk index products: {str(e)}")

@app.post("/products/load-from-file", status_code=201)
def load_products(client=Depends(get_client)):
    try:
        products = load_products_from_file()
        if not products:
            return {"success": False, "message": "No products found in data file"}

        result = bulk_index_products(client, products)
        return result
    except Exception as e:
        logger.error(f"Failed to load products from file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load products: {str(e)}")
