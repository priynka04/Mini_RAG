/**
 * Document upload component - supports file upload and text paste
 */
import React, { useState, useEffect } from "react";
import { uploadDocument, processText } from '../services/api';

export default function DocumentUpload({ onUploadSuccess }) {
  const [activeTab, setActiveTab] = useState('paste'); // 'paste' or 'upload'
  const [text, setText] = useState('');
  const [title, setTitle] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter some text');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await processText(text, title || 'Pasted Text');
      setSuccess(`✓ Processed! Created ${result.chunks_created} chunks with ${result.links_extracted} links`);
      setText('');
      setTitle('');
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error processing text');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSubmit = async (e) => {
    e.preventDefault();

    if (!file) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await uploadDocument(file, title);
      setSuccess(`✓ Uploaded! Created ${result.chunks_created} chunks with ${result.links_extracted} links`);
      setFile(null);
      setTitle('');
      
      // Reset file input
      const fileInput = document.getElementById('file-input');
      if (fileInput) fileInput.value = '';
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2>📄 Upload Documents</h2>

      {/* Tab Selector */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'paste' ? 'active' : ''}`}
          onClick={() => setActiveTab('paste')}
        >
          Paste Text
        </button>
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload File
        </button>
      </div>

      {/* Messages */}
      {error && <div className="message error">{error}</div>}
      {success && <div className="message success">{success}</div>}

      {/* Paste Text Tab */}
      {activeTab === 'paste' && (
        <form onSubmit={handleTextSubmit} className="upload-form">
          <input
            type="text"
            placeholder="Document title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
          />
          <textarea
            placeholder="Paste your text here... (supports markdown, links, etc.)"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={10}
            className="textarea"
          />
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Processing...' : 'Process Text'}
          </button>
        </form>
      )}

      {/* Upload File Tab */}
      {activeTab === 'upload' && (
        <form onSubmit={handleFileSubmit} className="upload-form">
          <input
            type="text"
            placeholder="Document title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
          />
          <div className="file-input-wrapper">
            <input
              id="file-input"
              type="file"
              accept=".pdf,.txt,.md"
              onChange={(e) => setFile(e.target.files[0])}
              className="file-input"
            />
            <label htmlFor="file-input" className="file-label">
              {file ? file.name : 'Choose file (PDF, TXT, MD)'}
            </label>
          </div>
          <button type="submit" disabled={loading || !file} className="btn btn-primary">
            {loading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>
      )}
    </div>
  );
}