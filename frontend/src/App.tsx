import React, { useState, useRef, useEffect } from 'react';
import './App.css';

interface Message {
  sender: 'user' | 'llm';
  text: string;
}

const API_URL = 'http://multivac:8000/prompt-llm';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const conversationEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendPrompt = async () => {
    if (!input.trim() || loading) return;
    setMessages((msgs) => [...msgs, { sender: 'user', text: input }]);
    setLoading(true);
    setError(null);
    const prompt = input;
    setInput('');
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) throw new Error('Server error');
      const data = await res.json();
      setMessages((msgs) => [...msgs, { sender: 'llm', text: data.response }]);
    } catch (err: any) {
      setError('Failed to get response from LLM.');
      setMessages((msgs) => [...msgs, { sender: 'llm', text: '[Error: No response from LLM]' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendPrompt();
  };

  return (
    <div className="chat-root">
      <div className="chat-header">Quotient LLM Chat</div>
      <div className="chat-conversation">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-bubble ${msg.sender}`}>{msg.text}</div>
        ))}
        {loading && <div className="chat-bubble llm loading">Thinking…</div>}
        <div ref={conversationEndRef} />
      </div>
      <div className="chat-input-bar">
        <input
          type="text"
          className="chat-input"
          placeholder="Type your prompt..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleInputKeyDown}
          disabled={loading}
        />
        <button className="chat-send-btn" onClick={sendPrompt} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
      {error && <div className="chat-error">{error}</div>}
    </div>
  );
}

export default App;
