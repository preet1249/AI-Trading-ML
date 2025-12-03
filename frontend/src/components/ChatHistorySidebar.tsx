'use client';

import { useChat } from '@/contexts/ChatContext';
import { ChatMetadata } from '@/types/chat';
import { useState } from 'react';

export default function ChatHistorySidebar() {
  const { chatHistory, currentChat, createNewChat, loadChat, deleteChat, isLoadingHistory } = useChat();
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleNewChat = async () => {
    try {
      await createNewChat();
    } catch (error: any) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleLoadChat = async (chatId: string) => {
    try {
      console.log(`🖱️ User clicked on chat: ${chatId}`);
      await loadChat(chatId);
      console.log(`✅ Successfully loaded chat: ${chatId}`);
    } catch (error: any) {
      console.error('❌ Failed to load chat:', error);
      alert(`Failed to load chat: ${error.message || 'Unknown error'}`);
    }
  };

  const handleDeleteChat = async (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingId(chatId);
    try {
      await deleteChat(chatId);
    } catch (error: any) {
      console.error('Failed to delete chat:', error);
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="h-full bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Header with New Chat Button */}
      <div className="p-4 border-b border-gray-800">
        <button
          onClick={handleNewChat}
          className="w-full px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Chat History List */}
      <div className="flex-1 overflow-y-auto">
        {isLoadingHistory ? (
          <div className="p-4 text-center text-gray-500">
            <svg className="animate-spin h-6 w-6 mx-auto mb-2" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="text-sm">Loading chats...</p>
          </div>
        ) : chatHistory.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            <p className="text-sm">No chats yet</p>
            <p className="text-xs mt-1">Click "New Chat" to start</p>
          </div>
        ) : (
          <div className="space-y-1 p-2">
            {chatHistory.map((chat) => (
              <div
                key={chat.id}
                onClick={() => handleLoadChat(chat.id)}
                className={`group relative p-3 rounded-lg cursor-pointer transition ${
                  currentChat?.id === chat.id
                    ? 'bg-gray-800 border border-emerald-600/50'
                    : 'hover:bg-gray-800/50'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate font-medium">
                      {chat.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(chat.updated_at)}
                    </p>
                  </div>

                  {/* Delete Button */}
                  <button
                    onClick={(e) => handleDeleteChat(chat.id, e)}
                    disabled={deletingId === chat.id}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 rounded transition"
                    title="Delete chat"
                  >
                    {deletingId === chat.id ? (
                      <svg className="animate-spin h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    ) : (
                      <svg className="w-4 h-4 text-gray-400 hover:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
