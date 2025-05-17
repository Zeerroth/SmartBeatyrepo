import openai
import json
import requests
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
from openai import OpenAI

class BeautyExpertBot:
    def __init__(self, api_key: str):
        """Initialize the beauty expert bot with OpenAI API key"""
        try:
            # Initialize OpenAI client with the provided API key
            self.client = OpenAI(api_key=api_key)
            
            # Test the connection with a simple embedding request
            self._test_connection()
            
        except Exception as e:
            print(f"Warning: Error initializing OpenAI client: {e}")
            print("Please ensure you have a valid OpenAI API key")
            raise

        self.conversation_history = []
        self.current_analysis = None
        self.product_data = self._load_product_data()
        self.product_embeddings = {}
        self._initialize_embeddings()

    def _test_connection(self):
        """Test the OpenAI connection with a simple request"""
        try:
            # Try a simple embedding request to verify the connection
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input="test"
            )
            print("Successfully connected to OpenAI API")
        except Exception as e:
            print(f"Failed to connect to OpenAI API: {e}")
            raise

    def _load_product_data(self) -> Dict:
        """Load product data from static source or API"""
        try:
            # First try to load from local cache if exists
            try:
                with open('product_cache.json', 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                pass

            # If no cache, fetch from API
            response = requests.get("https://api.inventra.ca/api/Product/getAllProducts")
            if response.status_code == 200:
                data = response.json()
                # Cache the data for future use
                with open('product_cache.json', 'w') as f:
                    json.dump(data, f)
                return data
            return {"products": []}
        except Exception as e:
            print(f"Warning: Could not load product data: {e}")
            return {"products": []}

    def _initialize_embeddings(self):
        """Initialize embeddings for all products"""
        try:
            # Try to load cached embeddings
            try:
                with open('embeddings_cache.json', 'r') as f:
                    self.product_embeddings = json.load(f)
                return
            except FileNotFoundError:
                pass

            # Generate embeddings for each product
            for product in self.product_data.get('products', []):
                text_to_embed = f"{product['name']} {product['description']} {product['keyBenefits']} {product['activeContent']}"
                try:
                    response = self.client.embeddings.create(
                        model="text-embedding-3-small",
                        input=text_to_embed
                    )
                    self.product_embeddings[product['id']] = response.data[0].embedding
                except Exception as e:
                    print(f"Warning: Could not generate embedding for product {product['id']}: {e}")

            # Cache the embeddings
            with open('embeddings_cache.json', 'w') as f:
                json.dump(self.product_embeddings, f)
        except Exception as e:
            print(f"Warning: Error initializing embeddings: {e}")

    def _get_relevant_products(self, query: str, top_k: int = 3) -> List[Dict]:
        """Get most relevant products using semantic search"""
        try:
            # Get query embedding
            query_response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = query_response.data[0].embedding

            # Calculate similarities
            similarities = {}
            for product_id, embedding in self.product_embeddings.items():
                similarity = np.dot(query_embedding, embedding)
                similarities[product_id] = similarity

            # Get top-k products
            top_products = []
            sorted_products = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
            for product_id, _ in sorted_products[:top_k]:
                for product in self.product_data['products']:
                    if str(product['id']) == str(product_id):
                        top_products.append(product)
                        break

            return top_products
        except Exception as e:
            print(f"Warning: Error in semantic search: {e}")
            return []

    def _get_product_recommendations(self, skin_concerns: List[str]) -> str:
        """Get product recommendations based on skin concerns using RAG"""
        if not self.product_data or not self.product_data.get('products'):
            return "I apologize, but I couldn't access the product database at the moment."

        # Create a detailed query based on skin concerns
        concern_descriptions = {
            'acne': "products for acne-prone skin, treating breakouts and preventing new acne",
            'blackheads': "products that unclog pores and remove blackheads",
            'dark spots': "products for hyperpigmentation and evening skin tone",
            'wrinkles': "anti-aging products that reduce fine lines and wrinkles",
            'redness': "products that calm and soothe irritated, red skin",
            'sensitivity': "gentle products for sensitive skin that won't cause irritation"
        }

        query = " ".join([concern_descriptions.get(concern.lower(), concern) 
                         for concern in skin_concerns])

        recommended_products = self._get_relevant_products(query)

        if not recommended_products:
            return "I couldn't find specific products matching your skin concerns in our database."

        # Format recommendations
        recommendations = "Based on your skin concerns, here are some recommended products:\n\n"
        for i, product in enumerate(recommended_products, 1):
            recommendations += f"{i}. {product['name']}\n"
            recommendations += f"   Key Benefits: {product['keyBenefits']}\n"
            recommendations += f"   Active Ingredients: {product['activeContent']}\n"
            recommendations += f"   How to Use: {product['howToUse']}\n"
            recommendations += f"   Price: ${product['price']:.2f}\n\n"

        return recommendations

    def _format_analysis_data(self, api_data: Dict) -> str:
        """Format the API analysis data for the conversation"""
        conditions = []
        skin_concerns = []
        
        for item in api_data.get('data', []):
            confidence = item['confidence'] * 100
            conditions.append(f"- {item['analysisType']}: {confidence:.2f}%")
            
            # Add to skin concerns if confidence is significant
            if confidence > 30:
                skin_concerns.append(item['analysisType'].lower())
        
        analysis_text = "\n".join(conditions)
        
        # Add product recommendations if concerns are identified
        if skin_concerns:
            recommendations = self._get_product_recommendations(skin_concerns)
            analysis_text += "\n\n" + recommendations
        
        return analysis_text

    async def start_conversation(self, api_data: Dict) -> str:
        """Start a new conversation with initial skin analysis"""
        self.current_analysis = api_data
        analysis_text = self._format_analysis_data(api_data)
        
        initial_prompt = f"""Based on the skin analysis results and product recommendations:

{analysis_text}

Provide a friendly introduction and initial assessment of the skin conditions. 
Discuss the main concerns, explain the recommended products, and ask if the user would like more specific information about any of the products or their skin concerns."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": initial_prompt}
                ]
            )

            initial_message = response.choices[0].message.content
            self.conversation_history = [
                {"role": "system", "content": self._create_system_prompt()},
                {"role": "user", "content": initial_prompt},
                {"role": "assistant", "content": initial_message}
            ]
            
            return initial_message
        except Exception as e:
            print(f"Error in GPT-4 call: {e}")
            return f"Here's your skin analysis:\n\n{analysis_text}\n\nWould you like to know more about any specific concern or product?"

    async def get_response(self, user_message: str) -> str:
        """Get a response from the beauty expert based on user input"""
        if not self.current_analysis:
            return "Please start a new conversation with skin analysis data first."

        # Get relevant product information based on user query
        relevant_products = self._get_relevant_products(user_message)
        product_context = ""
        if relevant_products:
            product_context = "Here are some relevant products for your question:\n"
            for product in relevant_products:
                product_context += f"- {product['name']}: {product['keyBenefits']}\n"

        # Add user message and product context to history
        self.conversation_history.append({"role": "user", "content": f"{user_message}\n\nRelevant product information:\n{product_context}"})
        
        # Get response from GPT-4
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=self.conversation_history
            )
            
            bot_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response

        except Exception as e:
            print(f"Error in GPT-4 call: {e}")
            if relevant_products:
                return f"I found some products that might help:\n\n{product_context}"
            return "I understand your question. Let me provide a simple response based on the available data."

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the beauty expert persona"""
        return """You are an expert dermatologist and beauty consultant with extensive experience in skincare. 
Your role is to:
1. Analyze skin condition measurements
2. Provide personalized skincare advice
3. Recommend treatments and products
4. Answer questions about skincare concerns
5. Give practical, actionable advice

Always maintain a professional yet friendly tone. Base your recommendations on the skin analysis data provided.
When discussing products, use the provided product information and explain why they would be beneficial.
If asked about something not related to the analysis data, politely redirect to skin-related topics."""

    def save_conversation(self, filename: str = None) -> str:
        """Save the conversation history to a file"""
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "skin_analysis": self.current_analysis,
            "conversation": self.conversation_history
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename

    def clear_conversation(self) -> None:
        """Clear the current conversation history"""
        self.conversation_history = []
        self.current_analysis = None 