#!/usr/bin/env python
"""
Flask backend for SmartBeauty AI Chatbot UI.

This Flask server provides a web interface for the conversational RAG system,
allowing users to interact with the SmartBeauty skincare advisor through a 
modern chat interface.

Usage:
    python app.py
    
API Endpoints:
    GET /                   - Serves the chatbot UI
    POST /api/chat         - Handles chat messages
    GET /api/health        - Health check endpoint
    POST /api/reset        - Reset conversation
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Flask imports
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add the core directory to sys.path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, '..', 'core')
core_dir = os.path.abspath(core_dir)

if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

# Import the conversational RAG system
try:
    from conversational_rag_system import SmartBeautyRAGSystem
    RAG_AVAILABLE = True
    print("✅ RAG system available")
except ImportError as e:
    print(f"❌ Could not import RAG system: {e}")
    print("💡 Running in mock mode with fallback responses")
    RAG_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Global RAG system instance
rag_system = None

class ChatbotBackend:
    """Backend handler for the SmartBeauty chatbot."""
    
    def __init__(self):
        """Initialize the chatbot backend."""
        self.rag_system = None
        self.conversation_sessions = {}  # Store multiple conversation sessions
        self.initialize_rag_system()
    
    def initialize_rag_system(self):
        """Initialize the RAG system if available."""
        if not RAG_AVAILABLE:
            logger.warning("RAG system not available, using mock responses")
            return
        
        try:
            logger.info("Initializing SmartBeauty RAG system...")
            self.rag_system = SmartBeautyRAGSystem(collection_name="products")
            
            # Check if system is properly initialized
            stats = self.rag_system.get_stats()
            if stats['initialized']:
                logger.info("✅ RAG system initialized successfully")
                logger.info(f"📊 System stats: {stats}")
            else:
                logger.error("❌ RAG system initialization incomplete")
                self.rag_system = None
                
        except Exception as e:
            logger.error(f"❌ Error initializing RAG system: {e}")
            logger.info("💡 Make sure embeddings have been created and database is accessible")
            self.rag_system = None
    
    def get_response(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Get a response to the user's message.
        
        Args:
            message: User's message
            session_id: Session identifier for conversation tracking
            
        Returns:
            Dictionary with response data matching frontend expectations
        """
        try:
            if self.rag_system:
                # Use the RAG system
                response = self.rag_system.ask(message, use_memory=True)
                
                # Transform response to match frontend expectations
                return {
                    "answer": response.get("answer", ""),
                    "sources": self._transform_sources(response.get("sources", [])),
                    "tokens": response.get("tokens", {}),
                    "using_memory": response.get("used_memory", True),
                    "conversation_turn": response.get("conversation_turn", 1),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Fallback to mock response
                return self._get_mock_response(message)
                
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return {
                "answer": "I'm sorry, I'm experiencing technical difficulties. Please try again.",
                "sources": [],
                "tokens": {},
                "using_memory": False,                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _transform_sources(self, sources: list) -> list:
        """Transform RAG sources to frontend format."""
        transformed = []
        for source in sources:
            # The RAG system returns sources with content_preview and metadata
            content = source.get("content_preview", "")
            name = source.get("name", "Unknown Source")
            doc_type = source.get("type", "product")
            
            # Estimate similarity score based on rank (higher rank = lower similarity)
            rank = source.get("rank", 1)
            estimated_similarity = max(0.95 - (rank - 1) * 0.1, 0.5)
            
            transformed.append({
                "content": content,
                "similarity": estimated_similarity,
                "name": name,
                "type": doc_type,
                "rank": rank
            })
        return transformed
    
    def _get_mock_response(self, message: str) -> Dict[str, Any]:
        """Generate a mock response when RAG system is not available."""
        message_lower = message.lower()
        
        # Mock responses for common skincare topics
        if any(keyword in message_lower for keyword in ['oily', 'acne', 'breakout']):
            answer = "For oily and acne-prone skin, I'd recommend looking for products with salicylic acid or benzoyl peroxide. A gentle cleanser, non-comedogenic moisturizer, and targeted treatment would be a good start."
            sources = [
                {"content": "Salicylic acid helps unclog pores and reduce oil production", "similarity": 0.92},
                {"content": "Non-comedogenic moisturizers won't clog pores", "similarity": 0.88}
            ]
        elif any(keyword in message_lower for keyword in ['dry', 'moisture', 'hydrat']):
            answer = "For dry skin, focus on hydrating ingredients like hyaluronic acid, ceramides, and glycerin. Look for gentle, creamy cleansers and rich moisturizers."
            sources = [
                {"content": "Hyaluronic acid can hold up to 1000 times its weight in water", "similarity": 0.94},
                {"content": "Ceramides help restore the skin barrier", "similarity": 0.89}
            ]
        elif any(keyword in message_lower for keyword in ['sensitive', 'irritat', 'red']):
            answer = "For sensitive skin, choose fragrance-free, hypoallergenic products with soothing ingredients like niacinamide, aloe vera, or chamomile. Always patch test new products."
            sources = [
                {"content": "Niacinamide reduces inflammation and redness", "similarity": 0.91},
                {"content": "Fragrance-free products reduce irritation risk", "similarity": 0.87}
            ]
        elif any(keyword in message_lower for keyword in ['aging', 'wrinkle', 'fine line']):
            answer = "For anti-aging, consider retinoids, vitamin C, and peptides. Start with gentle formulations and always use sunscreen during the day."
            sources = [
                {"content": "Retinoids stimulate collagen production", "similarity": 0.93},
                {"content": "Vitamin C provides antioxidant protection", "similarity": 0.90}
            ]
        else:
            answer = "I'd be happy to help you with your skincare concerns! Please tell me more about your skin type and specific issues you'd like to address."
            sources = [
                {"content": "Personalized skincare advice based on individual needs", "similarity": 0.85}
            ]
        
        return {
            "answer": answer,
            "sources": sources,
            "tokens": {"input_tokens": len(message.split()) * 4 // 3, "output_tokens": len(answer.split()) * 4 // 3, "total_tokens": (len(message.split()) + len(answer.split())) * 4 // 3},
            "using_memory": False,
            "conversation_turn": 1,
            "timestamp": datetime.now().isoformat(),
            "mock_mode": True
        }
    
    def reset_conversation(self, session_id: str = "default") -> Dict[str, Any]:
        """Reset the conversation for a session."""
        try:
            if self.rag_system:
                self.rag_system.clear_memory()
                logger.info("✅ Conversation memory cleared")
            
            # Clear session data
            if session_id in self.conversation_sessions:
                del self.conversation_sessions[session_id]
            
            return {"status": "success", "message": "Conversation reset successfully"}
            
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get the health status of the backend."""
        status = {
            "status": "healthy",
            "rag_system_available": self.rag_system is not None,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.rag_system:
            try:
                stats = self.rag_system.get_stats()
                status["rag_stats"] = stats
            except Exception as e:
                status["rag_error"] = str(e)
                status["status"] = "degraded"
        
        return status

# Initialize the chatbot backend
chatbot = ChatbotBackend()

# Routes
@app.route('/')
def index():
    """Serve the main chatbot interface."""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return f"Error loading chatbot interface: {e}", 500

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS, etc.)."""
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {e}")
        return f"File not found: {filename}", 404

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend."""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Get session ID from request or use default
        session_id = data.get('session_id', 'default')
        
        # Get response from chatbot
        response = chatbot.get_response(message, session_id)
        
        logger.info(f"Chat request processed - Message: '{message[:50]}...' - Response length: {len(response.get('answer', ''))}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "Internal server error",
            "answer": "I'm sorry, I'm experiencing technical difficulties. Please try again.",
            "sources": [],
            "tokens": {},
            "using_memory": False
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        status = chatbot.get_health_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error in health endpoint: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset conversation endpoint."""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', 'default')
        
        result = chatbot.reset_conversation(session_id)
        logger.info(f"Conversation reset for session: {session_id}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in reset endpoint: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    """Get system statistics."""
    try:
        if chatbot.rag_system:
            stats = chatbot.rag_system.get_stats()
            return jsonify(stats)
        else:
            return jsonify({
                "error": "RAG system not available",
                "mock_mode": True
            })
    except Exception as e:
        logger.error(f"Error in stats endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

def main():
    """Main entry point for the Flask app."""
    # Configuration
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting SmartBeauty AI Chatbot Backend")
    logger.info(f"📡 Server: http://{host}:{port}")
    logger.info(f"🔧 Debug mode: {debug}")
    logger.info(f"🤖 RAG system available: {RAG_AVAILABLE}")
    
    if not RAG_AVAILABLE:
        logger.warning("⚠️  Running in mock mode - some features may be limited")
        logger.info("💡 To enable full functionality, ensure the RAG system dependencies are installed")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down chatbot backend")
    except Exception as e:
        logger.error(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()
