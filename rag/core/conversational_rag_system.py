#!/usr/bin/env python
"""
RAG Chat System with conversational memory and enhanced inference.
This script provides a complete RAG system with memory for maintaining
conversation context across multiple turns.
"""

import os
import argparse
import json
import tiktoken
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Fix SSL certificate issues on Windows
if 'SSL_CERT_FILE' in os.environ:
    del os.environ['SSL_CERT_FILE']
if 'SSL_CERT_DIR' in os.environ:
    del os.environ['SSL_CERT_DIR']

# LangChain components
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores.pgvector import PGVector

# Import our modular components
import config
from data_loader import load_skin_condition_profiles
from rag_chain import get_rag_chain, get_conversational_rag_chain
from utils import setup_environment, test_db_connection

load_dotenv()


class SmartBeautyRAGSystem:
    """
    Complete RAG system with conversational memory for SmartBeauty skincare advisor.
    Manages LLM, vector store, retriever, memory, and conversation chain.
    """
    
    def __init__(self, collection_name: str = "products"):
        """
        Initialize the RAG system components.
        
        Args:
            collection_name: Name of the vector store collection to use
        """
        self.collection_name = collection_name
        self.embedding_model = None
        self.vector_store = None
        self.llm = None
        self.memory = None
        self.retriever = None
        self.conversational_chain = None
        self.simple_chain = None
        self.conversation_history = []
        
        # Initialize all components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG system components."""
        print("🚀 Initializing SmartBeauty RAG System...")
        
        # 1. Create embedding model
        self.embedding_model = self._create_embedding_model()
        if not self.embedding_model:
            raise Exception("Failed to create embedding model")
        
        # 2. Load vector store
        self.vector_store = self._load_vector_store()
        if not self.vector_store:
            raise Exception(f"Failed to load vector store '{self.collection_name}'")
        
        # 3. Initialize LLM
        self.llm = self._create_llm()
        if not self.llm:
            raise Exception("Failed to create LLM")
        
        # 4. Setup memory
        self.memory = self._create_memory()
        
        # 5. Create retriever
        self.retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 5}  # Retrieve top 5 relevant documents
        )
        
        # 6. Setup chains
        self._setup_chains()
        
        print("✅ RAG System initialized successfully!")
    
    def _create_embedding_model(self) -> Optional[HuggingFaceEmbeddings]:
        """Create and return the embedding model."""
        try:
            print(f"📡 Creating embedding model: {config.SENTENCE_TRANSFORMER_MODEL_NAME}")
            return HuggingFaceEmbeddings(
                model_name=config.SENTENCE_TRANSFORMER_MODEL_NAME,
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            print(f"❌ Error creating embedding model: {e}")
            return None
    
    def _load_vector_store(self) -> Optional[PGVector]:
        """Load vector store from database."""
        print(f"🗄️ Loading vector store: {self.collection_name}")
        
        # Test database connection
        if not test_db_connection(config.DATABASE_CONNECTION_STRING):
            print("❌ Failed to connect to database")
            return None
        
        try:
            vector_store = PGVector(
                embedding_function=self.embedding_model,
                connection_string=config.DATABASE_CONNECTION_STRING,
                collection_name=self.collection_name
            )
            
            # Test the connection
            test_results = vector_store.similarity_search("test", k=1)
            print(f"✅ Vector store loaded successfully ({len(test_results)} test results)")
            return vector_store
            
        except Exception as e:
            print(f"❌ Error loading vector store: {e}")
            print("💡 Make sure embeddings have been created using create_embeddings.py")
            return None
    
    def _create_llm(self) -> Optional[ChatOpenAI]:
        """Create and return the LLM."""
        if not config.OPENAI_API_KEY:
            print("❌ OpenAI API key not found. Please check your .env file.")
            return None
        
        try:
            print(f"🧠 Creating LLM: {config.LLM_MODEL_NAME}")
            return ChatOpenAI(
                model=config.LLM_MODEL_NAME, 
                api_key=config.OPENAI_API_KEY,
                temperature=0.7
            )
        except Exception as e:
            print(f"❌ Error creating LLM: {e}")
            return None
    
    def _create_memory(self) -> ConversationBufferMemory:
        """Create conversation memory."""
        print("🧠 Setting up conversation memory...")
        return ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )
    
    def _setup_chains(self):
        """Setup both conversational and simple RAG chains."""
        try:
            print("🔗 Setting up RAG chains...")
            
            # Simple chain for single queries
            self.simple_chain = get_rag_chain(self.llm, self.retriever)
            
            # Conversational chain with memory
            self.conversational_chain = get_conversational_rag_chain(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory
            )
            
            print("✅ RAG chains setup successfully!")
            
        except Exception as e:
            print(f"❌ Error setting up RAG chains: {e}")
            raise e
    
    def ask(self, question: str, use_memory: bool = True) -> Dict[str, Any]:
        """
        Ask a question to the RAG system.
        
        Args:
            question: The question to ask
            use_memory: Whether to use conversational memory
            
        Returns:
            Dictionary containing answer, sources, and metadata
        """
        try:
            # Choose chain based on memory preference
            chain = self.conversational_chain if use_memory else self.simple_chain
            
            # Get response
            if use_memory:
                # For conversational chain, use 'question' as input key
                response = chain.invoke({"question": question})
                answer = response.get('answer', '')
                source_docs = response.get('source_documents', [])
            else:
                # For simple chain, use 'query' as input key
                response = chain.invoke({"query": question})
                answer = response.get('result', '')
                source_docs = response.get('source_documents', [])
            
            # Process source documents
            sources = []
            for i, doc in enumerate(source_docs[:3]):  # Top 3 sources
                doc_info = {
                    "rank": i + 1,
                    "name": doc.metadata.get('name', doc.metadata.get('condition_name', 'Unknown')),
                    "type": doc.metadata.get('document_type', 'unknown'),
                    "id": doc.metadata.get('product_id', doc.metadata.get('condition_id', 'unknown')),
                    "content_preview": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content
                }
                sources.append(doc_info)
              # Store conversation turn
            token_info = self.count_total_tokens(question, answer)
            conversation_turn = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "sources": sources,
                "used_memory": use_memory,
                "tokens": token_info
            }
            self.conversation_history.append(conversation_turn)
            
            return {
                "answer": answer,
                "sources": sources,
                "conversation_turn": len(self.conversation_history),
                "used_memory": use_memory,
                "tokens": token_info
            }
            
        except Exception as e:
            print(f"❌ Error processing question: {e}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "sources": [],
                "conversation_turn": len(self.conversation_history),
                "used_memory": use_memory,
                "error": str(e)
            }
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the full conversation history."""
        return self.conversation_history
    
    def clear_memory(self):
        """Clear the conversation memory."""
        if self.memory:
            self.memory.clear()
            print("🧹 Conversation memory cleared")
    
    def get_memory_summary(self) -> str:
        """Get a summary of what's in memory."""
        if not self.memory or not hasattr(self.memory, 'chat_memory'):
            return "No conversation history"
        
        messages = self.memory.chat_memory.messages
        if not messages:
            return "No conversation history"
        
        return f"Conversation history: {len(messages)} messages"
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            encoding = tiktoken.encoding_for_model(config.LLM_MODEL_NAME)
            return len(encoding.encode(text))
        except Exception:
            # Fallback estimation
            return len(text.split()) * 4 // 3
    
    def count_total_tokens(self, question: str, answer: str) -> Dict[str, int]:
        """Count tokens for both input and output."""
        try:
            encoding = tiktoken.encoding_for_model(config.LLM_MODEL_NAME)
            input_tokens = len(encoding.encode(question))
            output_tokens = len(encoding.encode(answer))
            total_tokens = input_tokens + output_tokens
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
        except Exception:
            # Fallback estimation
            input_tokens = len(question.split()) * 4 // 3
            output_tokens = len(answer.split()) * 4 // 3
            total_tokens = input_tokens + output_tokens
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        return {
            "collection_name": self.collection_name,
            "conversation_turns": len(self.conversation_history),
            "memory_summary": self.get_memory_summary(),
            "llm_model": config.LLM_MODEL_NAME,
            "embedding_model": config.SENTENCE_TRANSFORMER_MODEL_NAME,
            "initialized": all([
                self.embedding_model, self.vector_store, 
                self.llm, self.memory, self.retriever, 
                self.conversational_chain, self.simple_chain
            ])
        }


def run_interactive_chat(rag_system: SmartBeautyRAGSystem):
    """
    Run an interactive chat session with the RAG system.
    
    Args:
        rag_system: Initialized RAG system instance
    """
    print(f"\n{'='*60}")
    print("🌟 Welcome to SmartBeauty Skincare Advisor!")
    print(f"{'='*60}")
    print("I'm your AI skincare expert with memory of our conversation.")
    print("Ask me about skincare products, routines, or skin conditions.")
    print("\nCommands:")
    print("  • Type your question normally for skincare advice")
    print("  • Type 'history' to see our conversation")
    print("  • Type 'memory' to see what I remember")
    print("  • Type 'clear' to clear conversation memory")
    print("  • Type 'stats' to see system information")
    print("  • Type 'quit' to exit")
    print(f"{'='*60}")
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input(f"\n💬 Your question (Turn {conversation_count + 1}): ").strip()
            
            # Handle special commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using SmartBeauty! Take care of your skin!")
                break
            
            if user_input.lower() == 'history':
                history = rag_system.get_conversation_history()
                if not history:
                    print("📜 No conversation history yet.")
                else:
                    print(f"\n📜 Conversation History ({len(history)} turns):")
                    for i, turn in enumerate(history[-5:], 1):  # Show last 5 turns
                        print(f"  {i}. Q: {turn['question'][:80]}...")
                        print(f"     A: {turn['answer'][:80]}...")
                continue
            
            if user_input.lower() == 'memory':
                memory_info = rag_system.get_memory_summary()
                print(f"🧠 Memory Status: {memory_info}")
                continue
            
            if user_input.lower() == 'clear':
                rag_system.clear_memory()
                conversation_count = 0
                print("🧹 Conversation memory cleared! Starting fresh.")
                continue
            
            if user_input.lower() == 'stats':
                stats = rag_system.get_stats()
                print(f"\n📊 System Statistics:")
                for key, value in stats.items():
                    print(f"  • {key}: {value}")
                continue
            
            if not user_input:
                print("Please enter a question or command.")
                continue
            
            # Process the question
            print(f"\n🔍 Thinking... (using conversational memory)")
            response = rag_system.ask(user_input, use_memory=True)
            
            # Display response
            print(f"\n🤖 SmartBeauty:")
            print(response['answer'])
            
            # Show sources
            if response['sources']:
                print(f"\n📚 Sources (Top {len(response['sources'])}):")
                for source in response['sources']:
                    print(f"  {source['rank']}. {source['name']} ({source['type']})")
              # Show turn information
            token_info = response.get('tokens', {})
            total_tokens = token_info.get('total_tokens', 0)
            input_tokens = token_info.get('input_tokens', 0)
            output_tokens = token_info.get('output_tokens', 0)
            
            print(f"\n📈 Turn {response['conversation_turn']} • Total Tokens: {total_tokens} (In: {input_tokens}, Out: {output_tokens}) • Memory: ✓")
            
            conversation_count += 1
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for chatting!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or type 'quit' to exit.")


def run_example_queries(rag_system: SmartBeautyRAGSystem):
    """
    Run a series of example queries to test the system.
    
    Args:
        rag_system: Initialized RAG system instance
    """
    print(f"\n{'='*50}")
    print("🧪 Running Example Queries")
    print(f"{'='*50}")
    
    # Define example conversation flow
    example_queries = [
        "What products do you recommend for oily skin?",
        "What about for acne-prone skin specifically?",
        "Can you recommend something with salicylic acid?",
        "What's the difference between the products you mentioned?",
        "Which one would be best for sensitive oily skin?"
    ]
    
    results = []
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{'='*30}")
        print(f"Query {i}/5: {query}")
        print('='*30)
        
        try:
            response = rag_system.ask(query, use_memory=True)
            
            print(f"\n🤖 Response:")
            print(response['answer'])
            
            if response['sources']:
                print(f"\n📚 Sources:")
                for source in response['sources']:
                    print(f"  • {source['name']} ({source['type']})")
            
            # Store result
            results.append({
                "query": query,
                "response": response,
                "turn": i
            })
            
            print(f"\n✅ Query {i} completed successfully")
            
        except Exception as e:
            print(f"\n❌ Error in query {i}: {e}")
            results.append({
                "query": query,
                "error": str(e),
                "turn": i
            })
    
    # Summary
    successful = sum(1 for r in results if 'error' not in r)
    print(f"\n{'='*50}")
    print(f"📊 Example Queries Summary")
    print(f"{'='*50}")
    print(f"Successful queries: {successful}/{len(example_queries)}")
    print(f"Total conversation turns: {len(rag_system.get_conversation_history())}")
    
    # Save results
    try:
        output_file = "conversational_rag_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "stats": rag_system.get_stats(),
                "queries": results,
                "conversation_history": rag_system.get_conversation_history()
            }, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")


def main():
    """Main entry point for the conversational RAG system."""
    # Check environment setup
    if not setup_environment():
        print("Environment setup failed. Please fix the issues above and try again.")
        return
    
    parser = argparse.ArgumentParser(description="SmartBeauty Conversational RAG System")
    parser.add_argument("--products-only", action="store_true", 
                       help="Use only product vector store for queries.")
    parser.add_argument("--conditions-only", action="store_true", 
                       help="Use only skin conditions vector store for queries.")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive chat mode (default).")
    parser.add_argument("--examples", action="store_true",
                       help="Run example queries to test the system.")
    parser.add_argument("--test-connection", action="store_true",
                       help="Test database connection only.")
    
    args = parser.parse_args()
    
    # Test connection only
    if args.test_connection:
        print("Testing database connection...")
        success = test_db_connection(config.DATABASE_CONNECTION_STRING)
        if success:
            print("✅ Database connection test passed!")
        else:
            print("❌ Database connection test failed!")
        return
    
    try:
        # Determine collection name
        if args.conditions_only:
            collection_name = "skin_conditions"
        else:
            collection_name = "products"  # Default to products
        
        # Initialize RAG system
        print(f"🚀 Initializing SmartBeauty RAG System with '{collection_name}' collection...")
        rag_system = SmartBeautyRAGSystem(collection_name=collection_name)
        
        # Show system stats
        stats = rag_system.get_stats()
        print(f"\n📊 System Ready!")
        print(f"  • Collection: {stats['collection_name']}")
        print(f"  • LLM: {stats['llm_model']}")
        print(f"  • Embeddings: {stats['embedding_model']}")
        print(f"  • Initialized: {stats['initialized']}")
        
        # Run based on arguments
        if args.examples:
            run_example_queries(rag_system)
        else:
            # Default to interactive mode
            run_interactive_chat(rag_system)
    
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        print("💡 Make sure embeddings have been created using: python create_embeddings.py")
        return


if __name__ == "__main__":
    main()
