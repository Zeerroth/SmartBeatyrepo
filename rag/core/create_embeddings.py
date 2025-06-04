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
from custom_vector_store import CustomDatabaseVectorManager
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
    """Process product data from database and store embeddings."""
    # Test database connection
    if not test_db_connection(config.DATABASE_CONNECTION_STRING):
        print("Failed to connect to database. Please check your connection settings.")
        return None
    
    # Use custom vector store manager
    try:
        vector_manager = CustomDatabaseVectorManager(
            embedding_model=embeddings_model,
            connection_string=config.DATABASE_CONNECTION_STRING
        )
        
        return vector_manager.process_products(rebuild=rebuild)
        
    except Exception as e:
        print(f"Error processing products: {e}")
        return None

def process_skin_conditions(embeddings_model, rebuild: bool = False):
    """Process skin condition data from database and store embeddings."""
    # Test database connection
    if not test_db_connection(config.DATABASE_CONNECTION_STRING):
        print("Failed to connect to database. Please check your connection settings.")
        return None
    
    # Use custom vector store manager
    try:
        vector_manager = CustomDatabaseVectorManager(
            embedding_model=embeddings_model,
            connection_string=config.DATABASE_CONNECTION_STRING
        )
        
        return vector_manager.process_skin_conditions(rebuild=rebuild)
        
    except Exception as e:
        print(f"Error processing skin conditions: {e}")
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
    
    # Show embedding statistics
    if success_count > 0:
        try:
            vector_manager = CustomDatabaseVectorManager(
                embedding_model=embedding_model,
                connection_string=config.DATABASE_CONNECTION_STRING
            )
            stats = vector_manager.get_embedding_stats()
            
            print(f"\nCurrent Embedding Statistics:")
            for collection_name, count in stats.items():
                print(f"  📊 {collection_name}: {count} embeddings")
                
        except Exception as e:
            print(f"Could not retrieve embedding statistics: {e}")
    
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
