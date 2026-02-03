/**
 * Main App component - ChatGPT-style interface with sidebar
 */
import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import DocumentUpload from './components/DocumentUpload';
import { getStats, healthCheck } from './services/api';
import './index.css';

function App() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);

  useEffect(() => {
    checkHealth();
    fetchStats();
    
    // Create initial conversation if none exists
    if (conversations.length === 0) {
      createNewConversation();
    }
  }, []);

  const checkHealth = async () => {
    try {
      const data = await healthCheck();
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const handleUploadSuccess = () => {
    fetchStats();
    setShowUploadModal(false);
  };

  const createNewConversation = () => {
    const newConv = {
      id: Date.now(),
      title: 'New conversation',
      timestamp: Date.now(),
      preview: ''
    };
    setConversations(prev => [newConv, ...prev]);
    setActiveConversationId(newConv.id);
  };

  const updateConversationTitle = (id, firstMessage) => {
    setConversations(convs =>
      convs.map(conv =>
        conv.id === id
          ? { ...conv, title: firstMessage.substring(0, 30) + '...', preview: firstMessage }
          : conv
      )
    );
  };

  return (
    <div className="chatgpt-app">
      {/* Sidebar */}
      <div className="chatgpt-sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={createNewConversation}>
            <span className="icon">+</span>
            <span>New chat</span>
          </button>
        </div>

        <div className="chat-list">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`chat-item ${activeConversationId === conv.id ? 'active' : ''}`}
              onClick={() => setActiveConversationId(conv.id)}
            >
              <span className="chat-icon">💬</span>
              <div className="chat-item-content">
                <div className="chat-title">{conv.title}</div>
                {conv.preview && (
                  <div className="chat-preview">{conv.preview.substring(0, 40)}...</div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <button className="upload-btn" onClick={() => setShowUploadModal(!showUploadModal)}>
            <span className="icon">📄</span>
            <span>Upload Documents</span>
          </button>
          
          {stats && stats.total_chunks > 0 && (
            <div className="stats-info">
              <span className="stat-item">
                <span className="stat-icon">📊</span>
                <span>{stats.total_chunks} chunks</span>
              </span>
            </div>
          )}

          {health && (
            <div className={`health-indicator ${health.status === 'healthy' ? 'healthy' : 'unhealthy'}`}>
              <span className="status-dot"></span>
              <span>{health.status === 'healthy' ? 'Connected' : 'Disconnected'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="chatgpt-main">
        <div className="chat-header">
          <h2>🔍 RAG Application</h2>
          <p className="subtitle">Chat with Your Documents</p>
        </div>

        <ChatInterface
          conversationId={activeConversationId}
          onFirstMessage={(message) => updateConversationTitle(activeConversationId, message)}
        />
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay" onClick={() => setShowUploadModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>📄 Upload Documents</h2>
              <button className="modal-close" onClick={() => setShowUploadModal(false)}>
                ✕
              </button>
            </div>
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;