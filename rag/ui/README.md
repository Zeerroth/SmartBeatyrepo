# SmartBeauty AI Chatbot UI

A modern, responsive web interface for the SmartBeauty AI skincare recommendation system.

## Features

- 🎨 **Classic Design**: Clean, professional interface with a modern gradient background
- 💬 **Real-time Chat**: Instant messaging with typing indicators and smooth animations
- 🔄 **Reset Functionality**: Clear conversation history with confirmation dialog
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- ⚡ **Quick Suggestions**: Pre-built questions for common skincare concerns
- 🔍 **Source Attribution**: Shows similarity scores and source documents
- 📊 **Token Counting**: Displays LLM token usage information
- 🌐 **API Integration**: Connects to backend RAG system with fallback support

## Quick Start

### Option 1: Use the Startup Script (Windows)

```bash
# Navigate to the ui folder
cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"

# Run the startup script
start_chatbot.bat
```

### Option 2: Manual Start

```bash
# Navigate to the ui folder
cd "c:\Projects\Personal Projects\ML\SmartBeauty\LLM\rag\ui"

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Start the server
python app.py
```

### Option 3: Direct File Access

If you prefer to use the frontend without the backend:

1. Open `index.html` directly in your browser
2. The chatbot will use mock responses for testing

## Usage

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
