import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, AlertCircle, Sparkles, X, MessageCircle } from 'lucide-react';
import { chatAPI } from '../services/api';

export default function ChatAI() {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hey! I'm Ashok AI. How can I help you today?",
      sender: 'ai',
      timestamp: new Date(),
      isWelcome: true
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen) inputRef.current?.focus();
  }, [isOpen]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { id: Date.now(), text: userMsg, sender: 'user', timestamp: new Date() }]);
    setInput('');
    setLoading(true);

    try {
      const res = await chatAPI.sendMessage(userMsg);
      const aiReply = res.data.response || "I'm not sure how to respond.";

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: aiReply,
        sender: 'ai',
        timestamp: new Date(res.data.timestamp || Date.now()),
      }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        text: "Sorry, Ashok AI is not responding right now.",
        sender: 'ai',
        error: true,
        timestamp: new Date(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTime = (date) => date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <>
      <style jsx>{`
        @keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.5 } }
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
        .pulse { animation: pulse 2s infinite; }
        .spin { animation: spin 1s linear infinite; }
      `}</style>

      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{
            position: 'fixed', bottom: '28px', right: '28px', width: '40px', height: '40px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', border: 'none', borderRadius: '50%',
            boxShadow: '0 20px 30px rgba(59,130,246,0.3)', cursor: 'pointer', zIndex: 9999,
            transition: 'all 0.3s', transform: isHovered ? 'scale(1.12)' : 'scale(1)',
          }}
        >
          <MessageCircle size={32} color="white" />
          <div className="pulse" style={{ position: 'absolute', top: '-6px', right: '-6px', width: '18px', height: '18px', background: '#10b981', borderRadius: '50%', border: '4px solid white' }} />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div style={{
          position: 'fixed', bottom: '28px', right: '28px', width: '400px', height: '640px',
          background: 'white', borderRadius: '20px', boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
          overflow: 'hidden', zIndex: 9999, display: 'flex', flexDirection: 'column',
          fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          border: '1px solid #e2e8f0',
        }}>
          {/* Header */}
          <div style={{ background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', padding: '18px 20px', color: 'white', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{ position: 'relative' }}>
                <div style={{ width: '48px', height: '48px', background: 'white', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={28} color="#8b5cf6" />
                </div>
                <div style={{ position: 'absolute', bottom: '-2px', right: '-2px', width: '16px', height: '16px', background: '#10b981', borderRadius: '50%', border: '3px solid white' }} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  Ashok AI <Sparkles size={18} color="#fbbf24" />
                </h3>
                <p style={{ margin: '4px 0 0', fontSize: '13px', opacity: 0.9 }}>Always here to help</p>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} style={{ background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '10px', padding: '8px', cursor: 'pointer' }}>
              <X size={22} />
            </button>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', background: '#f8fafc' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
              {messages.map(msg => (
                <div key={msg.id} style={{ display: 'flex', gap: '12px', flexDirection: msg.sender === 'user' ? 'row-reverse' : 'row', alignItems: 'flex-end' }}>
                  <div style={{
                    width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
                    background: msg.sender === 'user' ? 'linear-gradient(135deg, #34d399, #10b981)' : msg.error ? '#ef4444' : 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    {msg.sender === 'user' ? <User size={20} color="white" /> : msg.error ? <AlertCircle size={20} color="white" /> : <Bot size={20} color="white" />}
                  </div>
                  <div style={{ maxWidth: '78%' }}>
                    <div style={{
                      padding: '12px 16px', borderRadius: '20px', fontSize: '14.8px', lineHeight: '1.5', whiteSpace: 'pre-wrap',
                      background: msg.sender === 'user' ? 'linear-gradient(135deg, #3b82f6, #8b5cf6)' : msg.error ? '#fee2e2' : 'white',
                      color: msg.sender === 'user' ? 'white' : msg.error ? '#991b1b' : '#1f2937',
                      border: msg.sender === 'ai' && !msg.error ? '1px solid #e2e8f0' : 'none',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                    }}>
                      {msg.text}
                    </div>
                    {!msg.isWelcome && (
                      <div style={{ fontSize: '11.5px', color: '#94a3b8', marginTop: '6px', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                        {formatTime(msg.timestamp)}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                  <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Bot size={20} color="white" />
                  </div>
                  <div style={{ padding: '12px 16px', borderRadius: '20px', background: 'white', border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Loader2 size={18} className="spin" />
                    <span style={{ color: '#64748b' }}>Ashok is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input */}
          <div style={{ padding: '16px 20px', background: 'white', borderTop: '1px solid #e2e8f0' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask Ashok anything..."
                disabled={loading}
                rows={1}
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: '20px', border: '1px solid #cbd5e1',
                  background: '#f8fafc', outline: 'none', resize: 'none', fontSize: '15px', fontFamily: 'inherit'
                }}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                style={{
                  width: '46px', height: '46px', border: 'none', borderRadius: '16px', cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                  background: input.trim() && !loading ? 'linear-gradient(135deg, #3b82f6, #8b5cf6)' : '#94a3b8',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}
              >
                {loading ? <Loader2 size={20} className="spin" /> : <Send size={20} color="white" />}
              </button>
            </div>
            <p style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: '#94a3b8' }}>
              Press Enter to send • Shift+Enter for new line
            </p>
          </div>
        </div>
      )}
    </>
  );
}