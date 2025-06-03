# SmartBeauty RAG System - Split Architecture

This directory contains the core components of the SmartBeauty RAG (Retrieval-Augmented Generation) system, now split into modular components for better organization and maintainability.

## File Structure

### Main Entry Points

- **`main.py`** - Unified entry point for the entire system
- **`create_embeddings.py`** - Script for creating and storing embeddings in the database
- **`test_rag_inference.py`** - Script for testing RAG inference and running queries

### Core Components

- **`config.py`** - Configuration settings and environment variables
- **`utils.py`** - Utility functions including database connection helpers
- **`data_loader.py`** - Functions for loading raw data from various sources
- **`document_processor.py`** - Functions for processing documents into embeddings
- **`vector_store.py`** - PGVector store manager for database operations
- **`rag_chain.py`** - RAG chain setup and configuration
- **`class_descriptions.py`** - Skin condition profile definitions

## Usage

### 1. Setup Environment

Ensure your `.env` file contains the required environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+psycopg2://username:password@host:port/database
```

### 2. Test Database Connection

```bash
# Test basic database connectivity
python main.py --test-connection

# Or test directly
python create_embeddings.py --test-connection
```

### 3. Create Embeddings

```bash
# Create embeddings for both products and skin conditions
python main.py --create-embeddings

# Create embeddings with rebuild (deletes existing data)
python main.py --create-embeddings --rebuild

# Create only product embeddings
python main.py --create-embeddings --products-only

# Create only skin condition embeddings
python main.py --create-embeddings --conditions-only

# Or run directly
python create_embeddings.py [options]
```

### 4. Test RAG Inference

```bash
# Test with example queries
python main.py --test-inference

# Run interactive mode for custom queries
python main.py --test-inference --interactive

# Test using only product embeddings
python main.py --test-inference --products-only

# Test using only skin condition embeddings
python main.py --test-inference --conditions-only

# Or run directly
python test_rag_inference.py [options]
```

### 5. Complete Workflow

```bash
# Do everything: create embeddings then test inference
python main.py --all

# With rebuild and interactive mode
python main.py --all --rebuild --interactive
```

## Individual Script Usage

### create_embeddings.py

Creates and stores embeddings in the PostgreSQL vector database.

```bash
# Basic usage
python create_embeddings.py

# Options
python create_embeddings.py --rebuild              # Rebuild vector stores
python create_embeddings.py --products-only        # Process only products
python create_embeddings.py --conditions-only      # Process only skin conditions
python create_embeddings.py --test-connection      # Test DB connection only
```

### test_rag_inference.py

Tests RAG inference and runs queries against the stored embeddings.

```bash
# Basic usage with example queries
python test_rag_inference.py

# Interactive mode
python test_rag_inference.py --interactive

# Use specific vector store
python test_rag_inference.py --products-only       # Query products only
python test_rag_inference.py --conditions-only     # Query conditions only
python test_rag_inference.py --test-connection     # Test DB connection only
```

## Features

### Database Integration

- Automatic database connection testing
- PostgreSQL with pgvector extension support
- Robust error handling and connection management
- Table existence verification

### Modular Architecture

- **Separation of Concerns**: Embedding creation vs. inference testing
- **Reusable Components**: Shared utilities and configurations
- **Unified Interface**: Single entry point with comprehensive options
- **Independent Operation**: Each script can run standalone

### Enhanced User Experience

- **Interactive Mode**: Real-time query testing
- **Progress Indicators**: Clear feedback on operations
- **Comprehensive Logging**: Detailed error messages and status updates
- **Flexible Options**: Multiple ways to run and configure the system

### Error Handling

- **Connection Validation**: Pre-flight checks for database connectivity
- **Graceful Failures**: Informative error messages with recovery suggestions
- **Environment Validation**: Automatic checking of required dependencies
- **SSL Certificate Handling**: Automatic SSL certificate configuration

## Architecture Benefits

1. **Maintainability**: Each file has a single, clear responsibility
2. **Testability**: Individual components can be tested in isolation
3. **Scalability**: Easy to add new functionality without affecting existing code
4. **Debugging**: Issues can be isolated to specific components
5. **Deployment**: Different parts of the system can be deployed independently

## Dependencies

- `langchain-community`
- `langchain-openai`
- `sentence-transformers`
- `psycopg2-binary`
- `pgvector`
- `python-dotenv`
- `openai`

## Troubleshooting

### Common Issues

1. **Database Connection Errors**

   ```bash
   python main.py --test-connection
   ```

2. **Missing Environment Variables**

   - Check your `.env` file
   - Ensure `OPENAI_API_KEY` and `DATABASE_URL` are set

3. **SSL Certificate Issues**

   - The system automatically handles SSL certificate configuration
   - Uses `certifi` library for certificate management

4. **Table Not Found**

   - Run embedding creation first: `python main.py --create-embeddings`
   - Check database permissions and table existence

5. **Import Errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - Check Python path and virtual environment

### Getting Help

Run any script with `-h` or `--help` for detailed usage information:

```bash
python main.py --help
python create_embeddings.py --help
python test_rag_inference.py --help
```
