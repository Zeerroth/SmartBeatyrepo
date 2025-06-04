// SmartBeauty AI Chatbot JavaScript

class SmartBeautyChatbot {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
        this.conversationHistory = [];
        this.isWaitingForResponse = false;

        // Initialize character count
        this.updateCharCount();

        // Hide quick suggestions initially if chat has started
        this.checkQuickSuggestionsVisibility();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.resetBtn = document.getElementById('resetBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.charCount = document.getElementById('charCount');
        this.quickSuggestions = document.getElementById('quickSuggestions');
    }

    attachEventListeners() {
        // Send button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        // Enter key press (Shift+Enter for new line, Enter to send)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.updateCharCount();
            this.updateSendButtonState();
            this.autoResizeTextarea();
        });

        // Reset button
        this.resetBtn.addEventListener('click', () => this.resetConversation());

        // Quick suggestion clicks
        document.querySelectorAll('.suggestion-chip').forEach(chip => {
            chip.addEventListener('click', (e) => {
                const message = e.currentTarget.getAttribute('data-message');
                this.messageInput.value = message;
                this.updateCharCount();
                this.updateSendButtonState();
                this.sendMessage();
            });
        });
    }

    updateCharCount() {
        const count = this.messageInput.value.length;
        this.charCount.textContent = `${count}/500`;

        if (count > 450) {
            this.charCount.style.color = '#ef4444';
        } else if (count > 400) {
            this.charCount.style.color = '#f59e0b';
        } else {
            this.charCount.style.color = '#6b7280';
        }
    }

    updateSendButtonState() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText || this.isWaitingForResponse;
    }

    checkQuickSuggestionsVisibility() {
        // Hide suggestions after first user message
        if (this.conversationHistory.length > 0) {
            this.quickSuggestions.style.display = 'none';
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isWaitingForResponse) return;

        // Add user message to chat
        this.addMessage(message, 'user');

        // Clear input and update states
        this.messageInput.value = '';
        this.updateCharCount();
        this.updateSendButtonState();

        // Hide quick suggestions after first message
        this.quickSuggestions.style.display = 'none';

        // Show typing indicator
        this.showTypingIndicator();

        // Set waiting state
        this.isWaitingForResponse = true;
        this.updateSendButtonState();

        try {
            // Send message to backend
            const response = await this.sendToBackend(message);

            // Hide typing indicator
            this.hideTypingIndicator();

            // Add bot response
            this.addBotMessage(response);
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();

            // Add error message
            this.addMessage(
                "I'm sorry, I'm experiencing technical difficulties. Please check that the backend server is running and try again.",
                'bot',
                { isError: true }
            );
        } finally {
            this.isWaitingForResponse = false;
            this.updateSendButtonState();
        }
    } async sendToBackend(message) {
        try {
            // Send message to the backend API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Handle error responses from backend
            if (data.error) {
                throw new Error(data.error);
            }

            return data;
        } catch (error) {
            console.error('Backend API error:', error);
            throw error; // Let the calling function handle the error
        }
    }

    addMessage(text, sender, options = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = sender === 'user'
            ? '<i class="fas fa-user"></i>'
            : '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = text;

        if (options.isError) {
            textDiv.style.background = '#fee2e2';
            textDiv.style.color = '#dc2626';
            textDiv.style.borderColor = '#fecaca';
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.getCurrentTime();

        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Add to conversation history
        this.conversationHistory.push({
            sender,
            text,
            timestamp: new Date().toISOString()
        });
    }

    addBotMessage(response) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';

        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = '<i class="fas fa-robot"></i>';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = response.answer;

        // Add source documents if available
        if (response.sources && response.sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'source-documents';

            const sourcesTitle = document.createElement('div');
            sourcesTitle.className = 'source-title';
            sourcesTitle.textContent = 'Sources:';
            sourcesDiv.appendChild(sourcesTitle);

            response.sources.forEach((source, index) => {
                const sourceItem = document.createElement('div');
                sourceItem.className = 'source-item';
                sourceItem.innerHTML = `
                    <span class="similarity-score">${(source.similarity * 100).toFixed(1)}%</span> - 
                    ${source.content}
                `;
                sourcesDiv.appendChild(sourceItem);
            });

            textDiv.appendChild(sourcesDiv);
        }        // Add token information if available
        if (response.tokens) {
            const tokenInfo = document.createElement('div');
            tokenInfo.className = 'token-info';
            if (response.tokens.total_tokens) {
                // New format with input/output/total tokens
                tokenInfo.textContent = `Tokens: ${response.tokens.total_tokens} total (${response.tokens.input_tokens} input + ${response.tokens.output_tokens} output)`;
            } else {
                // Fallback to old format
                tokenInfo.textContent = `Tokens: ${response.tokens.prompt || 0} prompt + ${response.tokens.completion || 0} completion`;
            }
            textDiv.appendChild(tokenInfo);
        }

        // Add memory indicator if available
        if (response.using_memory !== undefined) {
            const memoryInfo = document.createElement('div');
            memoryInfo.className = 'memory-info';
            memoryInfo.textContent = response.using_memory ? '🧠 Using conversation memory' : '📝 Single query (no memory)';
            textDiv.appendChild(memoryInfo);
        }

        // Add conversation turn info if available
        if (response.conversation_turn) {
            const turnInfo = document.createElement('div');
            turnInfo.className = 'turn-info';
            turnInfo.textContent = `Turn: ${response.conversation_turn}`;
            textDiv.appendChild(turnInfo);
        }

        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = this.getCurrentTime();

        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Add to conversation history
        this.conversationHistory.push({
            sender: 'bot',
            text: response.answer,
            sources: response.sources,
            tokens: response.tokens,
            timestamp: new Date().toISOString()
        });

        // Save to local storage for persistence
        this.saveConversationHistory();
    }

    showTypingIndicator() {
        this.typingIndicator.classList.add('show');
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.classList.remove('show');
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    resetConversation() {
        // Confirm reset
        if (this.conversationHistory.length > 0) {
            if (!confirm('Are you sure you want to reset the conversation? This will clear all messages.')) {
                return;
            }
        }

        // Clear messages except the initial bot message
        const messages = this.chatMessages.querySelectorAll('.message');
        messages.forEach((message, index) => {
            if (index > 0) { // Keep the first message (welcome message)
                message.remove();
            }
        });

        // Clear conversation history
        this.conversationHistory = [];

        // Show quick suggestions again
        this.quickSuggestions.style.display = 'block';

        // Clear any pending states
        this.isWaitingForResponse = false;
        this.hideTypingIndicator();
        this.updateSendButtonState();

        // Clear local storage
        localStorage.removeItem('smartbeauty_conversation');

        // Focus input
        this.messageInput.focus();
    }

    saveConversationHistory() {
        try {
            localStorage.setItem('smartbeauty_conversation', JSON.stringify(this.conversationHistory));
        } catch (error) {
            console.warn('Failed to save conversation history:', error);
        }
    } loadConversationHistory() {
        try {
            const saved = localStorage.getItem('smartbeauty_conversation');
            if (saved) {
                const history = JSON.parse(saved);
                // Restore conversation (optional feature for persistence)
                // Implementation would go here if needed
            }
        } catch (error) {
            console.warn('Failed to load conversation history:', error);
        }
    }

    autoResizeTextarea() {
        // Reset height to calculate new height
        this.messageInput.style.height = 'auto';

        // Calculate new height based on scroll height
        const newHeight = Math.min(this.messageInput.scrollHeight, 120); // Max height of 120px
        this.messageInput.style.height = newHeight + 'px';
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chatbot = new SmartBeautyChatbot();

    // Focus on input field
    document.getElementById('messageInput').focus();

    console.log('SmartBeauty AI Chatbot initialized successfully!');
});
