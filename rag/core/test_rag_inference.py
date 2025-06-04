#!/usr/bin/env python
"""
Script for testing RAG inference and running queries.
This script loads existing embeddings from the database and runs queries
using the RAG chain to test the system's performance.
"""

import os
import argparse
import json
import tiktoken
from datetime import datetime
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']
if 'SSL_CERT_DIR' in os.environ:
    del os.environ['SSL_CERT_DIR']

# LangChain components
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI

# Import our modular components
import config
from data_loader import load_skin_condition_profiles
from langchain_community.vectorstores.pgvector import PGVector
from rag_chain import get_rag_chain
from utils import setup_environment, test_db_connection

load_dotenv()

def create_embeddings_model():
    """Create and return the embedding model."""
    print(f"Creating embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}")
    return HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}  # Use 'cuda' for GPU if available
    )

def load_vector_store(embeddings_model, collection_name: str):
    """Load an existing vector store from the database."""
    print(f"\n=== Loading Vector Store: {collection_name} ===")
    
    # Test database connection
    if not test_db_connection(config.DATABASE_CONNECTION_STRING):
        print(f"Failed to connect to database.")
        return None
    
    try:
        # Connect directly to the existing LangChain vector store
        # (embeddings should already exist from create_embeddings.py)
        vector_store = PGVector(
            embedding_function=embeddings_model,
            connection_string=config.DATABASE_CONNECTION_STRING,
            collection_name=collection_name
        )
        
        # Test the connection with a sample search
        test_results = vector_store.similarity_search("test", k=1)
        print(f"✓ Successfully loaded vector store: {collection_name} ({len(test_results)} test results)")
        return vector_store
        
    except Exception as e:
        print(f"✗ Error loading vector store '{collection_name}': {e}")
        print("Make sure embeddings have been created using create_embeddings.py")
        return None

def setup_rag_chain(vector_store):
    """Set up the RAG chain for querying."""
    if not vector_store:
        print("Vector store not available. Cannot set up RAG chain.")
        return None
        
    # Check for OpenAI API key
    if not config.OPENAI_API_KEY:
        print("OpenAI API key not found. Please check your .env file.")
        return None
        
    try:
        print("Setting up RAG chain...")
        llm = ChatOpenAI(model=config.LLM_MODEL_NAME, api_key=config.OPENAI_API_KEY)
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        chain = get_rag_chain(llm, retriever)
        print("✓ RAG chain setup successful!")
        return chain
        
    except Exception as e:
        print(f"✗ Error setting up RAG chain: {e}")
        return None

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to rough estimation
        return len(text.split()) * 4 // 3

def calculate_similarity_score(vector_store, query: str, doc_id: str) -> float:
    """Calculate similarity score between query and document."""
    try:
        # Use similarity_search_with_score to get similarity scores
        results = vector_store.similarity_search_with_score(query, k=10)
        for doc, score in results:
            if doc.metadata.get('id') == doc_id or doc.metadata.get('product_id') == doc_id:
                return float(score)
        return 0.0
    except Exception as e:
        print(f"Warning: Could not calculate similarity score: {e}")
        return 0.0

def run_example_queries(chain, skin_conditions, vector_store=None):
    """Run some example queries against the RAG chain."""
    if not chain:
        print("Cannot run example queries - RAG chain not available.")
        return
    
    print(f"\n{'='*50}")
    print("RUNNING EXAMPLE QUERIES")
    print(f"{'='*50}")
    
    # Initialize results storage
    rag_results = {
        "timestamp": datetime.now().isoformat(),
        "model": config.LLM_MODEL_NAME,
        "total_queries": 0,
        "successful_queries": 0,
        "queries": []
    }
    
    # Define example queries
    queries = {
        "General Oily Skin": "What products do you recommend for oily skin and why?",
        "Redness Concern": "My skin is often red and irritated, what can help calm it down?",
        "Anti-Aging": "I'm looking for products to help with fine lines and wrinkles. What do you recommend?",
        "Dry Skin": "My skin feels very dry and tight. What moisturizing products would help?",
        "Acne Treatment": "I have acne-prone skin. What products would be best for treating breakouts?"
    }
    
    # Add skin condition profile queries if available
    if skin_conditions:
        for condition_name, description in skin_conditions.items():
            if description.strip():  # Only add if description is not empty
                queries[f"{condition_name} Profile Match"] = description[:200] + "..." if len(description) > 200 else description
    
    successful_queries = 0
    total_queries = len(queries)
    rag_results["total_queries"] = total_queries
    
    for name, query in queries.items():
        if not query.strip():
            print(f"Skipping {name} - no query available")
            continue
            
        print(f"\n{'-'*30}")
        print(f"Query: {name}")
        print(f"{'-'*30}")
        print(f"Question: {query[:150]}{'...' if len(query) > 150 else ''}")
        
        try:
            response = chain.invoke({"query": query})
            ai_response = response['result']
            source_docs = response['source_documents']
            
            # Count tokens in the response
            token_count = count_tokens(ai_response, config.LLM_MODEL_NAME)
            
            print("\n🤖 AI Response:")
            print(ai_response)
            print(f"\n📊 Token Count: {token_count}")
            
            # Process source documents with similarity scores
            source_documents_info = []
            print(f"\n📚 Source Documents ({len(source_docs)}):")
            for i, doc in enumerate(source_docs[:3]):  # Show top 3 sources
                doc_name = doc.metadata.get('name', doc.metadata.get('condition_name', 'Unknown'))
                doc_type = doc.metadata.get('document_type', 'unknown')
                doc_id = doc.metadata.get('id', doc.metadata.get('product_id', 'unknown'))
                
                # Try to get similarity score if vector store is available
                similarity_score = 0.0
                if vector_store:
                    similarity_score = calculate_similarity_score(vector_store, query, str(doc_id))
                
                source_info = {
                    "rank": i + 1,
                    "name": doc_name,
                    "type": doc_type,
                    "id": doc_id,
                    "similarity_score": similarity_score,
                    "content_preview": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                }
                source_documents_info.append(source_info)
                
                print(f"  {i+1}. {doc_name} (type: {doc_type}, similarity: {similarity_score:.4f})")
            
            # Store query result
            query_result = {
                "query_name": name,
                "question": query,
                "answer": ai_response,
                "token_count": token_count,
                "source_documents": source_documents_info,
                "timestamp": datetime.now().isoformat()
            }
            rag_results["queries"].append(query_result)
            
            successful_queries += 1
            
        except Exception as e:
            print(f"✗ Error running query: {e}")
            # Store failed query
            query_result = {
                "query_name": name,
                "question": query,
                "answer": None,
                "error": str(e),
                "token_count": 0,
                "source_documents": [],
                "timestamp": datetime.now().isoformat()
            }
            rag_results["queries"].append(query_result)
    
    rag_results["successful_queries"] = successful_queries
    
    # Save results to JSON file
    output_file = "rag_output.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(rag_results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"✗ Error saving results to JSON: {e}")
    
    print(f"\n{'='*50}")
    print(f"QUERY RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"Successful queries: {successful_queries}/{total_queries}")
    if successful_queries > 0:
        total_tokens = sum(q.get("token_count", 0) for q in rag_results["queries"] if q.get("token_count"))
        avg_tokens = total_tokens / successful_queries if successful_queries > 0 else 0
        print(f"Total tokens used: {total_tokens}")
        print(f"Average tokens per response: {avg_tokens:.1f}")
    
    return rag_results
    
    if successful_queries == total_queries:
        print("🎉 All queries executed successfully!")
    else:
        print("⚠️  Some queries failed. Check the logs above for details.")

def run_interactive_mode(chain):
    """Run interactive query mode where user can input custom questions."""
    if not chain:
        print("Cannot run interactive mode - RAG chain not available.")
        return
        
    print(f"\n{'='*50}")
    print("INTERACTIVE QUERY MODE")
    print(f"{'='*50}")
    print("Enter your skincare questions (type 'quit' to exit):")
    
    while True:
        try:
            user_query = input("\n🧴 Your question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
                
            if not user_query:
                print("Please enter a question.")
                continue
                
            print(f"\n🤖 AI Response:")
            response = chain.invoke({"query": user_query})
            print(response['result'])
            
            # Optionally show sources
            show_sources = input("\nShow source documents? (y/n): ").strip().lower()
            if show_sources in ['y', 'yes']:
                print(f"\n📚 Source Documents:")
                for i, doc in enumerate(response["source_documents"][:3]):
                    doc_name = doc.metadata.get('name', doc.metadata.get('condition_name', 'Unknown'))
                    doc_type = doc.metadata.get('document_type', 'unknown')
                    print(f"  {i+1}. {doc_name} (type: {doc_type})")
                    
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"✗ Error: {e}")

def main():
    """Main entry point for RAG inference testing."""
    # Check environment setup
    if not setup_environment():
        print("Environment setup failed. Please fix the issues above and try again.")
        return
        
    parser = argparse.ArgumentParser(description="Test RAG inference and run queries.")
    parser.add_argument("--products-only", action="store_true", 
                       help="Use only product vector store for queries.")
    parser.add_argument("--conditions-only", action="store_true", 
                       help="Use only skin conditions vector store for queries.")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode for custom queries.")
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
    
    # Create embedding model
    embedding_model = create_embeddings_model()
    
    # Determine which vector store to use (default to products)
    if args.conditions_only:
        collection_name = config.CLASS_DESCRIPTIONS_COLLECTION_NAME
    else:
        collection_name = config.PRODUCTS_COLLECTION_NAME
    
    # Load vector store
    vector_store = load_vector_store(embedding_model, collection_name)
    if not vector_store:
        print(f"Failed to load vector store '{collection_name}'. Make sure embeddings have been created first.")
        print("Run 'python create_embeddings.py' to create embeddings.")
        return
    
    # Setup RAG chain
    chain = setup_rag_chain(vector_store)
    if not chain:
        print("Failed to setup RAG chain. Cannot proceed with queries.")
        return
    
    # Load skin conditions for example queries
    skin_conditions = load_skin_condition_profiles(config.CLASS_DESCRIPTIONS_MODULE)
      # Run queries
    if args.interactive:
        run_interactive_mode(chain)
    else:
        run_example_queries(chain, skin_conditions, vector_store)

if __name__ == "__main__":
    # Enable more detailed logging
    import logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    main()
