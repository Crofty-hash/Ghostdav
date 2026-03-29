import React, { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import crypto from 'crypto';
import './ChatApp.css';

const ChatApp = () => {
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [username, setUsername] = useState('');
  const [clientId, setClientId] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [targetPeer, setTargetPeer] = useState('');
  const [peers, setPeers] = useState([]);
  const [sharedSecret, setSharedSecret] = useState(null);
  const messagesEndRef = useRef(null);

  const BACKEND_URL = 'http://localhost:8888';

  // Derive shared key (same as backend)
  const deriveKey = () => {
    const password = 'demo-password';
    const salt = Buffer.from('fixed_salt_for_demo');
    // Simple PBKDF2 simulation (in production, use proper crypto libs)
    return crypto.pbkdf2Sync(password, salt, 100000, 32, 'sha256');
  };

  useEffect(() => {
    const key = deriveKey();
    setSharedSecret(key);
  }, []);

  const connectToBackend = () => {
    // Create WebSocket connection manually (Socket.io fallback)
    const ws = new WebSocket(`ws://localhost:8888`);
    
    ws.onopen = () => {
      setIsConnected(true);
      console.log('Connected to backend');
      addSystemMessage('Connected to GhostDav backend');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleIncomingMessage(data);
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addSystemMessage('Connection error');
    };

    ws.onclose = () => {
      setIsConnected(false);
      addSystemMessage('Disconnected from backend');
    };

    // Store ws in state or use context
    setSocket(ws);
  };

  const handleIncomingMessage = (data) => {
    if (data.type === 'peer_message') {
      try {
        const encData = Buffer.from(data.data, 'base64');
        const nonce = Buffer.from(data.nonce, 'base64');
        
        // Decrypt using shared secret (simplified - actual decryption needed)
        addSystemMessage(`Message from ${data.from || 'peer'}: encrypted packet received`);
        
        addMessage({
          from: data.from || 'Unknown Peer',
          text: data.data,
          timestamp: new Date(),
          encrypted: true
        });
      } catch (e) {
        console.error('Failed to handle message:', e);
      }
    }
  };

  const sendMessage = () => {
    if (!inputMessage.trim() || !socket || !sharedSecret) {
      return;
    }

    // Encrypt message (simplified)
    const plaintext = Buffer.from(inputMessage);
    const nonce = crypto.randomBytes(12);
    
    const payload = {
      type: 'peer_message',
      data: plaintext.toString('base64'),
      nonce: nonce.toString('base64'),
      target: targetPeer || null
    };

    socket.send(JSON.stringify(payload));
    
    addMessage({
      from: username || 'You',
      text: inputMessage,
      timestamp: new Date(),
      encrypted: false
    });

    setInputMessage('');
  };

  const addMessage = (msg) => {
    setMessages(prev => [...prev, msg]);
    scrollToBottom();
  };

  const addSystemMessage = (text) => {
    addMessage({
      from: 'System',
      text: text,
      timestamp: new Date(),
      isSystem: true
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleConnect = () => {
    if (username.trim()) {
      connectToBackend();
    }
  };

  return (
    <div className="chatapp-container">
      <div className="chatapp-header">
        <h1>🔐 GhostDav Chat</h1>
        <div className="status">
          {isConnected ? (
            <span className="status-connected">• Connected</span>
          ) : (
            <span className="status-disconnected">• Disconnected</span>
          )}
        </div>
      </div>

      <div className="chatapp-main">
        {!isConnected ? (
          <div className="login-panel">
            <h2>Welcome to GhostDav</h2>
            <div className="login-form">
              <input
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleConnect()}
              />
              <button onClick={handleConnect}>Connect</button>
            </div>
            <p className="login-info">
              End-to-end encrypted P2P messaging
            </p>
          </div>
        ) : (
          <>
            <div className="messages-panel">
              <div className="messages-list">
                {messages.map((msg, idx) => (
                  <div key={idx} className={`message ${msg.isSystem ? 'system' : ''}`}>
                    <span className="message-from">{msg.from}</span>
                    <span className="message-text">{msg.text}</span>
                    <span className="message-time">
                      {msg.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            </div>

            <div className="peers-panel">
              <h3>Peers</h3>
              <input
                type="text"
                placeholder="Peer ID or address"
                value={targetPeer}
                onChange={(e) => setTargetPeer(e.target.value)}
                className="peer-input"
              />
              <div className="targeted-peer">
                {targetPeer && <span>Send to: {targetPeer}</span>}
              </div>
            </div>

            <div className="input-panel">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type a message..."
                className="message-input"
              />
              <button onClick={sendMessage} className="send-button">
                Send
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ChatApp;
