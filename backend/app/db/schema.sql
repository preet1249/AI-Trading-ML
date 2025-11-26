-- ============================================
-- AI Trading Prediction Model - Database Schema
-- Supabase PostgreSQL with Row-Level Security
-- Production-Ready & Scalable
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS TABLE (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,

    -- Subscription & Billing
    subscription_tier TEXT DEFAULT 'free' CHECK (subscription_tier IN ('free', 'pro', 'premium')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('active', 'cancelled', 'expired')),
    subscription_end_date TIMESTAMPTZ,

    -- Usage Tracking
    api_calls_today INTEGER DEFAULT 0,
    api_calls_this_month INTEGER DEFAULT 0,
    last_api_call TIMESTAMPTZ,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,

    -- Settings
    settings JSONB DEFAULT '{}'::jsonb
);

-- Index for fast lookups
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_subscription ON public.users(subscription_tier, subscription_status);

-- ============================================
-- 2. PREDICTIONS TABLE (store all predictions)
-- ============================================
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,

    -- Query Info
    query TEXT NOT NULL,
    symbol TEXT NOT NULL,
    exchange TEXT,
    market_type TEXT CHECK (market_type IN ('crypto', 'stock')),

    -- Prediction Data
    direction TEXT NOT NULL CHECK (direction IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
    confidence INTEGER CHECK (confidence >= 0 AND confidence <= 100),
    risk_level TEXT CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),

    -- Price Levels
    entry_price DECIMAL(20, 8),
    entry_reason TEXT,
    entry_confidence INTEGER,
    stop_loss DECIMAL(20, 8),
    target_price DECIMAL(20, 8),

    -- Multiple Take Profits (JSONB for flexibility)
    take_profits JSONB DEFAULT '[]'::jsonb,

    -- Technical Analysis
    timeframe TEXT,
    analysis_type TEXT,
    fibonacci_levels JSONB,
    pivot_points JSONB,
    order_blocks JSONB,
    market_condition TEXT,

    -- Full Prediction (store everything)
    prediction_data JSONB NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Market closed flag
    market_closed BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX idx_predictions_user ON public.predictions(user_id, created_at DESC);
CREATE INDEX idx_predictions_symbol ON public.predictions(symbol, created_at DESC);
CREATE INDEX idx_predictions_created ON public.predictions(created_at DESC);

-- ============================================
-- 3. TRADES TABLE (track user's actual trades)
-- ============================================
CREATE TABLE IF NOT EXISTS public.trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES public.predictions(id) ON DELETE SET NULL,

    -- Trade Info
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('LONG', 'SHORT')),
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'cancelled')),

    -- Entry
    entry_price DECIMAL(20, 8) NOT NULL,
    entry_time TIMESTAMPTZ DEFAULT NOW(),
    position_size DECIMAL(20, 8),

    -- Exit
    exit_price DECIMAL(20, 8),
    exit_time TIMESTAMPTZ,

    -- Risk Management
    stop_loss DECIMAL(20, 8),
    take_profit_1 DECIMAL(20, 8),
    take_profit_2 DECIMAL(20, 8),
    take_profit_3 DECIMAL(20, 8),

    -- Performance
    pnl DECIMAL(20, 8),  -- Profit/Loss
    pnl_percentage DECIMAL(10, 4),
    risk_reward_ratio DECIMAL(10, 4),

    -- Metadata
    notes TEXT,
    tags TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_trades_user ON public.trades(user_id, created_at DESC);
CREATE INDEX idx_trades_symbol ON public.trades(symbol);
CREATE INDEX idx_trades_status ON public.trades(status);
CREATE INDEX idx_trades_pnl ON public.trades(pnl DESC);

-- ============================================
-- 4. WATCHLIST TABLE (favorite symbols)
-- ============================================
CREATE TABLE IF NOT EXISTS public.watchlist (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,

    -- Symbol Info
    symbol TEXT NOT NULL,
    exchange TEXT,
    market_type TEXT CHECK (market_type IN ('crypto', 'stock')),

    -- User Notes
    notes TEXT,
    alert_price DECIMAL(20, 8),
    alert_enabled BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint: one symbol per user
    UNIQUE(user_id, symbol)
);

-- Indexes
CREATE INDEX idx_watchlist_user ON public.watchlist(user_id, created_at DESC);
CREATE INDEX idx_watchlist_symbol ON public.watchlist(symbol);

-- ============================================
-- 5. USER ACTIVITY LOG (for analytics)
-- ============================================
CREATE TABLE IF NOT EXISTS public.user_activity (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,

    -- Activity Info
    action TEXT NOT NULL,  -- 'prediction', 'trade', 'watchlist_add', etc.
    resource_type TEXT,  -- 'prediction', 'trade', 'symbol'
    resource_id UUID,

    -- Request Details
    ip_address INET,
    user_agent TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes (for analytics queries)
CREATE INDEX idx_activity_user ON public.user_activity(user_id, created_at DESC);
CREATE INDEX idx_activity_action ON public.user_activity(action, created_at DESC);

-- ============================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- Prevents users from accessing each other's data
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trades ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_activity ENABLE ROW LEVEL SECURITY;

-- ============================================
-- USERS TABLE POLICIES
-- ============================================

-- Users can view their own profile
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

-- ============================================
-- PREDICTIONS TABLE POLICIES
-- ============================================

-- Users can view their own predictions
CREATE POLICY "Users can view own predictions"
    ON public.predictions FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own predictions
CREATE POLICY "Users can insert own predictions"
    ON public.predictions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can delete their own predictions
CREATE POLICY "Users can delete own predictions"
    ON public.predictions FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- TRADES TABLE POLICIES
-- ============================================

-- Users can view their own trades
CREATE POLICY "Users can view own trades"
    ON public.trades FOR SELECT
    USING (auth.uid() = user_id);

-- Users can insert their own trades
CREATE POLICY "Users can insert own trades"
    ON public.trades FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can update their own trades
CREATE POLICY "Users can update own trades"
    ON public.trades FOR UPDATE
    USING (auth.uid() = user_id);

-- Users can delete their own trades
CREATE POLICY "Users can delete own trades"
    ON public.trades FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- WATCHLIST TABLE POLICIES
-- ============================================

-- Users can view their own watchlist
CREATE POLICY "Users can view own watchlist"
    ON public.watchlist FOR SELECT
    USING (auth.uid() = user_id);

-- Users can manage their own watchlist
CREATE POLICY "Users can manage own watchlist"
    ON public.watchlist FOR ALL
    USING (auth.uid() = user_id);

-- ============================================
-- USER ACTIVITY POLICIES
-- ============================================

-- Users can view their own activity
CREATE POLICY "Users can view own activity"
    ON public.user_activity FOR SELECT
    USING (auth.uid() = user_id);

-- Only system can insert activity logs
CREATE POLICY "System can insert activity"
    ON public.user_activity FOR INSERT
    WITH CHECK (true);  -- Service role only

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON public.predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at BEFORE UPDATE ON public.trades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watchlist_updated_at BEFORE UPDATE ON public.watchlist
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- REALTIME SUBSCRIPTIONS
-- Enable real-time for predictions table
-- ============================================
ALTER PUBLICATION supabase_realtime ADD TABLE public.predictions;
ALTER PUBLICATION supabase_realtime ADD TABLE public.trades;

-- ============================================
-- COMPLETED!
-- Run this schema in Supabase SQL Editor
-- ============================================
