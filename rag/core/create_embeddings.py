#!/usr/bin/env python
"""
Script for creating embeddings and storing them in the database.
This script handles the processing of product and skin condition data,
creating embeddings and storing them in the PostgreSQL vector database.
"""

import os
import argparse
import json
import traceback
from typing import Optional
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']
if 'SSL_CERT_DIR' in os.environ:
    del os.environ['SSL_CERT_DIR']

# LangChain components
from langchain_community.embeddings import HuggingFaceEmbeddings

# Import our modular components
import config
from data_loader import load_raw_product_data, load_skin_condition_profiles
from document_processor import prepare_product_documents, prepare_skin_condition_documents
from vector_store import PGVectorStoreManager
from utils import setup_environment, test_db_connection

load_dotenv()

def create_embeddings_model():
    """Create and return the embedding model."""
    print(f"Creating embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}")
    return HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
    )

def process_products(embeddings_model, rebuild: bool = False):
    """Process product data and store in vector database."""
    print("\n=== Processing Product Data ===")
    
    # Check if collection name is set
    if not config.PRODUCTS_COLLECTION_NAME:
        print("Error: PRODUCTS_COLLECTION_NAME is not set in config.py")
        return None
    
    print(f"Using collection name: {config.PRODUCTS_COLLECTION_NAME}")
    
    # Test database connection
    if not test_db_connection(config.DATABASE_CONNECTION_STRING):
        print("Failed to connect to database. Please check your connection settings.")
        return None
    
    # Load raw product data
    raw_products = load_raw_product_data(
        config.DATA_SOURCE_TYPE, 
        filepath=config.PRODUCT_JSON_FILEPATH
    )
    
    if not raw_products:
        print("No product data found. Skipping product processing.")
        return None
    
    # Process into LangChain documents
    product_documents = prepare_product_documents(
        raw_products,
        config.PRODUCT_FEATURES_FOR_EMBEDDING,
        config.FEATURE_LABELS
    )
    
    if not product_documents:
        print("Failed to prepare product documents. Skipping vector store creation.")
        return None
    
    # Store in vector database
    try:
        vector_store_manager = PGVectorStoreManager(
            embedding_model=embeddings_model,
            connection_string=config.DATABASE_CONNECTION_STRING,
            collection_name=config.PRODUCTS_COLLECTION_NAME
        )
        
        vector_store = vector_store_manager.build_or_load_store(
            documents=product_documents, 
            pre_delete_collection=rebuild
        )
        
        print(f"Successfully processed {len(product_documents)} product documents")
        return vector_store
        
    except Exception as e:
        print(f"Error creating product vector store: {e}")
        return None

def process_skin_conditions(embeddings_model, rebuild: bool = False):
    """Process skin condition data and store in vector database."""
    print("\n=== Processing Skin Condition Data ===")
    
    # Test database connection
    if not test_db_connection(config.DATABASE_CONNECTION_STRING):
        print("Failed to connect to database. Please check your connection settings.")
        return None
    
    # Load skin condition profiles
    skin_conditions = load_skin_condition_profiles(config.CLASS_DESCRIPTIONS_MODULE)
    
    if not skin_conditions:
        print("No skin condition data found. Skipping skin condition processing.")
        return None
    
    # Process into LangChain documents
    condition_documents = prepare_skin_condition_documents(skin_conditions)
    
    if not condition_documents:
        print("Failed to prepare skin condition documents. Skipping vector store creation.")
        return None
    
    # Store in vector database
    try:
        vector_store_manager = PGVectorStoreManager(
            embedding_model=embeddings_model,
            connection_string=config.DATABASE_CONNECTION_STRING,
            collection_name=config.CLASS_DESCRIPTIONS_COLLECTION_NAME
        )
        
        vector_store = vector_store_manager.build_or_load_store(
            documents=condition_documents, 
            pre_delete_collection=rebuild
        )
        
        print(f"Successfully processed {len(condition_documents)} skin condition documents")
        return vector_store
        
    except Exception as e:
        print(f"Error creating skin condition vector store: {e}")
        return None

def main():
    """Main entry point for creating embeddings and storing them in the database."""
    # Check environment setup
    if not setup_environment():
        print("Environment setup failed. Please fix the issues above and try again.")
        return
        
    parser = argparse.ArgumentParser(description="Create embeddings and store them in the database.")
    parser.add_argument("--rebuild", action="store_true", 
                       help="Rebuild the vector stores (delete existing data).")
    parser.add_argument("--products-only", action="store_true", 
                       help="Process only product data.")
    parser.add_argument("--conditions-only", action="store_true", 
                       help="Process only skin condition data.")
    parser.add_argument("--test-connection", action="store_true",
                       help="Test database connection only.")
    args = parser.parse_args()
    
    # Test connection only
    if args.test_connection:
        print("Testing database connection...")
        success = test_db_connection(config.DATABASE_CONNECTION_STRING, config.PRODUCTS_COLLECTION_NAME)
        if success:
            print("Database connection test passed!")
        else:
            print("Database connection test failed!")
        return
    
    # Default to processing both if neither is specified
    process_all = not args.products_only and not args.conditions_only
    
    # Create embedding model
    embedding_model = create_embeddings_model()
    
    # Process data
    success_count = 0
    
    if args.products_only or process_all:
        print(f"\n{'='*50}")
        print("CREATING PRODUCT EMBEDDINGS")
        print(f"{'='*50}")
        product_store = process_products(embedding_model, args.rebuild)
        if product_store:
            success_count += 1
            print("✓ Product embeddings created successfully!")
        else:
            print("✗ Failed to create product embeddings.")
            
    if args.conditions_only or process_all:
        print(f"\n{'='*50}")
        print("CREATING SKIN CONDITION EMBEDDINGS")
        print(f"{'='*50}")
        condition_store = process_skin_conditions(embedding_model, args.rebuild)
        if condition_store:
            success_count += 1
            print("✓ Skin condition embeddings created successfully!")
        else:
            print("✗ Failed to create skin condition embeddings.")
    
    # Summary
    total_tasks = (1 if args.products_only else 0) + (1 if args.conditions_only else 0)
    if process_all:
        total_tasks = 2
        
    print(f"\n{'='*50}")
    print(f"EMBEDDING CREATION SUMMARY")
    print(f"{'='*50}")
    print(f"Tasks completed successfully: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("🎉 All embedding creation tasks completed successfully!")
    else:
        print("⚠️  Some embedding creation tasks failed. Check the logs above for details.")

if __name__ == "__main__":
    # Enable more detailed logging
    import logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    main()
