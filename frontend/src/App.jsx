import React, { useState, useEffect, useRef } from 'react';
import { 
  Database, 
  Bot,
  Send
} from 'lucide-react';
import './App.css';

const GREETING_TEXT = "Hello! I am your Uber Analytics AI Assistant. 🚗\n\nI can help you analyze patterns in our dataset (150K bookings across 2025). Feel free to ask queries like:\n- *Why are there fewer rides of Go Sedan?*\n- *Which payment method generates the most revenue?*\n- *What is the average driver rating for Auto rides?*\n\nIf you ask an analytical question, I will convert it into a SQL query and show you what MySQL code was executed! How can I help you today?";

function App() {
  // AI assistant states
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: GREETING_TEXT, timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [openedQueries, setOpenedQueries] = useState({}); // tracking which messages have their query block open

  const chatEndRef = useRef(null);

  // Scroll to bottom of chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, chatLoading]);

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

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-section">
          <h1 className="logo-title text-gradient">Uber Analytics</h1>
        </div>
      </header>

      {/* Body */}
      <main className="app-body">
        <div className="dashboard-layout" style={{ height: '100%' }}>

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
      </main>
    </div>
  );
}

export default App;
