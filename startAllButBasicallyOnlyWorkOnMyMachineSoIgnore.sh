#!/bin/bash

# 3DPMP Development Environment Startup Script
# This script starts all services needed for local development

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   3DPMP Development Environment${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    # Kill background processes
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$CELERY_PID" ]; then
        echo -e "${YELLOW}Stopping Celery worker (PID: $CELERY_PID)...${NC}"
        kill $CELERY_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo -e "${GREEN}Cleanup complete. Goodbye!${NC}"
    exit 0
}

# Trap Ctrl+C and other termination signals
trap cleanup SIGINT SIGTERM

# Step 1: Start db and redis containers
echo -e "\n${GREEN}[1/5] Starting database and Redis containers...${NC}"
cd "$SCRIPT_DIR"
podman-compose up -d db redis

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for containers to be healthy...${NC}"
sleep 3

# Check if containers are running
if podman ps | grep -q "3dprint_db_1\|3dprint-db-1"; then
    echo -e "${GREEN}  ✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}  ✗ PostgreSQL failed to start${NC}"
    exit 1
fi

if podman ps | grep -q "3dprint_redis_1\|3dprint-redis-1"; then
    echo -e "${GREEN}  ✓ Redis is running${NC}"
else
    echo -e "${RED}  ✗ Redis failed to start${NC}"
    exit 1
fi

# Step 2: Source backend environment variables
echo -e "\n${GREEN}[2/5] Loading backend environment variables...${NC}"
if [ -f "$SCRIPT_DIR/backend/.envrc" ]; then
    source "$SCRIPT_DIR/backend/.envrc"
    echo -e "${GREEN}  ✓ Environment variables loaded from backend/.envrc${NC}"
else
    echo -e "${RED}  ✗ backend/.envrc not found${NC}"
    exit 1
fi

# Step 3: Activate virtual environment and start backend
echo -e "\n${GREEN}[3/5] Starting backend server...${NC}"
if [ -d "$SCRIPT_DIR/.venv" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
    echo -e "${GREEN}  ✓ Virtual environment activated${NC}"
else
    echo -e "${RED}  ✗ Virtual environment not found at .venv${NC}"
    exit 1
fi

cd "$SCRIPT_DIR/backend"
python manage.py runserver &
BACKEND_PID=$!
echo -e "${GREEN}  ✓ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}    → Backend URL: http://localhost:8000${NC}"

# Give backend a moment to start
sleep 2

# Step 4: Start Celery worker for async tasks (slicing, etc.)
echo -e "\n${GREEN}[4/5] Starting Celery worker...${NC}"
cd "$SCRIPT_DIR/backend"
celery -A config worker -l INFO &
CELERY_PID=$!
echo -e "${GREEN}  ✓ Celery worker started (PID: $CELERY_PID)${NC}"

# Give Celery a moment to start
sleep 1

# Step 5: Start frontend development server
echo -e "\n${GREEN}[5/5] Starting frontend development server...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}  ✓ Frontend started (PID: $FRONTEND_PID)${NC}"
echo -e "${BLUE}    → Frontend URL: http://localhost:5173${NC}"

# Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}All services are running!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "  ${BLUE}PostgreSQL:${NC}    localhost:5433"
echo -e "  ${BLUE}Redis:${NC}         localhost:6379"
echo -e "  ${BLUE}Backend:${NC}       http://localhost:8000"
echo -e "  ${BLUE}Celery Worker:${NC} Processing async tasks"
echo -e "  ${BLUE}Frontend:${NC}      http://localhost:5173"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"

# Wait for processes to complete (or until interrupted)
wait

