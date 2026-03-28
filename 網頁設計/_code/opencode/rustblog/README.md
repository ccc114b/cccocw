# Rust Blog (YouBook)

一個用 Rust 開發的部落格系統，功能類似 Twitter/X。

## 功能

- 使用者註冊與登入
- 發布文章 (Post)
- 刪除自己的文章
- 評論功能
- 按讚 (Like)
- 轉分享 (Share)
- 查看用戶文章列表

## 技術栈

- **Web 框架**: Actix-web
- **資料庫**: SQLite (rusqlite)
- **密碼加密**: bcrypt
- **Session 管理**: actix-session

## 安裝與執行

### 前置需求

- Rust (請安裝 rustup: https://rustup.rs/)
- Cargo (會隨 Rust 安裝)

### 執行步驟

```bash
cd rustblog

# 編譯並執行
cargo run
```

或使用提供的 script：

```bash
./run.sh
```

伺服器啟動後，訪問 http://localhost:3000

## 使用說明

### 1. 註冊帳號

1. 訪問 http://localhost:3000
2. 點擊「Register」
3. 輸入使用者名稱和密碼
4. 點擊「Sign up」

### 2. 登入

1. 訪問 http://localhost:3000/login
2. 輸入使用者名稱和密碼
3. 點擊「Log in」

### 3. 發布文章

1. 登入後訪問 http://localhost:3000/my
2. 在文字框中輸入內容
3. 點擊「Post」

### 4. 刪除文章

在自己的文章列表中，點擊文章右上角的「✕」

### 5. 評論

1. 點擊任意文章
2. 在下方文字框輸入評論
3. 點擊「Reply」

### 6. 按讚與轉分享

在公開文章列表中：
- 點擊 ❤️/🤍 可以按讚/取消按讚
- 點擊 🔄/↗️ 可以轉分享/取消轉分享

## 專案結構

```
rustblog/
├── Cargo.toml          # 專案依賴配置
├── run.sh              # 啟動腳本 (自動 kill 舊程序)
├── rustblog.db         # SQLite 資料庫 (自動建立)
└── src/
    └── main.rs         # 主程式碼
```

## 開發相關指令

```bash
# 編譯 (檢查錯誤)
cargo check

# 編譯並執行
cargo run

# 重新編譯 (清除 cache)
cargo build --force
```

## 資料表結構

- **users**: 使用者資料
- **posts**: 文章
- **comments**: 評論
- **likes**: 按讚記錄
- **shares**: 轉分享記錄
