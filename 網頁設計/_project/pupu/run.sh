#!/bin/bash
cd /Users/Shared/ccc/project/pupu

pkill -f "app.py" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

echo "Starting backend..."
python3 app.py &
BACKEND_PID=$!
sleep 2

echo "Starting frontend..."
cd web
npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo " 普普 - 普男普女社群交友網站"
echo "========================================"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "GraphQL: http://localhost:8000/graphiql"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait