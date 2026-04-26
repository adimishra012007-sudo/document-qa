import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Upload, Send, FileText, Loader2, CheckCircle2 } from 'lucide-react';
import './App.css';

const API_BASE = 'http://localhost:8000/api/v1/documents';

function App() {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(localStorage.getItem('lastDocId') || null);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isQuerying, setIsQuerying] = useState(false);
  const messageEndRef = useRef(null);

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE}/upload`, formData);
      setDocumentId(response.data.document_id);
      localStorage.setItem('lastDocId', response.data.document_id);
      setMessages([{ 
        role: 'bot', 
        content: 'Document processed successfully! You can now ask questions about it.' 
      }]);
    } catch (error) {
      console.error('Upload failed', error);
      alert('Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !documentId || isQuerying) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsQuerying(true);

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        query: input,
        document_id: documentId
      });

      const botMessage = { 
        role: 'bot', 
        content: response.data.answer,
        sources: response.data.sources 
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Query failed', error);
      setMessages(prev => [...prev, { role: 'bot', content: 'Sorry, I encountered an error processing your question.' }]);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="container">
      <header>
        <h1>DocuMind AI</h1>
        <p className="subtitle">Upload PDFs and get instant, grounded answers</p>
      </header>

      <div className="upload-section">
        <div className="file-input-wrapper">
          <Upload size={20} className="text-muted" style={{ marginRight: '10px' }} />
          <span>{file ? file.name : "Select a PDF document"}</span>
          <input 
            type="file" 
            accept=".pdf" 
            onChange={(e) => setFile(e.target.files[0])}
          />
        </div>
        <button 
          className="btn" 
          onClick={handleUpload} 
          disabled={!file || isUploading}
        >
          {isUploading ? <Loader2 className="animate-spin" /> : <CheckCircle2 />}
          {isUploading ? "Processing..." : "Index Document"}
        </button>

        {documentId && (
          <div className="status-indicator">
            <div className="dot"></div>
            Online
          </div>
        )}
      </div>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && !documentId && (
            <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--text-muted)' }}>
              <FileText size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <p>Upload a document to start the conversation</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="content">{msg.content}</div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="sources">
                  <strong>Sources:</strong>
                  <div>
                    {Array.from(new Set(msg.sources.map(s => s.page))).sort().map(page => (
                      <span key={page} className="source-tag">Page {page}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
          {isQuerying && (
            <div className="message bot">
              <Loader2 className="animate-spin" /> Thinking...
            </div>
          )}
          <div ref={messageEndRef} />
        </div>

        <div className="input-area">
          <input 
            type="text" 
            placeholder={documentId ? "Ask a question..." : "Upload a document first"}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            disabled={!documentId}
          />
          <button 
            className="btn" 
            onClick={handleSend} 
            disabled={!documentId || !input.trim() || isQuerying}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
