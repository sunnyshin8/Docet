import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Plus,
  MessageCircle,
  Database,
  Clock,
  FileText,
  AlertCircle,
  Loader2,
  ExternalLink,
  Bot,
  Zap,
  Settings
} from 'lucide-react';
import './ChatbotSelection.css';

const ChatbotSelection = () => {
  const [chatbots, setChatbots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalData, setModalData] = useState({ url: '', chatbot_id: '', loading: false, error: '' });
  const navigate = useNavigate();

  useEffect(() => {
    fetchChatbots();
  }, []);

  const fetchChatbots = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/ingestion/chatbots');
      if (!response.ok) throw new Error('Failed to fetch chatbots');
      const data = await response.json();
      setChatbots(data.chatbots || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChatbotClick = (chatbotId) => {
    navigate(`/chat/${chatbotId}`);
  };

  const handleCreateChatbot = async (e) => {
    e.preventDefault();
    
    if (!modalData.url || !modalData.chatbot_id) {
      setModalData(prev => ({ ...prev, error: 'Please fill in all fields' }));
      return;
    }

    setModalData(prev => ({ ...prev, loading: true, error: '' }));

    try {
      const response = await fetch('http://localhost:8000/api/v1/ingestion/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: modalData.url,
          chatbot_id: modalData.chatbot_id,
          force_reingestion: true
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to create chatbot');
      }

      if (result.status === 'success') {
        // Success! Close modal and navigate to chat
        setShowModal(false);
        setModalData({ url: '', chatbot_id: '', loading: false, error: '' });
        navigate(`/chat/${result.chatbot_id}`);
      } else {
        throw new Error(result.message || 'Ingestion failed');
      }
    } catch (err) {
      setModalData(prev => ({ 
        ...prev, 
        loading: false, 
        error: err.message || 'Failed to create chatbot'
      }));
    }
  };

  const generateChatbotId = () => {
    const timestamp = new Date().getTime();
    const randomStr = Math.random().toString(36).substring(2, 8);
    return `${timestamp}-${randomStr}`;
  };

  if (loading) {
    return (
      <div className="selection-container">
        <div className="loading-center">
          <Loader2 className="loading-spinner" />
          <p>Loading chatbots...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="selection-container">
        <div className="error-center">
          <AlertCircle className="error-icon" />
          <h2>Failed to Load Chatbots</h2>
          <p>{error}</p>
          <button onClick={fetchChatbots} className="cyber-button primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      className="selection-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <section className="selection-hero">
        <div className="selection-hero-content">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h1 className="selection-title">
              NEURAL <span className="glow-text">ASSISTANTS</span>
              <br />
              <span className="subtitle">Documentation Chatbots</span>
            </h1>
            <p className="selection-description">
              Select an existing documentation assistant or create a new one 
              by ingesting API documentation from any source.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="chatbots-section">
        <div className="section-container">
          <div className="section-header">
            <h2 className="section-title">
              Available <span className="glow-text">Assistants</span>
            </h2>
            <button 
              className="cyber-button primary"
              onClick={() => setShowModal(true)}
            >
              <Plus className="button-icon" />
              Create New Assistant
            </button>
          </div>

          {chatbots.length === 0 ? (
            <motion.div 
              className="empty-state cyber-card"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
            >
              <Bot className="empty-icon" />
              <h3>No Assistants Yet</h3>
              <p>Create your first documentation assistant by clicking the button above.</p>
            </motion.div>
          ) : (
            <div className="chatbots-grid">
              {chatbots.map((chatbot, index) => (
                <motion.div
                  key={chatbot.chatbot_id}
                  className="chatbot-card cyber-card"
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.6 }}
                  onClick={() => handleChatbotClick(chatbot.chatbot_id)}
                  whileHover={{ y: -5, scale: 1.02 }}
                >
                  <div className="card-header">
                    <MessageCircle className="chatbot-icon" />
                    <div className="card-title-area">
                      <h3 className="chatbot-title">{chatbot.chatbot_id}</h3>
                      <span className="chatbot-status">Active</span>
                    </div>
                  </div>
                  
                  <div className="card-content">
                    {chatbot.source_url && (
                      <div className="info-item">
                        <ExternalLink className="info-icon" />
                        <span className="info-text">{chatbot.source_url}</span>
                      </div>
                    )}
                    
                    <div className="stats-row">
                      <div className="stat-item">
                        <FileText className="stat-icon" />
                        <span>{chatbot.document_count || 0} docs</span>
                      </div>
                      <div className="stat-item">
                        <Database className="stat-icon" />
                        <span>{chatbot.chunk_count || 0} chunks</span>
                      </div>
                      <div className="stat-item">
                        <Clock className="stat-icon" />
                        <span>{chatbot.last_updated || 'Unknown'}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="card-footer">
                    <span className="chat-cta">Click to start chatting</span>
                    <Zap className="cta-icon" />
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Create Chatbot Modal */}
      {showModal && (
        <motion.div 
          className="modal-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => !modalData.loading && setShowModal(false)}
        >
          <motion.div 
            className="modal-content cyber-card"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>Create New Documentation Assistant</h3>
              <button 
                className="modal-close"
                onClick={() => !modalData.loading && setShowModal(false)}
                disabled={modalData.loading}
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleCreateChatbot} className="modal-form">
              <div className="form-group">
                <label htmlFor="url">Documentation URL</label>
                <input
                  type="url"
                  id="url"
                  value={modalData.url}
                  onChange={(e) => setModalData(prev => ({ ...prev, url: e.target.value }))}
                  placeholder="https://api.example.com/docs"
                  className="cyber-input"
                  disabled={modalData.loading}
                  required
                />
                <p className="form-hint">
                  Enter the URL of the API documentation (Swagger, OpenAPI, etc.)
                </p>
              </div>

              <div className="form-group">
                <label htmlFor="chatbot_id">Assistant ID</label>
                <div className="input-with-button">
                  <input
                    type="text"
                    id="chatbot_id"
                    value={modalData.chatbot_id}
                    onChange={(e) => setModalData(prev => ({ ...prev, chatbot_id: e.target.value }))}
                    placeholder="my-api-assistant"
                    className="cyber-input"
                    disabled={modalData.loading}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setModalData(prev => ({ ...prev, chatbot_id: generateChatbotId() }))}
                    className="generate-button"
                    disabled={modalData.loading}
                  >
                    <Settings className="generate-icon" />
                  </button>
                </div>
                <p className="form-hint">
                  Choose a unique identifier for your assistant
                </p>
              </div>

              {modalData.error && (
                <div className="error-message">
                  <AlertCircle className="error-icon" />
                  {modalData.error}
                </div>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="cyber-button secondary"
                  disabled={modalData.loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="cyber-button primary"
                  disabled={modalData.loading}
                >
                  {modalData.loading ? (
                    <>
                      <Loader2 className="loading-spinner" />
                      Creating Assistant...
                    </>
                  ) : (
                    <>
                      <Plus className="button-icon" />
                      Create Assistant
                    </>
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default ChatbotSelection;