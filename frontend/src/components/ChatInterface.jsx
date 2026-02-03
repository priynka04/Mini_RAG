/**
 * Chat interface component - main query interface with chat history
 */
import { useState, useRef, useEffect } from 'react';
import { sendQuery } from '../services/api';
import MessageBubble from './MessageBubble';
import AnswerPanel from './AnswerPanel';

export default function ChatInterface() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [sessionId] = useState(`session-${Date.now()}`);
  
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, currentResponse]);

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
        content: response.answer
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

  const clearChat = () => {
    setChatHistory([]);
    setCurrentResponse(null);
    setError(null);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>💬 Chat with Your Documents</h2>
        {chatHistory.length > 0 && (
          <button onClick={clearChat} className="btn btn-secondary btn-small">
            Clear Chat
          </button>
        )}
      </div>

      {/* Chat History */}
      <div className="chat-history">
        {chatHistory.length === 0 ? (
          <div className="chat-empty">
            <p>👋 Ask me anything about your uploaded documents!</p>
            <p className="examples">
              <strong>Try asking:</strong><br />
              "What are the main topics discussed?"<br />
              "Summarize the key points"<br />
              "What links are referenced?"
            </p>
          </div>
        ) : (
          <>
            {chatHistory.map((msg, idx) => (
              <MessageBubble
                key={idx}
                message={msg.content}
                isUser={msg.role === 'user'}
              />
            ))}
            <div ref={chatEndRef} />
          </>
        )}

        {loading && (
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Thinking...</span>
          </div>
        )}
      </div>

      {/* Current Response Details */}
      {currentResponse && !loading && (
        <AnswerPanel response={currentResponse} />
      )}

      {/* Error Message */}
      {error && <div className="message error">{error}</div>}

      {/* Query Input */}
      <form onSubmit={handleSubmit} className="query-form">
        <input
          type="text"
          placeholder="Ask a question about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={loading}
          className="query-input"
        />
        <button 
          type="submit" 
          disabled={loading || !query.trim()}
          className="btn btn-primary"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
}