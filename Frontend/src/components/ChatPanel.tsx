import { useState, useRef, useEffect } from 'react';
import { MdSend } from 'react-icons/md';
import { ChatMessage } from '../types';
import Spinner from './Spinner';
import dayjs from 'dayjs';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
  disabled?: boolean;
  extraActions?: React.ReactNode;
}

export default function ChatPanel({
  messages,
  onSend,
  loading = false,
  placeholder = 'Type your message…',
  disabled = false,
  extraActions,
}: ChatPanelProps) {
  const [text, setText] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSend = () => {
    if (!text.trim() || loading || disabled) return;
    onSend(text.trim());
    setText('');
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state" style={{ padding: 40 }}>
            <div className="empty-state-icon">💬</div>
            <div className="empty-state-title">Conversation will appear here</div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div className={`chat-bubble ${msg.role}`}>
              <div className="role-label">{msg.role === 'agent' ? '🤖 Agent' : '👤 You'}</div>
              {msg.content}
            </div>
            <span style={{ fontSize: 10, color: 'var(--text-muted)', margin: '2px 4px' }}>
              {dayjs(msg.timestamp).format('HH:mm')}
            </span>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 16px' }}>
            <Spinner size={16} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Agent is thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-row">
        <textarea
          className="input textarea"
          style={{ minHeight: 44, maxHeight: 120, resize: 'none', padding: '10px 12px' }}
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder}
          disabled={disabled || loading}
          rows={1}
        />
        {extraActions}
        <button
          className="btn btn-primary btn-icon"
          onClick={handleSend}
          disabled={!text.trim() || loading || disabled}
          title="Send"
        >
          {loading ? <Spinner size={16} /> : <MdSend size={18} />}
        </button>
      </div>
    </div>
  );
}
