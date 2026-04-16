# Harness Engineering (馭繮工程)

## 概述

Harness Engineering（馭繮工程）是 2026 年提出的工程範式，工程師不再埋頭寫代碼，而是設計環境、明確意圖、建構反饋迴圈，讓 AI 智慧體能可靠地完成工作。

根據 OpenAI 的實驗：五個月內從零建立了一個包含百萬行代碼的產品，約 1500 個 PR，平均每位工程師每天 3.5 個 PR，人類從未直接寫任何一行代碼。

```
傳統工程：人類寫代碼 → 機器執行代碼
Harness Engineering：人類設計約束 → 智慧體寫代碼 → 機器執行代碼
```

## 核心轉變

工程師的產出從程式碼變成了約束系統：AGENTS.md、架構規則、自訂 linter、反饋迴圈。

人類的角色變成「掌舵者」，而非「執行者」：
```
人類：描述任務、打開 PR、驗證結果
智慧體：寫代碼、跑測試、回應回饋
```

## 為什麼需要 Harness

AI 智慧體能力越來越強，但可靠度卻沒跟上。問題不在於模型不夠聰明，而在於：

- 智慧體看不見倉庫裡的隱式規則
- 架構約束從未被傳達給它
- 規範寫在 Wiki 或群裡，智慧體讀不到
- Prompt 再長也裝不下整個倉庫的架構決策

## 兩大控制機制

### Feedforward（引導）

在智慧體行動前給予指導，預防問題發生：

| 類型 | 範例 | 費用 |
|------|------|------|
| 計算型 | Linter、類型檢查、结构测试 | 低（毫秒級） |
| 推理型 | AGENTS.md、Skills、系統提示 | 高（GPU 計算） |

### Feedback（感測）

在智慧體行動後觀察結果，自動修正：

| 類型 | 範例 | 費用 |
|------|------|------|
| 計算型 | 靜態分析、日誌、測試 | 低 |
| 推理型 | AI code review、LLM as judge | 高 |

只有引導沒有感測：智慧體會重複犯錯
只有感測沒有引導：智慧體會遵守規則但不知道是否正確

## 三種約束類別

### 1. 可維護性約束（Maintainability）

調節內部程式碼品質：

```
計算型感測：重複程式碼、圈複雜度、測試覆蓋率、架構漂移、風格違規
推理型感測：語意重複、過度工程、不必要功能
```

### 2. 架構適應性約束（Architecture Fitness）

定義和檢查系統的架構特性：

```typescript
// 範例：分層架構
Types → Config → Repo → Service → Runtime → UI

// 規則：高層可以依賴低層，反之不行
// 違反時：OpenCode linter 报错
```

透過自訂 linter 和結構測試強制執行。

### 3. 行為約束（Behaviour）

確保應用程式功能正確：

```
Feedforward：功能規格（spec）
Feedback：AI 生成的測試、人類審查、手動測試
```

這是目前最困難的約束類別。

## OpenAI 的六大支柱

### 1. 倉庫即系統紀錄

**給地圖，不要給說明書**：AGENTS.md 應該是目錄（約 100 行），不是百科全書。

```
AGENTS.md           → 目錄（inject into context）
docs/
├── design-docs/    → 設計文檔
├── exec-plans/    → 執行計劃
├── references/    → 參考資料
└── generated/     → 生成的內容
```

所有知識必須在倉庫裡，否則智慧體看不見。

### 2. 应用可讀性

讓應用程式本身對智慧體可讀：

```typescript
// 讓 OpenCode 可以啟動和驅動應用
// 範例：每個 worktree 有獨立的 app instance
opencode_dev_app = boot_worktree(git_branch)

// CDP 整合
opencode.snapshot_before()
opencode.trigger_ui_action()
opencode.snapshot_after()
opencode.compare_screenshots()
```

### 3. 可觀測性堆疊

```markdown
# 本地可觀測性堆疊
app -> logs, metrics, traces -> Vector -> Victoria Logs/Metrics/Traces

# OpenCode 可以查詢
opencode.query_logql("error | rate > 10")
opencode.query_promql("latency_p99 > 2s")
```

### 4. 強制架構與品味

```
分層領域架構（Layered Domain Architecture）：
- 每個業務領域分成固定層級
- 嚴格驗證依賴方向
- 允許的邊緣數量有限

Types → Config → Repo
Providers → Service → Runtime → UI
```

透過自訂 linter 強制執行（linter 本身也是 OpenCode 生成的）。

### 5. 吞吐量改變合併哲學

在高速吞吐量下：
- PR 生命周期短
- 測試 flake 用後續運行修復，而非阻塞
- 等待昂貴，修正便宜

### 6. 自主權遞進

隨著系統成熟，智慧體可以端到端驅動新功能：

```
1. 驗證代碼庫現狀
2. 重現 bug
3. 實作修復
4. 驗證修復
5. 打開 PR
6. 回應回饋
7. 合併
```

## AGENTS.md 最佳實踐

### 不要這樣做

```markdown
# 1000 行的 AGENTS.md
- 塞滿所有規則
- 很快就過時
- 智慧體無法驗證
- 變成「吸引人的麻煩」
```

### 應該這樣做

```markdown
# AGENTS.md（約 100 行）

## 專案概覽
[一行描述]

## 技術棧
- [技術 1]
- [技術 2]

## 架構
[ARCHITECTURE.md 的摘要]

## 約束
- [指向詳細規則]

## 驗證
[如何跑測試]

## 深入資料
[List of docs/ files]
```

### 機械性強制

```bash
# CI 工俱驗證知識庫是最新的
- linter 檢查文件結構
- 驗證交叉連結
- 檢查 freshness
- 「doc-gardening」agent 掃描過時文件
```

## 垃圾分類（Entropy & Garbage Collection）

問題：智慧體會複製現有模式，即使是不均勻或最佳的。

解決方案：編碼「黃金原則」到倉庫，建構定期清理流程：

```
1. 偏好共享工具包 over 手寫輔助函式
2. 不做「YOLO-style」探索資料——驗證邊界或使用類型 SDK
```

定期執行：
```markdown
# background tasks
- 掃描漂移
- 更新品質等級
- 打開重構 PR
- 大多數可在一分鐘內審查並自動合併
```

這像垃圾分類：技術債是高利貸，持續償還優於一次還清。

## 層級自主權

```
Level 0: 人類驅動
        human -> OpenCode -> PR

Level 1: OpenCode 可自審
        human -> OpenCode -> review -> PR

Level 2: OpenCode 可處理回饋
        human -> OpenCode -> feedback -> fix -> PR

Level 3: OpenCode 端到端驅動
        human -> OpenCode (full loop) -> PR -> merge
```

## OpenCode 實作範例

### AGENTS.md

```markdown
# AGENTS.md

## 專案
這是一個電子商務 API 服務

## 技術棧
- Framework: Hono
- Language: TypeScript
- Database: PostgreSQL + Prisma

## 架構
分層架構：
- src/routes/: API 路由
- src/services/: 業務邏輯
- src/repositories/: 資料存取

## 目錄結構
src/
├── routes/
├── services/
├── repositories/
├── types/
└── middleware/

## 驗證
npm run build   # 建置
npm run lint   # Lint
npm run test   # 測試

## 約束
- 禁止直接 import infrastructure/ 到 routes/
- 新服務放在 src/services/
- 遵循 src/CONVENTIONS.md
```

### 自訂 Linter

```typescript
// lint-arch.ts：依賴方向檢查
export function checkLayerImports(): Violation[] {
  const violations: Violation[] = []
  
  for (const file of allSourceFiles) {
    const imports = extractImports(file)
    const layer = getLayer(file)
    
    for (const imp of imports) {
      const impLayer = getLayer(imp)
      if (!canImport(layer, impLayer)) {
        violations.push({
          file,
          import: imp,
          message: `${layer} cant import ${impLayer}`
        })
      }
    }
  }
  
  return violations
}
```

### 品質檢查

```typescript
// scripts/quality-check.ts
export async function runQualityChecks(): Promise<QualityResult> {
  const results = {
    lint: await runLinter(),
    typeCheck: await runTypeChecker(),
    test: await runTests(),
    architecture: checkLayerImports(),
    complexity: checkCyclomaticComplexity()
  }
  
  return {
    passed: allPassed(results),
    details: results
  }
}
```

## OpenCode 中的 Harness 實作

### 1. 建立 AGENTS.md

```markdown
"請為這個專案建立 AGENTS.md：
- 專案描述：REST API 服務
- 技術棧：TypeScript + Hono + Prisma
- 架構：Clean Architecture
- 驗證命令：npm run build && npm run test"
```

### 2. 建立 Linter 規則

```markdown
"請建立 custom linter 規則：
- 禁止从 routes/ 直接 import infrastructure/
- 強制錯誤類型使用 Error 類別
- 強制有 JSDoc 注釋
- 違反時顯示清楚的錯誤訊息"
```

### 3. 建立品質檢查

```markdown
"請建立品質檢查指令：
1. 執行 npm run lint
2. 執行 npm run type-check
3. 執行測試
4. 檢查複雜度
5. 輸出整體評分"
```

## 黃金原則清單

1. 共享工具包優先於重複程式碼
2. 邊界驗證或類型 SDK，絕不「猜測」
3. 結構化日誌是必須的
4. Schema 和類型有命名規範
5. 檔案大小有限制
6. 平臺可靠性要求

## 與上下文工程的關係

```
Prompt 工程 → 問什麼（說清楚）
Context 工程 → 給什麼（喂對）
Harness 工程 → 整個系統怎麼跑（管得住）
```

Harness 是上下文工程的具體形式，專注於讓智慧體可靠工作。

## 相關資源

- [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
- [Martin Fowler: Harness engineering](https://martinfowler.com/articles/harness-engineering.html)
- 相關概念：[Prompt工程](Prompt工程.md)
- 相關概念：[Context工程](Context工程.md)
- 相關概念：[Skill文檔](Skill文檔.md)

## Tags

#Harness #馭繮工程 #AI工程 #智慧體 #OpenCode #代理工程