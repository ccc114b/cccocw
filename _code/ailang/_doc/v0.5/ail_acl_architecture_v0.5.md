# AIL 與 ACL 系統架構說明 v0.5

## 概述

v0.5 版本新增 **AICommander**，讓系統可以**自動回答執行者的問題**，無需人類介入。AICommander 了解整體架構（AIL/ACL），能夠根據人類的原始目標和系統能力做出合理回覆。

## 系統架構

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        人類開發者                                        │
│                    "建立一個購物網站"                                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    AICommander (Level 1 指揮官)                       │
│  ┌───────────────────────────────────────────────────────────────────┐│
│  │ 職責：                                                             ││
│  │ - 理解人類目標                                                     ││
│  │ - 規劃任務                                                         ││
│  │ - 回答執行者問題                                                   ││
│  │ - 監控執行進度                                                     ││
│  │                                                                    ││
│  │ 初始化時已知：                                                     ││
│  │ - AIL 框架能力 (Goal, Agent, Memory, Explore, Think)             ││
│  │ - ACL 指令集 (write, shell, read, ask, answer)                   ││
│  │ - 專案目標                                                         ││
│  │ - 執行環境                                                         ││
│  └───────────────────────────────────────────────────────────────────┘│
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   ACL 通訊      │
                    │ (除錯訊息)      │
                    └────────▼────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  AIExecutor (Level 2 執行者)                           │
│  ┌───────────────────────────────────────────────────────────────────┐│
│  │ 職責：                                                             ││
│  │ - 執行 ACL 指令                                                    ││
│  │ - 寫入檔案                                                         ││
│  │ - 執行命令                                                         ││
│  │ - 如有疑問，發出 <ask> 詢問                                        ││
│  │ - 回報 <result> 或 <error>                                        ││
│  └───────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

## AICommander 初始化

AICommander 在初始化時會載入完整的系統知識：

```python
class AICommander:
    def __init__(self):
        # 1. 載入 AIL 框架知識
        self.ail_knowledge = """
## AIL (AI Language) 框架

AIL 是一個讓人類以目標導向指揮 AI 完成任務的 Python 框架。

### 核心模組：
- **Goal**: 目標追蹤
- **Agent**: AI 代理程式
- **Memory**: 長期記憶
- **Explore**: 平行探索
- **Think**: 推理思考

### 使用範例：
```python
from ailang import goal, Agent

with goal("建立網站"):
    agent = Agent("coder")
    result = await agent(task="建立 Flask 後端")
```
"""
        
        # 2. 載入 ACL 指令集知識
        self.acl_knowledge = """
## ACL (AI Communication Language)

ACL 是 AI 與系統之間的結構化溝通格式。

### 指令集：
- **<write file="...">**: 寫入檔案
- **<shell>**: 執行命令
- **<read file="...">**: 讀取檔案
- **<ask>**: 詢問指揮官
- **<answer>**: 回覆執行者
- **<result>**: 回報結果

### 重要規則：
1. 執行者沒有檔案系統權限
2. 必須透過 ACL 指令操作檔案
3. 如有不清楚，發 <ask> 詢問
"""
        
        # 3. 專案上下文
        self.project_context = ""
        
        # 4. Ollama 執行者
        self.executor = OllamaAgent("executor")
    
    def set_project(self, task: str):
        """設定專案目標"""
        self.project_context = f"""
## 當前專案目標
{task}

## 執行環境
- 根目錄: ./generated
- 語言: Python + Flask
- 資料庫: SQLite
"""
    
    async def answer_question(self, question: str) -> str:
        """回答執行者的問題"""
        
        # 組合完整上下文
        full_context = f"""
{self.ail_knowledge}

{self.acl_knowledge}

{self.project_context}

## 執行者詢問
{question}

## 請根據以上資訊回答：
1. 這是否與 AIL/ACL 架構相關？
2. 根據專案目標，合理的回覆是什麼？
3. 如果需要做決定，請直接給出建議。

請用繁體中文回答，簡潔明確。
"""
        
        result = await self.executor(full_context)
        return result
```

## 通訊流程

### 完整範例

```
人類: "建立 SQLite TODO 應用"
     │
     ▼
┌────────────────────────────────────────────────────┐
│ AICommander.set_project("建立 SQLite TODO 應用")  │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│ AICommander → AIExecutor                           │
│ 任務: 建立 SQLite TODO 應用                       │
│ - backend.py                                      │
│ - templates/index.html                            │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│ AIExecutor 回傳:                                   │
│ <write file="backend.py">...</write>             │
│ <write file="templates/index.html">...</write>   │
└────────────────────┬────────────────────────────────┘
                     │ (如果沒有問題)
                     ▼
                    ✅ 完成

---
如果執行者有問題：

┌────────────────────────────────────────────────────┐
│ AIExecutor 回傳:                                   │
│ <ask>請問要用 SQLite 還是 PostgreSQL？</ask>     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│ AICommander.answer_question()                     │
│ 分析問題：執行者詢問資料庫選擇                      │
│ 根據專案目標：SQLite (簡單、本地儲存)              │
│ 回覆: <answer>使用 SQLite，簡單輕量</answer>     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────────────┐
│ AIExecutor 繼續執行                                │
└────────────────────────────────────────────────────┘
```

## 程式碼實作

### minicode_ail.py v0.5

```python
"""
MiniCode - 使用 AIL + ACL + AICommander
v0.5: 支援 AI 自動回答問題
"""

import asyncio
from pathlib import Path
from ailang import OllamaAgent, init_ollama
from ailang.acl_socket import ACLParser, ACLConsoleHandler


class AICommander:
    """AI 指揮官 - 自動回答執行者問題"""
    
    def __init__(self):
        self.agent = OllamaAgent(
            "ai-commander",
            system_prompt="""你是 AICommander，一個專業的 AI 專案管理員。

你了解以下架構：
- AIL (AI Language): 目標導向的 Python AI 框架
- ACL (AI Communication Language): 結構化溝通格式

## AIL 框架
- Goal: 目標追蹤
- Agent: AI 代理程式
- Memory: 長期記憶
- Explore: 平行探索

## ACL 指令集
- <write file="...">: 寫入檔案
- <shell>: 執行命令
- <read file="...">: 讀取檔案
- <ask>: 詢問
- <answer>: 回覆
- <result>: 結果回報

## 重要規則
1. 執行者沒有檔案系統權限
2. 所有檔案操作必須透過 ACL
3. 根據專案目標給出明確建議
4. 用繁體中文回覆"""
        )
        self.project_context = ""
    
    def set_project(self, task: str):
        """設定專案目標"""
        self.project_context = task
    
    async def answer(self, question: str) -> str:
        """回答執行者的問題"""
        prompt = f"""
## 專案目標
{self.project_context}

## 執行者詢問
{question}

請根據專案目標直接回答。如果需要做決定，請給出最合適的建議。
"""
        return await self.agent(prompt)


class MiniCode:
    """使用 AIL + ACL + AICommander 的 MiniCode"""
    
    def __init__(self, root_dir: str = ".", debug: bool = False):
        self.root = Path(root_dir)
        self.debug = debug
        
        # AI 指揮官
        self.commander = AICommander()
        
        # ACL 處理器
        self.acl_handler = ACLConsoleHandler(root_dir)
        
        # AI 執行者
        self.agent = OllamaAgent(
            "executor",
            system_prompt="""你是 AIExecutor，專門執行 ACL 指令。

**你沒有檔案系統權限**，只能輸出文字。

用以下格式輸出：
<write file="檔名">程式碼</write>
<shell>命令</shell>

如果有不清楚的，用 <ask> 詢問。"""
        )
    
    async def run(self, task: str) -> str:
        """執行任務"""
        print(f"\n🎯 任務: {task}")
        print("="*50)
        
        # 設定專案目標
        self.commander.set_project(task)
        
        files = self._list_files()
        print(f"📁 現有檔案:\n{files}")
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            prompt = f"""
現有檔案:
{files}

任務: {task}

直接寫出程式碼。有問題用 <ask> 詢問。
"""
            
            result = await self.agent(prompt)
            
            if self.debug:
                print(f"\n📝 AI 輸出:\n{result[:300]}...")
            
            # 解析 ACL
            parser = ACLParser(self.acl_handler, debug=self.debug)
            execution_result = await parser.execute(result)
            
            if self.debug:
                print(f"\n執行結果:\n{execution_result}")
            
            # 檢查是否有詢問
            if '<ask>' not in result:
                break
            
            # AICommander 自動回答
            import re
            ask_pattern = r'<ask>(.+?)</ask>'
            for match in re.finditer(ask_pattern, result, re.DOTALL):
                question = match.group(1).strip()
                print(f"\n❓ 執行者詢問: {question}")
                
                # AICommander 回答
                answer = await self.commander.answer(question)
                print(f"💬 AICommander 回覆: {answer[:200]}...")
        
        return result
```

## 優勢

### 1. 無需人類介入

- 執行者可以問問題
- AICommander 自動回答
- 人類只需最後驗證結果

### 2. 了解整體架構

- AICommander 知道 AIL/ACL 能做什麼
- 能給出符合框架的建議
- 確保執行方向正確

### 3. 可追蹤性

- 所有問答都有記錄
- 方便 Debug
- 可以回顧決策過程

## 使用範例

```python
# 初始化
init_ollama(model='minimax-m2.5:cloud')
agent = MiniCode(debug=True)

# 執行任務
await agent.run("建立購物網站")

# 過程中可能會：
# 1. AIExecutor 問: "購物車要用 session 還是資料庫？"
# 2. AICommander 回答: "使用資料庫，支援會員登入"
# 3. 繼續執行...
```

## 未來擴展

1. **多層指揮**
   - Level 1: AICommander (規劃)
   - Level 2: AIExecutor (執行)
   - Level 3: 工具執行 (檔案操作)

2. **學習機制**
   - 記住人類的偏好
   - 根據過往答案改進

3. **WebSocket 版本**
   - 支援多人協作
   - 即時顯示問答過程

## 結論

v0.5 版本的核心價值：

1. **AICommander** - 了解 AIL/ACL 架構的 AI 指揮官
2. **自動回答** - 執行者有問題時不用等人類
3. **架構感知** - 根據框架能力給出合適建議

這使得系統更加**自主**，可以處理複雜任務，減少人類介入次數。

```
人類 → AICommander → AIExecutor → 檔案系統
         ↑              |
         └───── <ask>───┘
```
