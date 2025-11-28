'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { useChat } from '@/contexts/ChatContext';
import PredictionDisplay from './PredictionDisplay';

interface Message {
  type: 'user' | 'ai' | 'error';
  content: string;
  prediction?: any;
}

export default function ChatPanel() {
  const { currentChat, saveMessage } = useChat();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Load messages from current chat
  useEffect(() => {
    if (currentChat) {
      const chatMessages: Message[] = currentChat.messages.map((msg) => ({
        type: msg.role === 'user' ? 'user' : 'ai',
        content: msg.content,
        prediction: msg.prediction,
      }));
      setMessages(chatMessages);
    } else {
      setMessages([]);
    }
  }, [currentChat]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);

    try {
      // Call prediction API with natural language query only
      const response = await apiClient.post('/api/v1/predictions', {
        query: userMessage,
      });

      if (response.data.success) {
        const aiMessage: Message = {
          type: 'ai',
          content: `Analysis for ${response.data.symbol}`,
          prediction: response.data.prediction,
        };

        setMessages(prev => [...prev, aiMessage]);

        // Save to chat history
        await saveMessage(
          userMessage,
          aiMessage.content,
          response.data.prediction
        );
      } else {
        setMessages(prev => [...prev, {
          type: 'error',
          content: response.data.error || 'Failed to get prediction'
        }]);
      }
    } catch (error: any) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: error.message || 'Failed to connect to server'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-zinc-900/30">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-center p-8">
            <div>
              <svg className="w-16 h-16 mx-auto mb-4 text-zinc-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <p className="text-zinc-500">Ask me about any crypto or stock</p>
              <p className="text-sm text-zinc-600 mt-2">
                Try: "What's the outlook for Bitcoin?" or "Analyze TSLA stock"
              </p>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={msg.type === 'user' ? 'flex justify-end' : ''}>
              {msg.type === 'user' ? (
                <div className="bg-emerald-600 text-white px-4 py-2 rounded-lg max-w-[80%]">
                  {msg.content}
                </div>
              ) : msg.type === 'error' ? (
                <div className="bg-red-900/50 border border-red-800 text-red-200 px-4 py-3 rounded-lg text-sm">
                  {msg.content}
                </div>
              ) : (
                <PredictionDisplay prediction={msg.prediction} />
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex items-center gap-3 text-zinc-400">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:150ms]" />
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce [animation-delay:300ms]" />
            </div>
            <span className="text-sm">Analyzing...</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-zinc-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about any symbol: BTC, TSLA, AAPL..."
            disabled={loading}
            className="flex-1 px-4 py-3 bg-zinc-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 disabled:bg-zinc-700 text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
