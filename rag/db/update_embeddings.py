#!/usr/bin/env python
"""
Script to update the embeddings in the products and skin_conditions tables.

This script:
1. Processes entries from both products and skin_conditions tables that don't have embeddings
2. Uses HuggingFace model to create embeddings
3. Updates the database with the embeddings

Usage:
python update_embeddings.py [--batch_size 10] [--table all|products|skin_conditions]

Optional arguments:
--batch_size: Number of items to process at once (default: 10)
--table: Which table to update (default: all)
"""
import os
import sys
import argparse
import psycopg2
import numpy as np

# Add the parent directory to sys.path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

# Import local modules
import rag.core.config as config

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Update embeddings in the database.")
    parser.add_argument("--batch_size", type=int, default=10, help="Number of items to process at once")
    parser.add_argument("--table", type=str, default="all", choices=["all", "products", "skin_conditions"],
                        help="Which table to update")
    return parser.parse_args()

def create_embeddings_model():
    """Create and return the embedding model."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    print(f"Loading embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}...")
    return HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
    )

def get_products_without_embeddings(conn, batch_size):
    """
    Get products from the database that don't have embeddings.
    
    Args:
        conn: PostgreSQL connection object
        batch_size: Number of products to fetch at once
        
    Returns:
        List of tuples (id, embedding_text_concatenated)
    """
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT id, embedding_text_concatenated
        FROM products
        WHERE embedding_vector IS NULL AND embedding_text_concatenated IS NOT NULL
        LIMIT %s
        """, (batch_size,))
        return cursor.fetchall()

def get_skin_conditions_without_embeddings(conn, batch_size):
    """
    Get skin conditions from the database that don't have embeddings.
    
    Args:
        conn: PostgreSQL connection object
        batch_size: Number of skin conditions to fetch at once
        
    Returns:
        List of tuples (id, description)
    """
    with conn.cursor() as cursor:
        cursor.execute("""
        SELECT id, description
        FROM skin_conditions
        WHERE embedding_vector IS NULL
        LIMIT %s
        """, (batch_size,))
        return cursor.fetchall()

def update_product_embedding(conn, product_id, embedding):
    """
    Update the embedding for a product in the database.
    
    Args:
        conn: PostgreSQL connection object
        product_id: ID of the product to update
        embedding: Vector embedding to store
    """
    with conn.cursor() as cursor:
        # Pass the embedding as is - PostgreSQL will handle the conversion
        cursor.execute("""
        UPDATE products
        SET embedding_vector = %s::vector
        WHERE id = %s
        """, (embedding, product_id))

def update_skin_condition_embedding(conn, condition_id, embedding):
    """
    Update the embedding for a skin condition in the database.
    
    Args:
        conn: PostgreSQL connection object
        condition_id: ID of the skin condition to update
        embedding: Vector embedding to store
    """
    with conn.cursor() as cursor:
        # Pass the embedding as is - PostgreSQL will handle the conversion
        cursor.execute("""
        UPDATE skin_conditions
        SET embedding_vector = %s::vector
        WHERE id = %s
        """, (embedding, condition_id))

def update_products(conn, embedding_model, batch_size):
    """
    Update product embeddings in batches.
    
    Args:
        conn: PostgreSQL connection object
        embedding_model: The embedding model to use
        batch_size: Number of products to process at once
        
    Returns:
        Number of products updated
    """
    total_updated = 0
    while True:
        # Get batch of products without embeddings
        products = get_products_without_embeddings(conn, batch_size)
        if not products:
            print("No more products without embeddings.")
            break
        
        print(f"Processing batch of {len(products)} products...")
        for i, (product_id, text) in enumerate(products, 1):
            try:
                # Generate embedding
                embedding = embedding_model.embed_query(text)
                
                # Convert to string format that pgvector can parse
                embedding_str = str(embedding)
                
                # Update the product
                update_product_embedding(conn, product_id, embedding_str)
                total_updated += 1
                print(f"Updated embedding for product {product_id} ({i}/{len(products)} in batch)")
            except Exception as e:
                print(f"Error updating embedding for product {product_id}: {e}")
                conn.rollback()
        
        # Commit after each batch
        conn.commit()
        print(f"Committed batch of {len(products)} products.")
    
    return total_updated

def update_skin_conditions(conn, embedding_model, batch_size):
    """
    Update skin condition embeddings in batches.
    
    Args:
        conn: PostgreSQL connection object
        embedding_model: The embedding model to use
        batch_size: Number of skin conditions to process at once
        
    Returns:
        Number of skin conditions updated
    """
    total_updated = 0
    while True:
        # Get batch of skin conditions without embeddings
        conditions = get_skin_conditions_without_embeddings(conn, batch_size)
        if not conditions:
            print("No more skin conditions without embeddings.")
            break
        
        print(f"Processing batch of {len(conditions)} skin conditions...")
        for i, (condition_id, description) in enumerate(conditions, 1):
            try:
                # Generate embedding
                embedding = embedding_model.embed_query(description)
                
                # Convert to string format that pgvector can parse
                embedding_str = str(embedding)
                
                # Update the skin condition
                update_skin_condition_embedding(conn, condition_id, embedding_str)
                total_updated += 1
                print(f"Updated embedding for skin condition {condition_id} ({i}/{len(conditions)} in batch)")
            except Exception as e:
                print(f"Error updating embedding for skin condition {condition_id}: {e}")
                conn.rollback()
        
        # Commit after each batch
        conn.commit()
        print(f"Committed batch of {len(conditions)} skin conditions.")
    
    return total_updated

def main():
    """Main function to update embeddings."""
    args = parse_args()
    
    # Extract connection parameters from the connection string
    conn_string = config.DATABASE_CONNECTION_STRING
    params_part = conn_string.split("://")[1]
    user_pass, host_port_db = params_part.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = host_port_db.split("/")
    host, port = host_port.split(":")
    
    # Load embedding model
    embedding_model = create_embeddings_model()
    
    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL at {host}:{port}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        
        products_updated = 0
        skin_conditions_updated = 0
        
        # Update products
        if args.table in ["all", "products"]:
            print("\n--- Processing Products ---")
            products_updated = update_products(conn, embedding_model, args.batch_size)
            print(f"Total products updated with embeddings: {products_updated}")
        
        # Update skin conditions
        if args.table in ["all", "skin_conditions"]:
            print("\n--- Processing Skin Conditions ---")
            skin_conditions_updated = update_skin_conditions(conn, embedding_model, args.batch_size)
            print(f"Total skin conditions updated with embeddings: {skin_conditions_updated}")
        
        conn.close()
        print("\nDatabase connection closed.")
        print(f"Summary: Updated {products_updated} products and {skin_conditions_updated} skin conditions.")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()