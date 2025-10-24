import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Zap, 
  MessageSquare, 
  FileText, 
  Info, 
  Settings,
  Menu,
  X
} from 'lucide-react';
import './Header.css';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { path: '/', label: 'Neural Core', icon: Zap },
    { path: '/chat', label: 'Interface', icon: MessageSquare },
    { path: '/docs', label: 'Archives', icon: FileText },
    { path: '/about', label: 'System Info', icon: Info },
    { path: '/admin', label: 'Control', icon: Settings }
  ];

  return (
    <motion.header 
      className={`cyber-header ${isScrolled ? 'scrolled' : ''}`}
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <div className="header-container">
        <Link to="/" className="logo-section">
          <div className="logo-icon">
            <Zap className="logo-zap" />
          </div>
          <div className="logo-text">
            <span className="logo-main">DOCET</span>
            <span className="logo-sub">Neural API Assistant</span>
          </div>
        </Link>

        <nav className={`cyber-nav ${isMenuOpen ? 'open' : ''}`}>
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link 
              key={path}
              to={path} 
              className={`nav-link ${location.pathname === path ? 'active' : ''}`}
              onClick={() => setIsMenuOpen(false)}
            >
              <Icon className="nav-icon" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>

        <button 
          className="menu-toggle"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
        >
          {isMenuOpen ? <X /> : <Menu />}
        </button>
      </div>
    </motion.header>
  );
};

export default Header;