# Context Engineering (上下文工程)

## 概述

上下文工程是設計和管理與 AI 模型互動時的上下文（Context）策略，最大化模型對任務的理解和表現。是 Prompt 工程的延伸，專注於資訊的組織和呈現方式。

## Context 的組成

```
┌─────────────────────────────────────────────────────────────┐
│                    Context 組成                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  System Context                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 角色定義、能力邊界、行為約束                          │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  Task Context                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 任務描述、成功標準、預期輸出格式                      │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  World Context                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 程式碼庫結構、相關檔案、領域知識                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                         ↓                                   │
│  Session Context                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 對話歷史、已確定的決策、相關約束                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 上下文管理策略

### 1. RAG (Retrieval Augmented Generation)

```markdown
# 在 OpenCode 中使用 RAG
"基於以下程式碼上下文回答問題：

## 檢索到的相關程式碼

### src/services/userService.ts
[程式碼內容]

### src/types/user.ts
[類型定義]

問題: 如何實作用戶認證？

請基於上述程式碼给出解決方案。"
```

### 2. 對話歷史管理

```markdown
# 在 OpenCode 中使用對話歷史
"根據之前的討論，我們已經：
- 確認使用 JWT 認證
- 建立 UserService
- 需要實作登入 API

請繼續實作登入 API：
- 驗證用戶 credential
- 回傳 JWT token
- 處理錯誤情況
"
```

### 3. 分塊策略 (Chunking)

```markdown
# 在 OpenCode 中依賴上下文建立程式碼
"請建立 OrderService：

## 參考的現有服務

### UserService (已建立)
```typescript
export class UserService {
  async findById(id: string): Promise<User>
  async create(data: CreateUserDTO): Promise<User>
}
```

### ProductService (已建立)
```typescript
export class ProductService {
  async findById(id: string): Promise<Product>
  async findAll(): Promise<Product[]>
}
```

請參考上述模式建立 OrderService。"
```

## 上下文最佳化

### 1. 相關性檢索

```markdown
# 指定具體範圍
"請查看：
- 只需要 src/services/ 目錄
- 相關的 types 在 src/types/
- 不要查看 tests/ 目錄

問題：現有的認證機制是什麼？"
```

### 2. 上下文視窗管理

```markdown
# 限制上下文範圍
"由於代碼較長，請：
1. 先閱讀 index.ts 了解整體結構
2. 閱讀 exports 的主要服務
3. 不要全部閱讀，只看相關部分

然後回答：如何新增一個 API endpoint？"
```

## OpenCode 上下文管理實作

### 1. 使用 CLAUDE.md

```markdown
# CLAUDE.md 內容範例
"""
# 專案資訊

## 技術棧
- TypeScript
- Node.js
- PostgreSQL

## 架構
- 使用 Clean Architecture
- src/domain: 領域模型
- src/application: 應用服務
- src/infrastructure: 基礎設施

## 約定
- 所有服務使用 async/await
- 錯誤使用 Error 類別
- 使用 JWT token 認證

## 常用指令
- npm run dev: 開發伺服器
- npm run test: 執行測試
"""
```

### 2. 使用 Context 引導

```markdown
# 在對話中提供上下文
"在我們的專案中：
- 已有 UserService in src/services/userService.ts
- 使用 Prisma ORM
- 資料庫是 PostgreSQL

請建立 OrderService，要求：
- 參考 UserService 的模式
- 使用 Prisma
- 建立对应的 API
"
```

### 3. 分層上下文

```markdown
# 分層提供上下文
"## 層 1: 專案結構
位置: src/
├── domain/
├── application/
└── infrastructure/

## 層 2: 相關檔案
- UserService: src/application/userService.ts
- UserRepository: src/infrastructure/userRepository.ts

## 層 3: 具體需求
- 建立 OrderService
- 需要包含 CRUD
- 使用現有的 Repository 模式
"
```

## 上下文工程最佳實踐

| 原則 | 說明 |
|------|------|
| 精確相關 | 只包含與當前任務相關的資訊 |
| 結構清晰 | 使用標題、分隔符號組織資訊 |
| 優先排序 | 最重要資訊放在前面 |
| 及時清理 | 移除不再需要的上下文 |
| 版本控制 | 追蹤上下文變化 |

## OpenCode 實作範例

### 1. 建立功能時的上下文

```markdown
# 在建立功能前提供上下文
"## 現有程式碼

### 現有服務模式
src/services/userService.ts:
```typescript
export class UserService {
  constructor(private repo: UserRepository) {}
  
  async findById(id: string): Promise<User> {
    return this.repo.findById(id)
  }
  
  async create(data: CreateUserDTO): Promise<User> {
    return this.repo.create(data)
  }
}
```

### 現有 Repository 模式
src/repositories/userRepository.ts:
```typescript
export class UserRepository {
  async findById(id: string): Promise<User | null>
  async create(data: CreateUserDTO): Promise<User>
}
```

請建立 OrderService 和 OrderRepository，遵循現有模式。"
```

### 2. 查詢時的上下文

```markdown
# 查詢時的上下文
"## 查詢範圍
- src/services/*.ts: 現有服務
- src/types/*.ts: 類型定義

## 需要查���
- 認證相關的程式碼
- API middleware

請找出：現有的認證機制如何處理 JWT？"
```

### 3. 重構時的上下文

```markdown
# 重構時提供完整的上下文
"## 現有程式碼
位置: src/utils/legacyAuth.ts

```typescript
// 舊的認證邏輯
function auth(req) {
  // ...
}
```

## 目標
- 使用 OpenCode 的新認證模式
- 保持相同的 API

## 約束
- 不要改變 API 介面
- 保持向後相容

請重構為新的架構。"
```

## 評估指標

```markdown
# 評估上下文品質
"評估以下上下文的品質：

## 提供的上下文
- 專案結構
- 相關服務
- 類型定義

## 任務
建立新功能

## 評估標準
1. relevance: 上下文與任務相關性
2. coverage: 是否覆蓋所需資訊
3. conciseness: 是否簡潔
4. effectiveness: 任務完成效果
"
```

## 相關資源

- 相關概念：[Prompt工程](Prompt工程.md)
- 相關概念：[Harness Engineering](Harness工程.md)
- 相關概念：[Skill文檔](Skill文檔.md)

## Tags

#Context #上下文工程 #RAG #LLM #資訊檢索 #OpenCode