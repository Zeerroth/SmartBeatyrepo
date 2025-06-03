#!/usr/bin/env python
"""
Enhanced version of the API wrapper with improved error handling.

This script demonstrates how to enhance the existing RAGDataAPI class
with the error handling utilities we created.

Usage:
Use this as a reference to update the api_wrapper.py file with improved error handling.
"""
import os
import sys
import json
import numpy as np
import psycopg2
from psycopg2.extras import Json
import logging
from typing import Dict, List, Union, Optional, Any

# Add the parent directory to sys.path to ensure imports work consistently
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import configuration and error handling
import rag.core.config as config
from data_loader import load_raw_product_data, load_skin_condition_profiles
from document_processor import create_embedding_text_from_features
from error_handling import (
    handle_errors, 
    DatabaseConnection, 
    DatabaseError,
    EmbeddingError,
    DataLoadingError,
    SearchError
)

# Configure logger
logger = logging.getLogger(__name__)

class EnhancedRAGDataAPI:
    """
    Enhanced version of the RAGDataAPI with improved error handling.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the API with optional connection string.
        
        Args:
            connection_string: The PostgreSQL connection string. If None, uses config.DATABASE_CONNECTION_STRING.
        """
        self.connection_string = connection_string or config.DATABASE_CONNECTION_STRING
        self.embedding_model = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Extract connection parameters for direct DB access
        try:
            params_part = self.connection_string.split("://")[1]
            user_pass, host_port_db = params_part.split("@")
            user, password = user_pass.split(":")
            host_port, dbname = host_port_db.split("/")
            host, port = host_port.split(":")
            
            self.db_params = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "dbname": dbname
            }
            self.logger.info(f"Initialized API with connection to {host}:{port}/{dbname}")
        except Exception as e:
            self.logger.error(f"Error parsing connection string: {e}")
            self.db_params = None
            raise DatabaseError(f"Invalid connection string format: {e}")
    
    def get_db_connection(self):
        """Get a direct database connection using psycopg2."""
        if not self.db_params:
            raise DatabaseError("Database connection parameters are not available")
            
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model if not already done."""
        if self.embedding_model is None:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                
                self.logger.info(f"Loading embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}...")
                self.embedding_model = HuggingFaceEmbeddings(
                    model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
                    model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
                )
            except Exception as e:
                self.logger.error(f"Failed to initialize embedding model: {e}")
                raise EmbeddingError(f"Could not initialize embedding model: {e}")
    
    @handle_errors(error_type=EmbeddingError)
    def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for the given text.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            List of float values representing the embedding vector
        """
        self._initialize_embedding_model()
        try:
            return self.embedding_model.embed_query(text)
        except Exception as e:
            raise EmbeddingError(f"Failed to create embedding: {e}")
    
    def format_embedding_for_db(self, embedding: List[float]) -> str:
        """
        Format an embedding vector for database storage.
        
        Args:
            embedding: The embedding vector as a list of floats
            
        Returns:
            String representation compatible with pgvector
        """
        return str(embedding)
    
    # --- Product-related methods ---
    
    @handle_errors(error_type=DataLoadingError, default_return=[])
    def load_products_from_file(self) -> List[Dict]:
        """
        Load product data from the file specified in config.
        
        Returns:
            List of product dictionaries
        """
        try:
            return load_raw_product_data(
                config.DATA_SOURCE_TYPE,
                filepath=config.PRODUCT_JSON_FILEPATH
            )
        except Exception as e:
            self.logger.error(f"Failed to load products from file: {e}")
            raise DataLoadingError(f"Failed to load products from file: {e}")
    
    @handle_errors(error_type=DatabaseError, default_return=[])
    def load_products_from_db(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load products directly from the database.
        
        Args:
            limit: Optional limit on number of products to retrieve
            
        Returns:
            List of product dictionaries
        """
        with DatabaseConnection(self.get_db_connection) as conn:
            with conn.cursor() as cursor:
                query = """
                SELECT id, name, original_product_data
                FROM products
                """
                if limit:
                    query += f" LIMIT {limit}"
                    
                cursor.execute(query)
                products = []
                for product_id, name, data in cursor.fetchall():
                    # Add the ID and name to the top level of the product data
                    product_data = data.copy() if data else {}
                    product_data["id"] = product_id
                    product_data["name"] = name
                    products.append(product_data)
            
            self.logger.info(f"Loaded {len(products)} products from database")
            return products
    
    def get_product_embedding_text(self, product: Dict) -> str:
        """
        Generate embedding text for a product.
        
        Args:
            product: Product dictionary
            
        Returns:
            Text to use for embedding
        """
        return create_embedding_text_from_features(
            product,
            config.PRODUCT_FEATURES_FOR_EMBEDDING,
            config.FEATURE_LABELS
        )
    
    @handle_errors(error_type=DatabaseError, default_return=False)
    def store_product_embedding(self, product_id: int, embedding: List[float]) -> bool:
        """
        Store a product embedding in the database.
        
        Args:
            product_id: ID of the product
            embedding: Embedding vector
            
        Returns:
            Success status
        """
        embedding_str = self.format_embedding_for_db(embedding)
        
        with DatabaseConnection(self.get_db_connection) as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                    UPDATE products
                    SET embedding_vector = %s::vector
                    WHERE id = %s
                    """, (embedding_str, product_id))
                    
                conn.commit()
                self.logger.info(f"Stored embedding for product {product_id}")
                return True
            except Exception as e:
                self.logger.error(f"Error storing product embedding: {e}")
                conn.rollback()
                raise DatabaseError(f"Failed to store product embedding: {e}")
    
    @handle_errors(error_type=DatabaseError, default_return=None)
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Get a product by its ID.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Product dictionary or None if not found
        """
        with DatabaseConnection(self.get_db_connection) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                SELECT id, name, original_product_data,
                       embedding_text_concatenated, embedding_vector
                FROM products
                WHERE id = %s
                """, (product_id,))
                
                result = cursor.fetchone()
                
            if result:
                product_id, name, data, text, vector = result
                self.logger.info(f"Found product with ID {product_id}: {name}")
                return {
                    "id": product_id,
                    "name": name,
                    "data": data,
                    "embedding_text": text,
                    "has_embedding": vector is not None
                }
            else:
                self.logger.warning(f"Product with ID {product_id} not found")
                return None
    
    # Example of enhanced error handling for search methods
    @handle_errors(error_type=SearchError, default_return=[])
    def find_similar_products(self, 
                             embedding: List[float], 
                             top_n: int = 5) -> List[Dict]:
        """
        Find products similar to a given embedding.
        
        Args:
            embedding: Embedding vector to search with
            top_n: Number of top results to return
            
        Returns:
            List of product dictionaries with similarity scores
        """
        if not embedding:
            self.logger.warning("Empty embedding provided, cannot search")
            return []
            
        try:
            embedding_str = self.format_embedding_for_db(embedding)
            
            with DatabaseConnection(self.get_db_connection) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                    SELECT 
                        id, 
                        name, 
                        original_product_data,
                        1 - (embedding_vector <=> %s::vector) AS similarity
                    FROM products
                    WHERE embedding_vector IS NOT NULL
                    ORDER BY similarity DESC
                    LIMIT %s
                    """, (embedding_str, top_n))
                    
                    results = []
                    for row in cursor.fetchall():
                        product_id, name, original_data, similarity = row
                        results.append({
                            "id": product_id,
                            "name": name,
                            "similarity": float(similarity),
                            "data": original_data
                        })
            
            self.logger.info(f"Found {len(results)} similar products")
            return results
        except Exception as e:
            self.logger.error(f"Error searching for similar products: {e}")
            raise SearchError(f"Failed to find similar products: {e}")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create API instance
    api = EnhancedRAGDataAPI()
    
    # Test error handling
    try:
        # This should handle errors gracefully and return an empty list
        products = api.load_products_from_db(limit=5)
        print(f"Loaded {len(products)} products")
        
        # This should create an embedding
        if products:
            product = products[0]
            text = api.get_product_embedding_text(product)
            embedding = api.create_embedding(text)
            print(f"Created embedding with length {len(embedding)}")
            
            # Find similar products
            similar = api.find_similar_products(embedding, top_n=3)
            print(f"Found {len(similar)} similar products")
            
    except Exception as e:
        print(f"Unhandled exception: {e}")
