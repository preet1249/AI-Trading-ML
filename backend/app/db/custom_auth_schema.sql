-- ============================================
-- CUSTOM AUTHENTICATION SCHEMA
-- Standalone users table (no Supabase Auth SDK)
-- Run this in Supabase SQL Editor to set up custom auth
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- DROP EXISTING USERS TABLE IF IT EXISTS
-- WARNING: This will delete all user data!
-- ============================================
DROP TABLE IF EXISTS public.users CASCADE;

-- ============================================
-- CUSTOM USERS TABLE (Standalone)
-- ============================================
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
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
-- DISABLE ROW-LEVEL SECURITY FOR NOW
-- (Since we're using custom JWT auth, not Supabase Auth)
-- ============================================
ALTER TABLE public.users DISABLE ROW LEVEL SECURITY;

-- ============================================
-- Function to update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- GRANT PERMISSIONS
-- Allow service role to access users table
-- ============================================
GRANT ALL ON public.users TO postgres;
GRANT ALL ON public.users TO service_role;

-- ============================================
-- COMPLETED!
-- Your custom auth users table is ready
-- ============================================
