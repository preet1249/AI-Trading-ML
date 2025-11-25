# 🚀 Deployment Guide

## Quick Deployment Commands

### For Vercel (Frontend)
```bash
Root Directory: frontend
Build Command: npm run build
Output Directory: .next
Install Command: npm install
Start Command: npm start
Framework: Next.js
Node Version: 18.x
```

### For Render (Backend)
```bash
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT
Python Version: 3.11
```

---

## 📦 Step-by-Step Deployment

### 1️⃣ Deploy Frontend to Vercel

#### A. Via Vercel Dashboard (Recommended)
1. Go to https://vercel.com/
2. Click "Add New Project"
3. Import from GitHub: `https://github.com/preet1249/AI-Trading-ML`
4. **Configure Project:**
   ```
   Framework Preset: Next.js
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: .next
   Install Command: npm install
   Node Version: 18.x
   ```

5. **Add Environment Variables:**
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_SOCKET_URL=https://your-backend.onrender.com
   NEXT_PUBLIC_APP_NAME=AI Trading Predictor
   NODE_ENV=production
   ```

6. Click "Deploy"

#### B. Via Vercel CLI
```bash
npm install -g vercel
cd frontend
vercel --prod
```

---

### 2️⃣ Deploy Backend to Render

#### A. Via Render Dashboard (Recommended)
1. Go to https://render.com/
2. Click "New" → "Web Service"
3. Connect GitHub repository: `https://github.com/preet1249/AI-Trading-ML`
4. **Configure Service:**
   ```
   Name: trading-agent-backend
   Runtime: Python 3
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn app.main:socket_app --host 0.0.0.0 --port $PORT
   Python Version: 3.11.0
   ```

5. **Add Environment Variables:**
   ```env
   # API Keys
   OPENROUTER_API_KEY=your_key_here
   OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct
   TWELVE_DATA_API_KEY=your_key_here
   GOOGLE_CUSTOM_SEARCH_API_KEY=your_key_here
   GOOGLE_SEARCH_ENGINE_ID=your_id_here

   # Database
   MONGODB_URI=your_mongodb_atlas_connection_string
   MONGODB_DB_NAME=trading_agent

   # Redis (Upstash)
   UPSTASH_REDIS_URL=your_upstash_redis_url
   UPSTASH_REDIS_TOKEN=your_upstash_token

   # Supabase
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   SUPABASE_JWT_SECRET=your_jwt_secret

   # Security
   JWT_SECRET=your_jwt_secret_min_32_chars
   JWT_ALGORITHM=HS256

   # CORS (Add your Vercel domain)
   CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000

   # Config
   ENVIRONMENT=production
   DEBUG=False
   HOST=0.0.0.0
   LOG_LEVEL=INFO
   ```

6. Click "Create Web Service"

---

### 3️⃣ Setup External Services

#### MongoDB Atlas (Free Tier)
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free M0 cluster
3. Create database user
4. Whitelist IP: `0.0.0.0/0` (allow all)
5. Get connection string
6. Add to backend env: `MONGODB_URI`

#### Upstash Redis (Free Tier)
1. Go to https://upstash.com
2. Create Redis database
3. Get REST URL and token
4. Add to backend env:
   - `UPSTASH_REDIS_URL`
   - `UPSTASH_REDIS_TOKEN`

#### Supabase (Free Tier)
1. Go to https://supabase.com
2. Create new project
3. Go to Settings → API
4. Copy:
   - Project URL → `NEXT_PUBLIC_SUPABASE_URL`
   - Anon public key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Service role key → `SUPABASE_SERVICE_ROLE_KEY`
   - JWT secret → `SUPABASE_JWT_SECRET`

---

## 🔗 Update Frontend with Backend URL

After deploying backend to Render, update frontend environment variables:

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update:
   ```
   NEXT_PUBLIC_API_URL=https://trading-agent-backend.onrender.com
   NEXT_PUBLIC_SOCKET_URL=https://trading-agent-backend.onrender.com
   ```
3. Redeploy frontend

---

## ✅ Verify Deployment

### Frontend (Vercel)
- Visit: `https://your-frontend.vercel.app`
- Should show homepage

### Backend (Render)
- Visit: `https://your-backend.onrender.com`
- Should return API info
- Visit: `https://your-backend.onrender.com/docs`
- Should show Swagger UI

### Health Check
- `https://your-backend.onrender.com/health`
- Should return: `{"status": "healthy"}`

---

## 🐛 Troubleshooting

### Vercel Build Fails
- Check build logs
- Verify `package.json` scripts
- Ensure all dependencies are in `package.json`

### Render Build Fails
- Check if `requirements.txt` has all dependencies
- Verify Python version is 3.11
- Check build logs for missing system dependencies

### CORS Errors
- Add your Vercel domain to `CORS_ORIGINS` in backend
- Format: `https://your-app.vercel.app`

### Environment Variables Not Working
- Restart service after adding env vars
- Check spelling and format
- No quotes needed in Render/Vercel dashboard

---

## 📊 Cost Estimate

All services have FREE tiers:
- ✅ Vercel: Free (100GB bandwidth/month)
- ✅ Render: Free (750 hours/month)
- ✅ MongoDB Atlas: Free (512MB storage)
- ✅ Upstash Redis: Free (10,000 requests/day)
- ✅ Supabase: Free (50,000 MAUs)

**Total Monthly Cost: $0** 🎉

---

## 🔄 Continuous Deployment

Both Vercel and Render auto-deploy on git push to main branch!

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Vercel and Render will auto-deploy!
```

---

## 📞 Support

- Vercel Docs: https://vercel.com/docs
- Render Docs: https://render.com/docs
- Issues: https://github.com/preet1249/AI-Trading-ML/issues
