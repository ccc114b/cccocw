#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Testing agent0.py to create a blog system ==="
echo ""

rm -rf blog2

echo "Creating blog... (15 sec)"
echo -e "Create a Node.js blog in blog2/\nCreate app.js and views/index.ejs\n/quit" | python3 agent0.py 2>&1 &
PID=$!
sleep 15
if ps -p $PID > /dev/null 2>&1; then
    kill $PID 2>/dev/null || true
fi
wait 2>/dev/null || true

echo ""
echo "=== Files created ==="
find blog2 -type f 2>/dev/null | head -10 || echo "No blog2"

echo ""
echo "=== Tests completed ==="