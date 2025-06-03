# SmartBeauty RAG System

This is a modular Retrieval-Augmented Generation (RAG) system for skincare product recommendations.

## Project Structure

The system is organized into the following modules:

- **config.py**: Contains all configuration settings for the application
- **data_loader.py**: Functions for loading data from various sources
- **document_processor.py**: Tools for processing raw data into documents for embedding
- **vector_store.py**: Manages the vector database using PGVector
- **rag_chain.py**: Sets up the RAG chain for generating recommendations
- **utils.py**: Utility functions for environment setup and validation
- **main.py**: Entry point with command-line arguments
- **example.py**: Simple example script demonstrating the use of modular components
- **indexing.py**: Original implementation (now updated to use the modular structure)
- **class_descriptions.py**: Contains detailed descriptions of skin conditions

## Getting Started

### Prerequisites

1. PostgreSQL with pgvector extension installed and running on port 5433
2. Python 3.8+ with pip
3. OpenAI API key

### Installation

1. Set your OpenAI API key in your environment:

   ```bash
   # In bash.exe
   export OPENAI_API_KEY="your_api_key_here"

   # Or in PowerShell
   $env:OPENAI_API_KEY="your_api_key_here"
   ```

2. Set your PostgreSQL database URL (optional - if different from default in config.py):

   ```bash
   # In bash.exe
   export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5433/database_name"

   # Or in PowerShell
   $env:DATABASE_URL="postgresql+psycopg2://username:password@localhost:5433/database_name"
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Run the main application with various options:

```bash
# Process both products and skin conditions
python main.py

# Run a simple example
python example.py
```

## Command Line Arguments

The `main.py` script supports the following arguments:

- `--rebuild`: Rebuild vector stores (delete and recreate)
- `--products-only`: Process only product data
- `--conditions-only`: Process only skin condition data
- `--query`: Run example queries after processing data

Example:

```bash
# Process both products and skin conditions, rebuild the vector stores
python main.py --rebuild

# Process only products and run example queries
python main.py --products-only --query
```

## Database Configuration

Configure the database connection in `config.py` or set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql+psycopg2://username:password@localhost:5433/database_name"
```
