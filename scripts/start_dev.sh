#!/bin/bash
# FortifAI Development Server Startup Script

echo "=========================================="
echo "FortifAI Development Environment"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

# Start infrastructure services
echo "Starting database and cache services..."
cd infrastructure/docker
docker-compose up -d postgres redis

# Wait for services
echo "Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "Running database setup..."
cd ../../
python scripts/setup_database.py

# Start backend services in background
echo "Starting backend services..."

# API
cd backend/api
uvicorn main:app --reload --port 8000 &
API_PID=$!
echo "API started (PID: $API_PID)"

# ML Engine
cd ../ml-engine
python main.py &
ML_PID=$!
echo "ML Engine started (PID: $ML_PID)"

# Alert Service
cd ../alert-service
python main.py &
ALERT_PID=$!
echo "Alert Service started (PID: $ALERT_PID)"

cd ../../

echo ""
echo "=========================================="
echo "Services Running:"
echo "  - API:           http://localhost:8000"
echo "  - API Docs:      http://localhost:8000/docs"
echo "  - ML Engine:     http://localhost:5000"
echo "  - Alert Service: http://localhost:5001"
echo "=========================================="
echo ""
echo "To start the frontend:"
echo "  cd frontend/dashboard && npm run dev"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $API_PID $ML_PID $ALERT_PID 2>/dev/null; docker-compose -f infrastructure/docker/docker-compose.yml stop postgres redis; exit" INT
wait
