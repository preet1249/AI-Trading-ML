'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '@/lib/api-client';
import { Chat, ChatMetadata, ChatContextType, Message } from '@/types/chat';
import { useAuth } from './AuthContext';

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMetadata[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  // Load chat history only when authenticated
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      refreshHistory();
    }
  }, [isAuthenticated, isLoading]);

  const refreshHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const response = await apiClient.get('/api/v1/chat/history');
      if (response.data.success) {
        setChatHistory(response.data.chats);
      }
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const createNewChat = async () => {
    try {
      const response = await apiClient.post('/api/v1/chat/new', {
        title: 'New Chat',
      });

      if (response.data.success) {
        const newChat: Chat = {
          id: response.data.chat_id,
          user_id: '',
          title: 'New Chat',
          messages: [],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          is_active: true,
        };
        setCurrentChat(newChat);
        await refreshHistory();
        return newChat; // Return the created chat
      }
      throw new Error('Failed to create chat');
    } catch (error: any) {
      throw new Error(error.message || 'Failed to create new chat');
    }
  };

  const loadChat = async (chatId: string) => {
    try {
      console.log(`📂 Loading chat: ${chatId}`);
      const response = await apiClient.get(`/api/v1/chat/${chatId}`);
      if (response.data.success && response.data.chat) {
        console.log(`✅ Chat loaded: ${chatId} with ${response.data.chat.messages?.length || 0} messages`);
        setCurrentChat(response.data.chat);
      } else {
        console.error('❌ Failed to load chat: No chat data in response');
        throw new Error('No chat data received');
      }
    } catch (error: any) {
      console.error(`❌ Error loading chat ${chatId}:`, error);
      throw new Error(error.message || 'Failed to load chat');
    }
  };

  const saveMessage = async (
    userMessage: string,
    aiResponse: any,
    predictionData?: any
  ) => {
    // Ensure we have a current chat before saving
    let chatToUse = currentChat;

    if (!chatToUse) {
      // Create new chat if none exists and get the returned chat
      try {
        chatToUse = await createNewChat();
      } catch (error) {
        console.error('Failed to create chat:', error);
        return;
      }
    }

    if (!chatToUse) {
      console.error('No chat available to save message');
      return;
    }

    try {
      await apiClient.post('/api/v1/chat/save', {
        chat_id: chatToUse.id,
        user_message: userMessage,
        ai_response: { content: aiResponse },
        prediction_data: predictionData,
      });

      // Update local state immediately
      const userMsg: Message = {
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString(),
      };

      const aiMsg: Message = {
        role: 'assistant',
        content: aiResponse,
        prediction: predictionData,
        timestamp: new Date().toISOString(),
      };

      setCurrentChat(prev => prev ? {
        ...prev,
        messages: [...prev.messages, userMsg, aiMsg],
        updated_at: new Date().toISOString(),
      } : null);

      // Refresh history in background (don't wait)
      refreshHistory().catch(err => console.error('Failed to refresh history:', err));
    } catch (error: any) {
      console.error('Failed to save message:', error);
    }
  };

  const deleteChat = async (chatId: string) => {
    try {
      await apiClient.delete(`/api/v1/chat/${chatId}`);

      // Clear current chat if it was deleted
      if (currentChat?.id === chatId) {
        setCurrentChat(null);
      }

      await refreshHistory();
    } catch (error: any) {
      throw new Error(error.message || 'Failed to delete chat');
    }
  };

  const value: ChatContextType = {
    currentChat,
    chatHistory,
    isLoadingHistory,
    createNewChat,
    loadChat,
    saveMessage,
    deleteChat,
    refreshHistory,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
