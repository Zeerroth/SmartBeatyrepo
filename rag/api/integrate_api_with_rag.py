#!/usr/bin/env python
"""
Integration script for using the RAGDataAPI with the existing RAG chain.

This script demonstrates how the API wrapper can be integrated with the existing
LangChain-based RAG system to provide a unified interface for both database-direct
and LangChain approaches.

Usage:
python integrate_api_with_rag.py "What products are good for acne?"
"""
import os
import sys
import argparse
from typing import List, Dict

# Add the parent directory to sys.path to import local modules
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import local modules
import rag.core.config as config
from api_wrapper import RAGDataAPI
from rag_chain import get_rag_chain

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Integrate API wrapper with RAG chain.")
    parser.add_argument("query", type=str, help="Query to process")
    parser.add_argument("--top_k", type=int, default=5, help="Number of top results to retrieve")
    parser.add_argument("--use_langchain", action="store_true", help="Use LangChain approach for retrieval")
    return parser.parse_args()

class APIRetriever:
    """Custom retriever that uses RAGDataAPI for document retrieval."""
    
    def __init__(self, api: RAGDataAPI, top_k: int = 5):
        """
        Initialize the retriever with the API.
        
        Args:
            api: RAGDataAPI instance
            top_k: Number of top results to retrieve
        """
        self.api = api
        self.top_k = top_k
    
    def get_relevant_documents(self, query: str) -> List[Dict]:
        """
        Get relevant documents for the query.
        
        Args:
            query: Query string
            
        Returns:
            List of documents with page_content and metadata
        """
        print(f"Retrieving documents for query: {query}")
        
        # Create embedding for the query
        embedding = self.api.create_embedding(query)
        
        # Find similar products using the embedding
        similar_products = self.api.find_similar_products(embedding, top_n=self.top_k)
        
        # Convert to LangChain document format
        documents = []
        for product in similar_products:
            # Create embedding text from product data
            product_text = self.api.get_product_embedding_text(product["data"])
            
            # Create document with metadata
            documents.append({
                "page_content": product_text,
                "metadata": {
                    "product_id": product["id"],
                    "name": product["name"],
                    "similarity": product["similarity"],
                    "document_type": "product"
                }
            })
        
        print(f"Found {len(documents)} relevant documents")
        return documents

def setup_langchain_retrieval():
    """Set up LangChain retrieval using the Vector Store."""
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from vector_store import PGVectorStoreManager
    
    print("Setting up LangChain retrieval...")
    
    # Initialize embedding model
    embedding_model = HuggingFaceEmbeddings(
        model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
        model_kwargs={'device': 'cpu'}
    )
    
    # Initialize vector store manager
    vector_store_manager = PGVectorStoreManager(
        embedding_model=embedding_model,
        connection_string=config.DATABASE_CONNECTION_STRING,
        collection_name="products"
    )
    
    # Connect to the vector store
    vector_store = vector_store_manager.build_or_load_store()
    
    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    
    print("LangChain retrieval setup complete.")
    return retriever

def setup_api_retrieval():
    """Set up API-based retrieval."""
    print("Setting up API-based retrieval...")
    api = RAGDataAPI()
    retriever = APIRetriever(api)
    print("API retrieval setup complete.")
    return retriever

def setup_llm():
    """Set up the language model for the RAG chain."""
    from langchain_openai import ChatOpenAI
    
    print("Setting up language model...")
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo", 
        temperature=0.3
    )
    print("Language model setup complete.")
    return llm

def main():
    """Main function to integrate API with RAG chain."""
    args = parse_args()
    
    # Set up retriever based on user preference
    if args.use_langchain:
        print("\n--- Using LangChain approach ---")
        retriever = setup_langchain_retrieval()
    else:
        print("\n--- Using API wrapper approach ---")
        retriever = setup_api_retrieval()
    
    # Set up language model
    llm = setup_llm()
    
    # Create RAG chain
    print("\nCreating RAG chain...")
    rag_chain = get_rag_chain(llm, retriever)
    
    # Process query
    print(f"\nProcessing query: '{args.query}'")
    result = rag_chain.invoke({"query": args.query})
    
    # Print result
    print("\nAnswer:")
    print(result["result"])
    
    # Print source documents
    print("\nSource Documents Used:")
    for i, doc in enumerate(result["source_documents"], 1):
        print(f"\n{i}. {doc.metadata.get('name', 'Unnamed product')}")
        if 'similarity' in doc.metadata:
            print(f"   Similarity: {doc.metadata['similarity']:.4f}")
        print(f"   {doc.page_content[:100]}...")
    
    return 0

if __name__ == "__main__":
    main()
