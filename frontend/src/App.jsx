import { useState, useEffect, useRef } from 'react';
import ChatMessage from './components/ChatMessage';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Welcome to ChefRAG! 👨‍🍳 Upload recipe documents or just ask me anything about cooking. I can find recipes, adapt them to your dietary needs, provide nutritional info, and generate shopping lists!' }
  ]);
  const [documents, setDocuments] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [preferences, setPreferences] = useState({
    dietary_restrictions: '',
    cuisine_preference: '',
    available_ingredients: '',
    max_cooking_time: ''
  });

  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/documents`);
      const data = await res.json();
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    setUploadStatus('Uploading...');
    const formData = new FormData();
    formData.append('document', file);

    try {
      const res = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setUploadStatus(data.message || 'Upload successful');
      setFile(null);
      fetchDocuments();
    } catch (err) {
      console.error('Error uploading:', err);
      setUploadStatus('Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (sourceName) => {
    try {
      await fetch(`${API_BASE_URL}/documents/${encodeURIComponent(sourceName)}`, {
        method: 'DELETE',
      });
      fetchDocuments();
    } catch (err) {
      console.error('Error deleting doc:', err);
    }
  };

  const handleClearHistory = async () => {
    try {
      await fetch(`${API_BASE_URL}/clear-history?session_id=default`, { method: 'POST' });
      setMessages([
        { role: 'assistant', content: 'Welcome to ChefRAG! 👨‍🍳 Upload recipe documents or just ask me anything about cooking. I can find recipes, adapt them to your dietary needs, provide nutritional info, and generate shopping lists!' }
      ]);
    } catch (err) {
      console.error('Error clearing history:', err);
    }
  };

  const handleSend = async () => {
    if (!question.trim()) return;

    const userMsg = { role: 'user', content: question.trim() };
    setMessages(prev => [...prev, userMsg]);
    setQuestion('');
    setIsAsking(true);

    const activePrefs = Object.fromEntries(
      Object.entries(preferences).filter(([_, v]) => v.trim() !== '')
    );

    const payload = {
      question: userMsg.content,
      session_id: 'default',
    };
    
    if (Object.keys(activePrefs).length > 0) {
      payload.preferences = activePrefs;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      console.error('Error chatting:', err);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setIsAsking(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handlePrefChange = (e) => {
    const { name, value } = e.target;
    setPreferences(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="app-shell">
      <div className="sidebar">
        <div className="brand-section">
          <h1>ChefRAG 👨‍🍳</h1>
          <p>Your AI Recipe Assistant</p>
        </div>

        <div className="upload-panel">
          <div className="section-title">Upload Documents</div>
          <input 
            type="file" 
            accept=".pdf,.txt,.text" 
            onChange={e => setFile(e.target.files[0])}
          />
          <button className="btn-upload" onClick={handleUpload} disabled={!file || isUploading}>
            {isUploading ? 'Uploading...' : 'Upload'}
          </button>
          {uploadStatus && <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>{uploadStatus}</div>}
        </div>

        <div className="documents-panel">
          <div className="section-title">Indexed Documents</div>
          {documents.length === 0 ? (
            <div style={{ fontSize: '0.875rem', color: 'var(--muted)' }}>No documents found.</div>
          ) : (
            documents.map((doc, idx) => (
              <div key={idx} className="doc-item">
                <span>{doc}</span>
                <button className="btn-delete" onClick={() => handleDeleteDoc(doc)}>Delete</button>
              </div>
            ))
          )}
        </div>

        <div className="preferences-panel">
          <div className="section-title">Preferences</div>
          <div className="pref-field">
            <label>Dietary Restrictions</label>
            <input 
              name="dietary_restrictions" 
              placeholder="e.g. vegan, gluten-free"
              value={preferences.dietary_restrictions}
              onChange={handlePrefChange}
            />
          </div>
          <div className="pref-field">
            <label>Cuisine Preference</label>
            <input 
              name="cuisine_preference" 
              placeholder="e.g. Italian, Indian"
              value={preferences.cuisine_preference}
              onChange={handlePrefChange}
            />
          </div>
          <div className="pref-field">
            <label>Available Ingredients</label>
            <textarea 
              name="available_ingredients" 
              placeholder="e.g. chicken, rice, tomatoes"
              value={preferences.available_ingredients}
              onChange={handlePrefChange}
            />
          </div>
          <div className="pref-field">
            <label>Max Cooking Time</label>
            <input 
              name="max_cooking_time" 
              placeholder="e.g. 30 minutes"
              value={preferences.max_cooking_time}
              onChange={handlePrefChange}
            />
          </div>
        </div>

        <div className="quick-actions-section">
          <div className="section-title">Quick Actions</div>
          <div className="quick-actions">
            <button className="quick-btn" onClick={() => setQuestion('Find me a recipe for ')}>
              🔍 Find a Recipe
            </button>
            <button className="quick-btn" onClick={() => setQuestion('How can I make a [dietary] version of ')}>
              🔄 Adapt Recipe
            </button>
            <button className="quick-btn" onClick={() => setQuestion('What is the nutritional information for ')}>
              📊 Nutrition Info
            </button>
            <button className="quick-btn" onClick={() => setQuestion('Generate a shopping list for ')}>
              🛒 Shopping List
            </button>
          </div>
        </div>
      </div>

      <div className="chat-layout">
        <div className="chat-topbar">
          <h2>ChefRAG Chat</h2>
          <button className="btn-clear" onClick={handleClearHistory}>Clear History</button>
        </div>

        <div className="messages">
          {messages.map((msg, idx) => (
            <ChatMessage key={idx} role={msg.role} content={msg.content} />
          ))}
          {isAsking && (
            <div className="message-row assistant">
              <div className="message-bubble assistant">
                <div className="role-label">ChefRAG</div>
                <div className="markdown-body">Thinking...</div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="composer">
          <textarea 
            placeholder="Ask for a recipe or cooking advice..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="btn-send" onClick={handleSend} disabled={isAsking || !question.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
