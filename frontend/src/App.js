import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import Home from './pages/Home';
import Chat from './pages/Chat';
import ChatbotSelection from './pages/ChatbotSelection';
import Documentation from './pages/Documentation';
import About from './pages/About';
import Admin from './pages/Admin';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <div className="grid-background"></div>
        <Header />
        <main className="main-content">
          <AnimatePresence mode="wait">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/chat" element={<ChatbotSelection />} />
              <Route path="/chat/:chatbotId" element={<Chat />} />
              <Route path="/chatbots" element={<ChatbotSelection />} />
              <Route path="/docs" element={<Documentation />} />
              <Route path="/about" element={<About />} />
              <Route path="/admin" element={<Admin />} />
            </Routes>
          </AnimatePresence>
        </main>
      </div>
    </Router>
  );
}

export default App;