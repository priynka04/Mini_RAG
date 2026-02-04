/**
 * Main App component with sidebar and session management
 */
import { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import { healthCheck } from './services/api';

function App() {
  const [health, setHealth] = useState(null);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [forceUpdate, setForceUpdate] = useState(0);

  useEffect(() => {
    // ONE-TIME INITIALIZATION ON PAGE LOAD
    // This runs ONCE when the component mounts (empty dependency array)
    
    const initializeApp = async () => {
      // Step 1: Reset vector database (only in development, optional guard)
      if (import.meta.env.DEV) {
        try {
          const response = await fetch('http://localhost:8000/api/chat/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('✓ Vector DB reset:', data.message);
          } else {
            console.warn('Vector DB reset failed:', response.statusText);
          }
        } catch (error) {
          console.error('Error resetting vector DB:', error);
          // Don't block app initialization on reset failure
        }
      }
      
      // Step 2: Check health
      checkHealth();
      
      // Step 3: Clear sessions - START FRESH
      localStorage.removeItem('rag_sessions');
      
      // Step 4: Create first session
      createNewSession();
    };
    
    initializeApp();
  }, []); // EMPTY DEPENDENCY ARRAY = runs once on mount only

  // Save sessions whenever they change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('rag_sessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  const checkHealth = async () => {
    try {
      const data = await healthCheck();
      setHealth(data);
    } catch (error) {
      console.error('Health check failed:', error);
    }
  };

  const createNewSession = () => {
    const newSession = {
      id: `session-${Date.now()}`,
      title: 'New conversation',
      createdAt: new Date().toISOString(),
      documents: [],
      chatHistory: [],
      messages: [] // Separate messages array for UI
    };
    
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
  };

  const updateSessionTitle = (sessionId, firstQuery) => {
    setSessions(prev => prev.map(session => 
      session.id === sessionId
        ? { ...session, title: firstQuery.slice(0, 50) + (firstQuery.length > 50 ? '...' : '') }
        : session
    ));
  };

  const addDocumentToSession = (sessionId, document) => {
    setSessions(prev => prev.map(session =>
      session.id === sessionId
        ? { ...session, documents: [...session.documents, document] }
        : session
    ));
  };

  const updateSessionMessages = (sessionId, messages) => {
    setSessions(prev => prev.map(session =>
      session.id === sessionId
        ? { ...session, messages: messages }
        : session
    ));
  };

  const updateSessionChatHistory = (sessionId, chatHistory) => {
    setSessions(prev => prev.map(session =>
      session.id === sessionId
        ? { ...session, chatHistory: chatHistory }
        : session
    ));
  };

  const deleteSession = async (sessionId) => {
    const sessionToDelete = sessions.find(s => s.id === sessionId);
    
    // Delete all document chunks from this session
    if (sessionToDelete && sessionToDelete.documents.length > 0) {
      try {
        // Import deleteDocumentChunks function
        const { deleteDocumentChunks } = await import('./services/api');
        
        for (const doc of sessionToDelete.documents) {
          await deleteDocumentChunks(doc.document_id);
        }
      } catch (error) {
        console.error('Error deleting document chunks:', error);
      }
    }
    
    // Remove session from state
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    
    // If deleted current session, switch to another
    if (sessionId === currentSessionId) {
      const remaining = sessions.filter(s => s.id !== sessionId);
      if (remaining.length > 0) {
        setCurrentSessionId(remaining[0].id);
      } else {
        createNewSession();
      }
    }
  };

  const currentSession = sessions.find(s => s.id === currentSessionId);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSelect={setCurrentSessionId}
        onNewSession={createNewSession}
        onDeleteSession={deleteSession}
        currentSessionDocuments={currentSession?.documents || []}
        health={health}
      />

      {/* Main Chat Area */}
      <div className="main-content">
        {currentSession && (
          <ChatInterface
            key={currentSessionId} // Force re-render on session change
            sessionId={currentSession.id}
            sessionDocuments={currentSession.documents}
            initialMessages={currentSession.messages || []}
            initialChatHistory={currentSession.chatHistory || []}
            onDocumentAdded={(doc) => addDocumentToSession(currentSession.id, doc)}
            onMessagesUpdate={(msgs) => updateSessionMessages(currentSession.id, msgs)}
            onChatHistoryUpdate={(history) => updateSessionChatHistory(currentSession.id, history)}
            onTitleUpdate={(query) => updateSessionTitle(currentSession.id, query)}
          />
        )}
      </div>
    </div>
  );
}

export default App;