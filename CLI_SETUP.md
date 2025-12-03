# AI Trading CLI - Simple Setup Guide

Easy command-line interface to chat with your AI trading model!

## 🚀 One-Time Setup

Install CLI dependencies (only needed once):

```bash
pip install -r requirements_cli.txt
```

## 📖 How to Use (Every Time)

### Step 1: Start Backend Server

Open **Windows CMD** and run:

```bash
start_backend.bat
```

This will:
- Start the FastAPI backend on http://localhost:8000
- Keep this window open (don't close it!)

### Step 2: Run CLI Client

Open **another CMD window** and run:

```bash
start_cli.bat
```

This will:
- Ask for password: `Preet@1246`
- Connect to the backend
- Let you chat with the AI!

### Step 3: Chat with AI

Just type your trading questions:

```
You: Bitcoin prediction for next 4 hours
🤖 AI is thinking...

AI Response:
[AI's detailed analysis and prediction]

You: What about Tesla stock?
```

Type `exit` or `quit` to stop.

## 🎯 Quick Commands

| Command | Description |
|---------|-------------|
| `start_backend.bat` | Start backend server (CMD 1) |
| `start_cli.bat` | Run CLI client (CMD 2) |
| `exit` or `quit` | Stop CLI client |
| `Ctrl+C` | Stop backend server |

## 💡 Example Session

```
========================================
    AI TRADING PREDICTION MODEL - CLI
========================================

Enter password to start: Preet@1246
✅ Access granted!

✅ Backend is running on http://localhost:8000

Ready to chat! Type your trading questions below.
Commands: 'exit', 'quit', or Ctrl+C to stop

You: BTC scalping strategy for 15 minute timeframe
🤖 AI is thinking...

AI Response:
[Detailed AI analysis with technical indicators, entry/exit points, etc.]

You: exit

Goodbye! Happy trading! 📈
```

## 🔧 Troubleshooting

**Backend not running?**
- Make sure you ran `start_backend.bat` first
- Check if port 8000 is free: `netstat -ano | findstr :8000`

**Module not found?**
- Install CLI dependencies: `pip install -r requirements_cli.txt`

**Password wrong?**
- Use: `Preet@1246` (case-sensitive)

## 📝 Notes

- No authentication/database needed - just direct AI chat
- Backend must be running for CLI to work
- Each session is independent (no chat history)
- Perfect for quick trading analysis without opening IDE!

## 🎨 Features

✅ Simple password protection
✅ Colorful CLI output
✅ Real-time AI predictions
✅ Works with crypto and stocks
✅ No JWT/database complexity
✅ Pure Windows CMD compatible
