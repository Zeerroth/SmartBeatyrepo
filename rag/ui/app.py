"""
SmartBeauty AI Chatbot Backend API
Connects the chatbot UI to the RAG inference system
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import subprocess
import tempfile

# Add the core directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# Try to import RAG components
try:
    from config import get_openai_key, DATABASE_URL
    from rag_chain import RAGChain
    from utils import create_db_connection, test_db_connection
    print("✅ Successfully imported RAG components")
except ImportError as e:
    print(f"⚠️  Warning: Could not import RAG components: {e}")
    print("   API will use mock responses only")

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for frontend communication

class ChatbotAPI:
    def __init__(self):
        self.rag_chain = None
        self.use_rag = False
        self.initialize_rag()
    
    def initialize_rag(self):
        """Initialize the RAG system"""
        try:
            # Test database connection
            print("🔍 Testing database connection...")
            conn = create_db_connection()
            if conn:
                test_result = test_db_connection(conn)
                conn.close()
                
                if test_result:
                    print("✅ Database connection successful")
                    
                    # Initialize RAG chain
                    print("🔗 Initializing RAG chain...")
                    self.rag_chain = RAGChain()
                    self.use_rag = True
                    print("✅ RAG system initialized successfully")
                else:
                    print("❌ Database connection test failed")
            else:
                print("❌ Could not establish database connection")
                
        except Exception as e:
            print(f"❌ Error initializing RAG system: {e}")
            print("   Falling back to mock responses")
            traceback.print_exc()
    
    def get_rag_response(self, question):
        """Get response from RAG system"""
        if not self.use_rag or not self.rag_chain:
            return self.get_mock_response(question)
        
        try:
            # Use the RAG chain to get response
            print(f"🤖 Processing question: {question}")
            
            # Call the RAG chain
            response = self.rag_chain.answer_question(question)
            
            # Parse the response
            if isinstance(response, dict):
                answer = response.get('answer', 'I apologize, but I could not generate a response.')
                sources = response.get('sources', [])
                tokens = response.get('tokens', {})
            else:
                answer = str(response)
                sources = []
                tokens = {}
            
            return {
                'answer': answer,
                'sources': sources,
                'tokens': tokens,
                'timestamp': datetime.now().isoformat(),
                'using_rag': True
            }
            
        except Exception as e:
            print(f"❌ Error getting RAG response: {e}")
            traceback.print_exc()
            return self.get_mock_response(question)
    
    def get_mock_response(self, question):
        """Get mock response for testing"""
        print(f"🎭 Using mock response for: {question}")
        
        # Mock responses based on keywords
        mock_responses = {
            'oily': {
                'answer': "For oily skin, I recommend using a gentle foaming cleanser with salicylic acid, followed by a lightweight, oil-free moisturizer. Look for products containing niacinamide, which helps regulate oil production. The Ordinary Niacinamide 10% + Zinc 1% is excellent for controlling excess sebum.",
                'sources': [
                    {'content': "Salicylic acid helps unclog pores and reduce oil production", 'similarity': 0.89},
                    {'content': "Niacinamide regulates sebum production and minimizes pores", 'similarity': 0.87}
                ],
                'tokens': {'prompt': 45, 'completion': 78}
            },
            'sensitive': {
                'answer': "For sensitive skin that gets red easily, focus on gentle, fragrance-free products. Look for ingredients like ceramides, hyaluronic acid, and colloidal oatmeal. Avoid products with alcohol, strong fragrances, or harsh acids. CeraVe Gentle Foaming Cleanser and their PM Facial Moisturizing Lotion are great options.",
                'sources': [
                    {'content': "Ceramides help restore and maintain the skin barrier", 'similarity': 0.92},
                    {'content': "Fragrance-free formulas reduce irritation risk", 'similarity': 0.85}
                ],
                'tokens': {'prompt': 52, 'completion': 89}
            },
            'aging': {
                'answer': "For anti-aging and wrinkle prevention, incorporate retinoids, vitamin C, and peptides into your routine. Start with a gentle retinol like Neutrogena Rapid Wrinkle Repair, use vitamin C serum in the morning, and always apply SPF 30+ sunscreen. Hyaluronic acid helps plump fine lines.",
                'sources': [
                    {'content': "Retinoids boost collagen production and reduce fine lines", 'similarity': 0.94},
                    {'content': "Vitamin C protects against environmental damage", 'similarity': 0.88}
                ],
                'tokens': {'prompt': 38, 'completion': 95}
            },
            'dry': {
                'answer': "For very dry skin, use a cream-based cleanser and rich moisturizers with ceramides, glycerin, and hyaluronic acid. Apply moisturizer to damp skin to lock in hydration. Consider adding a facial oil like argan or jojoba oil. Avoid hot water and harsh cleansers that strip natural oils.",
                'sources': [
                    {'content': "Ceramides and glycerin provide long-lasting hydration", 'similarity': 0.91},
                    {'content': "Applying moisturizer to damp skin increases effectiveness", 'similarity': 0.86}
                ],
                'tokens': {'prompt': 41, 'completion': 82}
            }
        }
        
        # Simple keyword matching
        question_lower = question.lower()
        
        if 'oily' in question_lower:
            response = mock_responses['oily']
        elif any(word in question_lower for word in ['sensitive', 'red', 'irritat']):
            response = mock_responses['sensitive']
        elif any(word in question_lower for word in ['aging', 'wrinkle', 'anti-aging']):
            response = mock_responses['aging']
        elif 'dry' in question_lower:
            response = mock_responses['dry']
        else:
            # Default response
            response = {
                'answer': "I'd be happy to help you with your skincare concerns! Could you tell me more about your specific skin type or the issues you're experiencing? For example, do you have oily, dry, sensitive, or combination skin?",
                'sources': [],
                'tokens': {'prompt': 25, 'completion': 45}
            }
        
        response['timestamp'] = datetime.now().isoformat()
        response['using_rag'] = False
        return response

# Initialize the API
chatbot_api = ChatbotAPI()

@app.route('/')
def serve_ui():
    """Serve the chatbot UI"""
    try:
        ui_path = os.path.join(os.path.dirname(__file__), 'index.html')
        with open(ui_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error loading UI: {e}", 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        question = data['message'].strip()
        
        if not question:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get response from RAG system or mock
        response = chatbot_api.get_rag_response(question)
        
        # Log the interaction
        print(f"📝 Question: {question}")
        print(f"🤖 Response: {response['answer'][:100]}...")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ Error in chat endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'answer': "I'm sorry, I'm experiencing technical difficulties. Please try again later.",
            'sources': [],
            'tokens': {},
            'timestamp': datetime.now().isoformat(),
            'using_rag': False
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'rag_available': chatbot_api.use_rag,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation (placeholder for future session management)"""
    return jsonify({
        'status': 'conversation_reset',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting SmartBeauty AI Chatbot API...")
    print(f"💡 RAG System Available: {chatbot_api.use_rag}")
    print("🌐 Open http://localhost:5000 to access the chatbot")
    print("📡 API endpoints available at /api/chat, /api/health, /api/reset")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
