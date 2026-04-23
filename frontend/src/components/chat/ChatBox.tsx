import React, { useState } from 'react';
import { useChat } from '../../hooks/useChat';
import { Button } from '../ui/Button';
import { Send } from 'lucide-react';

interface ChatBoxProps {
  fileId: string;
}

export const ChatBox: React.FC<ChatBoxProps> = ({ fileId }) => {
  const { messages, sendMessage, isLoading } = useChat(fileId);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-2xl bg-white rounded-xl shadow-xl overflow-hidden border border-slate-200">
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm shadow-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-none'
                  : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-none px-4 py-2 text-sm animate-pulse text-slate-400">
              Thinking...
            </div>
          </div>
        )}
      </div>
      
      <div className="p-4 bg-white border-t border-slate-200 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask something about this file..."
          className="flex-1 px-4 py-2 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
        />
        <Button onClick={handleSend} isLoading={isLoading}>
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};
