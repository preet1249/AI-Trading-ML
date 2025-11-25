#!/bin/bash

# ============================================
# Setup Script - AI Trading Predictor
# Initializes development environment
# ============================================

echo "🚀 Setting up AI Trading Predictor..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ============================================
# Check Prerequisites
# ============================================

echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $(python3 --version)${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker is not installed (optional for development)${NC}"
else
    echo -e "${GREEN}✓ Docker $(docker --version)${NC}"
fi

# ============================================
# Setup Environment Files
# ============================================

echo -e "\n${YELLOW}Setting up environment files...${NC}"

# Root .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created root .env${NC}"
else
    echo -e "${YELLOW}⚠ Root .env already exists${NC}"
fi

# Frontend .env.local
if [ ! -f "frontend/.env.local" ]; then
    cp frontend/.env.local.example frontend/.env.local
    echo -e "${GREEN}✓ Created frontend/.env.local${NC}"
else
    echo -e "${YELLOW}⚠ frontend/.env.local already exists${NC}"
fi

# Backend .env
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✓ Created backend/.env${NC}"
else
    echo -e "${YELLOW}⚠ backend/.env already exists${NC}"
fi

echo -e "${YELLOW}⚠ Remember to fill in your API keys in the .env files!${NC}"

# ============================================
# Install Dependencies
# ============================================

echo -e "\n${YELLOW}Installing dependencies...${NC}"

# Frontend dependencies
echo -e "${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
cd ..

# Backend dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
cd backend
python3 -m pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
cd ..

# ============================================
# Done
# ============================================

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Fill in API keys in .env files"
echo "2. Start MongoDB and Redis (or use Docker)"
echo "3. Run 'npm run dev' in frontend/"
echo "4. Run 'uvicorn app.main:app --reload' in backend/"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
