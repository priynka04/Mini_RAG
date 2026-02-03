/**
 * Main App component
 */
import React from "react";
import SourceCard from "./components/SourceCard";
import "./index.css";
import { useState, useEffect } from 'react';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import { getStats, healthCheck } from './services/api';

function App() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    // Check health on mount
    checkHealth();
    fetchStats();
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
    // Refresh stats after upload
    fetchStats();
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <h1>🔍 RAG Application</h1>
        <p className="subtitle">Retrieval-Augmented Generation with Citations</p>
        
        {/* Stats Bar */}
        <div className="stats-bar">
          {health && (
            <div className={`health-status ${health.status === 'healthy' ? 'healthy' : 'unhealthy'}`}>
              <span className="status-dot"></span>
              {health.status === 'healthy' ? 'Connected' : 'Disconnected'}
            </div>
          )}
          
          {stats && stats.total_chunks > 0 && (
            <div className="stat">
              <span className="stat-label">📊 Chunks:</span>
              <span className="stat-value">{stats.total_chunks}</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        <div className="container">
          {/* Left Column - Document Upload */}
          <div className="column left-column">
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Right Column - Chat */}
          <div className="column right-column">
            <ChatInterface />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Built with React + FastAPI + Gemini + Qdrant + Cohere</p>
      </footer>
    </div>
  );
}

export default App;