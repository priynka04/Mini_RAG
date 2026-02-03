/**
 * Chat interface component - main query interface with chat history
 */
import { useState, useRef, useEffect } from 'react';
import { sendQuery } from '../services/api';
import MessageBubble from './MessageBubble';
import AnswerPanel from './AnswerPanel';

export default function ChatInterface({ conversationId, onFirstMessage }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [sessionId] = useState(`session-${Date.now()}`);
  
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Reset chat when conversation changes
  useEffect(() => {
    if (conversationId) {
      setChatHistory([]);
      setCurrentResponse(null);
      setError(null);
      setQuery('');
    }
  }, [conversationId]);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, currentResponse]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [query]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!query.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError(null);

    // Add user message to chat
    const userMessage = { role: 'user', content: query };
    const newHistory = [...chatHistory, userMessage];
    setChatHistory(newHistory);

    // Update conversation title with first message
    if (newHistory.length === 1 && onFirstMessage) {
      onFirstMessage(query);
    }

    // Clear input
    const currentQuery = query;
    setQuery('');

    try {
      // Prepare chat history for API (last 3 turns)
      const apiChatHistory = newHistory.slice(-6).map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      // Send query
      const response = await sendQuery(currentQuery, apiChatHistory, sessionId);
      
      setCurrentResponse(response);

      // Add assistant message to chat
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        response: response
      };
      setChatHistory([...newHistory, assistantMessage]);

    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing query');
      // Remove user message if query failed
      setChatHistory(chatHistory);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="chat-interface">
      {/* Chat Messages */}
      <div className="chat-messages">
        {chatHistory.length === 0 ? (
          <div className="chat-empty">
            <div className="empty-icon">💬</div>
            <h3>Ask me anything about your documents!</h3>
            <div className="example-prompts">
              <button className="example-prompt" onClick={() => setQuery('What are the main topics discussed?')}>
                "What are the main topics discussed?"
              </button>
              <button className="example-prompt" onClick={() => setQuery('Summarize the key points')}>
                "Summarize the key points"
              </button>
              <button className="example-prompt" onClick={() => setQuery('What links are referenced?')}>
                "What links are referenced?"
              </button>
            </div>
          </div>
        ) : (
          <>
            {chatHistory.map((msg, idx) => (
              <div key={idx}>
                {msg.role === 'user' ? (
                  <MessageBubble
                    message={msg.content}
                    isUser={true}
                  />
                ) : (
                  msg.response && <AnswerPanel response={msg.response} />
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </>
        )}

        {loading && (
          <div className="loading-message">
            <div className="loading-icon">
              <div className="spinner"></div>
            </div>
            <span>Thinking...</span>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="input-area">
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-container">
            <textarea
              ref={textareaRef}
              placeholder="Ask a question about your documents..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              rows={1}
            />
            <button 
              type="submit" 
              disabled={loading || !query.trim()}
              className="send-button"
            >
              {loading ? (
                <div className="button-spinner"></div>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}