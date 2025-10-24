import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Zap, 
  MessageSquare, 
  Database, 
  Cpu, 
  Shield, 
  Globe,
  ArrowRight,
  Play
} from 'lucide-react';
import './Home.css';

const Home = () => {
  const [currentText, setCurrentText] = useState('');
  const [textIndex, setTextIndex] = useState(0);
  
  const heroTexts = [
    'Neural API Assistant',
    'Smart Documentation Engine',
    'Cybernetic Support System'
  ];

  useEffect(() => {
    const text = heroTexts[textIndex];
    let currentIndex = 0;
    
    const typeInterval = setInterval(() => {
      if (currentIndex <= text.length) {
        setCurrentText(text.slice(0, currentIndex));
        currentIndex++;
      } else {
        clearInterval(typeInterval);
        setTimeout(() => {
          setTextIndex((prev) => (prev + 1) % heroTexts.length);
        }, 2000);
      }
    }, 100);

    return () => clearInterval(typeInterval);
  }, [textIndex]);

  const features = [
    {
      icon: Database,
      title: 'Auto-Ingestion',
      description: 'Seamlessly absorb documentation from multiple sources with neural precision',
      color: 'var(--cyber-green)'
    },
    {
      icon: Cpu,
      title: 'RAG Processing',
      description: 'Advanced retrieval-augmented generation for contextual intelligence',
      color: 'var(--cyber-blue)'
    },
    {
      icon: Shield,
      title: 'Secure Interface',
      description: 'Military-grade security protocols protect your data streams',
      color: 'var(--cyber-purple)'
    },
    {
      icon: Globe,
      title: 'Multi-Protocol',
      description: 'Support for OpenAPI, Swagger, Markdown, and legacy formats',
      color: 'var(--cyber-orange)'
    }
  ];

  return (
    <motion.div 
      className="home-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <section className="hero-section">
        <div className="hero-content">
          <motion.div 
            className="hero-text"
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h1 className="hero-title">
              DOCET
              <span className="title-glow">NEURAL</span>
            </h1>
            <div className="hero-subtitle">
              <span className="typing-text">{currentText}</span>
              <span className="cursor">|</span>
            </div>
            <p className="hero-description">
              Advanced artificial intelligence system designed for real-time API documentation 
              analysis and intelligent developer assistance. Interface with the future of 
              technical support through neural-enhanced conversation protocols.
            </p>
            <div className="hero-actions">
              <Link to="/chat" className="cyber-button primary pulse">
                <Play className="button-icon" />
                Initialize Interface
                <ArrowRight className="button-arrow" />
              </Link>
              <Link to="/about" className="cyber-button secondary">
                <Zap className="button-icon" />
                System Specs
              </Link>
            </div>
          </motion.div>
          
          <motion.div 
            className="hero-visual"
            initial={{ x: 100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.4, duration: 0.8 }}
          >
            <div className="neural-network">
              <div className="network-node central">
                <Zap className="node-icon" />
              </div>
              <div className="network-node node-1">
                <Database className="node-icon" />
              </div>
              <div className="network-node node-2">
                <MessageSquare className="node-icon" />
              </div>
              <div className="network-node node-3">
                <Cpu className="node-icon" />
              </div>
              <div className="network-connection conn-1"></div>
              <div className="network-connection conn-2"></div>
              <div className="network-connection conn-3"></div>
            </div>
          </motion.div>
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
            Core <span className="glow-text">Systems</span>
          </motion.h2>
          
          <div className="features-grid">
            {features.map((feature, index) => (
              <motion.div 
                key={index}
                className="feature-card cyber-card"
                initial={{ y: 50, opacity: 0 }}
                whileInView={{ y: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.6 }}
                whileHover={{ y: -10, scale: 1.02 }}
              >
                <div className="feature-icon" style={{ color: feature.color }}>
                  <feature.icon />
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="cta-section">
        <div className="section-container">
          <motion.div 
            className="cta-content cyber-card neon-border"
            initial={{ scale: 0.9, opacity: 0 }}
            whileInView={{ scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="cta-title">
              Ready to <span className="glow-text">Interface</span>?
            </h2>
            <p className="cta-description">
              Connect to the neural network and experience the future of API documentation assistance.
            </p>
            <Link to="/chat" className="cyber-button primary large">
              <MessageSquare className="button-icon" />
              Start Neural Session
            </Link>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
};

export default Home;