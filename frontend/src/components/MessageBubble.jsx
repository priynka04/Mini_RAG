/**
 * Message bubble component - displays individual chat messages
 */
export default function MessageBubble({ message, isUser }) {
  return (
    <div className={`message-bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-header">
        <span className="message-role">{isUser ? '👤 You' : '🤖 Assistant'}</span>
      </div>
      <div className="message-content">
        {message}
      </div>
    </div>
  );
}