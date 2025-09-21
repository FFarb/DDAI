import { FormEvent, useState } from 'react';
import { useChatStore } from '../store/chat';

const Chat = () => {
  const { messages, sendMessage, isStreaming, model, setModel, systemPrompt, setSystemPrompt } =
    useChatStore();
  const [input, setInput] = useState('');

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="card">
      <div className="flex" style={{ gap: '24px' }}>
        <div className="flex-column" style={{ flex: 1 }}>
          <h3>Conversation</h3>
          <div style={{ maxHeight: '400px', overflowY: 'auto', padding: '12px', background: '#191919' }}>
            {messages.map((message, index) => (
              <div key={index} style={{ marginBottom: '12px' }}>
                <strong>{message.role.toUpperCase()}</strong>
                <div>{message.content}</div>
              </div>
            ))}
            {!messages.length && <p>No messages yet. Start chatting!</p>}
          </div>
        </div>
        <div className="flex-column" style={{ width: '240px' }}>
          <label>
            Model
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              <option value="gpt">GPT (Default)</option>
              <option value="stub">Stub</option>
            </select>
          </label>
          <label>
            System prompt
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={8}
              placeholder="You are a helpful assistant"
            />
          </label>
        </div>
      </div>
      <form onSubmit={handleSubmit} className="flex" style={{ marginTop: '16px' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={3}
          style={{ flex: 1 }}
          placeholder="Ask something..."
        />
        <button type="submit" disabled={isStreaming} style={{ alignSelf: 'flex-end' }}>
          {isStreaming ? 'Streaming...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default Chat;
