# Blog 系統開發摘要

## 技術堆疊
- Node.js + Express
- SQLite (sqlite3)
- bcryptjs (密碼雜湊)
- express-session ( sessions 管理)
- marked (Markdown 渲染)

## 功能

### 用戶系統
- 註冊 `/register`
- 登入 `/login`
- 登出 `/logout`
- 密碼使用 bcrypt 加密儲存

### 貼文系統
- `/` - 公共貼文區（所有用戶的貼文）
- `/my` - 個人貼文區（可發文、刪除自己的貼文）
- `/user/:id` - 查看特定用戶的貼文
- `/post/:id` - 查看單篇貼文

### 介面設計
- 左側：導航欄 + 用戶資訊
  - 未登入：顯示 Login、Register 連結
  - 已登入：顯示 Public、My Posts 連結 + 用戶頭像 + Log out
- 主區域：寬度 700px，Threads 風格深色主題
- 發文者帳號可點擊進入該用戶版面

## 檔案結構
```
blog/
├── package.json
├── server.js      - Express 伺服器
├── database.js    - SQLite 資料庫初始化
└── blog.db        - SQLite 資料庫檔案
```

## 啟動方式
```bash
cd blog
npm install
npm start
```