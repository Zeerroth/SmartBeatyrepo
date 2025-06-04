#!/usr/bin/env python
"""
Vector store helper functions for easy loading and connection.
This provides simple functions to connect to existing vector stores
created by the CustomDatabaseVectorManager.
"""

from typing import Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
import config


def create_embedding_model():
    """Create the standard embedding model used across the system."""
    return HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )


def load_products_vector_store(embedding_model=None) -> Optional[PGVector]:
    """
    Load the products vector store.
    
    Args:
        embedding_model: Optional embedding model. If None, creates default.
        
    Returns:
        PGVector store or None if failed
    """
    if embedding_model is None:
        embedding_model = create_embedding_model()
    
    try:
        vector_store = PGVector(
            embedding_function=embedding_model,
            connection_string=config.DATABASE_CONNECTION_STRING,
            collection_name="products"
        )
        
        # Test the connection
        vector_store.similarity_search("test", k=1)
        return vector_store
        
    except Exception as e:
        print(f"Error loading products vector store: {e}")
        return None


def load_skin_conditions_vector_store(embedding_model=None) -> Optional[PGVector]:
    """
    Load the skin conditions vector store.
    
    Args:
        embedding_model: Optional embedding model. If None, creates default.
        
    Returns:
        PGVector store or None if failed
    """
    if embedding_model is None:
        embedding_model = create_embedding_model()
    
    try:
        vector_store = PGVector(
            embedding_function=embedding_model,
            connection_string=config.DATABASE_CONNECTION_STRING,
            collection_name="skin_conditions"
        )
        
        # Test the connection
        vector_store.similarity_search("test", k=1)
        return vector_store
        
    except Exception as e:
        print(f"Error loading skin conditions vector store: {e}")
        return None


def load_combined_retriever(embedding_model=None, k: int = 5):
    """
    Create a retriever that can search across both products and skin conditions.
    
    Args:
        embedding_model: Optional embedding model. If None, creates default.
        k: Number of results to return
        
    Returns:
        Combined retriever or None if failed
    """
    if embedding_model is None:
        embedding_model = create_embedding_model()
    
    products_store = load_products_vector_store(embedding_model)
    conditions_store = load_skin_conditions_vector_store(embedding_model)
    
    if not products_store and not conditions_store:
        print("❌ No vector stores available")
        return None
    
    if products_store and conditions_store:
        print("✓ Loaded both products and skin conditions vector stores")
        # For now, return products retriever (you could implement ensemble retrieval)
        return products_store.as_retriever(search_kwargs={"k": k})
    elif products_store:
        print("✓ Loaded products vector store only")
        return products_store.as_retriever(search_kwargs={"k": k})
    else:
        print("✓ Loaded skin conditions vector store only")
        return conditions_store.as_retriever(search_kwargs={"k": k})


def get_vector_store_stats(embedding_model=None) -> dict:
    """
    Get statistics about available vector stores.
    
    Args:
        embedding_model: Optional embedding model. If None, creates default.
        
    Returns:
        Dictionary with statistics
    """
    if embedding_model is None:
        embedding_model = create_embedding_model()
    
    stats = {
        "products_available": False,
        "skin_conditions_available": False,
        "products_count": 0,
        "skin_conditions_count": 0
    }
    
    # Check products store
    try:
        products_store = load_products_vector_store(embedding_model)
        if products_store:
            stats["products_available"] = True
            # Try to get approximate count by searching
            results = products_store.similarity_search("", k=1000)  # Large k to get estimate
            stats["products_count"] = f"~{len(results)}+" if len(results) == 1000 else len(results)
    except:
        pass
    
    # Check skin conditions store
    try:
        conditions_store = load_skin_conditions_vector_store(embedding_model)
        if conditions_store:
            stats["skin_conditions_available"] = True
            results = conditions_store.similarity_search("", k=100)
            stats["skin_conditions_count"] = f"~{len(results)}+" if len(results) == 100 else len(results)
    except:
        pass
    
    return stats
