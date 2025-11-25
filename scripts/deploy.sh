#!/bin/bash

# ============================================
# Deployment Script - AI Trading Predictor
# Deploys to Vercel (frontend) and Render (backend)
# ============================================

echo "🚀 Deploying AI Trading Predictor..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ============================================
# Deploy Frontend to Vercel
# ============================================

echo -e "\n${YELLOW}Deploying frontend to Vercel...${NC}"

cd frontend

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm install -g vercel
fi

# Deploy to Vercel
vercel --prod

echo -e "${GREEN}✓ Frontend deployed to Vercel${NC}"
cd ..

# ============================================
# Deploy Backend to Render
# ============================================

echo -e "\n${YELLOW}Deploying backend to Render...${NC}"
echo -e "${YELLOW}Please follow these steps manually:${NC}"
echo ""
echo "1. Push your code to GitHub"
echo "2. Go to https://render.com"
echo "3. Create a new Web Service"
echo "4. Connect your GitHub repository"
echo "5. Set the following:"
echo "   - Name: trading-agent-backend"
echo "   - Root Directory: backend"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: uvicorn app.main:socket_app --host 0.0.0.0 --port \$PORT"
echo "6. Add environment variables from backend/.env"
echo "7. Deploy!"
echo ""

# ============================================
# Database Setup
# ============================================

echo -e "\n${YELLOW}Database Setup:${NC}"
echo ""
echo "MongoDB Atlas (Free Tier):"
echo "1. Go to https://www.mongodb.com/cloud/atlas"
echo "2. Create a free M0 cluster"
echo "3. Get connection string"
echo "4. Add to backend .env: MONGODB_URI"
echo ""
echo "Upstash Redis (Free Tier):"
echo "1. Go to https://upstash.com"
echo "2. Create a Redis database"
echo "3. Get REST URL and token"
echo "4. Add to backend .env: UPSTASH_REDIS_URL and UPSTASH_REDIS_TOKEN"
echo ""

echo -e "${GREEN}✅ Deployment instructions complete!${NC}"
