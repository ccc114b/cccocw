對於 AI 指揮者而言，可以透過 AIL 同時指揮數個 agent 去嘗試解決同一個任務（也有可能要求用不同方法）
然後在 agent 完成任務後，選定其中某個納入系統。

這感覺也很符合 explore.py 所建構出來的功能。

但是要選擇哪一個 agent 的結果，應該是由指揮者檢視成果之後，再來決定要納入哪一個 agent 的結果。

所以我覺得這裡其實應該有三種角色

1. 指揮者
2. minicode_ail.py
3. 被指揮者

指揮者寫出 minicode_ail.py 的程式，類似這樣

```py
import asyncio
from minicode_ail import MiniCode, init_ollama

init_ollama(model='minimax-m2.5:cloud')

async def main():
    agent = MiniCode(root_dir='./generated')
    await agent.run('''建立一個 SQLite TODO 網頁應用：

詳細需求：
1. 後端用 Flask + SQLite
2. 首頁路由 / 回傳 templates/index.html
3. API: GET/POST /api/todos, PUT/DELETE /api/todos/<id>
4. 資料表欄位：id, title, completed
5. 前端用 HTML + JavaScript
6. 功能：顯示列表、新增、刪除、勾選完成

如果任務交代不夠清楚，或者缺乏某些資訊，你可以透過 websocket 發 <ask>...</ask> 訊息問我。''')

asyncio.run(main())
```

