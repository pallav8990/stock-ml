#!/bin/bash

# Stock-ML Full Stack Demo Script
# This script demonstrates the complete React + FastAPI + MongoDB integration

set -e

echo "🚀 Starting Stock-ML Full Stack Demo..."
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - waiting..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start within expected time"
    return 1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking prerequisites...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# Check ports
if ! check_port 8000; then
    echo "Please stop any service running on port 8000 and try again."
    exit 1
fi

if ! check_port 3000; then
    echo "Please stop any service running on port 3000 and try again."
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}🐍 Activating Python environment...${NC}"
source .venv/bin/activate

# Check environment
echo -e "${BLUE}🔧 Environment Status:${NC}"
python manage_environments.py status

# Start MongoDB if not running (for local development)
echo -e "${BLUE}🗄️  Starting MongoDB (if needed)...${NC}"
if ! pgrep -x "mongod" > /dev/null; then
    echo "ℹ️  MongoDB not running locally. Using mock environment."
    export DEP_TYPE=mock
else
    echo "✅ MongoDB is running"
    export DEP_TYPE=prod
fi

# Run the ML pipeline to ensure we have data
echo -e "${BLUE}🤖 Running ML Pipeline...${NC}"
echo "This will take a few minutes to collect NSE data and train models..."

if python run_production_pipeline.py; then
    echo -e "${GREEN}✅ ML Pipeline completed successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Pipeline had issues, but continuing with existing data...${NC}"
fi

# Start the FastAPI backend
echo -e "${BLUE}🔄 Starting FastAPI Backend (port 8000)...${NC}"
DEP_TYPE=$DEP_TYPE nohup .venv/bin/uvicorn app.serve:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to be ready
if wait_for_service "http://localhost:8000/health" "Backend API"; then
    echo -e "${GREEN}✅ Backend API is running successfully${NC}"
else
    echo -e "${RED}❌ Backend failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start the React frontend
echo -e "${BLUE}🎨 Starting React Frontend (port 3000)...${NC}"
cd frontend

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating frontend .env file..."
    cat > .env << EOF
REACT_APP_GOOGLE_CLIENT_ID=demo_client_id
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_NAME=Stock-ML Dashboard
EOF
    echo "⚠️  Note: Update REACT_APP_GOOGLE_CLIENT_ID in frontend/.env for Google OAuth"
fi

# Start React development server
nohup npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
if wait_for_service "http://localhost:3000" "React Frontend"; then
    echo -e "${GREEN}✅ React Frontend is running successfully${NC}"
else
    echo -e "${RED}❌ Frontend failed to start${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

# Display status and URLs
echo ""
echo -e "${GREEN}🎉 Stock-ML Full Stack is now running!${NC}"
echo "======================================="
echo ""
echo -e "${BLUE}📊 Application URLs:${NC}"
echo "  🌐 React Dashboard: http://localhost:3000"
echo "  🔧 API Backend:     http://localhost:8000"
echo "  📚 API Docs:        http://localhost:8000/docs"
echo ""
echo -e "${BLUE}🔗 Quick API Tests:${NC}"
echo "  Health Check:     curl http://localhost:8000/health"
echo "  Predictions:      curl http://localhost:8000/predict_today"
echo "  Accuracy:         curl http://localhost:8000/accuracy_by_stock"
echo ""
echo -e "${BLUE}📝 Process Information:${NC}"
echo "  Backend PID:      $BACKEND_PID"
echo "  Frontend PID:     $FRONTEND_PID"
echo "  Logs:             backend.log, frontend.log"
echo ""
echo -e "${YELLOW}⚠️  Setup Notes:${NC}"
echo "  1. For Google OAuth, update REACT_APP_GOOGLE_CLIENT_ID in frontend/.env"
echo "  2. Get Google OAuth credentials from: https://console.cloud.google.com/"
echo "  3. Add http://localhost:3000 to authorized redirect URIs"
echo ""
echo -e "${BLUE}🛑 To stop the services:${NC}"
echo "  pkill -f uvicorn && pkill -f 'react-scripts start'"
echo ""

# Save PIDs for easy cleanup
echo "$BACKEND_PID" > backend.pid
echo "$FRONTEND_PID" > frontend.pid

echo -e "${GREEN}🚀 Ready to use! Open http://localhost:3000 in your browser${NC}"
echo "Press Ctrl+C to stop this demo"

# Wait for user interrupt
trap 'echo -e "\n${YELLOW}🛑 Stopping services...${NC}"; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; rm -f backend.pid frontend.pid; echo -e "${GREEN}✅ Services stopped${NC}"; exit 0' INT

# Keep script running
wait