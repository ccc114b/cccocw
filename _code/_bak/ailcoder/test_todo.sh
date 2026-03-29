#!/bin/bash
# Test ailcoder - 使用 .ail 檔案

cd "$(dirname "$0")"

echo "========================================"
echo "  ailcoder Test - TODO App"
echo "========================================"

# 清理舊檔案
rm -rf generated/*

# 執行 ailcoder
echo ""
echo "建立 SQLite TODO 應用..."
PYTHONPATH=src ailcoder ail/todo.ail -o ./generated -d

echo ""
echo "========================================"
echo "  生成的檔案"
echo "========================================"
ls -la generated/
ls -la generated/templates/ 2>/dev/null || echo "(templates 目錄不存在)"

echo ""
echo "========================================"
echo "  啟動伺服器 (Ctrl+C 停止)"
echo "========================================"
cd generated
lsof -ti :5000 | xargs kill -9 2>/dev/null
python3 backend.py 2>&1 &

sleep 2
echo "測試 API..."
curl -s http://localhost:5000/api/todos || echo "API 測試失敗"
