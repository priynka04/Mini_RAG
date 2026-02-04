/**
 * API service for communicating with the backend.
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Upload a document file
 */
export const uploadDocument = async (file, title = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (title) {
    formData.append('title', title);
  }

  const response = await api.post('/api/documents/upload', formData);

  return response.data;
};

/**
 * Process pasted text
 */
export const processText = async (text, title = 'Pasted Text') => {
  const response = await api.post('/api/documents/text', {
    text,
    title,
  });

  return response.data;
};

/**
 * Get document statistics
 */
export const getStats = async () => {
  const response = await api.get('/api/documents/stats');
  return response.data;
};

/**
 * Send a query to the RAG system
 */
export const sendQuery = async (query, chatHistory = [], sessionId = null) => {
  const response = await api.post('/api/chat/query', {
    query,
    chat_history: chatHistory,
    session_id: sessionId,
  });

  return response.data;
};

/**
 * Delete document chunks from vector store
 */
export const deleteDocumentChunks = async (documentId) => {
  const response = await api.delete(`/api/documents/${documentId}`);
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
