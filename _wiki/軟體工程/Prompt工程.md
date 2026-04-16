# Prompt Engineering (提示詞工程)

## 概述

提示詞工程是設計和最佳化輸入提示詞（Prompt）的實踐，以獲得更好的 AI 模型輸出。是與大型語言模型 (LLM) 有效互動的關鍵技能。

## 提示詞基本結構

```
┌─────────────────────────────────────────────────────────────┐
│                    Prompt 結構                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [System]     你是一個專業的程式設計師                      │
│      ↓                                                   │
│  [Context]    使用 TypeScript，遵循 Clean Architecture     │
│      ↓                                                   │
│  [Examples]   輸入: 用戶登入                               │
│               輸出: JWT token                             │
│      ↓                                                   │
│  [Task]       寫一個 AuthService 類別                      │
│      ↓                                                   │
│  [Format]     只輸出程式碼，不做解釋                        │
│                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 核心策略

### 1. 清晰具體的指令

```markdown
# ❌ 不好的提示
"Write code"

# ✅ 好的提示
"寫一個 OpenCode 指令，實現用戶認證功能：
- 使用 JWT token
- 包含 login, logout, verify 三個指令
- 遵循專案的 Clean Architecture
- 輸出完整的實作內容"
```

### 2. Few-shot 範例

```markdown
# 在 OpenCode 中使用 Few-shot
"為我建立一個登入功能，參考以下模式：

模式 1 (建立 API):
[instruction]
建立 GET /api/users 端點
[/instruction]
[result]
成功建立 users.ts 和 users.test.ts

模式 2 (建立 Service):
[instruction]
建立 UserService 類別
[/instruction]
[result]
成功建立 userService.ts

現在請建立：
[instruction]
建立 AuthService 用於 JWT 認證
[/instruction]
"
```

### 3. Chain-of-Thought (思維鏈)

```markdown
# 使用 OpenCode 的思考過程
"我需要建立一個搜尋功能，請逐步思考：

步驟 1: 先分析需求
- 關鍵字搜尋
- 支援分頁
- 排序功能

步驟 2: 設計資料結構
- SearchRequest
- SearchResponse

步驟 3: 實作
- [實作程式碼]

步驟 4: 測試
- [測試程式碼]
"
```

### 4. 角色扮演

```markdown
# 指定專家角色
"你是一位資深架構師，專精：
- 領域驅動設計 (DDD)
- 雲端原生架構
- 事件溯源

請評估以下 OpenCode 專案結構，並提供改進建議：

[專案結構]
src/
  domain/
  application/
  infrastructure/
"
```

## 進階技巧

### 1. 限制輸出格式

```markdown
# 要求特定輸出格式
"用以下格式建立 OpenCode 指令：

## 指令名稱
auth:login

## 輸入參數
- email: string
- password: string

## 回傳
{ token: string, expiresAt: Date }

只回傳 YAML 格式的指令規格，不要其他���明。"
```

### 2. 結構化輸出

```markdown
# 使用 YAML 格式
"你是一個需求分析師。分析以下需求並以 YAML 格式回傳：

需求：用戶管理系統

回傳格式：
```yaml
features:
  - name: 用戶建立
    priority: high
  - name: 用戶查詢
    priority: medium
services:
  - name: UserService
    actions:
      - create
      - findById
```
"
```

### 3. 分解複雜任務

```markdown
# ❌ 一步完成複雜任務
"建立電子商務系統"

# ✅ 分步驟
"分三個階段建立：

**階段 1**: 建立領域模型
- Product, Order, User 實體
- 建立對應的 test files

**階段 2**: 建立 Application Service
- ProductService, OrderService
- 實作 CRUD 邏輯

**階段 3**: 建立 API
- REST endpoints
- 錯誤處理
"
```

## Prompt 模式

### 1. Template Pattern

```markdown
# 使用 Template 建立指令
"""
建立 {entity} 的 CRUD 功能：

## 實體定義
{entity} = {{
  id: UUID,
  name: string,
  createdAt: Date
}}

## 需要建立
- service: {entity}Service
- test: {entity}Service.test.ts
- handler: {entity}Handler

請輸出完整的程式碼。
"""
```

### 2. Chain Pattern

```markdown
# 多步驟指令鏈
"**步驟 1**: 分析現有程式碼結構
[讓 OpenCode 分析 src/ 目錄]

**步驟 2**: 根據分析結果建立模型
[根據步驟 1 的分析建立]

**步驟 3**: 驗證
[執行測試驗證]
"
```

### 3. Ensemble Pattern

```markdown
# 多視角分析
"從三個角度分析這個程式碼問題：

**角度 1 - 效能**:
[分析效能問題]

**角度 2 - 安全**:
[分析安全問題]

**角度 3 - 可維護性**:
[分析架構問題]

請綜合三個角度給出最佳解決方案。"
```

## OpenCode 實作範例

### 1. 建立 Service

```markdown
"建立一個 UserService：

```typescript
// src/services/userService.ts
export class UserService {
  async findById(id: string): Promise<User | null> {
    // 查詢用戶
  }
  
  async create(data: CreateUserDTO): Promise<User> {
    // 建立用戶
  }
}
```

請產生完整的程式碼和測試。"
```

### 2. 建立 MCP Server

```markdown
"建立一個 MCP server：

```typescript
// 需要實現
- tools: list, get, create, update, delete
- resources: user://{{id}}
- prompts: 用戶管理相關

請產生完整的 server 程式碼。"
```

### 3. 建立Hermes Agent

```markdown
"建立 Hermes agent 指令：

```typescript
// 定義
agent: user-manager
description: 管理用戶的 autonomous agent

// capabilities
- 查詢用戶資料
- 建立/更新/刪除用戶
- 權限管理

// tools
- database: read, write
- notifications: send
```
"
```

## 常見陷阱

| 陷阱 | 說明 | 解決方法 |
|------|------|----------|
| 模糊指令 | 指令不夠具體 | 使用明確的動作詞 |
| 資訊過載 | 一次給太多資訊 | 分步驟處理 |
| 缺乏上下文 | 模型不知道背景 | 提供相關上下文 |
| 忽略限制 | 沒說不要做什麼 | 明確列舉限制 |

## 測試和疊代

```markdown
# 驗證 Prompt 效果
"測試以下 Prompt 三次，並評估結果：

Prompt: "建立簡單的登入 API"

測試 1: [結果 1]
評估: [優點/問題]

測試 2: [結果 2]
評估: [優點/問題]

測試 3: [結果 3]
評估: [優點/問題]

最佳化建議: [改進後的 Prompt]
"
```

## 相關資源

- 相關概念：[Context Engineering](Context工程.md)
- 相關概念：[Harness Engineering](Harness工程.md)
- 相關概念：[Skill文檔](Skill文檔.md)

## Tags

#Prompt #提示詞工程 #LLM #AI工程 #OpenCode