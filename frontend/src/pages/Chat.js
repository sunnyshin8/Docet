import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Send, 
  Bot, 
  User, 
  Loader,
  Zap,
  MessageSquare,
  Settings,
  RefreshCw,
  ArrowLeft,
  AlertCircle
} from 'lucide-react';
import './Chat.css';

// Function to format message content with basic markdown-like formatting
const formatMessageContent = (content) => {
  if (!content) return '';
  
  // Split content by lines to preserve structure
  const lines = content.split('\n');
  
  return lines.map((line, lineIndex) => {
    // Handle different types of formatting
    let formattedLine = line;
    
    // Bold text with **text**
    formattedLine = formattedLine.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Inline code with `code`
    formattedLine = formattedLine.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Handle special patterns
    if (line.trim() === '') {
      // Empty lines for spacing
      return <div key={lineIndex} className="message-line empty-line"></div>;
    } else if (line.trim().startsWith('**') && line.trim().endsWith('**') && line.includes(':')) {
      // Headers like **Operation ID:** or **Example using curl:**
      return (
        <div key={lineIndex} className="message-line header-line">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    } else if (line.includes('curl') || line.includes('POST') || line.includes('GET') || line.includes('```')) {
      // Code examples and API calls
      return (
        <div key={lineIndex} className="message-line code-line">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    } else if (line.trim().startsWith('/') && (line.includes('endpoint') || line.includes('API'))) {
      // API endpoints
      return (
        <div key={lineIndex} className="message-line endpoint-line">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    } else if (formattedLine.includes('<strong>')) {
      // Lines with bold formatting
      return (
        <div key={lineIndex} className="message-line emphasis-line">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    } else {
      // Regular text
      return (
        <div key={lineIndex} className="message-line">
          <span dangerouslySetInnerHTML={{ __html: formattedLine }} />
        </div>
      );
    }
  });
};

const Chat = () => {
  const { chatbotId } = useParams();
  const navigate = useNavigate();
  
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: `Neural interface established. I am DOCET, your AI documentation assistant for "${chatbotId}". How may I assist you with your API queries today?`,
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatbotError, setChatbotError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Validate chatbot exists or redirect if no chatbot ID
    if (!chatbotId) {
      navigate('/chatbots');
      return;
    }
    
    // Optionally verify the chatbot exists
    validateChatbot();
  }, [chatbotId, navigate]);

  const validateChatbot = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/ingestion/chatbots');
      if (response.ok) {
        const data = await response.json();
        const chatbotExists = data.chatbots?.some(bot => bot.chatbot_id === chatbotId);
        if (!chatbotExists) {
          setChatbotError(`Chatbot "${chatbotId}" not found`);
        }
      }
    } catch (error) {
      console.error('Error validating chatbot:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading || !chatbotId) return;

    const userMessage = {
      id: messages.length + 1,
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          chatbot_id: chatbotId,
          session_id: `session-${Date.now()}`
        })
      });

      const data = await response.json();
      
      const assistantMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: data.message || 'Neural pathways temporarily disrupted. Please retry your query.',
        timestamp: new Date(),
        sources: data.sources || []
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Communication error:', error);
      
      const errorMessage = {
        id: messages.length + 2,
        role: 'assistant',
        content: 'System malfunction detected. Neural network temporarily offline. Please check your connection and try again.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        role: 'assistant',
        content: 'Neural interface reset. Memory banks cleared. Ready for new session.',
        timestamp: new Date()
      }
    ]);
  };

  // Show error state if chatbot not found
  if (chatbotError) {
    return (
      <motion.div 
        className="chat-container"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="error-state">
          <AlertCircle className="error-icon" />
          <h2>Chatbot Not Found</h2>
          <p>{chatbotError}</p>
          <button 
            onClick={() => navigate('/chatbots')} 
            className="cyber-button primary"
          >
            <ArrowLeft className="button-icon" />
            Back to Assistants
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div 
      className="chat-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="chat-header cyber-card">
        <div className="chat-info">
          <div className="chat-title">
            <button 
              onClick={() => navigate('/chatbots')} 
              className="back-button"
              title="Back to Assistants"
            >
              <ArrowLeft className="back-icon" />
            </button>
            <MessageSquare className="title-icon" />
            <div className="title-text">
              <h2>Neural Interface</h2>
              <span className="chatbot-name">{chatbotId}</span>
            </div>
          </div>
          <div className="chat-status">
            <div className="status-indicator online"></div>
            <span>System Online - {messages.length - 1} Transmissions</span>
          </div>
        </div>
        
        <div className="chat-controls">
          <button 
            className="control-button" 
            onClick={clearChat}
            title="Reset Interface"
          >
            <RefreshCw size={16} />
          </button>
          <button 
            className="control-button" 
            title="Interface Settings"
          >
            <Settings size={16} />
          </button>
        </div>
      </div>

      <div className="chat-messages scrollbar-cyber">
        <AnimatePresence>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              className={`message ${message.role}`}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="message-avatar">
                {message.role === 'user' ? (
                  <User className="avatar-icon" />
                ) : (
                  <Bot className="avatar-icon" />
                )}
              </div>
              
              <div className="message-content">
                <div className="message-header">
                  <span className="message-sender">
                    {message.role === 'user' ? 'USER' : 'DOCET'}
                  </span>
                  <span className="message-time">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                
                <div className="message-text">
                  {formatMessageContent(message.content)}
                </div>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="message-sources">
                    <div className="sources-header">
                      <Zap size={14} />
                      <span>Neural Sources</span>
                    </div>
                    {message.sources.slice(0, 3).map((source, index) => (
                      <div key={index} className="source-item">
                        <span className="source-title">
                          {source.metadata?.document_title || 'Unknown Source'}
                        </span>
                        <span className="source-confidence">
                          {Math.round(source.score * 100)}% match
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isLoading && (
          <motion.div
            className="message assistant loading"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="message-avatar">
              <Bot className="avatar-icon" />
            </div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-sender">DOCET</span>
                <span className="message-time">Processing...</span>
              </div>
              <div className="message-text">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>Neural pathways activating...</span>
              </div>
            </div>
          </motion.div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container cyber-card">
        <div className="input-wrapper">
          <textarea
            className="chat-input cyber-input"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Transmit your query to the neural network..."
            rows={1}
            disabled={isLoading}
          />
          <button
            className={`send-button ${inputMessage.trim() && !isLoading ? 'active' : ''}`}
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
          >
            {isLoading ? (
              <Loader className="button-icon spinning" />
            ) : (
              <Send className="button-icon" />
            )}
          </button>
        </div>
        
        <div className="input-info">
          <span className="input-hint">
            Press Enter to transmit • Shift+Enter for new line
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default Chat;