import React from 'react';
import { motion } from 'framer-motion';
import { 
  Zap, 
  Brain, 
  Database, 
  Cpu, 
  Shield, 
  Globe,
  GitBranch,
  Code,
  Users,
  Rocket,
  Target,
  Layers
} from 'lucide-react';
import './About.css';

const About = () => {
  const techSpecs = [
    {
      category: 'Neural Core',
      icon: Brain,
      specs: [
        'Google Gemini 2.5 Pro Integration',
        'Advanced RAG Processing Pipeline',
        'Function Calling Capabilities',
        'Multi-Session Context Management'
      ]
    },
    {
      category: 'Data Systems',
      icon: Database,
      specs: [
        'ChromaDB Vector Storage',
        'Sentence Transformer Embeddings',
        'Real-time Document Ingestion',
        'Version-Aware Processing'
      ]
    },
    {
      category: 'Processing Units',
      icon: Cpu,
      specs: [
        'FastAPI Backend Framework',
        'Async/Await Architecture',
        'Local Model Training Support',
        'GPU Acceleration Ready'
      ]
    },
    {
      category: 'Security Protocols',
      icon: Shield,
      specs: [
        'JWT Authentication',
        'Environment Variable Protection',
        'Rate Limiting',
        'Input Validation & Sanitization'
      ]
    }
  ];

  const features = [
    {
      icon: Globe,
      title: 'Multi-Protocol Support',
      description: 'Seamlessly ingests documentation from OpenAPI/Swagger, Markdown, HTML, and custom formats with intelligent parsing algorithms.'
    },
    {
      icon: GitBranch,
      title: 'Version Intelligence',
      description: 'Automatically detects and manages multiple API versions, ensuring responses are contextually accurate for each version.'
    },
    {
      icon: Code,
      title: 'Developer-First Design',
      description: 'Built by developers for developers with comprehensive APIs, extensive documentation, and modular architecture.'
    },
    {
      icon: Users,
      title: 'Team Collaboration',
      description: 'Multi-chatbot support allows different teams to maintain separate knowledge bases while sharing the same infrastructure.'
    }
  ];

  const architecture = [
    {
      layer: 'Interface Layer',
      components: ['React Frontend', 'Cyberpunk UI', 'Real-time Chat']
    },
    {
      layer: 'API Gateway',
      components: ['FastAPI Routes', 'Authentication', 'Rate Limiting']
    },
    {
      layer: 'Processing Core',
      components: ['RAG Pipeline', 'Document Parser', 'Vector Search']
    },
    {
      layer: 'AI Services',
      components: ['Gemini Integration', 'Local Models', 'Function Tools']
    },
    {
      layer: 'Data Storage',
      components: ['ChromaDB', 'Local Storage', 'Session Management']
    }
  ];

  return (
    <motion.div 
      className="about-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <section className="hero-about">
        <div className="about-hero-content">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h1 className="about-title">
              DOCET <span className="glow-text">NEURAL</span>
              <br />
              <span className="subtitle">System Architecture</span>
            </h1>
            <p className="about-description">
              Advanced artificial intelligence system engineered for real-time API documentation 
              analysis and intelligent developer assistance. Built with cutting-edge neural 
              processing capabilities and cybernetic interface protocols.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="mission-section">
        <div className="section-container">
          <motion.div
            className="mission-content cyber-card"
            initial={{ scale: 0.9, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="mission-header">
              <Target className="mission-icon" />
              <h2>Mission Protocol</h2>
            </div>
            <p className="mission-text">
              To eliminate the friction between developers and API documentation by creating 
              an intelligent, self-updating assistant that understands context, maintains 
              accuracy, and provides instant, relevant responses. DOCET represents the 
              evolution of technical support into the neural age.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="specs-section">
        <div className="section-container">
          <motion.h2 
            className="section-title"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Technical <span className="glow-text">Specifications</span>
          </motion.h2>
          
          <div className="specs-grid">
            {techSpecs.map((spec, index) => (
              <motion.div 
                key={index}
                className="spec-card cyber-card"
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                whileHover={{ y: -5, scale: 1.02 }}
              >
                <div className="spec-header">
                  <spec.icon className="spec-icon" />
                  <h3 className="spec-title">{spec.category}</h3>
                </div>
                <ul className="spec-list">
                  {spec.specs.map((item, itemIndex) => (
                    <li key={itemIndex} className="spec-item">
                      <Zap className="bullet-icon" />
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="features-section">
        <div className="section-container">
          <motion.h2 
            className="section-title"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            Core <span className="glow-text">Capabilities</span>
          </motion.h2>
          
          <div className="features-list">
            {features.map((feature, index) => (
              <motion.div 
                key={index}
                className="feature-item cyber-card"
                initial={{ x: index % 2 === 0 ? -50 : 50, opacity: 0 }}
                whileInView={{ x: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.2, duration: 0.8 }}
              >
                <div className="feature-icon-wrapper">
                  <feature.icon className="feature-icon" />
                </div>
                <div className="feature-content">
                  <h3 className="feature-title">{feature.title}</h3>
                  <p className="feature-description">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="architecture-section">
        <div className="section-container">
          <motion.h2 
            className="section-title"
            initial={{ y: 30, opacity: 0 }}
            whileInView={{ y: 0, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            System <span className="glow-text">Architecture</span>
          </motion.h2>
          
          <div className="architecture-diagram">
            {architecture.map((layer, index) => (
              <motion.div 
                key={index}
                className="architecture-layer cyber-card"
                initial={{ scale: 0.8, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.6 }}
              >
                <div className="layer-header">
                  <Layers className="layer-icon" />
                  <h3 className="layer-title">{layer.layer}</h3>
                </div>
                <div className="layer-components">
                  {layer.components.map((component, compIndex) => (
                    <span key={compIndex} className="component-tag">
                      {component}
                    </span>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="cta-about">
        <div className="section-container">
          <motion.div 
            className="cta-content cyber-card neon-border"
            initial={{ scale: 0.9, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <Rocket className="cta-icon" />
            <h2 className="cta-title">
              Ready to Deploy <span className="glow-text">Neural Interface</span>?
            </h2>
            <p className="cta-description">
              Initialize DOCET in your development environment and experience 
              the future of API documentation assistance.
            </p>
            <div className="cta-links">
              <a 
                href="https://github.com/sunnyshin8/Docet" 
                target="_blank" 
                rel="noopener noreferrer"
                className="cyber-button primary"
              >
                <Code className="button-icon" />
                Access Repository
              </a>
              <a 
                href="#" 
                className="cyber-button secondary"
                onClick={() => window.open('/docs', '_blank')}
              >
                <Zap className="button-icon" />
                System Documentation
              </a>
            </div>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
};

export default About;