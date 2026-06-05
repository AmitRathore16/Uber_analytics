import React, { useState, useEffect, useRef } from 'react';
import { 
  Database, 
  CheckCircle, 
  ChevronDown, 
  ChevronUp, 
  Send, 
  RefreshCw, 
  BookOpen,
  Bot
} from 'lucide-react';
import './App.css';

const GREETING_TEXT = "Hello! I am your Uber Analytics AI Assistant. 🚗\n\nI can help you analyze patterns in our dataset (150K bookings across 2025). Feel free to ask queries like:\n- *Why are there fewer rides of Go Sedan?*\n- *Which payment method generates the most revenue?*\n- *What is the average driver rating for Auto rides?*\n\nIf you ask an analytical question, I will convert it into a SQL query and show you what MySQL code was executed! How can I help you today?";

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // AI assistant states
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: GREETING_TEXT, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [openedQueries, setOpenedQueries] = useState({}); // tracking which messages have their query block open

  // SQL Tab states
  const [sqlQuestions, setSqlQuestions] = useState([]);
  const [sqlLoading, setSqlLoading] = useState(true);
  const [selectedQuestionId, setSelectedQuestionId] = useState(1);
  const [expandedAccordions, setExpandedAccordions] = useState({ query: true, results: true });

  const chatEndRef = useRef(null);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, chatLoading]);

  // Load 15 SQL Questions
  useEffect(() => {
    setSqlLoading(true);
    fetch('/api/sql-questions')
      .then(res => res.json())
      .then(data => {
        setSqlQuestions(data);
        setSqlLoading(false);
      })
      .catch(err => {
        console.error("Error loading SQL questions:", err);
        setSqlLoading(false);
      });
  }, []);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg = {
      role: 'user',
      content: chatInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);

    // Prepare history payload for context (last 5 messages)
    const historyPayload = chatHistory.map(m => ({ role: m.role, content: m.content }));

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMsg.content, history: historyPayload })
    })
      .then(res => res.json())
      .then(data => {
        setChatLoading(false);
        if (data.error) {
          setChatHistory(prev => [...prev, {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${data.error}`,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }]);
        } else {
          setChatHistory(prev => [...prev, {
            role: 'assistant',
            content: data.answer,
            query: data.query,
            query_results: data.query_results,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }]);
        }
      })
      .catch(err => {
        console.error("Chat error:", err);
        setChatLoading(false);
        setChatHistory(prev => [...prev, {
          role: 'assistant',
          content: "Sorry, I could not connect to the backend server.",
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }]);
      });
  };

  const handleNewChat = () => {
    setChatHistory([
      { role: 'assistant', content: GREETING_TEXT, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
    ]);
    setOpenedQueries({});
  };

  const toggleQueryBlock = (index) => {
    setOpenedQueries(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const toggleAccordion = (key) => {
    setExpandedAccordions(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const currentSqlQuestion = sqlQuestions.find(q => q.id === selectedQuestionId);

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-section">
          <h1 className="logo-title text-gradient">Uber Analytics</h1>
        </div>
        <div className="tabs-container">
          <button 
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`tab-btn ${activeTab === 'sql' ? 'active' : ''}`}
            onClick={() => setActiveTab('sql')}
          >
            SQL Portal
          </button>
        </div>
      </header>

      {/* Body */}
      <main className="app-body">
        {/* Tab 1: Dashboard */}
        <div className={`tab-content ${activeTab === 'dashboard' ? 'active' : ''}`}>
          <div className="dashboard-layout">

            {/* Left Column: Power BI Embed */}
            <div className="powerbi-container">
              <iframe 
                title="uber_dashboard_final" 
                className="powerbi-iframe"
                src={import.meta.env.VITE_POWERBI_EMBED_URL || "https://app.powerbi.com/reportEmbed?reportId=df59c1ba-73d8-4d2b-b85a-47b8ba5699c3&autoAuth=true&ctid=945ef104-7619-4ac0-aebb-ed348ffd933d"} 
                frameBorder="0" 
                allowFullScreen={true}
              />
            </div>

            {/* Right Column: AI Assistant Chat */}
            <div className="assistant-panel">
              <div className="assistant-header">
                <div className="assistant-info">
                  <div className="assistant-avatar"><Bot size={20} /></div>
                  <div className="assistant-name-group">
                    <span className="assistant-name">AI Assistant</span>
                    <span className="assistant-status">Online</span>
                  </div>
                </div>
                <button className="new-chat-btn" onClick={handleNewChat}>
                  New Chat
                </button>
              </div>

              {/* Chat history */}
              <div className="chat-messages-container">
                {chatHistory.map((msg, index) => (
                  <div key={index} className={`chat-message ${msg.role}`}>
                    <div className="message-bubble">
                      {msg.content}
                      
                      {/* Show query toggle if query exists */}
                      {msg.query && (
                        <div className="chat-sql-block">
                          <button 
                            className="show-query-btn"
                            onClick={() => toggleQueryBlock(index)}
                          >
                            <Database size={12} />
                            {openedQueries[index] ? "Hide Query" : "Show Query"}
                          </button>
                          
                          {openedQueries[index] && (
                            <div className="animate-fade-in">
                              <pre className="query-viewer-embed">
                                {msg.query}
                              </pre>
                              {msg.query_results && msg.query_results.length > 0 && (
                                <div className="query-results-table-wrapper">
                                  <table className="query-results-table">
                                    <thead>
                                      <tr>
                                        {Object.keys(msg.query_results[0]).map((col) => (
                                          <th key={col}>{col}</th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {msg.query_results.slice(0, 10).map((row, rIdx) => (
                                        <tr key={rIdx}>
                                          {Object.values(row).map((val, cIdx) => (
                                            <td key={cIdx}>
                                              {typeof val === 'number' ? val.toFixed(2).replace(/\.00$/, '') : String(val)}
                                            </td>
                                          ))}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                  {msg.query_results.length > 10 && (
                                    <div style={{ fontSize: '9px', color: 'var(--text-secondary)', padding: '4px 8px', textAlign: 'center', background: '#f8fafc' }}>
                                      Showing top 10 of {msg.query_results.length} rows
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <span className="message-meta">{msg.timestamp}</span>
                  </div>
                ))}
                
                {chatLoading && (
                  <div className="chat-message assistant">
                    <div className="message-bubble" style={{ display: 'inline-block' }}>
                      <div className="loading-dots">
                        <div className="loading-dot"></div>
                        <div className="loading-dot"></div>
                        <div className="loading-dot"></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Form */}
              <form className="chat-input-form" onSubmit={handleSendMessage}>
                <input 
                  type="text" 
                  className="chat-input"
                  placeholder="Ask a question about the dataset..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                />
                <button 
                  type="submit" 
                  className="chat-send-btn" 
                  disabled={!chatInput.trim() || chatLoading}
                >
                  <Send size={16} />
                </button>
              </form>
            </div>

          </div>
        </div>

        {/* Tab 2: SQL Portal */}
        <div className={`tab-content ${activeTab === 'sql' ? 'active' : ''}`}>
          <div className="sql-tab-layout">
            
            {/* SQL Left Sidebar: Questions list */}
            <div className="sql-sidebar">
              <span className="sql-sidebar-title">SQL Inquiries</span>
              {sqlLoading ? (
                <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  <RefreshCw className="animate-spin" size={24} style={{ margin: '0 auto 8px auto' }} />
                  <span>Loading Questions...</span>
                </div>
              ) : (
                sqlQuestions.map((q) => (
                  <button 
                    key={q.id}
                    className={`sql-question-nav-item ${selectedQuestionId === q.id ? 'active' : ''}`}
                    onClick={() => setSelectedQuestionId(q.id)}
                  >
                    <span className="sql-q-num">Q{q.id}.</span>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebKitLineClamp: 2, WebKitBoxOrient: 'vertical' }}>
                      {q.question}
                    </span>
                  </button>
                ))
              )}
            </div>

            {/* SQL Right Pane: Question details */}
            <div className="sql-workspace">
              {sqlLoading ? (
                <div style={{ display: 'flex', flex: 1, justifyContent: 'center', alignItems: 'center', color: 'var(--text-secondary)' }}>
                  <RefreshCw className="animate-spin" size={32} />
                </div>
              ) : currentSqlQuestion ? (
                <div className="sql-workspace-card animate-fade-in">
                  <div className="sql-workspace-header">
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                      <span className="sql-workspace-q-tag">Question Number {currentSqlQuestion.id}</span>
                      <h2 className="sql-workspace-q-text">{currentSqlQuestion.question}</h2>
                    </div>
                  </div>

                  {/* Accordion 1: MySQL Query */}
                  <div className="sql-accordion-section">
                    <div className="sql-accordion-header" onClick={() => toggleAccordion('query')}>
                      <span className="sql-accordion-title">
                        <Database size={16} />
                        MySQL Query Executed
                      </span>
                      {expandedAccordions.query ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                    {expandedAccordions.query && (
                      <div className="sql-accordion-content">
                        <pre className="sql-code-block">{currentSqlQuestion.query}</pre>
                      </div>
                    )}
                  </div>

                  {/* Accordion 2: MySQL Answer */}
                  <div className="sql-accordion-section">
                    <div className="sql-accordion-header" onClick={() => toggleAccordion('results')}>
                      <span className="sql-accordion-title">
                        <CheckCircle size={16} />
                        Query Execution Result Table
                      </span>
                      {expandedAccordions.results ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                    {expandedAccordions.results && (
                      <div className="sql-accordion-content" style={{ padding: 0 }}>
                        {currentSqlQuestion.results && currentSqlQuestion.results.length > 0 ? (
                          <div className="sql-results-table-container">
                            <table className="sql-results-table">
                              <thead>
                                <tr>
                                  {Object.keys(currentSqlQuestion.results[0]).map((col) => (
                                    <th key={col}>{col}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {currentSqlQuestion.results.map((row, rIdx) => (
                                  <tr key={rIdx}>
                                    {Object.values(row).map((val, cIdx) => (
                                      <td key={cIdx}>
                                        {typeof val === 'number' 
                                          ? val.toFixed(2).replace(/\.00$/, '') 
                                          : String(val === null ? 'NULL' : val)
                                        }
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ) : (
                          <div style={{ padding: '20px 0', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            No rows returned
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Topics Covered */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      SQL Concepts Covered:
                    </span>
                    <div className="sql-topics-container">
                      {currentSqlQuestion.topics.map((t, idx) => (
                        <div key={idx} className="sql-topic-tag-card">
                          <BookOpen size={12} style={{ marginRight: '6px' }} />
                          {t}
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              ) : (
                <div style={{ display: 'flex', flex: 1, justifyContent: 'center', alignItems: 'center', color: 'var(--text-secondary)' }}>
                  Select a question to view details.
                </div>
              )}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
