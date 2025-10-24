import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Shield, 
  Cpu, 
  Database, 
  Activity, 
  Users, 
  Settings,
  Monitor,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  HardDrive,
  Network,
  Brain,
  Clock,
  BarChart3,
  FileText
} from 'lucide-react';
import './Admin.css';

const Admin = () => {
  const [systemStats, setSystemStats] = useState({
    status: 'operational',
    uptime: '72h 15m 33s',
    cpu_usage: 45,
    memory_usage: 62,
    neural_core: 'online',
    vector_db: 'connected',
    documents_indexed: 1247,
    active_sessions: 12,
    total_queries: 8943,
    response_time: '0.8s'
  });

  const [logs, setLogs] = useState([
    { id: 1, timestamp: '2024-01-15 10:30:15', level: 'INFO', message: 'Neural core initialized successfully', source: 'CORE' },
    { id: 2, timestamp: '2024-01-15 10:29:45', level: 'SUCCESS', message: 'Vector database connection established', source: 'DB' },
    { id: 3, timestamp: '2024-01-15 10:29:12', level: 'INFO', message: 'Document ingestion pipeline started', source: 'INGEST' },
    { id: 4, timestamp: '2024-01-15 10:28:58', level: 'WARNING', message: 'High memory usage detected (85%)', source: 'MONITOR' },
    { id: 5, timestamp: '2024-01-15 10:28:30', level: 'INFO', message: 'New chat session initiated: user-789', source: 'CHAT' }
  ]);

  const [activeConnections, setActiveConnections] = useState([
    { id: 'conn-1', user: 'dev-team-alpha', ip: '192.168.1.101', sessions: 3, last_active: '2m ago', status: 'active' },
    { id: 'conn-2', user: 'qa-automation', ip: '192.168.1.102', sessions: 1, last_active: '5m ago', status: 'active' },
    { id: 'conn-3', user: 'frontend-dev', ip: '192.168.1.103', sessions: 2, last_active: '1m ago', status: 'active' },
    { id: 'conn-4', user: 'api-tester', ip: '192.168.1.104', sessions: 1, last_active: '8m ago', status: 'idle' }
  ]);

  const refreshStats = () => {
    // Simulate real-time data updates
    setSystemStats(prev => ({
      ...prev,
      cpu_usage: Math.floor(Math.random() * 20) + 40,
      memory_usage: Math.floor(Math.random() * 30) + 50,
      active_sessions: Math.floor(Math.random() * 10) + 8,
      response_time: (Math.random() * 0.5 + 0.5).toFixed(1) + 's'
    }));
  };

  useEffect(() => {
    const interval = setInterval(refreshStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
      case 'online':
      case 'connected':
      case 'active':
        return 'var(--cyber-blue)';
      case 'warning':
      case 'idle':
        return '#ffff00';
      case 'error':
      case 'offline':
        return '#ff4500';
      default:
        return 'var(--text-secondary)';
    }
  };

  const getLogLevelIcon = (level) => {
    switch (level) {
      case 'SUCCESS':
        return <CheckCircle className="log-icon success" />;
      case 'WARNING':
        return <AlertTriangle className="log-icon warning" />;
      case 'ERROR':
        return <XCircle className="log-icon error" />;
      default:
        return <Activity className="log-icon info" />;
    }
  };

  return (
    <motion.div 
      className="admin-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <section className="admin-hero">
        <div className="admin-hero-content">
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.8 }}
          >
            <h1 className="admin-title">
              NEURAL <span className="glow-text">CONTROL</span>
              <br />
              <span className="subtitle">System Administration</span>
            </h1>
            <p className="admin-description">
              Advanced monitoring and control interface for DOCET neural systems. 
              Real-time diagnostics, performance metrics, and system management protocols.
            </p>
          </motion.div>
        </div>
      </section>

      <section className="admin-dashboard">
        <div className="section-container">
          {/* System Status Cards */}
          <div className="status-grid">
            <motion.div 
              className="status-card cyber-card"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.6 }}
            >
              <div className="card-header">
                <Cpu className="card-icon" style={{ color: getStatusColor(systemStats.neural_core) }} />
                <h3>Neural Core</h3>
                <span className={`status-badge ${systemStats.neural_core}`}>{systemStats.neural_core}</span>
              </div>
              <div className="metric-display">
                <div className="metric-item">
                  <span className="metric-label">CPU Usage</span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${systemStats.cpu_usage}%` }}
                    ></div>
                  </div>
                  <span className="metric-value">{systemStats.cpu_usage}%</span>
                </div>
              </div>
            </motion.div>

            <motion.div 
              className="status-card cyber-card"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <div className="card-header">
                <Database className="card-icon" style={{ color: getStatusColor(systemStats.vector_db) }} />
                <h3>Vector Database</h3>
                <span className={`status-badge ${systemStats.vector_db}`}>{systemStats.vector_db}</span>
              </div>
              <div className="metric-display">
                <div className="metric-item">
                  <span className="metric-label">Memory Usage</span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill memory" 
                      style={{ width: `${systemStats.memory_usage}%` }}
                    ></div>
                  </div>
                  <span className="metric-value">{systemStats.memory_usage}%</span>
                </div>
              </div>
            </motion.div>

            <motion.div 
              className="status-card cyber-card"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <div className="card-header">
                <Users className="card-icon" style={{ color: getStatusColor('active') }} />
                <h3>Active Sessions</h3>
                <span className="status-badge active">active</span>
              </div>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-number">{systemStats.active_sessions}</span>
                  <span className="stat-label">Current</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{systemStats.total_queries}</span>
                  <span className="stat-label">Total Queries</span>
                </div>
              </div>
            </motion.div>

            <motion.div 
              className="status-card cyber-card"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.6 }}
            >
              <div className="card-header">
                <Clock className="card-icon" style={{ color: getStatusColor('operational') }} />
                <h3>System Uptime</h3>
                <button className="refresh-btn" onClick={refreshStats}>
                  <RefreshCw className="refresh-icon" />
                </button>
              </div>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-number">{systemStats.uptime}</span>
                  <span className="stat-label">Uptime</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">{systemStats.response_time}</span>
                  <span className="stat-label">Avg Response</span>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Performance Metrics */}
          <motion.div 
            className="metrics-section"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
          >
            <h2 className="section-title">Performance <span className="glow-text">Metrics</span></h2>
            <div className="metrics-grid">
              <div className="metric-card cyber-card">
                <div className="metric-header">
                  <BarChart3 className="metric-icon" />
                  <h3>Processing Load</h3>
                </div>
                <div className="metric-chart">
                  <div className="chart-bars">
                    {[65, 45, 78, 92, 55, 73, 88, 42, 67, 85].map((value, index) => (
                      <div 
                        key={index}
                        className="chart-bar"
                        style={{ height: `${value}%` }}
                      ></div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="metric-card cyber-card">
                <div className="metric-header">
                  <FileText className="metric-icon" />
                  <h3>Document Processing</h3>
                </div>
                <div className="processing-stats">
                  <div className="processing-item">
                    <span className="processing-label">Documents Indexed</span>
                    <span className="processing-value">{systemStats.documents_indexed.toLocaleString()}</span>
                  </div>
                  <div className="processing-item">
                    <span className="processing-label">Chunks Created</span>
                    <span className="processing-value">4,988</span>
                  </div>
                  <div className="processing-item">
                    <span className="processing-label">Embeddings Generated</span>
                    <span className="processing-value">12,456</span>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Active Connections */}
          <motion.div 
            className="connections-section"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.6 }}
          >
            <h2 className="section-title">Active <span className="glow-text">Connections</span></h2>
            <div className="connections-table cyber-card">
              <div className="table-header">
                <div className="header-cell">User</div>
                <div className="header-cell">IP Address</div>
                <div className="header-cell">Sessions</div>
                <div className="header-cell">Last Active</div>
                <div className="header-cell">Status</div>
              </div>
              <div className="table-body">
                {activeConnections.map((connection) => (
                  <div key={connection.id} className="table-row">
                    <div className="table-cell">
                      <Users className="user-icon" />
                      {connection.user}
                    </div>
                    <div className="table-cell">
                      <Network className="ip-icon" />
                      {connection.ip}
                    </div>
                    <div className="table-cell">{connection.sessions}</div>
                    <div className="table-cell">{connection.last_active}</div>
                    <div className="table-cell">
                      <span 
                        className={`status-indicator ${connection.status}`}
                        style={{ color: getStatusColor(connection.status) }}
                      >
                        {connection.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* System Logs */}
          <motion.div 
            className="logs-section"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7, duration: 0.6 }}
          >
            <h2 className="section-title">System <span className="glow-text">Logs</span></h2>
            <div className="logs-container cyber-card">
              <div className="logs-header">
                <Monitor className="logs-icon" />
                <h3>Real-time Activity Monitor</h3>
                <div className="logs-controls">
                  <button className="log-filter active">All</button>
                  <button className="log-filter">Errors</button>
                  <button className="log-filter">Warnings</button>
                </div>
              </div>
              <div className="logs-list">
                {logs.map((log) => (
                  <div key={log.id} className={`log-entry ${log.level.toLowerCase()}`}>
                    <div className="log-timestamp">{log.timestamp}</div>
                    <div className="log-level">
                      {getLogLevelIcon(log.level)}
                      {log.level}
                    </div>
                    <div className="log-source">[{log.source}]</div>
                    <div className="log-message">{log.message}</div>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Control Panel */}
          <motion.div 
            className="control-panel"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.6 }}
          >
            <h2 className="section-title">System <span className="glow-text">Controls</span></h2>
            <div className="controls-grid">
              <div className="control-card cyber-card">
                <Brain className="control-icon" />
                <h3>Neural Core</h3>
                <p>Restart neural processing engine</p>
                <button className="control-button danger">Restart Core</button>
              </div>

              <div className="control-card cyber-card">
                <Database className="control-icon" />
                <h3>Vector Database</h3>
                <p>Rebuild vector indices</p>
                <button className="control-button warning">Rebuild Indices</button>
              </div>

              <div className="control-card cyber-card">
                <HardDrive className="control-icon" />
                <h3>Data Management</h3>
                <p>Cleanup temporary files</p>
                <button className="control-button primary">Cleanup Data</button>
              </div>

              <div className="control-card cyber-card">
                <Settings className="control-icon" />
                <h3>Configuration</h3>
                <p>Update system settings</p>
                <button className="control-button secondary">Edit Config</button>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </motion.div>
  );
};

export default Admin;