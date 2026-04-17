#!/bin/bash
cd /Users/Shared/ccc/project/pupu

# Kill existing servers
pkill -f "app.py" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

echo "=== Starting servers ==="
python3 app.py > /tmp/backend.log 2>&1 &
sleep 2
cd web && npm run dev -- --host > /tmp/frontend.log 2>&1 &
sleep 3
echo "Servers started"
echo ""

echo "=== API Tests (pytest) ==="
python3 -m pytest test/test_api.py -v --tb=short

echo ""
echo "=== Browser Tests ==="
python3 test/e2e/test_browser.py "$@"

echo ""
echo "=== Tests complete ==="
pkill -f "app.py" 2>/dev/null
pkill -f "vite" 2>/dev/null