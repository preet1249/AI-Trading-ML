# 📁 Project Structure

Complete file structure for AI Trading Prediction Model

## 📊 Overview

```
trading-agent-ml/
├── frontend/              # Next.js frontend application
├── backend/               # Python FastAPI backend
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker orchestration
├── .env.example           # Environment template
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation
```

## 🎨 Frontend Structure (Next.js)

```
frontend/
├── .next/                 # Next.js build output (auto-generated)
├── node_modules/          # Dependencies (auto-generated)
├── public/                # Static assets
│   └── assets/           # Images, icons, etc.
├── src/
│   ├── app/              # Next.js 14 App Router
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   ├── auth/         # Authentication pages
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── dashboard/    # Main dashboard
│   │   └── api/          # API routes (optional)
│   ├── components/       # React components
│   │   ├── ui/           # Reusable UI components
│   │   ├── charts/       # TradingView & chart components
│   │   ├── chat/         # Chat interface
│   │   └── layout/       # Layout components (header, sidebar)
│   ├── lib/              # Utilities & clients
│   │   ├── supabase.ts   # Supabase client
│   │   ├── socket.ts     # Socket.io client
│   │   └── utils.ts      # Helper functions
│   ├── hooks/            # Custom React hooks
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts      # All types (User, Prediction, etc.)
│   └── styles/           # Global styles
│       └── globals.css   # Tailwind CSS
├── .env.local            # Environment variables (DO NOT COMMIT)
├── .env.local.example    # Environment template
├── .gitignore            # Frontend gitignore
├── .eslintrc.json        # ESLint config
├── .dockerignore         # Docker ignore
├── Dockerfile            # Docker build
├── next.config.js        # Next.js configuration
├── package.json          # Dependencies & scripts
├── postcss.config.js     # PostCSS config
├── tailwind.config.js    # Tailwind CSS config
└── tsconfig.json         # TypeScript config
```

## 🐍 Backend Structure (Python/FastAPI)

```
backend/
├── __pycache__/          # Python bytecode (auto-generated)
├── venv/                 # Virtual environment (auto-generated)
├── app/                  # Main application
│   ├── __init__.py
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Configuration & settings
│   │
│   ├── api/              # API layer
│   │   ├── __init__.py
│   │   ├── routes/       # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── predictions.py  # Prediction endpoints
│   │   │   └── health.py       # Health check
│   │   └── middleware/   # Middleware
│   │       ├── __init__.py
│   │       ├── auth.py         # JWT authentication
│   │       └── rate_limit.py   # Rate limiting
│   │
│   ├── agents/           # LangGraph agents
│   │   ├── __init__.py
│   │   ├── graph.py            # LangGraph setup
│   │   ├── ta_agent.py         # Technical Analysis agent
│   │   ├── news_agent.py       # News sentiment agent
│   │   └── predict_agent.py    # Prediction synthesis agent
│   │
│   ├── core/             # Core business logic
│   │   ├── __init__.py
│   │   ├── indicators.py       # TA-Lib indicators (RSI, MACD, EMA)
│   │   ├── market_structure.py # ICT/SMC logic (swings, CHOCH, BOS)
│   │   └── data_fetcher.py     # WebSocket data handlers
│   │
│   ├── services/         # External services
│   │   ├── __init__.py
│   │   ├── websocket.py        # Socket.io server
│   │   ├── binance.py          # Binance WebSocket
│   │   ├── twelve_data.py      # Twelve Data API
│   │   └── news.py             # News API (Google Search)
│   │
│   ├── models/           # Data models
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic models
│   │   └── database.py         # MongoDB & Redis clients
│   │
│   └── utils/            # Utilities
│       ├── __init__.py
│       ├── logger.py           # Structured logging
│       └── helpers.py          # Helper functions
│
├── tests/                # Unit tests
│   ├── __init__.py
│   ├── test_api.py
│   └── test_agents.py
│
├── .env                  # Environment variables (DO NOT COMMIT)
├── .env.example          # Environment template
├── .gitignore            # Backend gitignore
├── .dockerignore         # Docker ignore
├── Dockerfile            # Docker build
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Poetry config (optional)
```

## 🛠️ Scripts

```
scripts/
├── setup.sh              # Development setup script
└── deploy.sh             # Deployment script
```

## 🐳 Docker Files

```
├── docker-compose.yml    # Multi-container orchestration
├── frontend/Dockerfile   # Frontend container
└── backend/Dockerfile    # Backend container
```

## 📝 Configuration Files

```
Root:
├── .env.example          # Root environment template
├── .gitignore            # Root gitignore
├── README.md             # Project documentation
└── PROJECT_STRUCTURE.md  # This file
```

## 🔑 Key Files Explained

### Frontend Key Files

- **`src/app/layout.tsx`** - Root layout with fonts, metadata
- **`src/app/page.tsx`** - Home page
- **`src/lib/supabase.ts`** - Supabase authentication client
- **`src/lib/socket.ts`** - Socket.io client for real-time updates
- **`src/types/index.ts`** - TypeScript type definitions
- **`next.config.js`** - Next.js configuration (images, headers, etc.)
- **`tailwind.config.js`** - Tailwind CSS theme configuration

### Backend Key Files

- **`app/main.py`** - FastAPI application entry point
- **`app/config.py`** - Environment variables & settings
- **`app/agents/graph.py`** - LangGraph agent orchestration
- **`app/core/indicators.py`** - Technical analysis calculations
- **`app/core/market_structure.py`** - ICT/SMC methodology
- **`app/services/websocket.py`** - Socket.io server
- **`app/models/schemas.py`** - Pydantic data models
- **`app/models/database.py`** - MongoDB & Redis connections

## 🚫 What NOT to Commit

**Never commit these files/folders:**
- `.env`, `.env.local`, `.env.*` (except `.example` files)
- `node_modules/`, `__pycache__/`, `venv/`, `.venv/`
- `.next/`, `build/`, `dist/`
- API keys, secrets, credentials
- Database files (`.db`, `.sqlite`)
- Log files (`*.log`)

All sensitive files are already in `.gitignore` files.

## 📦 Generated Folders (Auto-created)

These folders are created automatically and should NOT be committed:
- `frontend/node_modules/` - NPM dependencies
- `frontend/.next/` - Next.js build cache
- `backend/__pycache__/` - Python bytecode
- `backend/venv/` or `backend/.venv/` - Python virtual environment

## 🔄 Workflow

1. **Development:**
   - Edit files in `frontend/src/` and `backend/app/`
   - Use environment variables from `.env.local` (frontend) and `.env` (backend)

2. **Testing:**
   - Run tests in `backend/tests/`
   - Test API endpoints via `/docs` (Swagger UI)

3. **Deployment:**
   - Frontend → Vercel (from `frontend/` folder)
   - Backend → Render (from `backend/` folder)
   - Databases → MongoDB Atlas + Upstash Redis

## 🎯 Next Steps

1. Fill in API keys in `.env` files
2. Install dependencies (see `README.md`)
3. Start development servers or Docker
4. Begin implementing agents and features

---

**Security Note:** Always keep `.env` files secure and NEVER commit them to Git. The `.gitignore` files are configured to prevent this, but double-check before pushing!
