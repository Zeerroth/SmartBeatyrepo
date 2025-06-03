#!/usr/bin/env python
"""
Script to search for products and skin conditions using vector similarity search.

This script:
1. Takes a search query as input
2. Converts the query to an embedding using the same model as used for embeddings
3. Performs vector similarity search against products and/or skin conditions
4. Returns the top N most similar results

Usage:
python search.py "skincare for dry skin" [--top_n 5] [--table all|products|skin_conditions]

Arguments:
query: The search query
--top_n: Number of top results to return (default: 5)
--table: Which table to search (default: all)
"""
import os
import sys
import argparse
import psycopg2
import json

# Add the parent directory to sys.path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, parent_dir)

# Import local modules
import rag.core.config as config

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Search using vector similarity.")
    parser.add_argument("query", type=str, help="Search query text")
    parser.add_argument("--top_n", type=int, default=5, help="Number of top results to return")
    parser.add_argument("--table", type=str, default="all", choices=["all", "products", "skin_conditions"],
                        help="Which table to search")
    parser.add_argument("--output", type=str, default="search_results.json", help="Output JSON file")
    return parser.parse_args()

def create_embeddings_model():
    """Create and return the embedding model."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    
    print(f"Loading embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}...")
    return HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
    )

def search_products(conn, query_embedding, top_n):
    """
    Search for products by vector similarity.
    
    Args:
        conn: PostgreSQL connection object
        query_embedding: Vector embedding of the search query
        top_n: Number of top results to return
        
    Returns:
        List of dictionaries with product info and similarity score
    """
    # Convert embedding to string format that pgvector can parse
    import numpy as np
    query_embedding_str = str(query_embedding)
    
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
        """, (query_embedding_str, top_n))
        
        results = []
        for row in cursor.fetchall():
            product_id, name, original_data, similarity = row
            results.append({
                "id": product_id,
                "name": name,
                "similarity": float(similarity),  # Convert Decimal to float for JSON serialization
                "original_data": original_data,
                "type": "product"
            })
        
        return results

def search_skin_conditions(conn, query_embedding, top_n):
    """
    Search for skin conditions by vector similarity.
    
    Args:
        conn: PostgreSQL connection object
        query_embedding: Vector embedding of the search query
        top_n: Number of top results to return
        
    Returns:
        List of dictionaries with skin condition info and similarity score
    """
    # Convert embedding to string format that pgvector can parse
    import numpy as np
    query_embedding_str = str(query_embedding)
    
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
        """, (query_embedding_str, top_n))
        
        results = []
        for row in cursor.fetchall():
            condition_id, name, description, similarity = row
            results.append({
                "id": condition_id,
                "name": name,
                "description": description[:200] + "..." if len(description) > 200 else description,  # Truncate long descriptions
                "similarity": float(similarity),  # Convert Decimal to float for JSON serialization
                "type": "skin_condition"
            })
        
        return results

def main():
    """Main function to search for products and skin conditions."""
    args = parse_args()
    
    # Extract connection parameters from the connection string
    conn_string = config.DATABASE_CONNECTION_STRING
    params_part = conn_string.split("://")[1]
    user_pass, host_port_db = params_part.split("@")
    user, password = user_pass.split(":")
    host_port, dbname = host_port_db.split("/")
    host, port = host_port.split(":")
    
    # Load embedding model and generate query embedding
    embedding_model = create_embeddings_model()
    print(f"Generating embedding for query: '{args.query}'")
    query_embedding = embedding_model.embed_query(args.query)
    
    # Connect to PostgreSQL and search
    print(f"Connecting to PostgreSQL at {host}:{port}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname
        )
        
        # Initialize results containers
        product_results = []
        skin_condition_results = []
        
        # Search products if requested
        if args.table in ["all", "products"]:
            product_results = search_products(conn, query_embedding, args.top_n)
            
        # Search skin conditions if requested
        if args.table in ["all", "skin_conditions"]:
            skin_condition_results = search_skin_conditions(conn, query_embedding, args.top_n)
        
        conn.close()
        
        # Combine and sort results by similarity
        all_results = product_results + skin_condition_results
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Limit to top_n overall if searching both tables
        if args.table == "all":
            all_results = all_results[:args.top_n]
        
        # Display results
        print(f"\nTop {len(all_results)} results for '{args.query}':")
        print("-" * 80)
        
        for i, result in enumerate(all_results, 1):
            result_type = "Product" if result["type"] == "product" else "Skin Condition"
            print(f"{i}. [{result_type}] {result['name']} (ID: {result['id']})")
            print(f"   Similarity: {result['similarity']:.4f}")
            
            if result["type"] == "product":
                # Get key benefits if available
                key_benefits = result['original_data'].get('keyBenefits', '')
                if key_benefits:
                    if isinstance(key_benefits, list):
                        key_benefits = ', '.join(key_benefits)
                    print(f"   Key Benefits: {key_benefits[:150]}..." if len(str(key_benefits)) > 150 else f"   Key Benefits: {key_benefits}")
            else:
                # Show beginning of description for skin conditions
                print(f"   Description: {result['description'][:150]}..." if len(result['description']) > 150 else f"   Description: {result['description']}")
                
            print("-" * 80)
        
        # Save results to file for reference
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"Detailed results saved to {args.output}")
        
    except Exception as e:
        print(f"Error searching: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
