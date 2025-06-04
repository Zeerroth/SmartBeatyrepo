#!/usr/bin/env python
"""
Custom vector store manager that works with existing database tables.
This pulls data from the existing 'products' and 'skin_conditions' tables
and stores embeddings in LangChain format for seamless integration.
"""

import json
import traceback
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores.pgvector import PGVector
from utils import create_db_connection


class CustomDatabaseVectorManager:
    """
    Custom vector store manager that pulls data from existing database tables
    and manages embeddings in LangChain format.
    """
    
    def __init__(self, embedding_model, connection_string: str):
        """
        Initialize the custom vector store manager.
        
        Args:
            embedding_model: The embedding model to use
            connection_string: PostgreSQL connection string
        """
        self.embedding_model = embedding_model
        self.connection_string = connection_string
        self.products_vector_store = None
        self.conditions_vector_store = None
        
    def get_products_from_database(self) -> List[Dict[str, Any]]:
        """
        Fetch all products from the products table.
        
        Returns:
            List of product dictionaries
        """
        conn = create_db_connection(self.connection_string)
        if not conn:
            print("Failed to connect to database")
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description
                FROM products 
                ORDER BY id;
            """)
            
            products = []
            for row in cursor.fetchall():
                product_id, name, original_data = row
                
                # Parse the JSON data
                product_data = {}
                if original_data:
                    try:
                        product_data = json.loads(original_data) if isinstance(original_data, str) else original_data
                    except:
                        product_data = {'name': name}
                
                products.append({
                    'id': product_id,
                    'name': name,
                    'description': product_data
                })
                
            cursor.close()
            conn.close()
            print(f"✓ Loaded {len(products)} products from database")
            return products
            
        except Exception as e:
            print(f"Error fetching products: {e}")
            if conn:
                conn.close()
            return []
    
    def get_skin_conditions_from_database(self) -> List[Dict[str, Any]]:
        """
        Fetch all skin conditions from the skin_conditions table.
        
        Returns:
            List of skin condition dictionaries
        """
        conn = create_db_connection(self.connection_string)
        if not conn:
            print("Failed to connect to database")
            return []
            
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, description
                FROM skin_conditions 
                ORDER BY id;
            """)
            
            conditions = []
            for row in cursor.fetchall():
                condition_id, name, description = row
                
                conditions.append({
                    'id': condition_id,
                    'name': name,
                    'description': description or ''
                })
                
            cursor.close()
            conn.close()
            print(f"✓ Loaded {len(conditions)} skin conditions from database")
            return conditions
            
        except Exception as e:
            print(f"Error fetching skin conditions: {e}")
            if conn:
                conn.close()
            return []
    
    def create_product_documents(self, products: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert products to LangChain Document objects.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for product in products:
            # Use the pre-computed embedding text if available, otherwise create it
            if product.get('embedding_text'):
                content = product['embedding_text']
            else:
                # Fallback: create basic content from available data
                original_data = product.get('original_data', {})
                content_parts = [f"Product Name: {product['name']}"]
                
                if original_data.get('description'):
                    content_parts.append(f"Description: {original_data['description']}")
                if original_data.get('keyBenefits'):
                    content_parts.append(f"Key Benefits: {original_data['keyBenefits']}")
                if original_data.get('activeContent'):
                    content_parts.append(f"Active Ingredients: {original_data['activeContent']}")
                
                content = ". ".join(content_parts)
            
            # Create metadata for easy filtering and identification
            metadata = {
                'document_type': 'product',
                'product_id': str(product['id']),
                'name': product['name'],
                'source': f"product_{product['id']}",
                'original_data_json_str': json.dumps(product.get('original_data', {}))
            }
            
            # Add price if available
            original_data = product.get('original_data', {})
            if original_data.get('price'):
                metadata['price'] = str(original_data['price'])
            
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
        
        return documents
    
    def create_condition_documents(self, conditions: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert skin conditions to LangChain Document objects.
        
        Args:
            conditions: List of skin condition dictionaries
            
        Returns:
            List of Document objects
        """
        documents = []
        
        for condition in conditions:
            content = f"{condition['name']}: {condition['description']}"
            
            metadata = {
                'document_type': 'skin_condition',
                'condition_id': str(condition['id']),
                'condition_name': condition['name'],
                'source': f"condition_{condition['id']}"
            }
            
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
        
        return documents
    
    def get_existing_embeddings_count(self, collection_name: str) -> Tuple[int, List[str]]:
        """
        Get count and list of existing embeddings in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Tuple of (count, list_of_source_ids)
        """
        conn = create_db_connection(self.connection_string)
        if not conn:
            return 0, []
            
        try:
            cursor = conn.cursor()
            
            # Get collection UUID
            cursor.execute("""
                SELECT uuid FROM langchain_pg_collection 
                WHERE name = %s;
            """, (collection_name,))
            
            result = cursor.fetchone()
            if not result:
                cursor.close()
                conn.close()
                return 0, []
                
            collection_uuid = result[0]
            
            # Get existing sources
            cursor.execute("""
                SELECT COUNT(*), array_agg(cmetadata::json->>'source') 
                FROM langchain_pg_embedding 
                WHERE collection_id = %s;
            """, (collection_uuid,))
            
            count, sources = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return count or 0, sources or []
            
        except Exception as e:
            print(f"Error checking existing embeddings: {e}")
            if conn:
                conn.close()
            return 0, []
    
    def process_products(self, rebuild: bool = False) -> Optional[PGVector]:
        """
        Process products and create/update embeddings.
        
        Args:
            rebuild: Whether to rebuild the entire collection
            
        Returns:
            PGVector store or None
        """
        print("\n=== Processing Products from Database ===")
        
        # Get products from database
        products = self.get_products_from_database()
        if not products:
            print("No products found in database")
            return None
        
        # Convert to documents
        documents = self.create_product_documents(products)
        print(f"✓ Created {len(documents)} product documents")
        
        # Check existing embeddings
        existing_count, existing_sources = self.get_existing_embeddings_count('products')
        print(f"ℹ  Existing product embeddings: {existing_count}")
        
        if not rebuild and existing_count > 0:
            # Filter out already embedded products
            new_documents = []
            for doc in documents:
                if doc.metadata['source'] not in existing_sources:
                    new_documents.append(doc)
            
            if not new_documents:
                print("✓ All products already have embeddings. Use --rebuild to recreate.")
                # Just connect to existing store
                try:
                    vector_store = PGVector(
                        embedding_function=self.embedding_model,
                        connection_string=self.connection_string,
                        collection_name='products'
                    )
                    return vector_store
                except:
                    print("Could not connect to existing store")
                    return None
            else:
                print(f"→ Adding {len(new_documents)} new product embeddings")
                documents = new_documents
        
        # Create or update vector store
        try:
            if rebuild:
                print("🔄 Rebuilding product embeddings...")
                vector_store = PGVector.from_documents(
                    embedding=self.embedding_model,
                    documents=documents,
                    connection_string=self.connection_string,
                    collection_name='products',
                    pre_delete_collection=True
                )
            else:
                print("➕ Adding new product embeddings...")
                try:
                    # Try to connect to existing collection
                    vector_store = PGVector(
                        embedding_function=self.embedding_model,
                        connection_string=self.connection_string,
                        collection_name='products'
                    )
                    vector_store.add_documents(documents)
                except:
                    # Collection doesn't exist, create it
                    vector_store = PGVector.from_documents(
                        embedding=self.embedding_model,
                        documents=documents,
                        connection_string=self.connection_string,
                        collection_name='products',
                        pre_delete_collection=False
                    )
            
            print(f"✅ Successfully processed {len(documents)} product embeddings")
            return vector_store
            
        except Exception as e:
            print(f"❌ Error creating product embeddings: {e}")
            traceback.print_exc()
            return None
    
    def process_skin_conditions(self, rebuild: bool = False) -> Optional[PGVector]:
        """
        Process skin conditions and create/update embeddings.
        
        Args:
            rebuild: Whether to rebuild the entire collection
            
        Returns:
            PGVector store or None
        """
        print("\n=== Processing Skin Conditions from Database ===")
        
        # Get conditions from database
        conditions = self.get_skin_conditions_from_database()
        if not conditions:
            print("No skin conditions found in database")
            return None
        
        # Convert to documents
        documents = self.create_condition_documents(conditions)
        print(f"✓ Created {len(documents)} skin condition documents")
        
        # Check existing embeddings
        existing_count, existing_sources = self.get_existing_embeddings_count('skin_conditions')
        print(f"ℹ  Existing skin condition embeddings: {existing_count}")
        
        if not rebuild and existing_count > 0:
            # Filter out already embedded conditions
            new_documents = []
            for doc in documents:
                if doc.metadata['source'] not in existing_sources:
                    new_documents.append(doc)
            
            if not new_documents:
                print("✓ All skin conditions already have embeddings. Use --rebuild to recreate.")
                # Just connect to existing store
                try:
                    vector_store = PGVector(
                        embedding_function=self.embedding_model,
                        connection_string=self.connection_string,
                        collection_name='skin_conditions'
                    )
                    return vector_store
                except:
                    print("Could not connect to existing store")
                    return None
            else:
                print(f"→ Adding {len(new_documents)} new skin condition embeddings")
                documents = new_documents
        
        # Create or update vector store
        try:
            if rebuild:
                print("🔄 Rebuilding skin condition embeddings...")
                vector_store = PGVector.from_documents(
                    embedding=self.embedding_model,
                    documents=documents,
                    connection_string=self.connection_string,
                    collection_name='skin_conditions',
                    pre_delete_collection=True
                )
            else:
                print("➕ Adding new skin condition embeddings...")
                try:
                    # Try to connect to existing collection
                    vector_store = PGVector(
                        embedding_function=self.embedding_model,
                        connection_string=self.connection_string,
                        collection_name='skin_conditions'
                    )
                    vector_store.add_documents(documents)
                except:
                    # Collection doesn't exist, create it
                    vector_store = PGVector.from_documents(
                        embedding=self.embedding_model,
                        documents=documents,
                        connection_string=self.connection_string,
                        collection_name='skin_conditions',
                        pre_delete_collection=False
                    )
            
            print(f"✅ Successfully processed {len(documents)} skin condition embeddings")
            return vector_store
            
        except Exception as e:
            print(f"❌ Error creating skin condition embeddings: {e}")
            traceback.print_exc()
            return None
    
    def get_embedding_stats(self) -> Dict[str, int]:
        """
        Get statistics about current embeddings.
        
        Returns:
            Dictionary with embedding counts
        """
        conn = create_db_connection(self.connection_string)
        if not conn:
            return {}
            
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Get counts for each collection
            cursor.execute("""
                SELECT c.name, COUNT(e.uuid)
                FROM langchain_pg_collection c
                LEFT JOIN langchain_pg_embedding e ON c.uuid = e.collection_id
                GROUP BY c.name, c.uuid
                ORDER BY c.name;
            """)
            
            for name, count in cursor.fetchall():
                stats[name] = count
            
            cursor.close()
            conn.close()
            
            return stats
            
        except Exception as e:
            print(f"Error getting embedding stats: {e}")
            if conn:
                conn.close()
            return {}
