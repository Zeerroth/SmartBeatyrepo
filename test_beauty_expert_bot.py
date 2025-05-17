import asyncio
from beauty_expert_bot import BeautyExpertBot
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv("api_key.env")

# Get the API key from the environment variable
API_KEY = os.getenv("OPENAI_API_KEY")

async def test_get_response():
    """Tests the get_response method of the BeautyExpertBot."""
    if not API_KEY:
        print("Error: OPENAI_API_KEY not found. Please set it in api_key.env.")
        return

    bot = BeautyExpertBot(api_key=API_KEY)

    # Sample skin analysis data
    sample_analysis_data = {
        "data": [
            {"analysisType": "Acne", "confidence": 0.8},
            {"analysisType": "Redness", "confidence": 0.6},
            {"analysisType": "Dark Spots", "confidence": 0.2}
        ]
    }

    print("Starting conversation...")
    initial_response = await bot.start_conversation(sample_analysis_data)
    print(f"Bot (Initial): {initial_response}")

    user_query = "Tell me more about products for acne and redness."
    print(f"User: {user_query}")

    response = await bot.get_response(user_query)
    print(f"Bot: {response}")

    user_query_2 = "What is the price of the first product you recommended for acne?"
    print(f"User: {user_query_2}")
    response_2 = await bot.get_response(user_query_2)
    print(f"Bot: {response_2}")

    # Example of saving the conversation
    # saved_file = bot.save_conversation()
    # print(f"Conversation saved to: {saved_file}")

    # Example of clearing conversation
    # bot.clear_conversation()
    # print("Conversation cleared.")
    # response_after_clear = await bot.get_response("Hello again")
    # print(f"Bot (after clear): {response_after_clear}")


if __name__ == "__main__":
    asyncio.run(test_get_response())