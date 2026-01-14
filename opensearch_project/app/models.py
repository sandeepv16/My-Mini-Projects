from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Product(BaseModel):
    """Product data model"""
    id: str
    name: str
    description: str
    price: float
    category: str
    brand: str
    in_stock: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    def to_dict(self):
        """Convert to dictionary for OpenSearch indexing"""
        product_dict = self.dict()
        # Convert datetime to ISO format string
        product_dict['created_at'] = product_dict['created_at'].isoformat()
        return product_dict

class SearchRequest(BaseModel):
    """Search request model"""
    query: str
    min_price: Optional[float] = 0.0
    max_price: Optional[float] = float('inf')
    category: Optional[str] = None
    brand: Optional[str] = None
    sort_by: Optional[str] = None
    page: int = 1
    size: int = 10

class SearchResponse(BaseModel):
    """Search response model"""
    total: int
    took_ms: int
    products: List[Product]
    page: int
    size: int
    total_pages: int
