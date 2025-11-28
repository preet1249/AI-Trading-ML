export interface Message {
  role: 'user' | 'assistant';
  content: string;
  prediction?: any;
  timestamp: string;
}

export interface Chat {
  id: string;
  user_id: string;
  title: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ChatMetadata {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatContextType {
  currentChat: Chat | null;
  chatHistory: ChatMetadata[];
  isLoadingHistory: boolean;
  createNewChat: () => Promise<void>;
  loadChat: (chatId: string) => Promise<void>;
  saveMessage: (userMessage: string, aiResponse: any, predictionData?: any) => Promise<void>;
  deleteChat: (chatId: string) => Promise<void>;
  refreshHistory: () => Promise<void>;
}
