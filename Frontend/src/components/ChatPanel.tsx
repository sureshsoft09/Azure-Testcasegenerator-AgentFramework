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

// Simple markdown-like formatter
function formatMessageContent(content: string) {
  const lines = content.split('\n');
  const result: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Headers
    if (line.startsWith('## ')) {
      result.push(<h2 key={i} style={{ margin: '8px 0 4px', fontSize: 15, fontWeight: 700 }}>{line.substring(3)}</h2>);
      i++;
      continue;
    }
    if (line.startsWith('### ')) {
      result.push(<h3 key={i} style={{ margin: '8px 0 4px', fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>{line.substring(4)}</h3>);
      i++;
      continue;
    }

    // Collect consecutive list items into a <ul>
    if (line.trim().startsWith('- ')) {
      const items: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('- ')) {
        items.push(lines[i].trim().substring(2));
        i++;
      }
      result.push(
        <ul key={`ul-${i}`} style={{ margin: '4px 0', paddingLeft: 20, lineHeight: 1.7 }}>
          {items.map((item, j) => <li key={j} style={{ marginBottom: 4 }}>{renderInline(item)}</li>)}
        </ul>
      );
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      result.push(<br key={i} />);
      i++;
      continue;
    }

    // Regular text (with inline bold/italic)
    result.push(<div key={i} style={{ marginBottom: 2 }}>{renderInline(line)}</div>);
    i++;
  }

  return result;
}

function renderInline(text: string): React.ReactNode {
  // Handle bold **text**
  if (/\*\*[^*]+\*\*/.test(text)) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return <>{parts.map((p, i) => p.startsWith('**') ? <strong key={i}>{p.slice(2, -2)}</strong> : p)}</>;
  }
  // Handle italic *text*
  if (/\*[^*]+\*/.test(text)) {
    const parts = text.split(/(\*[^*]+\*)/g);
    return <>{parts.map((p, i) => p.startsWith('*') ? <em key={i}>{p.slice(1, -1)}</em> : p)}</>;
  }
  return text;
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
              <div style={{ lineHeight: '1.6' }}>{formatMessageContent(msg.content)}</div>
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
