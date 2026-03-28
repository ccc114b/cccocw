#!/bin/bash
# Test AIL MiniCode - 建立 SQLite TODO 應用

cd "$(dirname "$0")"

echo "========================================"
echo "  AIL MiniCode Test - TODO App"
echo "========================================"

# 清理舊檔案
rm -rf generated/*

# 執行 MiniCode - 提供完整需求
echo ""
echo "建立 SQLite TODO 應用..."
PYTHONPATH=src python3 -c "
import asyncio
from minicode_ail import MiniCode, init_ollama

init_ollama(model='minimax-m2.5:cloud')

async def main():
    agent = MiniCode(root_dir='./generated', debug=True)
    await agent.run('''建立一個 SQLite TODO 網頁應用：

詳細需求：
1. 後端用 Flask + SQLite
2. 首頁路由 / 回傳 templates/index.html
3. API: GET/POST /api/todos, PUT/DELETE /api/todos/<id>
4. 資料表欄位：id, title, completed
5. 前端用 HTML + JavaScript
6. 功能：顯示列表、新增、刪除、勾選完成

請直接寫出程式碼，不需要詢問。''')

asyncio.run(main())
"

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
