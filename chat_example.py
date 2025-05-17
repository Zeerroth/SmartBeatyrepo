import os
from dotenv import load_dotenv
from beauty_expert_bot import BeautyExpertBot

# Example API response data
SAMPLE_ANALYSIS = {
    "data": [
        {
            "analysisType": "acne",
            "confidence": 0.3376757907246589,
            "createdAt": "2025-05-17T12:34:13.481886Z"
        },
        {
            "analysisType": "eyebag",
            "confidence": 0.5498298763790739,
            "createdAt": "2025-05-17T12:34:23.753216Z"
        },
        {
            "analysisType": "redness",
            "confidence": 0,
            "createdAt": "2025-05-17T12:34:34.172279Z"
        },
        {
            "analysisType": "wrinkle",
            "confidence": 0.6211300007235936,
            "createdAt": "2025-05-17T12:34:44.097766Z"
        }
    ]
}

def validate_api_key(api_key: str) -> bool:
    """Validate the API key format"""
    if not api_key:
        return False
    return True

def chat_session():
    # Load OpenAI API key
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not validate_api_key(api_key):
        print("Error: Invalid or missing OpenAI API key")
        print("Please ensure your api_key.env file contains a valid OpenAI API key")
        return

    try:
        # Initialize the beauty expert bot
        print("\nInitializing Beauty Expert Bot...")
        bot = BeautyExpertBot(api_key)
        
        # Start conversation with skin analysis
        print("Starting analysis...")
        initial_response = bot.start_conversation(SAMPLE_ANALYSIS)
        print(f"\nBeauty Expert: {initial_response}")

        # Interactive chat loop
        while True:
            # Get user input
            user_input = input("\nYou (type 'quit' to end): ").strip()
            
            # Check for exit command
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nBeauty Expert: Thank you for the conversation! Take care of your skin!")
                
                # Save conversation history
                filename = bot.save_conversation()
                print(f"\nConversation saved to: {filename}")
                break
            
            # Get bot's response
            response = bot.get_response(user_input)
            print(f"\nBeauty Expert: {response}")

    except Exception as e:
        print(f"\nError: Failed to initialize or run the chatbot")
        print(f"Details: {str(e)}")
        print("\nPlease check your API key and internet connection")

if __name__ == "__main__":
    print("Welcome to the Beauty Expert Chat!")
    print("=" * 50)
    print("Ask questions about your skin analysis, get personalized recommendations,")
    print("or seek advice about specific skin concerns.")
    print("=" * 50)
    
    chat_session() 