# SmartBeauty AI Chatbot UI

A modern, responsive web interface for the SmartBeauty AI skincare advisor powered by the conversational RAG system.

## Features

- 🎨 **Classic Design**: Clean, professional interface with a modern gradient background
- 💬 **Real-time Chat**: Instant messaging with typing indicators and smooth animations
- 🔄 **Reset Functionality**: Clear conversation history with confirmation dialog
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- ⚡ **Quick Suggestions**: Pre-built questions for common skincare concerns
- 🔍 **Source Attribution**: Shows similarity scores and source documents
- 📊 **Token Counting**: Displays LLM token usage information
- 🌐 **Flask Backend**: Direct integration with conversational RAG system
- 🧠 **Memory**: Maintains conversation context across multiple turns
- 🎯 **Smart Responses**: Powered by the full conversational RAG system

## Quick Start

### Option 1: Use the Startup Script (Windows)

```bash
# Navigate to the ui folder
cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"

# Run the Flask backend startup script
start_backend.bat
```

### Option 2: Use the Startup Script (Linux/Mac)

```bash
# Navigate to the ui folder
cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"

# Make the script executable and run it
chmod +x start_backend.sh
./start_backend.sh
```

### Option 3: Manual Start

```bash
# Navigate to the ui folder
cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the Flask backend
python app.py
```

## Usage

1. **Start the Backend**: Use one of the methods above to start the Flask backend server
2. **Open Browser**: Navigate to `http://127.0.0.1:5000`
3. **Start Chatting**: Type your skincare questions or use the quick suggestion chips
4. **View Sources**: See the source documents and similarity scores for each response
5. **Reset Conversation**: Use the reset button to start fresh and clear memory

## File Structure

```
ui/
├── index.html          # Main HTML interface
├── style.css           # CSS styling (classic design)
├── script.js           # JavaScript functionality
├── app.py              # Flask backend with RAG integration
├── requirements.txt    # Python dependencies
├── start_backend.bat   # Windows startup script
├── start_backend.sh    # Linux/Mac startup script
├── test_backend.py     # Backend testing script
└── README.md          # This file
```

## API Endpoints

The Flask backend provides the following endpoints:

- `GET /` - Serves the chatbot UI (index.html)
- `GET /<filename>` - Serves static files (CSS, JS, etc.)
- `POST /api/chat` - Handles chat messages and returns AI responses
- `GET /api/health` - Health check endpoint with system status
- `POST /api/reset` - Reset conversation memory
- `GET /api/stats` - Get RAG system statistics

### API Request/Response Format

#### Chat Request
```json
{
  "message": "What products do you recommend for oily skin?",
  "session_id": "optional_session_id"
}
```

#### Chat Response
```json
{
  "answer": "For oily skin, I'd recommend...",
  "sources": [
    {
      "content": "Source document content...",
      "similarity": 0.92,
      "name": "Product Name",
      "type": "product",
      "rank": 1
    }
  ],
  "tokens": {
    "input_tokens": 15,
    "output_tokens": 85,
    "total_tokens": 100
  },
  "using_memory": true,
  "conversation_turn": 2,
  "timestamp": "2025-06-04T10:30:00"
}
```

## Backend Integration

### RAG System Integration

The Flask backend directly integrates with the conversational RAG system:

- **Direct Import**: Imports `SmartBeautyRAGSystem` from the core module
- **Memory Management**: Maintains conversation context using LangChain memory
- **Source Attribution**: Returns actual source documents with similarity scores
- **Token Counting**: Accurate token counting using tiktoken
- **Error Handling**: Graceful fallback to mock responses if RAG system fails

### Fallback Mode

If the RAG system is unavailable (missing dependencies, database issues, etc.):

- Automatically switches to mock response mode
- Provides keyword-based responses for common skincare topics
- Shows clear indicators when in fallback mode
- Maintains UI functionality for testing and development

## Features in Detail

### Chat Interface

- **Message Types**: User and bot messages with distinct styling
- **Timestamps**: All messages include time information
- **Character Counter**: Input field shows character count (500 max)
- **Send Button**: Automatically enables/disables based on input
- **Auto-resize**: Input textarea expands with content

### Source Documents

- **Similarity Scores**: Shows how relevant each source is (0-100%)
- **Source Content**: Displays the actual text that informed the response
- **Source Names**: Product or condition names from the database
- **Ranking**: Sources ordered by relevance

### Token Information

- **Input/Output Split**: Shows tokens used for prompt vs completion
- **Total Count**: Combined token usage for the conversation turn
- **Real-time Tracking**: Updated with each API response

### Memory & Context

- **Conversational Memory**: Remembers previous questions and answers
- **Turn Tracking**: Shows current conversation turn number
- **Memory Indicators**: Visual feedback when using conversation memory
- **Memory Reset**: Clear conversation history and start fresh

### Quick Suggestions

Pre-built questions to get users started:

- **Oily Skin**: "What products do you recommend for oily skin?"
- **Sensitive Skin**: "I have sensitive skin that gets red easily. What can help?"
- **Anti-Aging**: "What are good anti-aging products for wrinkles?"
- **Dry Skin**: "My skin is very dry. What moisturizing products would help?"

## Configuration

### Environment Variables

The backend respects these environment variables:

- `FLASK_HOST`: Server host (default: 127.0.0.1)
- `FLASK_PORT`: Server port (default: 5000)
- `FLASK_DEBUG`: Debug mode (default: False)
- `FLASK_ENV`: Environment (default: development)

### RAG System Configuration

The backend uses the same configuration as the core RAG system:

- Database connection from `core/config.py`
- OpenAI API key from environment variables
- Embedding model settings
- Collection name (default: "products")

## Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```bash
   # Solution: Ensure you're in the ui directory and install dependencies
   cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"
   pip install -r requirements.txt
   ```

2. **RAG system import errors**
   ```bash
   # Solution: Check if core dependencies are installed
   cd ../core
   pip install -r requirements.txt
   ```

3. **Database connection failures**
   - Check PostgreSQL is running
   - Verify database credentials in `core/.env`
   - Backend will automatically fall back to mock responses

4. **OpenAI API errors**
   - Check API key in `core/.env`
   - Verify internet connection
   - Backend will show clear error messages

5. **Port already in use**
   ```bash
   # Solution: Use a different port
   set FLASK_PORT=5001
   python app.py
   ```

### Debug Information

The Flask backend provides extensive logging:

- Startup information with configuration details
- Request/response logging for API calls
- Error messages with stack traces in debug mode
- RAG system initialization status

### Health Check

Use the health endpoint to check system status:

```bash
curl http://127.0.0.1:5000/api/health
```

Response includes:
- Backend status
- RAG system availability
- System statistics (if available)
- Error information (if any)

## Development

### Backend Development

To modify the Flask backend (`app.py`):

1. **Add new endpoints**: Follow the existing pattern with error handling
2. **Modify RAG integration**: Update the `ChatbotBackend` class
3. **Change response format**: Update `_transform_sources()` method
4. **Add new features**: Extend the API with additional functionality

### Frontend Development

To modify the chat interface:

1. **HTML changes**: Edit `index.html` for structure
2. **Styling changes**: Edit `style.css` for appearance
3. **JavaScript changes**: Edit `script.js` for functionality
4. **API integration**: Update fetch calls to match backend endpoints

### Testing

Use the included test script:

```bash
python test_backend.py
```

This tests:
- Import functionality
- Mock response generation
- Basic Flask app creation
- Error handling

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance

- **Fast Loading**: Minimal dependencies and optimized assets
- **Smooth Animations**: Hardware-accelerated CSS transitions
- **Efficient Backend**: Direct RAG system integration
- **Memory Management**: Automatic conversation cleanup
- **Caching**: Static file serving with appropriate headers

## Security Considerations

- **Input Validation**: All user inputs are validated and sanitized
- **Error Handling**: No sensitive information leaked in error messages
- **CORS**: Configured for local development (adjust for production)
- **Session Management**: Basic session isolation by session ID

---

For issues or questions about the chatbot UI, please check the main project README or create an issue in the repository.

1. **Start the Server**: Use one of the methods above to start the backend server
2. **Open Browser**: Navigate to `http://localhost:5000`
3. **Start Chatting**: Type your skincare questions or use the quick suggestion chips
4. **View Sources**: See the source documents and similarity scores for each response
5. **Reset Conversation**: Use the reset button to start fresh

## File Structure

```
ui/
├── index.html          # Main HTML interface
├── style.css           # CSS styling (classic design)
├── script.js           # JavaScript functionality
├── app.py              # Flask backend API
├── requirements.txt    # Python dependencies
├── start_chatbot.bat   # Windows startup script
└── README.md          # This file
```

## API Endpoints

- `GET /` - Serves the chatbot UI
- `POST /api/chat` - Handles chat messages
- `GET /api/health` - Health check endpoint
- `POST /api/reset` - Reset conversation

## Features in Detail

### Chat Interface

- **Message Types**: User and bot messages with distinct styling
- **Timestamps**: All messages include time information
- **Character Counter**: Input field shows character count (500 max)
- **Send Button**: Automatically enables/disables based on input

### Source Documents

- **Similarity Scores**: Shows how relevant each source is (0-100%)
- **Source Content**: Displays the actual text that informed the response
- **Token Information**: Shows prompt and completion token counts

### Quick Suggestions

- **Oily Skin**: "What products do you recommend for oily skin?"
- **Sensitive Skin**: "I have sensitive skin that gets red easily. What can help?"
- **Anti-Aging**: "What are good anti-aging products for wrinkles?"
- **Dry Skin**: "My skin is very dry. What moisturizing products would help?"

### Responsive Design

- **Desktop**: Full-width layout with side-by-side message bubbles
- **Tablet**: Optimized spacing and touch-friendly buttons
- **Mobile**: Stacked layout with larger touch targets

## Backend Integration

The UI connects to the RAG system through the Flask backend:

### RAG System Available

- Uses the full RAG chain for intelligent responses
- Accesses the PostgreSQL database with product information
- Provides real similarity scores and source documents
- Accurate token counting with tiktoken

### Fallback Mode

- If RAG system is unavailable, uses mock responses
- Keyword-based matching for common skincare topics
- Graceful degradation with error handling

## Customization

### Styling

Modify `style.css` to change:

- Color scheme (currently purple/blue gradient)
- Font families and sizes
- Animation timings
- Layout dimensions

### Functionality

Modify `script.js` to change:

- Message handling logic
- API endpoints
- Mock responses
- User interaction behavior

### Backend

Modify `app.py` to change:

- RAG system integration
- API response format
- Error handling
- Logging behavior

## Troubleshooting

### Common Issues

1. **"Module not found" errors**

   - Ensure you're in the correct directory
   - Install dependencies: `pip install -r requirements.txt`

2. **Database connection failures**

   - Check PostgreSQL is running on localhost:5433
   - Verify database credentials in core/.env
   - The UI will fall back to mock responses

3. **OpenAI API errors**

   - Check API key in core/.env
   - Verify internet connection
   - The UI will show error messages for failed requests

4. **Port already in use**
   - Change the port in app.py: `app.run(port=5001)`
   - Or stop other Flask applications

### Debug Mode

The Flask app runs in debug mode by default, which provides:

- Automatic reloading when files change
- Detailed error messages
- Console logging

## Development

To contribute or modify the chatbot:

1. **Frontend Changes**: Edit HTML, CSS, or JavaScript files
2. **Backend Changes**: Modify app.py for API behavior
3. **RAG Integration**: Update the RAG chain connection logic
4. **Testing**: Use both the browser console and Flask debug output

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Performance

- **Fast Loading**: Minimal dependencies and optimized assets
- **Smooth Animations**: Hardware-accelerated CSS transitions
- **Efficient API**: Lightweight JSON responses
- **Memory Management**: Conversation history cleanup

---

For issues or questions about the chatbot UI, please check the main project README or create an issue in the repository.
