#!/usr/bin/env python
"""
API Wrapper for SmartBeauty RAG System

This module provides a unified API for working with both skin conditions and products,
allowing seamless interaction with either the database-direct approach or the LangChain approach.

It provides functions to:
1. Load data (from files or database)
2. Create embeddings
3. Store data in the database
4. Search for similar items

Usage:
This can be used as a library or integrated into a web API server.
"""
import os
import sys
import json
import numpy as np
import psycopg2
from psycopg2.extras import Json
from typing import Dict, List, Union, Optional, Any, Tuple

# Add the parent directory to sys.path to ensure imports work consistently
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import configuration
import rag.core.config as config
from data_loader import load_raw_product_data, load_skin_condition_profiles
from document_processor import create_embedding_text_from_features


class RAGDataAPI:
    """
    Unified API for the RAG system that can handle both database-direct and LangChain approaches.
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the API with optional connection string.
        
        Args:
            connection_string: The PostgreSQL connection string. If None, uses config.DATABASE_CONNECTION_STRING.
        """
        self.connection_string = connection_string or config.DATABASE_CONNECTION_STRING
        self.embedding_model = None
        
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
        except Exception as e:
            print(f"Error parsing connection string: {e}")
            self.db_params = None
    
    def get_db_connection(self):
        """Get a direct database connection using psycopg2."""
        if not self.db_params:
            raise ValueError("Database connection parameters are not available")
            
        return psycopg2.connect(**self.db_params)
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model if not already done."""
        if self.embedding_model is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            print(f"Loading embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}...")
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
                model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
            )
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create an embedding vector for the given text.
        
        Args:
            text: Text to create embedding for
            
        Returns:
            List of float values representing the embedding vector
        """
        self._initialize_embedding_model()
        return self.embedding_model.embed_query(text)
    
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
    
    def load_products_from_file(self) -> List[Dict]:
        """
        Load product data from the file specified in config.
        
        Returns:
            List of product dictionaries
        """
        return load_raw_product_data(
            config.DATA_SOURCE_TYPE,
            filepath=config.PRODUCT_JSON_FILEPATH
        )
    
    def load_products_from_db(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load products directly from the database.
        
        Args:
            limit: Optional limit on number of products to retrieve
            
        Returns:
            List of product dictionaries
        """
        conn = self.get_db_connection()
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
                
        conn.close()
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
        conn = self.get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE products
                SET embedding_vector = %s::vector
                WHERE id = %s
                """, (embedding_str, product_id))
                
            conn.commit()
            success = True
        except Exception as e:
            print(f"Error storing product embedding: {e}")
            conn.rollback()
            success = False
            
        conn.close()
        return success
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """
        Get a product by its ID.
        
        Args:
            product_id: ID of the product
            
        Returns:
            Product dictionary or None if not found
        """
        conn = self.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, name, original_product_data,
                   embedding_text_concatenated, embedding_vector
            FROM products
            WHERE id = %s
            """, (product_id,))
            
            result = cursor.fetchone()
            
        conn.close()
        
        if result:
            product_id, name, data, text, vector = result
            return {
                "id": product_id,
                "name": name,
                "data": data,
                "embedding_text": text,
                "has_embedding": vector is not None
            }
        
        return None
    
    # --- Skin condition-related methods ---
    
    def load_skin_conditions_from_module(self) -> Dict[str, str]:
        """
        Load skin conditions from the module specified in config.
        
        Returns:
            Dictionary mapping condition names to descriptions
        """
        return load_skin_condition_profiles(config.CLASS_DESCRIPTIONS_MODULE)
    
    def load_skin_conditions_from_db(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Load skin conditions directly from the database.
        
        Args:
            limit: Optional limit on number of conditions to retrieve
            
        Returns:
            List of skin condition dictionaries
        """
        conn = self.get_db_connection()
        with conn.cursor() as cursor:
            query = """
            SELECT id, name, description
            FROM skin_conditions
            """
            if limit:
                query += f" LIMIT {limit}"
                
            cursor.execute(query)
            conditions = []
            for condition_id, name, description in cursor.fetchall():
                conditions.append({
                    "id": condition_id,
                    "name": name,
                    "description": description
                })
                
        conn.close()
        return conditions
    
    def get_skin_condition_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a skin condition by its name (case insensitive).
        
        Args:
            name: Name of the skin condition
            
        Returns:
            Skin condition dictionary or None if not found
        """
        conn = self.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT id, name, description, embedding_vector
            FROM skin_conditions
            WHERE LOWER(name) = LOWER(%s)
            """, (name,))
            
            result = cursor.fetchone()
            
            # Try partial match if exact match fails
            if not result:
                cursor.execute("""
                SELECT id, name, description, embedding_vector
                FROM skin_conditions
                WHERE LOWER(name) LIKE LOWER(%s)
                LIMIT 1
                """, (f"%{name}%",))
                
                result = cursor.fetchone()
                
        conn.close()
        
        if result:
            condition_id, name, description, vector = result
            return {
                "id": condition_id,
                "name": name,
                "description": description,
                "has_embedding": vector is not None,
                "embedding_vector": vector
            }
        
        return None
    
    def store_skin_condition_embedding(self, condition_id: int, embedding: List[float]) -> bool:
        """
        Store a skin condition embedding in the database.
        
        Args:
            condition_id: ID of the skin condition
            embedding: Embedding vector
            
        Returns:
            Success status
        """
        embedding_str = self.format_embedding_for_db(embedding)
        conn = self.get_db_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                UPDATE skin_conditions
                SET embedding_vector = %s::vector
                WHERE id = %s
                """, (embedding_str, condition_id))
                
            conn.commit()
            success = True
        except Exception as e:
            print(f"Error storing skin condition embedding: {e}")
            conn.rollback()
            success = False
            
        conn.close()
        return success
    
    # --- Search methods ---
    
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
        embedding_str = self.format_embedding_for_db(embedding)
        conn = self.get_db_connection()
        
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
            
        conn.close()
        return results
    
    def find_similar_skin_conditions(self, 
                                    embedding: List[float], 
                                    top_n: int = 5) -> List[Dict]:
        """
        Find skin conditions similar to a given embedding.
        
        Args:
            embedding: Embedding vector to search with
            top_n: Number of top results to return
            
        Returns:
            List of skin condition dictionaries with similarity scores
        """
        embedding_str = self.format_embedding_for_db(embedding)
        conn = self.get_db_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT 
                id, 
                name,
                description,
                1 - (embedding_vector <=> %s::vector) AS similarity
            FROM skin_conditions
            WHERE embedding_vector IS NOT NULL
            ORDER BY similarity DESC
            LIMIT %s
            """, (embedding_str, top_n))
            
            results = []
            for row in cursor.fetchall():
                condition_id, name, description, similarity = row
                results.append({
                    "id": condition_id,
                    "name": name,
                    "description": description,
                    "similarity": float(similarity)
                })
            
        conn.close()
        return results
    
    def get_product_recommendations_for_condition(self, condition_name: str, top_n: int = 5) -> Dict:
        """
        Get product recommendations for a specific skin condition.
        
        Args:
            condition_name: Name of the skin condition
            top_n: Number of recommendations to return
            
        Returns:
            Dictionary with skin condition info and recommended products
        """
        # Find the skin condition
        condition = self.get_skin_condition_by_name(condition_name)
        if not condition:
            return {
                "error": f"Skin condition '{condition_name}' not found",
                "recommendations": []
            }
            
        # If condition has no embedding, create one
        if not condition.get("has_embedding"):
            embedding = self.create_embedding(condition["description"])
            self.store_skin_condition_embedding(condition["id"], embedding)
        else:
            # Extract embedding from the condition data
            embedding = condition["embedding_vector"]
            
        # Find similar products
        recommendations = self.find_similar_products(embedding, top_n)
        
        return {
            "skin_condition": {
                "id": condition["id"],
                "name": condition["name"],
                "description": condition["description"]
            },
            "recommendations": recommendations
        }


# Example usage in a script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartBeauty RAG API Example")
    parser.add_argument("--condition", type=str, help="Get product recommendations for skin condition")
    parser.add_argument("--top_n", type=int, default=5, help="Number of recommendations to return")
    args = parser.parse_args()
    
    # Initialize the API
    rag_api = RAGDataAPI()
    
    if args.condition:
        print(f"Getting product recommendations for '{args.condition}'...")
        results = rag_api.get_product_recommendations_for_condition(args.condition, args.top_n)
        
        if "error" in results:
            print(f"Error: {results['error']}")
        else:
            print(f"Condition: {results['skin_condition']['name']}")
            print(f"\nTop {len(results['recommendations'])} recommended products:")
            for i, product in enumerate(results['recommendations'], 1):
                print(f"\n{i}. {product['name']} (Similarity: {product['similarity']:.4f})")
                
                key_benefits = product['data'].get("keyBenefits", "")
                if key_benefits:
                    if isinstance(key_benefits, list):
                        key_benefits = ', '.join(key_benefits)
                    print(f"   Key Benefits: {key_benefits}")
    else:
        print("Please specify a skin condition with --condition")
