import warnings
from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores.pgvector import PGVector

class PGVectorStoreManager:
    """
    Manager class for PGVector-based vector stores.
    Handles connecting to or creating vector stores for document embedding and retrieval.
    """
    def __init__(self, embedding_model, connection_string: str, collection_name: str):
        """
        Initialize the PGVectorStoreManager.
        
        Args:
            embedding_model: The embedding model to use for vectorization.
            connection_string: The PostgreSQL connection string.
            collection_name: The name for the collection (table) in PostgreSQL.
        """
        self.embedding_model = embedding_model
        self.connection_string = connection_string
        self.collection_name = collection_name
        self.vector_store = None

        # Test DB connection early
        self._test_db_connection()

    def _test_db_connection(self):
        """
        Attempt a basic test of the database connection.
        """
        try:
            print(f"PGVector will attempt to connect to: {self.connection_string.split('@')[-1]}")
        except ImportError:
            raise ImportError("psycopg2-binary is not installed. Please install it with 'pip install psycopg2-binary'")
        except Exception as e:
            raise ConnectionError(f"Failed to pre-check PostgreSQL connection: {e}\n"
                                  f"Ensure your DATABASE_URL is correct and PostgreSQL server is running and accessible.")

    def build_or_load_store(self, 
                           documents: Optional[List[Document]] = None, 
                           pre_delete_collection: bool = False):
        """
        Build a new vector store or load an existing one.
        
        Args:
            documents: Optional list of documents to add to the store.
            pre_delete_collection: Whether to delete and recreate the collection.
            
        Returns:
            The initialized PGVector store.
        """
        print(f"Initializing PGVector store for collection: {self.collection_name}")
        
        try:
            # Case 1: Rebuild collection with documents
            if documents and pre_delete_collection:
                print(f"Creating new collection '{self.collection_name}'...")
                self.vector_store = PGVector.from_documents(
                    embedding=self.embedding_model,
                    documents=documents,
                    connection_string=self.connection_string,
                    collection_name=self.collection_name,
                    pre_delete_collection=True
                )
                print(f"Collection '{self.collection_name}' created with {len(documents)} documents.")
                  # Case 2: Add documents to existing collection (or create if it doesn't exist)
            elif documents:
                print(f"Adding documents to collection '{self.collection_name}'...")
                try:
                    # Try connecting to the existing collection first
                    self.vector_store = PGVector(
                        embedding_function=self.embedding_model,
                        connection_string=self.connection_string,
                        collection_name=self.collection_name,
                    )
                    # Test if the collection exists
                    try:
                        self.vector_store.similarity_search("test", k=1)
                        # Collection exists, add documents
                        self.vector_store.add_documents(documents)
                        print(f"Added {len(documents)} documents to existing collection '{self.collection_name}'.")
                    except Exception as e:
                        if "Collection not found" in str(e):
                            # Collection doesn't exist, create it with documents
                            print(f"Collection '{self.collection_name}' not found. Creating new collection...")
                            self.vector_store = PGVector.from_documents(
                                embedding=self.embedding_model,
                                documents=documents,
                                connection_string=self.connection_string,
                                collection_name=self.collection_name,
                                pre_delete_collection=False
                            )
                            print(f"Collection '{self.collection_name}' created with {len(documents)} documents.")
                        else:
                            raise e
                except Exception as e:
                    print(f"Error working with collection '{self.collection_name}': {e}")
                    self.vector_store = None
                
            # Case 3: Just connect to existing collection
            else:
                print(f"Connecting to existing collection '{self.collection_name}'...")
                self.vector_store = PGVector(
                    embedding_function=self.embedding_model,
                    connection_string=self.connection_string,
                    collection_name=self.collection_name,
                )
                
                # Check if the connection works
                try:
                    self.vector_store.similarity_search("test", k=1)
                    print(f"Successfully connected to collection: {self.collection_name}")
                except Exception as e:
                    warnings.warn(f"Connected to PGVector, but collection '{self.collection_name}' might be empty or an issue occurred: {e}")
                    
        except Exception as e:
            print(f"Error with PGVector store: {e}")
            print("Check that PostgreSQL server is running and pgvector extension is installed.")
            print(f"Verify connection string: '{self.connection_string.split('@')[0]}@host:port/db'")
            self.vector_store = None
            
        return self.vector_store
