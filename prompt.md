Trading prediction Model by AI agents (qwen3 from openrouter)

1. High-Level Architecture
Bird's-eye: User chats in Next.js dashboard → Triggers LangGraph workflow (3 agents: TA → News → Predict) → Qwen 3 powers each → Outputs stream back via WebSockets for live chart updates (e.g., trend lines, zones drawn). Data flows real-time from WS sources. No trades—just predictions with visuals.
Key Components:

Frontend (Next.js): Chat UI + TradingView embed (for drawing zones/lines).
Backend (Python/FastAPI): API gateways, LangGraph supervisor, WebSocket server (Socket.io).
Agents (LangGraph): Stateful graph: TA Agent (calcs/TA), News Agent (Google search), Predict Agent (synthesis via Qwen).
Data Sources: Binance WS (crypto), Finnhub WS (USA/Indian stocks—free tier, real-time quotes/candles; sign up for key).
Storage: Supabase (user auth/sessions, realtime subs), MongoDB (cache TA results, news snippets).
AI: OpenRouter Qwen 3 for all agents (prompt-engineered per role).
Real-Time: Socket.io broadcasts: taUpdate (e.g., {rsi: 65, zones: [...]}) → FE draws on chart.

High-Level Diagram (Mermaid: Overview):
mermaidgraph TD
    A[User: Next.js Chat] -->|Msg: "Predict BTC"| B[FastAPI: Trigger LangGraph]
    B --> C[LangGraph Supervisor]
    C --> D[Agent 1: TA - Fetch WS Data + Calcs]
    D --> E[Binance/Finnhub WS: Real-Time Candles]
    D --> F[MongoDB: Cache TA Outputs]
    C --> G[Agent 2: News - Google Search API]
    G --> H[SerpAPI: Recent News <2 Days]
    C --> I[Agent 3: Predict - Qwen Synthesis]
    I --> D
    I --> G
    I --> J[Qwen 3: Final Pred]
    J --> B
    B -->|Socket.io| A
    A -->|Draw API| K[TradingView: Zones/Lines Visuals]
    Supabase[Supabase: Auth + Sessions] --> B
    style I fill:#f9f
Pro Tip: LangGraph's graph runs async—<5s end-to-end. Cache in Mongo to avoid re-fetching on retries.

2. Low-Level System Design
Zooming in: Modules, formulas, fetches, error-proofing. Agents compute in Python (using TA-Lib for basics, custom funcs for ICT/SMC—Qwen verifies/expands).
Data Fetching (Real-Time via WebSockets)

Crypto (Binance): Use python-binance lib. Connect to wss://stream.binance.com:9443/ws/btcusdt@kline_1m (multi-TF: 15m/1h/4h/1d streams). Buffer last 200 candles per TF in Redis (add if scaling; else in-memory dict).
On tick: Parse {k: {t: ts, o: open, h: high, l: low, c: close, v: vol}} → Store closes/highs/lows for TA.

USA Stocks (e.g., AAPL): Twelve Data → Subscribe /stock:candle?symbol=AAPL&resolution=1 (1min candles). Free tier: 8 calls/min, real-time.
Indian Stocks (e.g., RELIANCE): Same Twelve data WS—supports NSE symbols REST API Side (The 800 Calls): This is for grabbing historical or on-demand chunks—like loading those first 200 candles for each TF (1m/15m etc.) when a query kicks off. Each fetch? 1 call per TF (so 5 for multi-TF). You could blast 800 of these a day if you're testing wild, but in our setup, it's smart and sparse—maybe 5-10 per full pred. Agent 1 receives 'em instantly (sub-second on a good net), crunches, and passes to Qwen. No lag, just quota watch.
Real-Time Magic (WebSockets): This is the hero for your live vibes—once loaded, the WS streams endless ticks/prices without touching your 800-call quota (it's that "8 trial WS" perk: Up to 8 connections for symbols/streams, quota-free flow). Agent 1 taps in, gets pushes every tick (e.g., new 1m close), updates calcs on the fly (RSI refresh, swing detects), and feeds the graph. Super smooth—your preds stay fresh as a daisy, no polling nonsense.
Why Twelve Data? Best free real-time per my quick scout (WebSockets, global coverage, JSON easy). Sign up: Twelve Data—key in env vars.

Error Handling: Reconnect on disconnect (exponential backoff via websocket-client). Fallback: Poll REST every 1min. Validate data (e.g., no NaNs).

Calculations & Formulas (In Agent 1)
All in Python—use NumPy/Pandas for speed, TA-Lib for RSI/MACD/EMA. For ICT/SMC: Custom logic (swing detection via argrelextrema), then Qwen refines via prompt. Outputs JSON: {rsi: 65, macd: {line:120, hist:10}, ema20:68000, swings: [{high:68200, ts:ts}], choch: 'bullish', liquidity: [67500], obs: [{type:'demand', price:67800}], trend: 'bullish'}.

RSI (14-period): Measures overbought/oversold.Pythonimport talib
rsi = talib.RSI(np.array(closes), timeperiod=14)[-1]  # Last valueFormula: RS = (Avg Gain over 14) / (Avg Loss over 14); RSI = 100 - (100 / (1 + RS)). Gains/Losses: |close - prev| signed.
MACD (12/26/9): Momentum oscillator.Pythonmacd_line, signal, hist = talib.MACD(np.array(closes), fast=12, slow=26, signal=9)
latest = {'line': macd_line[-1], 'signal': signal[-1], 'hist': hist[-1]}Formula: MACD Line = EMA(closes,12) - EMA(closes,26); Signal = EMA(MACD,9); Hist = Line - Signal.
EMA(N): α = 2/(N+1); EMA_t = (close_t * α) + (EMA_{t-1} * (1-α)).
EMA (20-period): Smoothed trend.Pythonema20 = talib.EMA(np.array(closes), timeperiod=20)[-1]
Real-Time Swings (Highs/Lows): Detect peaks/troughs for structure.Pythonfrom scipy.signal import argrelextrema
highs_idx = argrelextrema(highs, np.greater, order=5)[0]  # Last 5 candles
swings = [{'type': 'high' if highs[i] else 'low', 'price': highs[i] or lows[i], 'ts': ts[i]} for i in highs_idx[-10:]]  # Last 10Real-time: Update on new candle; confirm after 2-3 bars.
Internal CHOCH & BOS (Market Structure - ICT/SMC):
BOS: Break of Structure—new swing high > prev swing high (bull) or low < prev low (bear) in trend direction.
Internal CHOCH: Change of Character—break against trend (e.g., bull trend breaks below internal low).
Pythondef detect_structure(swings):
    trend = 'bull' if swings[-1]['price'] > swings[-2]['price'] else 'bear'
    prev_high = max(s['price'] for s in swings if s['type']=='high' and s['ts']<swings[-1]['ts'])
    if highs[-1] > prev_high: return {'bos': 'bullish'}
    # CHOCH: If trend=='bull' and lows[-1] < min internal low...
    return {'choch': 'internal_bearish' if condition else None}Qwen Prompt: "From swings [json], confirm BOS/CHOCH: Bull BOS if new HH, etc."
Liquidity Identification: Pools beyond swings (e.g., equal highs/lows for stops).Pythonliquidity = [p for p in highs[-20:] if abs(p - highs[-21]) < 0.1% * p]  # Equal highs
Order Blocks (OBs): Last bearish candle before bullish impulse (demand OB).Python# Scan for strong move: If closes[i+1:] > opens[i+1:] * 1.5% after bear candle
obs = [{'type': 'demand' if bearish else 'supply', 'price': (high[i]+low[i])/2, 'ts': ts[i]}]
Supply/Demand Zones: Consolidation (range < ATR) before breakout.Pythonatr = talib.ATR(highs, lows, closes, 14)[-1]
zones = []  # If range(highs[-10:]-lows[-10:]) < 0.5*atr, mark as S/D
Market Trends/Structure: HH/HL (bull), LH/LL (bear). Use swings: If last two highs > prev, bullish.

All feed predictions: E.g., Bull trend + BOS + Demand OB hit + RSI>50 = Strong buy signal.

News Integration: Agent 2 uses SerpAPI (Google wrapper—$50/mo free tier? Nah, free alt: Google Custom Search JSON API, free 100/day). Query: site:news.google.com {symbol} after:{today-2} → Filter snippets <2 days → JSON to Agent 3.
Error Handling: Try/except on calcs (e.g., insufficient data → "Need 50+ candles"). Retries: 3x for WS/API. Logging: Structlog to console/DB.

Low-Level Diagram (Mermaid: Agent 1 TA Flow):
mermaidsequenceDiagram
    participant Lang as LangGraph
    participant TA as Agent 1 (Qwen TA)
    participant WS as Finnhub/Binance
    participant Calc as Python Calcs
    Lang->>WS: Subscribe Multi-TF Candles
    WS-->>Lang: Real-Time OHLCV
    Lang->>TA: Prompt: "Calc RSI/MACD/EMA on [closes]; Detect swings/CHOCH/BOS/liquidity/OBs/S D/zones/trend w/ formulas"
    TA->>Calc: Invoke TA-Lib/Custom Funcs
    Calc-->>TA: JSON Outputs
    TA-->>Lang: TA_Data {rsi:.., zones:..}
3 Agents via LangGraph
LangGraph (from LangChain): Builds graphs of nodes (agents) + edges (conditional routing). Each agent: Qwen 3 tool-caller (via OpenRouter). State: Shared dict {user_query, ta_data, news_data, pred}. Run on trigger.

Infuse Your TA Knowledge into Agent 1: System prompt in LangGraph node—paste your rules: "You are my TA mentor. Always use ICT/SMC: Prioritize BOS over internal CHOCH in trends. Liquidity = equal highs/lows beyond 1% wick. OBs: Mitigate only if retested. For ranging: Focus S/D zones. Output JSON only." Chain-of-thought: "Step1: Trend? Step2: Structure breaks? etc." Test/refine prompts iteratively—your "how I do it" becomes the prompt bible.
Situational Smarts: Router node in graph: Based on query/state.
Trending (e.g., |slope(EMA)| > 0.5%): Agent 1 emphasizes BOS/CHOCH, liquidity sweeps.
Ranging (low ATR): S/D zones, OBs for reversals.
Volatile (high VIX/news): Weight news heavier in Agent 3.
E.g., If ta_data['trend']=='sideways', route to deeper zone scan.


Agent Workflows:

TA Agent (Node: ta_node): Input: Query/symbol. Fetch WS data → Calcs (as above) → Qwen: "Analyze [data] w/ my rules: RSI/MACD/EMA + swings/CHOCH/BOS/liquidity/OBs/S D/trend. JSON: {indicators, structure}." Output: ta_data JSON. Situational: If volatile (std(closes)>2%), add Vol profile.
News Agent (Node: news_node): Input: Symbol. SerpAPI call: query=f"{symbol} stock news after:{date-2days}" → Parse titles/snippets → Qwen: "Summarize sentiment: Bull/bear/neutral from [snippets]." Output: news_data {sentiment:0.7, key_events:['Fed rate cut']}. Limit: 10 results.
Predict Agent (Node: predict_node): Input: ta_data + news_data. Qwen: "Synthesize: From TA [json] + News [json], predict next 15min-1h move for {symbol}: UP/DOWN/SIDEWAYS, target, conf (0-100%), why (cite confluences). Very accurate—align TFs." Output: Final pred text/JSON.

LangGraph Setup Snippet (Python):
Pythonfrom langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI  # Adapt for Qwen via OpenRouter

llm = ChatOpenAI(model="qwen/qwen-3", api_key=...)  # Your setup

class State(TypedDict):  # Shared
    query: str
    symbol: str
    ta_data: dict
    news_data: dict
    pred: str

def ta_node(state):  # Fetch + calc + Qwen
    # WS fetch, calcs, prompt
    return {"ta_data": ta_json}

def route(state):  # Situational
    if state['ta_data']['atr'] < threshold: return "deep_zones"
    return "standard"

graph = StateGraph(State)
graph.add_node("ta", ta_node)
graph.add_node("news", news_node)
graph.add_node("predict", predict_node)
graph.add_conditional_edges("ta", route, {"standard": "news", "deep_zones": "zones_subnode"})  # Example
graph.add_edge("news", "predict")
graph.add_edge("predict", END)
app = graph.compile()
# Trigger: result = app.invoke({"query": "Predict AAPL", "symbol": "AAPL"})

Integration: FastAPI endpoint /predict: result = app.invoke(...) → Socket.io emit prediction: {text: pred, visuals: {draw_zones: [...]}}.
Errors: LangGraph retries on tool fails. If news dry, fallback neutral sentiment.

Agent Graph Diagram (Mermaid):
mermaidgraph LR
    Start[User Query] --> Supervisor[LangGraph Supervisor]
    Supervisor --> TA[Agent 1: TA Calcs + Structure]
    TA --> Router[Route: Trending? Volatile?]
    Router -->|Standard| News[Agent 2: Google News <2d]
    Router -->|Ranging| Zones[Sub: Deep S/D Scan]
    Zones --> News
    News --> Predict[Agent 3: Qwen Synthesis]
    Predict --> End[Pred + Draw]
    TA -.-> Predict
    News -.-> Predict

3. User Workflow
Intuitive, chat-driven—like texting your quant buddy.

Load Dashboard: Next.js page → Auth w/ Supabase → Default chart (BTC or pick symbol).
Query: Chat: "Predict next move for RELIANCE.NS" → Spinner: "Fetching live data..."
Backend Triggers: LangGraph runs (agents in parallel where possible) → ~3-5s.
Response Streams: Socket.io: First taUpdate (e.g., "RSI 72—overbought; Bull BOS confirmed") + draws trend lines/zones on TradingView.
Full Pred: "UP to ₹3050 (85% conf)—HH trend + demand OB at ₹2980 + positive earnings news. Watch liquidity sweep low."
Visuals: Auto-draw: Green trendline (bull structure), shaded S/D zones, red liquidity pools.
Follow-Up: "Why CHOCH?" → Re-run partial graph (TA focus).

Quick Table:

StepUser ActionSystem ResponseReal-Time VisualQuery"Predict AAPL"Agents fireChart zooms to zonesTAAuto"EMA support @$220"Draw EMA lineNewsAuto"Sentiment: Bullish (Fed news)"News ticker in chatPredAutoFull analysis + callHighlight target price

4. Backend/System Workflow

On Startup: FastAPI → Connect WS clients → Init LangGraph → Supabase realtime sub for user sessions.
Main Loop: /chat POST → Parse symbol → Invoke graph → Parse outputs → Mongo insert (for history) → Socket broadcast.
WebSockets (Socket.io): Server: On connect, join room (userId). Events: livePrice (WS tick → update chart), agentUpdate (partial results), draw (e.g., {type: 'zone', coords: [2980,3050]} → FE: TradingView createShape).
Smoothness: Throttle to 1Hz; compress JSON.

Full System Flow: User msg → Auth check (Supabase) → Graph → Qwen calls → Calcs/TA → News fetch → Synth → Cache Mongo → Emit Socket → FE renders/draws.
Scaling/Errors: Docker multi-container (agents in separate service?). Supabase for low-latency auth; Mongo for heavy caches. Alerts: If Qwen latency >10s, queue w/ asyncio.

Backend Workflow Diagram (Mermaid):
mermaidsequenceDiagram
    U[User] ->> F[Next.js]: POST /chat {query:"Predict BTC"}
    F ->> B[FastAPI]: Invoke LangGraph
    B ->> TA: Agent 1 - WS Fetch + Calcs
    Note over TA: RSI=100-100/(1+RS); MACD=EMA12-EMA26; Swings=argrelextrema; BOS=new HH in bull
    TA -->> B: ta_data JSON
    B ->> News: Agent 2 - SerpAPI "BTC news after:2025-11-23"
    News -->> B: news_data {bullish:0.8}
    B ->> Predict: Agent 3 - Qwen: "Synth [ta][news] → Pred JSON"
    Predict -->> B: {up: true, target:70000, conf:90}
    B ->> M[Mongo]: Cache Results
    B ->> F: Socket: prediction + draw{zones, lines}
    F ->> TV[TradingView]: Draw OB/S D/Liquidity
    U -->> F: See Live Pred + Visuals

5. Deployment & Everything Else

Docker Compose (docker-compose.yml):YAMLservices:
  frontend:
    build: ./nextjs
    ports: ["3000:3000"]
    depends_on: [backend]
  backend:
    build: ./python
    ports: ["8000:8000"]
    environment:
      FINNHUB_KEY: yourkey
      OPENROUTER_KEY: yourkey
      SERPAPI_KEY: yourkey  # For news
    depends_on: [mongo, supabase]
  mongo:
    image: mongo:latest
    ports: ["27017:27017"]
  supabase:  # Or self-host CLI
    image: supabase/postgres  # Full stack via docker-compose from docsRun: docker-compose up—env vars in .env.

    Make it scalable

