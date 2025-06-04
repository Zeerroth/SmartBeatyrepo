# filepath: c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\scripts\populate_products_table.py
#!/usr/bin/env python
"""
Script to populate the products table in PostgreSQL with data from the product_cache.json file.
This script extracts id, name, original product data, and creates a new row for each product.

Table schema:
- id: Primary key (integer) - From product's id
- name: Product name (text) - From product's name
- original_product_data: JSON data (jsonb) - The complete product object
- embedding_text_concatenated: Concatenated text for embedding (text) 
- embedding_vector: Vector data (vector) - To be filled later by update_embeddings.py

Usage:
python populate_products_table.py

The script reads configuration from config.py, including database connection and product file path.
"""
import os
import sys
import json
import psycopg2

# Add the parent directory to sys.path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, parent_dir)

# Import local modules
import rag.core.config as config
from rag.core.document_processor import create_embedding_text_from_features

def create_products_table(conn):
    """
    Create the products table if it doesn't exist.
    
    Args:
        conn: PostgreSQL connection object
    """
    with conn.cursor() as cursor:
        # Create the simplified products table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT
        );
        """)
        conn.commit()
        print("Products table created or already exists.")

def load_products_from_json(filepath):
    """
    Load products from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of product dictionaries
    """
    try:
        print(f"Loading products from {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract products list
        if isinstance(data, dict) and "products" in data:
            products = data["products"]
        elif isinstance(data, list):
            products = data
        else:
            raise ValueError(f"Unexpected data structure in {filepath}.")
        
        print(f"Successfully loaded {len(products)} products.")
        return products
    except Exception as e:
        print(f"Error loading products from {filepath}: {e}")
        return []

def generate_embedding_text(product_data):
    """
    Generate embedding text for a product using the document processor.
    
    Args:
        product_data: Product dictionary
        
    Returns:
        Concatenated text for embedding
    """
    return create_embedding_text_from_features(
        product_data,
        config.PRODUCT_FEATURES_FOR_EMBEDDING,
        config.FEATURE_LABELS
    )

def insert_product(cursor, product):
    """
    Insert a product into the products table.
    
    Args:
        cursor: PostgreSQL cursor
        product: Product dictionary
    """
    # Extract required fields
    product_id = product.get("id")
    name = product.get("name", "")
    
    # Generate embedding text using the document processor
    embedding_text = generate_embedding_text(product)
    
    # Insert the product with simplified structure
    cursor.execute("""
    INSERT INTO products (id, name, description)
    VALUES (%s, %s, %s)
    ON CONFLICT (id) DO UPDATE 
    SET name = EXCLUDED.name,
        description = EXCLUDED.description;
    """, (product_id, name, embedding_text))

def populate_products_table(conn, products):
    """
    Populate the products table with the provided list of products.
    
    Args:
        conn: PostgreSQL connection object
        products: List of product dictionaries
    """
    with conn.cursor() as cursor:
        for i, product in enumerate(products, 1):
            try:
                if not product.get("id"):
                    print(f"Skipping product without id: {product}")
                    continue
                
                insert_product(cursor, product)
                if i % 10 == 0 or i == len(products):
                    print(f"Processed {i}/{len(products)} products.")
                    conn.commit()
            except Exception as e:
                print(f"Error inserting product {product.get('id', 'unknown')}: {e}")
                conn.rollback()
    
    conn.commit()
    print("Products table population complete.")

def count_products_in_table(conn):
    """
    Count the number of products in the products table.
    
    Args:
        conn: PostgreSQL connection object
        
    Returns:
        Number of products in the table
    """
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        return count

def main():
    """Main function to populate the products table."""
    # Construct the correct path to product_cache.json (in core directory)
    script_dir = os.path.dirname(__file__)
    product_file_path = os.path.join(script_dir, "..", "core", "product_cache.json")
    
    # Load products from JSON
    products = load_products_from_json(product_file_path)
    if not products:
        print("No products to insert. Exiting.")
        return
    
    # Extract connection parameters from the connection string
    conn_string = config.DATABASE_CONNECTION_STRING
    params_part = conn_string.split("://")[1]
    user_pass, host_port_db = params_part.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = host_port_db.split("/")
    host, port = host_port.split(":")
    
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
        
        print("Connected to PostgreSQL. Creating table if it doesn't exist...")
        create_products_table(conn)
        
        # Count existing products
        initial_count = count_products_in_table(conn)
        print(f"Current product count in database: {initial_count}")
        
        # Populate the table
        print(f"Populating products table with {len(products)} products...")
        populate_products_table(conn, products)
        
        # Count after insertion
        final_count = count_products_in_table(conn)
        print(f"Final product count in database: {final_count}")
        print(f"Added {final_count - initial_count} new products.")
        
        conn.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
