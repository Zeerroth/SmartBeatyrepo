# Smart Beauty AI Skincare Assistant

An intelligent skincare recommendation system that combines the power of OpenAI's GPT-4 with a comprehensive product database to provide personalized skincare advice and product recommendations.

## Features

- Skin analysis processing and interpretation
- Personalized product recommendations based on skin concerns
- Semantic search for relevant skincare products
- Conversation history management
- Local caching of product data and embeddings
- Integration with Inventra API for product information
- RAG (Retrieval-Augmented Generation) system for accurate recommendations

## Requirements

- Python 3.12+
- OpenAI API key
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeerroth/SmartBeatyrepo.git
cd SmartBeatyrepo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
Create a `.env` file in the root directory and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

Run the example chat interface:
```bash
python chat_example.py
```

The chatbot will:
1. Analyze provided skin data
2. Generate personalized recommendations
3. Engage in an interactive conversation about skincare concerns
4. Save conversation history for future reference

## Project Structure

- `beauty_expert_bot.py`: Main bot implementation with OpenAI integration
- `chat_example.py`: Example implementation of the chat interface
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not tracked in git)

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details. #   S m a r t B e a t y r e p o  
 