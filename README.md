# AI Trading Prediction Model 🤖📈

A multi-agent AI system for trading predictions using LangGraph, Qwen 3, and real-time market data.

## 🚀 Features

- **Multi-Agent System**: 3 specialized agents (TA, News, Prediction) powered by LangGraph
- **Real-Time Data**: Live market data from Binance (crypto) and Twelve Data (stocks)
- **Advanced TA**: ICT/SMC methodology (CHOCH, BOS, Order Blocks, Liquidity, S/D Zones)
- **Live Charts**: TradingView integration with auto-drawn zones and indicators
- **Secure Auth**: Supabase authentication with JWT and MFA
- **Scalable**: Docker + Redis + MongoDB architecture

## 📦 Tech Stack

### Frontend
- **Next.js** (App Router) - React framework
- **TypeScript** - Type safety
- **TradingView** - Chart visualization
- **Socket.io Client** - Real-time updates
- **Supabase JS** - Authentication

### Backend
- **Python 3.11+** - Core language
- **FastAPI** - API framework
- **LangGraph** - Agent orchestration
- **Qwen 3** (via OpenRouter) - AI model
- **Socket.io** - WebSocket server
- **TA-Lib** - Technical analysis

### Infrastructure
- **MongoDB** - Data caching
- **Upstash Redis** - Rate limiting & sessions
- **Supabase** - Auth & user management
- **Docker** - Containerization
- **Vercel** - Frontend deployment
- **Render** - Backend deployment

## 🛠️ Setup Instructions

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Git

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd "Trading agent (ML)"
```

### 2. Environment Setup

#### Root Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

#### Frontend Environment
```bash
cd frontend
cp .env.local.example .env.local
# Add Supabase and API URLs
cd ..
```

#### Backend Environment
```bash
cd backend
cp .env.example .env
# Add API keys and database URLs
cd ..
```

### 3. Install Dependencies

#### Frontend
```bash
cd frontend
npm install
# or
pnpm install
cd ..
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
# or
poetry install
cd ..
```

### 4. Run with Docker (Recommended)
```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 5. Run Locally (Development)

#### Terminal 1 - Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

#### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

## 📚 API Keys Setup

### Required APIs (All Free Tier)

1. **OpenRouter** (Qwen 3)
   - Sign up: https://openrouter.ai/
   - Get API key from dashboard

2. **Twelve Data** (Stock Market)
   - Sign up: https://twelvedata.com/
   - Free: 800 calls/day + 8 WebSocket connections

3. **Supabase** (Auth)
   - Create project: https://supabase.com/
   - Get URL and anon key from settings

4. **Upstash Redis** (Free)
   - Sign up: https://upstash.com/
   - Create Redis database, copy URL & token

5. **Google Custom Search** (News)
   - Enable API: https://console.cloud.google.com/
   - Create search engine: https://cse.google.com/

6. **MongoDB** (Optional - use Atlas free tier)
   - Sign up: https://www.mongodb.com/cloud/atlas
   - Create free M0 cluster

## 📁 Project Structure

```
trading-agent-ml/
├── frontend/          # Next.js application
│   ├── src/
│   │   ├── app/       # App Router pages
│   │   ├── components/# React components
│   │   ├── lib/       # Utilities & clients
│   │   └── types/     # TypeScript types
│   └── public/        # Static assets
├── backend/           # Python FastAPI application
│   ├── app/
│   │   ├── agents/    # LangGraph agents
│   │   ├── api/       # API routes
│   │   ├── core/      # TA calculations
│   │   ├── services/  # External services
│   │   └── models/    # Data models
│   └── tests/         # Unit tests
└── scripts/           # Deployment scripts
```

## 🚢 Deployment

### Frontend (Vercel)
1. Push to GitHub
2. Import project in Vercel
3. Set root directory: `frontend`
4. Add environment variables
5. Deploy

### Backend (Render)
1. Create new Web Service
2. Set root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables
6. Deploy

## 🔒 Security

- All API keys in `.env` (never committed)
- Supabase JWT authentication
- Rate limiting (10 req/min per user)
- CORS protection
- Input validation with Pydantic
- HTTPS only in production

## 📖 Usage

1. **Login**: Create account via Supabase auth
2. **Select Market**: Choose crypto (Binance) or stock (Twelve Data)
3. **Chat Query**: "Predict next move for BTC"
4. **View Results**: See prediction + live chart with zones drawn
5. **Follow Up**: Ask clarification questions

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push and create PR

## 📄 License

MIT License

## 🆘 Support

- Documentation: See `/docs` folder
- Issues: GitHub Issues
- Contact: your-email@example.com

---

Built with ❤️ using LangGraph, Qwen 3, and Next.js
