#!/usr/bin/env python
"""
FastAPI server for the SmartBeauty RAG system.

This server provides REST API endpoints to interact with the RAG system,
allowing users to:
1. Get product recommendations for skin conditions
2. Search for products by text query
3. Get details about specific products and skin conditions

Usage:
uvicorn api_server:app --reload
"""
import os
import sys
from typing import List, Dict, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# Add the parent directory to sys.path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the RAGDataAPI
from api_wrapper import RAGDataAPI

# Create the API instance
rag_api = RAGDataAPI()

# Create the FastAPI app
app = FastAPI(
    title="SmartBeauty RAG API",
    description="API for retrieving skincare product recommendations based on skin conditions",
    version="1.0.0",
)

# Define Pydantic models for request/response validation
class ProductBase(BaseModel):
    id: int
    name: str
    
class ProductDetail(ProductBase):
    data: Dict[str, Any]
    similarity: Optional[float] = None
    
class SkinConditionBase(BaseModel):
    id: int
    name: str
    
class SkinConditionDetail(SkinConditionBase):
    description: str
    
class RecommendationsResponse(BaseModel):
    skin_condition: SkinConditionDetail
    recommendations: List[ProductDetail]
    
class SearchResponse(BaseModel):
    query: str
    results: List[ProductDetail]

# Define API endpoints
@app.get("/")
async def root():
    """Root endpoint that provides API information."""
    return {
        "name": "SmartBeauty RAG API",
        "version": "1.0.0",
        "endpoints": [
            "/skin-conditions",
            "/skin-conditions/{condition_name}",
            "/skin-conditions/{condition_name}/products",
            "/products",
            "/products/search",
            "/products/{product_id}"
        ]
    }

@app.get("/skin-conditions", response_model=List[SkinConditionBase])
async def get_skin_conditions(limit: int = Query(10, ge=1, le=100)):
    """Get a list of skin conditions."""
    try:
        conditions = rag_api.load_skin_conditions_from_db(limit=limit)
        return conditions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/skin-conditions/{condition_name}", response_model=SkinConditionDetail)
async def get_skin_condition_by_name(condition_name: str):
    """Get details about a specific skin condition by name."""
    condition = rag_api.get_skin_condition_by_name(condition_name)
    if not condition:
        raise HTTPException(status_code=404, detail=f"Skin condition '{condition_name}' not found")
    return condition

@app.get("/skin-conditions/{condition_name}/products", response_model=RecommendationsResponse)
async def get_recommendations_for_condition(condition_name: str, top_n: int = Query(5, ge=1, le=20)):
    """Get product recommendations for a specific skin condition."""
    try:
        recommendations = rag_api.get_product_recommendations_for_condition(condition_name, top_n=top_n)
        if "error" in recommendations:
            raise HTTPException(status_code=404, detail=recommendations["error"])
        return recommendations
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products", response_model=List[ProductBase])
async def get_products(limit: int = Query(10, ge=1, le=100)):
    """Get a list of products."""
    try:
        products = rag_api.load_products_from_db(limit=limit)
        return [{"id": p["id"], "name": p["name"]} for p in products]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/search", response_model=SearchResponse)
async def search_products(q: str, top_n: int = Query(5, ge=1, le=20)):
    """Search for products using a text query."""
    try:
        # Create embedding for the query
        embedding = rag_api.create_embedding(q)
        
        # Search for similar products
        results = rag_api.find_similar_products(embedding, top_n=top_n)
        
        return {
            "query": q,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}", response_model=ProductDetail)
async def get_product_by_id(product_id: int):
    """Get details about a specific product by ID."""
    product = rag_api.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
    
    # Convert to response format
    return {
        "id": product["id"],
        "name": product["name"],
        "data": product["data"]
    }

# Run the API when this file is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
