# AIL 與 ACL 系統架構說明 v0.4

## 概述

AIL (AI Language) 與 ACL (AI Communication Language) 構成一個完整的 AI 程式開發框架。本版本新增**多層指揮架構**與**詢問機制**，讓 AI 可以在執行過程中向指揮官請求澄清，確保任務正確完成。

## 系統分層架構

### 多層指揮體系

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Level 1: 人類指揮官 (或 AI 指揮官)               │
│                        "建立購物網站"                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ACL 訊息傳遞      │
                    │   (WebSocket)      │
                    └──────────┬──────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Level 2: AI 指揮官                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ - 理解人類目標                                                   ││
│  │ - 規劃任務                                                      ││
│  │ - 如不清楚，發出 <ask> 詢問                                      ││
│  │ - 整合回覆並繼續執行                                             ││
│  └─────────────────────────────────────────────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   ACL 訊息傳遞      │
                    │   (WebSocket)      │
                    └──────────┬──────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Level 3: AI 執行者                              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │ - <write file="..."> 寫入檔案                                   ││
│  │ - <shell> 執行命令                                              ││
│  │ - <read file="..."> 讀取檔案                                    ││
│  │ - 如有疑問，發出 <ask> 詢問                                      ││
│  │ - 回報 <result> 執行結果                                         ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 為什麼需要詢問機制

在 `v0.3` 版本中，`minicode_ail.py` 有一句：
> "3. 立即开始写文件，不要询问"

但這會造成問題：
- 執行者對任務有疑慮時，無法詢問
- 可能產生不符合預期的結果
- 浪費時間修正錯誤

**解決方案**：讓 ACL 支援雙向溝通，被指揮者可以向指揮者詢問。

## ACL 指令集 v0.4

### 下行指令（指揮官 → 執行者）

| 指令 | 說明 | 範例 |
|------|------|------|
| `<write file="...">` | 寫入檔案 | `<write file="app.py">...</write>` |
| `<shell>` | 執行命令 | `<shell>pip install flask</shell>` |
| `<read file="...">` | 讀取檔案 | `<read file="config.json"></read>` |
| `<answer>` | 回覆執行者的問題 | `<answer>是實體商品</answer>` |
| `<confirm>` | 確認是否繼續 | `<confirm>確定要刪除檔案嗎？</confirm>` |

### 上行指令（執行者 → 指揮官）

| 指令 | 說明 | 範例 |
|------|------|------|
| `<ask>` | 詢問指揮官 | `<ask>商品要用什麼資料庫？</ask>` |
| `<result>` | 回報執行結果 | `<result>成功寫入 3 個檔案</result>` |
| `<error>` | 報告錯誤 | `<error>檔案不存在</error>` |
| `<confirm_request>` | 請求確認 | `<confirm_request>刪除確認？</confirm_request>` |

### 詢問-回覆流程

```
執行者                                    指揮官
  │                                         │
  │ <ask>                                   │
  │ 商品資料庫要用 SQL 還是 NoSQL？          │
  │ </ask>                                  │
  │────────────── WebSocket ──────────────▶│
  │                              分析問題     │
  │                              <answer>   │
  │                              使用 SQLite │
  │                              </answer>  │
  │◀───────────── WebSocket ──────────────│
  │                                         │
  │ <write file="db.py">                   │
  │ import sqlite3                          │
  │ ...                                     │
  │ </write>                               │
  │                                         │
  │ <result>                                │
  │ 已建立 SQLite 資料庫模組                │
  │ </result>                               │
  ▼                                         ▼
```

## WebSocket 實現

### 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                     ACLSocketServer                         │
│  ┌───────────────────────────────────────────────────────┐│
│  │  WebSocket Handler                                    ││
│  │  - 維護多個連線 (指揮官、執行者)                       ││
│  │  - 轉發訊息                                           ││
│  │  - 訊息格式驗證                                       ││
│  └───────────────────────────────────────────────────────┘│
└────────────────────────┬──────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ 人類指揮官 │   │ AI 指揮官 │   │ AI 執行者 │
   └──────────┘   └──────────┘   └──────────┘
```

### 程式碼範例

```python
# acl_socket.py - ACL WebSocket 通訊模組

import asyncio
import json
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum


class ACLMessageType(Enum):
    """ACL 訊息類型"""
    WRITE = "write"
    SHELL = "shell"
    READ = "read"
    ASK = "ask"
    ANSWER = "answer"
    RESULT = "result"
    ERROR = "error"
    CONFIRM = "confirm"


@dataclass
class ACLMessage:
    """ACL 訊息"""
    type: ACLMessageType
    content: str
    metadata: dict = None
    
    def to_xml(self) -> str:
        """轉換為 XML 格式"""
        if self.type in [ACLMessageType.WRITE, ACLMessageType.READ]:
            return f'<{self.type.value} file="{self.metadata.get("file", "")}">{self.content}</{self.type.value}>'
        elif self.type == ACLMessageType.ASK:
            return f'<ask>{self.content}</ask>'
        elif self.type == ACLMessageType.ANSWER:
            return f'<answer>{self.content}</answer>'
        elif self.type == ACLMessageType.RESULT:
            return f'<result>{self.content}</result>'
        elif self.type == ACLMessageType.ERROR:
            return f'<error>{self.content}</error>'
        return self.content
    
    @staticmethod
    def from_xml(xml_str: str) -> 'ACLMessage':
        """從 XML 解析"""
        import re
        
        # 解析 write
        match = re.search(r'<write file="([^"]+)">(.+?)</write>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.WRITE, match.group(2), {"file": match.group(1)})
        
        # 解析 ask
        match = re.search(r'<ask>(.+?)</ask>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ASK, match.group(1))
        
        # 解析 answer
        match = re.search(r'<answer>(.+?)</answer>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ANSWER, match.group(1))
        
        # 解析 result
        match = re.search(r'<result>(.+?)</result>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.RESULT, match.group(1))
        
        # 解析 error
        match = re.search(r'<error>(.+?)</error>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.ERROR, match.group(1))
        
        # 解析 shell
        match = re.search(r'<shell>(.+?)</shell>', xml_str, re.DOTALL)
        if match:
            return ACLMessage(ACLMessageType.SHELL, match.group(1))
        
        return None


class ACLWebSocket:
    """ACL WebSocket 客戶端"""
    
    def __init__(self, url: str = "ws://localhost:8765"):
        self.url = url
        self.ws = None
        self.pending_asks = {}  # 儲存待回覆的詢問
    
    async def connect(self):
        """連接到 WebSocket 伺服器"""
        import websockets
        self.ws = await websockets.connect(self.url)
    
    async def send(self, message: ACLMessage):
        """發送訊息"""
        await self.ws.send(message.to_xml())
    
    async def receive(self) -> ACLMessage:
        """接收訊息"""
        data = await self.ws.recv()
        return ACLMessage.from_xml(data)
    
    async def ask(self, question: str) -> str:
        """發出詢問並等待回覆"""
        import uuid
        ask_id = str(uuid.uuid4())
        
        await self.send(ACLMessage(ACLMessageType.ASK, question, {"id": ask_id}))
        
        # 等待 answer
        while True:
            msg = await self.receive()
            if msg.type == ACLMessageType.ANSWER and msg.metadata.get("id") == ask_id:
                return msg.content
    
    async def send_write(self, file_path: str, content: str):
        """發送寫入檔案指令"""
        await self.send(ACLMessage(ACLMessageType.WRITE, content, {"file": file_path}))
    
    async def send_shell(self, command: str):
        """發送執行命令指令"""
        await self.send(ACLMessage(ACLMessageType.SHELL, command))
    
    async def send_result(self, result: str):
        """發送結果"""
        await self.send(ACLMessage(ACLMessageType.RESULT, result))


class ACLWebSocketServer:
    """ACL WebSocket 伺服器"""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.clients = {}  # client_id -> websocket
        self.roles = {}    # client_id -> "commander" | "executor"
    
    async def handle_client(self, websocket, path: str):
        """處理客戶端連線"""
        import uuid
        client_id = str(uuid.uuid4())
        self.clients[client_id] = websocket
        
        try:
            # 接收角色設定
            role_msg = await websocket.recv()
            role_data = json.loads(role_msg)
            self.roles[client_id] = role_data.get("role", "executor")
            
            # 訊息轉發循環
            async for message in websocket:
                await self转发訊息(client_id, message)
        
        finally:
            del self.clients[client_id]
            del self.roles[client_id]
    
    async def forward_message(self, from_id: str, message: str):
        """轉發訊息到其他客戶端"""
        target_role = "executor" if self.roles[from_id] == "commander" else "commander"
        
        for client_id, ws in self.clients.items():
            if self.roles[client_id] == target_role:
                await ws.send(message)
    
    async def start(self):
        """啟動伺服器"""
        import websockets
        await websockets.serve(self.handle_client, "localhost", self.port)
        print(f"ACL WebSocket Server 啟動: ws://localhost:{self.port}")
```

## 使用範例

### 範例 1: 執行者詢問指揮官

```python
# executor.py - AI 執行者

from acl_socket import ACLWebSocket

async def main():
    ws = ACLWebSocket()
    await ws.connect()
    
    # 告知角色
    await ws.ws.send(json.dumps({"role": "executor"}))
    
    # 執行任務時發現疑問
    question = "目標中提到「商品」，是指實體商品還是數位商品？"
    print(f"詢問指揮官: {question}")
    
    # 等待回覆
    answer = await ws.ask(question)
    print(f"指揮官回覆: {answer}")
    
    # 根據回覆繼續執行
    if "實體" in answer:
        await ws.send_write("models.py", "class Product:\n    stock: int")
    else:
        await ws.send_write("models.py", "class DigitalProduct:\n    download_url: str")
    
    await ws.send_result("完成建立資料模型")

asyncio.run(main())
```

### 範例 2: 人類指揮官

```python
# commander.py - 人類指揮官

from acl_socket import ACLWebSocket

async def main():
    ws = ACLWebSocket()
    await ws.connect()
    
    # 告知角色
    await ws.ws.send(json.dumps({"role": "commander"}))
    
    # 發送任務
    await ws.send_shell("ls")
    
    # 接收執行者的詢問
    while True:
        msg = await ws.receive()
        
        if msg.type == ACLMessageType.ASK:
            print(f"執行者詢問: {msg.content}")
            answer = input("你的回覆: ")
            await ws.send(ACLMessage(ACLMessageType.ANSWER, answer))
        
        elif msg.type == ACLMessageType.RESULT:
            print(f"執行結果: {msg.content}")

asyncio.run(main())
```

### 範例 3: AI 指揮官（自動回覆）

```python
# ai_commander.py - AI 指揮官

from acl_socket import ACLWebSocket
from minicode_ail import MiniCode

class AICommander:
    def __init__(self):
        self.minicode = MiniCode()
    
    async def handle_ask(self, question: str) -> str:
        """用 AI 分析問題並回覆"""
        prompt = f"""
執行者詢問：{question}

人類的原始目標是：建立購物網站

請根據目標給出合理的回覆。
"""
        result = await self.minicode.agent(prompt)
        return result
    
    async def run(self):
        ws = ACLWebSocket()
        await ws.connect()
        await ws.ws.send(json.dumps({"role": "commander"}))
        
        while True:
            msg = await ws.receive()
            
            if msg.type == ACLMessageType.ASK:
                answer = await self.handle_ask(msg.content)
                await ws.send(ACLMessage(ACLMessageType.ANSWER, answer))

asyncio.run(AICommander().run())
```

## 多層指揮擴展

### Level 1 → Level 2 → Level 3 完整流程

```
人類: "建立一個有購物車的網店"
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ Level 2: AI 指揮官 #1                                     │
│  分析：需要                                          │
│    - 商品系統                                          │
│    - 購物車系統                                        │
│    - 訂單系統                                          │
│                                                            │
│  <ask>人類說的「網店」是指：                            │
│    1. 簡單的單頁應用                                    │
│    2. 完整的多頁商城                                     │
│    3. 已有系統需要整合？                                  │
│  </ask>                                                 │
└────────────────────────────────────────────────────────────┘
     │ WebSocket
     ▼
┌────────────────────────────────────────────────────────────┐
│ 人類回覆: "2. 完整的多頁商城"                              │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ Level 2: AI 指揮官 #1                                     │
│  規劃：                                                  │
│    - 後端：Flask + SQLite                                │
│    - 前端：HTML + JavaScript                             │
│    - API：商品、購物車、訂單                              │
│                                                            │
│  任務發給 Level 3:                                        │
│    "建立 Flask 後端，包含商品 CRUD、購物車 API"          │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ Level 3: AI 執行者                                        │
│                                                            │
│  <ask>                                                    │
│  「購物車」需要支援：                                      │
│    - 匿名用戶（session based）                            │
│    - 登入用戶（user based）                              │
│    哪種？                                                 │
│  </ask>                                                  │
└────────────────────────────────────────────────────────────┘
     │ WebSocket
     ▼
┌────────────────────────────────────────────────────────────┐
│ Level 2: AI 指揮官 #1                                     │
│  <answer>支援匿名用戶即可，簡化處理</answer>              │
└────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────┐
│ Level 3: AI 執行者                                        │
│                                                            │
│  <write file="cart.py">...</write>                       │
│  <write file="templates/cart.html">...</write>            │
│                                                            │
│  <result>已完成購物車功能</result>                        │
└────────────────────────────────────────────────────────────┘
```

## 未來擴展

1. **多執行者並行**：同時發給多個執行者不同任務
2. **自我詢問**：執行者自己嘗試後仍有疑問再詢問
3. **學習機制**：記住指揮官的回覆模式
4. **階層指揮**：Level 2 指揮官也可以是 AI，形成更深層

## 結論

v0.4 版本新增的核心能力：

1. **詢問機制**：被指揮者可以向指揮官請求澄清
2. **WebSocket 通訊**：即時、雙向、多層傳遞
3. **多層指揮**：人類 → AI 指揮官 → AI 執行者
4. **角色分工**：指揮官規劃決策，執行者實際操作

這使得系統更加靈活，能夠處理複雜任務，減少誤解和錯誤。

```
人類 → AI 指揮官 → AI 執行者
  │         │          │
  │         │          │ <ask> (詢問)
  │         │          │
  │         │          │ <answer> (回覆)
  │         │          │
  │         │          │ <write> (執行)
  ▼         ▼          ▼
```
