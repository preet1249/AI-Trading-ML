// ============================================
// User Types
// ============================================
export interface User {
  id: string;
  email: string;
  created_at: string;
}

// ============================================
// Market Data Types
// ============================================
export interface Candle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketData {
  symbol: string;
  timeframe: string;
  candles: Candle[];
}

// ============================================
// Technical Analysis Types
// ============================================
export interface Swing {
  type: 'high' | 'low';
  price: number;
  timestamp: number;
}

export interface OrderBlock {
  type: 'demand' | 'supply';
  price: number;
  timestamp: number;
}

export interface Zone {
  type: 'support' | 'resistance' | 'demand' | 'supply';
  high: number;
  low: number;
}

export interface TechnicalAnalysis {
  rsi: number;
  macd: {
    line: number;
    signal: number;
    histogram: number;
  };
  ema20: number;
  swings: Swing[];
  choch?: string;
  bos?: string;
  liquidity: number[];
  orderBlocks: OrderBlock[];
  zones: Zone[];
  trend: 'bullish' | 'bearish' | 'sideways';
}

// ============================================
// News Types
// ============================================
export interface NewsData {
  sentiment: number; // -1 to 1
  key_events: string[];
  summary: string;
}

// ============================================
// Prediction Types
// ============================================
export interface Prediction {
  id: string;
  symbol: string;
  direction: 'UP' | 'DOWN' | 'SIDEWAYS';
  target?: number;
  confidence: number; // 0-100
  reasoning: string;
  ta_data: TechnicalAnalysis;
  news_data: NewsData;
  created_at: string;
}

// ============================================
// Socket Event Types
// ============================================
export interface SocketEvents {
  livePrice: (data: { symbol: string; price: number; timestamp: number }) => void;
  taUpdate: (data: TechnicalAnalysis) => void;
  prediction: (data: Prediction) => void;
  error: (error: { message: string }) => void;
}

// ============================================
// API Response Types
// ============================================
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
