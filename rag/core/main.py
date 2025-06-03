#!/usr/bin/env python
"""
Main entry point for the SmartBeauty RAG system.

This file provides a unified interface to the RAG system's functionality:
- Creating embeddings and storing them in the database (create_embeddings.py)
- Testing RAG inference and running queries (test_rag_inference.py)

Use this file as the main entry point, or run the individual scripts directly
for more specific functionality.
"""

import os
import argparse
import subprocess
import sys
from dotenv import load_dotenv

# Import our modular components
import config
from utils import setup_environment, test_db_connection

load_dotenv()

def run_script(script_name: str, args: list):
    """Run a Python script with the given arguments."""
    try:
        cmd = [sys.executable, script_name] + args
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    """Main entry point for the SmartBeauty RAG system."""
    print("🧴 SmartBeauty RAG System")
    print("=" * 50)
    
    # Check environment setup
    if not setup_environment():
        print("Environment setup failed. Please fix the issues above and try again.")
        return
        
    parser = argparse.ArgumentParser(
        description="SmartBeauty RAG System - Main Entry Point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create embeddings for both products and skin conditions
  python main.py --create-embeddings
  
  # Create embeddings with rebuild (delete existing data)
  python main.py --create-embeddings --rebuild
  
  # Create only product embeddings
  python main.py --create-embeddings --products-only
  
  # Test RAG inference with example queries
  python main.py --test-inference
  
  # Run interactive RAG mode
  python main.py --test-inference --interactive
  
  # Test database connection
  python main.py --test-connection
  
  # Do everything: create embeddings then test inference
  python main.py --all
        """
    )
    
    # Main action groups
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--create-embeddings", action="store_true",
                             help="Create and store embeddings in the database")
    action_group.add_argument("--test-inference", action="store_true",
                             help="Test RAG inference with queries")
    action_group.add_argument("--test-connection", action="store_true",
                             help="Test database connection")
    action_group.add_argument("--all", action="store_true",
                             help="Create embeddings then test inference")
    
    # Options for create-embeddings
    parser.add_argument("--rebuild", action="store_true",
                       help="Rebuild vector stores (delete existing data)")
    parser.add_argument("--products-only", action="store_true",
                       help="Process only product data")
    parser.add_argument("--conditions-only", action="store_true",
                       help="Process only skin condition data")
    
    # Options for test-inference
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode for custom queries")
    
    args = parser.parse_args()
    
    # Test connection only
    if args.test_connection:
        print("Testing database connection...")
        success = test_db_connection(config.DATABASE_CONNECTION_STRING, config.PRODUCTS_COLLECTION_NAME)
        if success:
            print("✅ Database connection test passed!")
        else:
            print("❌ Database connection test failed!")
        return
    
    success = True
    
    # Create embeddings
    if args.create_embeddings or args.all:
        print("\n🔧 CREATING EMBEDDINGS")
        print("=" * 50)
        
        embedding_args = []
        if args.rebuild:
            embedding_args.append("--rebuild")
        if args.products_only:
            embedding_args.append("--products-only")
        if args.conditions_only:
            embedding_args.append("--conditions-only")
            
        success = run_script("create_embeddings.py", embedding_args)
        
        if not success:
            print("❌ Embedding creation failed!")
            if not args.all:
                return
    
    # Test inference
    if args.test_inference or args.all:
        if args.all:
            print("\n" + "=" * 50)
            
        print("\n🧠 TESTING RAG INFERENCE")
        print("=" * 50)
        
        inference_args = []
        if args.products_only:
            inference_args.append("--products-only")
        if args.conditions_only:
            inference_args.append("--conditions-only")
        if args.interactive:
            inference_args.append("--interactive")
            
        success = success and run_script("test_rag_inference.py", inference_args)
        
        if not success:
            print("❌ RAG inference testing failed!")
            return
    
    if success:
        print("\n🎉 All operations completed successfully!")
    else:
        print("\n❌ Some operations failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
