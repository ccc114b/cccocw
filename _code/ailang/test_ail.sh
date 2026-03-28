#!/bin/bash
# Test AIL MiniCode - 建立 SQLite TODO 應用

cd "$(dirname "$0")"

echo "========================================"
echo "  AIL MiniCode Test - TODO App"
echo "========================================"

# 清理舊檔案
rm -rf generated/*

# 執行 MiniCode
echo ""
echo "建立 SQLite TODO 應用..."
PYTHONPATH=src python3 -c "
import asyncio
from minicode_ail import MiniCode, init_ollama

init_ollama(model='minimax-m2.5:cloud')

async def main():
    agent = MiniCode(root_dir='./generated')
    await agent.run('''建立 SQLite TODO 應用：
1. backend.py - Flask 後端，首頁 /
2. templates/index.html - 前端
功能：新增、刪除、標記完成''')

asyncio.run(main())
"

echo ""
echo "========================================"
echo "  生成的檔案"
echo "========================================"
ls -la generated/
ls -la generated/templates/

echo ""
echo "========================================"
echo "  啟動伺服器 (Ctrl+C 停止)"
echo "========================================"
cd generated
lsof -ti :5000 | xargs kill -9 2>/dev/null
python3 backend.py
