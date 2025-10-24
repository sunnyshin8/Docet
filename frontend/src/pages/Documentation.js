import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  FileText, 
  Code, 
  Zap, 
  Database, 
  Settings, 
  Play, 
  Copy, 
  Check,
  ExternalLink,
  BookOpen,
  Terminal,
  Cpu,
  Lock
} from 'lucide-react';
import './Documentation.css';

const Documentation = () => {
  const [activeTab, setActiveTab] = useState('endpoints');
  const [copiedCode, setCopiedCode] = useState('');

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(''), 2000);
  };

  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/chat/message',
      description: 'Send a message to the neural assistant and receive an intelligent response',
      parameters: [
        { name: 'message', type: 'string', required: true, description: 'User query or request' },
        { name: 'session_id', type: 'string', required: false, description: 'Session identifier for context' },
        { name: 'context', type: 'object', required: false, description: 'Additional context data' }
      ],
      example: {
        request: `{
  "message": "How do I authenticate with this API?",
  "session_id": "user-123",
  "context": {
    "current_page": "/docs",
    "user_level": "developer"
  }
}`,
        response: `{
  "response": "To authenticate with this API, use JWT tokens...",
  "session_id": "user-123",
  "timestamp": "2024-01-15T10:30:00Z",
  "context_used": true
}`
      }
    },
    {
      method: 'POST',
      path: '/api/v1/ingest',
      description: 'Ingest new documentation into the neural knowledge base',
      parameters: [
        { name: 'source_url', type: 'string', required: true, description: 'URL of documentation source' },
        { name: 'type', type: 'string', required: true, description: 'Document type (swagger, markdown, html)' },
        { name: 'version', type: 'string', required: false, description: 'API version identifier' }
      ],
      example: {
        request: `{
  "source_url": "https://api.example.com/swagger.json",
  "type": "swagger",
  "version": "v2.1"
}`,
        response: `{
  "status": "success",
  "documents_processed": 45,
  "chunks_created": 180,
  "processing_time": "12.3s"
}`
      }
    },
    {
      method: 'GET',
      path: '/api/v1/status',
      description: 'Get system status and neural core diagnostics',
      parameters: [],
      example: {
        request: `GET /api/v1/status`,
        response: `{
  "status": "operational",
  "neural_core": "online",
  "vector_db": "connected",
  "documents_indexed": 1247,
  "uptime": "72h 15m 33s"
}`
      }
    },
    {
      method: 'GET',
      path: '/api/v1/sessions',
      description: 'List active chat sessions',
      parameters: [
        { name: 'limit', type: 'integer', required: false, description: 'Maximum number of sessions to return' },
        { name: 'active_only', type: 'boolean', required: false, description: 'Only return active sessions' }
      ],
      example: {
        request: `GET /api/v1/sessions?limit=10&active_only=true`,
        response: `{
  "sessions": [
    {
      "session_id": "user-123",
      "created_at": "2024-01-15T09:00:00Z",
      "last_activity": "2024-01-15T10:30:00Z",
      "message_count": 15
    }
  ],
  "total": 1
}`
      }
    }
  ];

  const quickStart = [
    {
      step: 1,
      title: 'Installation',
      icon: Terminal,
      content: `# Clone the repository
git clone https://github.com/sunnyshin8/Docet.git
cd Docet

# Setup backend environment
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys`
    },
    {
      step: 2,
      title: 'Configuration',
      icon: Settings,
      content: `# configuration.json
{
  "gemini": {
    "api_key": "your-gemini-api-key",
    "model": "gemini-2.0-flash-exp"
  },
  "chroma": {
    "persist_directory": "./data/chromadb"
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000
  }
}`
    },
    {
      step: 3,
      title: 'Launch System',
      icon: Cpu,
      content: `# Start the neural core
python -m app.main

# In another terminal, start frontend
cd ../frontend
npm install
npm start

# System ready at http://localhost:3000`
    }
  ];

  const tabs = [
    { id: 'endpoints', label: 'API Endpoints', icon: Zap },
    { id: 'quickstart', label: 'Quick Start', icon: Play },
    { id: 'authentication', label: 'Authentication', icon: Lock },
    { id: 'examples', label: 'Code Examples', icon: Code }
  ];

  return (
    <motion.div 
      className="docs-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <section className="docs-hero">
        <div className="docs-hero-content">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h1 className="docs-title">
              NEURAL <span className="glow-text">DOCUMENTATION</span>
              <br />
              <span className="subtitle">System Interface Protocols</span>
            </h1>
            <p className="docs-description">
              Comprehensive guide to interfacing with the DOCET neural system. 
              Access real-time API documentation, integration examples, and 
              advanced configuration protocols.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="docs-nav-section">
        <div className="section-container">
          <motion.div 
            className="docs-nav"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.6 }}
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <tab.icon className="tab-icon" />
                {tab.label}
              </button>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="docs-content">
        <div className="section-container">
          {activeTab === 'endpoints' && (
            <motion.div
              key="endpoints"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="content-title">API <span className="glow-text">Endpoints</span></h2>
              <div className="endpoints-grid">
                {endpoints.map((endpoint, index) => (
                  <motion.div 
                    key={index}
                    className="endpoint-card cyber-card"
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1, duration: 0.5 }}
                  >
                    <div className="endpoint-header">
                      <span className={`method-badge ${endpoint.method.toLowerCase()}`}>
                        {endpoint.method}
                      </span>
                      <code className="endpoint-path">{endpoint.path}</code>
                    </div>
                    
                    <p className="endpoint-description">{endpoint.description}</p>
                    
                    {endpoint.parameters.length > 0 && (
                      <div className="parameters-section">
                        <h4 className="section-subtitle">Parameters</h4>
                        <div className="parameters-list">
                          {endpoint.parameters.map((param, paramIndex) => (
                            <div key={paramIndex} className="parameter-item">
                              <code className="param-name">{param.name}</code>
                              <span className={`param-type ${param.required ? 'required' : 'optional'}`}>
                                {param.type} {param.required && '*'}
                              </span>
                              <p className="param-description">{param.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="example-section">
                      <h4 className="section-subtitle">Example</h4>
                      <div className="code-tabs">
                        <div className="code-tab active">Request</div>
                        <div className="code-tab">Response</div>
                      </div>
                      <div className="code-block">
                        <button 
                          className="copy-button"
                          onClick={() => copyToClipboard(endpoint.example.request, `req-${index}`)}
                        >
                          {copiedCode === `req-${index}` ? <Check /> : <Copy />}
                        </button>
                        <pre><code>{endpoint.example.request}</code></pre>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'quickstart' && (
            <motion.div
              key="quickstart"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="content-title">Quick <span className="glow-text">Start</span></h2>
              <div className="quickstart-steps">
                {quickStart.map((step, index) => (
                  <motion.div 
                    key={index}
                    className="step-card cyber-card"
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.2, duration: 0.6 }}
                  >
                    <div className="step-header">
                      <div className="step-number">{step.step}</div>
                      <step.icon className="step-icon" />
                      <h3 className="step-title">{step.title}</h3>
                    </div>
                    <div className="code-block">
                      <button 
                        className="copy-button"
                        onClick={() => copyToClipboard(step.content, `step-${index}`)}
                      >
                        {copiedCode === `step-${index}` ? <Check /> : <Copy />}
                      </button>
                      <pre><code>{step.content}</code></pre>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'authentication' && (
            <motion.div
              key="authentication"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="content-title">Authentication <span className="glow-text">Protocols</span></h2>
              <div className="auth-content">
                <div className="auth-card cyber-card">
                  <Lock className="auth-icon" />
                  <h3>Security Implementation</h3>
                  <p>DOCET uses JWT-based authentication for secure API access. All requests must include proper authorization headers.</p>
                  
                  <div className="code-section">
                    <h4>Header Format</h4>
                    <div className="code-block">
                      <button 
                        className="copy-button"
                        onClick={() => copyToClipboard('Authorization: Bearer <your-jwt-token>', 'auth-header')}
                      >
                        {copiedCode === 'auth-header' ? <Check /> : <Copy />}
                      </button>
                      <pre><code>Authorization: Bearer &lt;your-jwt-token&gt;</code></pre>
                    </div>
                  </div>

                  <div className="code-section">
                    <h4>Token Generation</h4>
                    <div className="code-block">
                      <pre><code>{`# Generate authentication token
curl -X POST http://localhost:8000/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"username": "your-username", "password": "your-password"}'`}</code></pre>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'examples' && (
            <motion.div
              key="examples"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="content-title">Code <span className="glow-text">Examples</span></h2>
              <div className="examples-grid">
                <div className="example-card cyber-card">
                  <h3>Python Integration</h3>
                  <div className="code-block">
                    <pre><code>{`import requests
import json

# Initialize DOCET client
class DocetClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def chat(self, message, session_id=None):
        payload = {
            "message": message,
            "session_id": session_id
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/chat/message",
            json=payload
        )
        return response.json()

# Usage
client = DocetClient()
response = client.chat("How do I use this API?")`}</code></pre>
                  </div>
                </div>

                <div className="example-card cyber-card">
                  <h3>JavaScript/React</h3>
                  <div className="code-block">
                    <pre><code>{`// DOCET API service
class DocetService {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }

    async sendMessage(message, sessionId) {
        const response = await fetch(\`\${this.baseURL}/api/v1/chat/message\`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message,
                session_id: sessionId
            })
        });
        return response.json();
    }
}

// Usage in React component
const docet = new DocetService();
const response = await docet.sendMessage("Hello DOCET!");`}</code></pre>
                  </div>
                </div>

                <div className="example-card cyber-card">
                  <h3>cURL Commands</h3>
                  <div className="code-block">
                    <pre><code>{`# Send chat message
curl -X POST http://localhost:8000/api/v1/chat/message \\
  -H "Content-Type: application/json" \\
  -d '{
    "message": "Explain the neural architecture",
    "session_id": "demo-session"
  }'

# Ingest documentation
curl -X POST http://localhost:8000/api/v1/ingest \\
  -H "Content-Type: application/json" \\
  -d '{
    "source_url": "https://api.example.com/docs",
    "type": "swagger",
    "version": "v2.0"
  }'`}</code></pre>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </section>

      <section className="docs-cta">
        <div className="section-container">
          <motion.div 
            className="cta-content cyber-card neon-border"
            initial={{ scale: 0.9, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <BookOpen className="cta-icon" />
            <h2 className="cta-title">
              Ready to <span className="glow-text">Interface</span>?
            </h2>
            <p className="cta-description">
              Deploy DOCET in your environment and start experiencing 
              intelligent API documentation assistance.
            </p>
            <div className="cta-buttons">
              <a 
                href="https://github.com/sunnyshin8/Docet" 
                target="_blank" 
                rel="noopener noreferrer"
                className="cyber-button primary"
              >
                <ExternalLink className="button-icon" />
                View Source Code
              </a>
              <button 
                className="cyber-button secondary"
                onClick={() => setActiveTab('quickstart')}
              >
                <Play className="button-icon" />
                Start Integration
              </button>
            </div>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
};

export default Documentation;