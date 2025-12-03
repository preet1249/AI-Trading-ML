# 🚀 Render Deployment Guide

Complete guide to deploy AI Trading Prediction Model to Render.

## 📋 **REQUIRED ENVIRONMENT VARIABLES FOR RENDER**

### **1. API KEYS (REQUIRED)**

```bash
# OpenRouter (Qwen AI Model) - REQUIRED
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Twelve Data (Stock Market Data) - OPTIONAL (has free tier)
TWELVE_DATA_API_KEY=your_twelve_data_api_key

# Google Custom Search (News) - OPTIONAL
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_search_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

**Where to get API keys:**
- **OpenRouter**: https://openrouter.ai/keys (REQUIRED - $5 minimum balance)
- **Twelve Data**: https://twelvedata.com/pricing (FREE tier: 800 calls/day)
- **Google Search**: https://developers.google.com/custom-search/v1/overview (FREE tier: 100/day)

---

### **2. DATABASES (REQUIRED)**

```bash
# MongoDB Atlas (Free M0 Cluster)
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/trading_agent?retryWrites=true&w=majority

# Upstash Redis (Free 10K commands/day)
UPSTASH_REDIS_URL=https://your-redis-instance.upstash.io
UPSTASH_REDIS_TOKEN=your_upstash_token

# Supabase (Auth & Database)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**Where to get:**
- **MongoDB Atlas**: https://www.mongodb.com/cloud/atlas/register (FREE M0 cluster)
- **Upstash Redis**: https://upstash.com/ (FREE 10K commands/day)
- **Supabase**: https://supabase.com/ (FREE tier)

---

### **3. APPLICATION CONFIG (REQUIRED)**

```bash
# Backend Configuration
BACKEND_URL=https://your-backend-app.onrender.com
BACKEND_PORT=8000
ENVIRONMENT=production

# Security
JWT_SECRET=your_super_secret_jwt_key_minimum_32_characters_long

# CORS (Add your frontend URL)
CORS_ORIGINS=https://your-frontend.vercel.app,https://yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_DAY=500

# Logging
LOG_LEVEL=INFO
```

---

### **4. OPTIONAL (Not Required, System Uses Free Fallbacks)**

```bash
# These are OPTIONAL - system will use free alternatives if not provided:

# JWT Legacy (Optional - kept for backward compatibility)
JWT_EXPIRATION_HOURS=24

# CoinCap (FREE - No API key needed, auto-fallback for Binance)
# Binance doesn't work on Render → CoinCap automatically used

# Yahoo Finance (FREE - No API key needed, auto-fallback for stocks)
# System uses Yahoo Finance when TwelveData quota exceeded
```

---

## 🛠️ **RENDER SETUP STEPS**

### **Step 1: Create Web Service on Render**

1. Go to https://render.com/
2. Click **"New +" → "Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-trading-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT`

### **Step 2: Add Environment Variables**

Go to **Environment** tab and add ALL variables from section above.

### **Step 3: Deploy**

Click **"Create Web Service"** - Render will automatically deploy!

---

## ✅ **WHAT WORKS IN PRODUCTION:**

### **Crypto Data:**
- ✅ **CoinCap API** (FREE, unlimited) - Auto-fallback when Binance blocked
- ✅ Real-time data
- ✅ Works globally (no regional restrictions)

### **Stock Data:**
- ✅ **Yahoo Finance** (FREE) - Indian & US stocks
- ✅ Historical data (15min delay)
- ✅ Works for day trading, swing, long-term
- ⚠️ No scalping (removed for stocks due to delay)

### **News:**
- ✅ **Google Custom Search** (FREE 100/day)
- ✅ < 24 hours news only
- ✅ Always runs for stocks
- ✅ Conditional for crypto (skips for scalping)

---

## 📊 **DATA SOURCE PRIORITY:**

### **Crypto:**
1. Try **Binance** (works on local CLI)
2. Fallback to **CoinCap** (works on Render production) ✅

### **Stocks:**
1. Try **TwelveData** (800 free calls/day)
2. Fallback to **Yahoo Finance** (unlimited, 15min delay) ✅

### **News:**
- **Google Custom Search** (100 free/day)
- Falls back gracefully if quota exceeded

---

## 🔗 **AFTER DEPLOYMENT:**

### **Update Frontend Environment:**

In Vercel, add:
```bash
NEXT_PUBLIC_API_URL=https://your-backend-app.onrender.com
NEXT_PUBLIC_SOCKET_URL=https://your-backend-app.onrender.com
```

### **Test Deployment:**

```bash
# Health check
curl https://your-backend-app.onrender.com/health

# Test crypto (should use CoinCap on Render)
curl -X POST https://your-backend-app.onrender.com/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"query": "Bitcoin prediction"}'

# Test stock
curl -X POST https://your-backend-app.onrender.com/api/v1/predictions \
  -H "Content-Type: application/json" \
  -d '{"query": "Reliance Industries prediction"}'
```

---

## 🎯 **MINIMAL REQUIRED SETUP (FREE TIER):**

**Absolutely Required:**
- ✅ OPENROUTER_API_KEY ($5 balance)
- ✅ MONGODB_URI (Free M0 cluster)
- ✅ UPSTASH_REDIS_URL + TOKEN (Free 10K/day)
- ✅ SUPABASE (URL + Keys) (Free tier)
- ✅ JWT_SECRET (Generate: `openssl rand -hex 32`)
- ✅ CORS_ORIGINS (Add your frontend URL)

**Optional (Has Free Fallbacks):**
- ⚠️ TWELVE_DATA_API_KEY (Falls back to Yahoo Finance)
- ⚠️ GOOGLE_CUSTOM_SEARCH_API_KEY (Falls back gracefully)

**Auto-Handled (No Keys Needed):**
- ✅ CoinCap (FREE, unlimited crypto)
- ✅ Yahoo Finance (FREE, unlimited stocks)
- ✅ Binance (blocked on Render, but CoinCap fallback works)

---

## 🚨 **IMPORTANT NOTES:**

1. **Binance on Render:** Doesn't work due to regional restrictions → CoinCap fallback automatic ✅

2. **Free Tier Limits:**
   - TwelveData: 800 calls/day → Yahoo Finance fallback
   - Google Search: 100 calls/day → Graceful fallback
   - CoinCap: Unlimited ✅
   - Yahoo Finance: Unlimited ✅

3. **OpenRouter:** $5 minimum balance required, but lasts long time

4. **Cold Starts:** Render free tier has cold starts (~30s) - upgrade to paid for instant response

---

## 📱 **VERCEL (FRONTEND) VARIABLES:**

```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=https://your-backend-app.onrender.com
NEXT_PUBLIC_SOCKET_URL=https://your-backend-app.onrender.com
NEXT_PUBLIC_APP_NAME=AI Trading Predictor
NODE_ENV=production
```

---

## ✅ **DEPLOYMENT CHECKLIST:**

- [ ] MongoDB Atlas cluster created
- [ ] Upstash Redis created
- [ ] Supabase project created
- [ ] OpenRouter API key obtained ($5 balance)
- [ ] GitHub repo connected to Render
- [ ] All environment variables added to Render
- [ ] Backend deployed successfully
- [ ] Frontend environment variables updated
- [ ] Frontend deployed to Vercel
- [ ] Test crypto prediction (should use CoinCap)
- [ ] Test stock prediction (should use Yahoo Finance)
- [ ] Test authentication flow

---

🎉 **Your AI Trading Predictor is now live in production!**
