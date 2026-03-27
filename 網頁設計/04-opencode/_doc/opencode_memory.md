# OpenCode 使用記憶

## 專案資訊

- **工作目錄**: `/Users/ccc/Desktop/ccc/cccocw/網頁設計/04-opencode`
- **專案**: Node.js + SQLite 網誌系統（Threads 風格）

## 快速啟動

```bash
cd /Users/ccc/Desktop/ccc/cccocw/網頁設計/04-opencode/blog
npm start
```

然後瀏覽 http://localhost:3000

## 檔案結構

```
04-opencode/
├── blog/
│   ├── package.json
│   ├── server.js          # 主程式
│   ├── database.js        # 資料庫
│   └── blog.db            # SQLite 資料庫
└── _doc/
    ├── blog-summary.md           # 摘要
    ├── blog-ai-ccc-chat.md       # 對話紀錄
    └── blog_code_detail.md       # 程式碼詳解
```

## 功能

- 用戶註冊/登入/登出
- 公共貼文區 `/`
- 個人貼文區 `/my`
- 發文、刪除貼文
- 點擊帳號查看用戶貼文 `/user/:id`

## Git

已更新 `.gitignore` 加入 Node.js 相關規則（node_modules、package-lock.json 等）。