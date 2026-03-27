# Youbook 網站設計教學手冊

## 課程概述

本教學手冊旨在帶領學生從頭開始建立一個類似 Twitter/Threads 的社群網站應用程式。學生將學會如何使用 Node.js、Express 和 SQLite 來建構一個功能完整的網站。

---

## 第一章：環境建置

### 1.1 安裝 Node.js

1. 前往 [Node.js 官網](https://nodejs.org/) 下載 LTS 版本
2. 安裝完成後，在終端機輸入以下指令驗證：
   ```bash
   node --version
   npm --version
   ```

### 1.2 建立專案

```bash
mkdir youbook
cd youbook
npm init -y
```

### 1.3 安裝所需套件

```bash
npm install express sqlite3 bcryptjs express-session
```

### 1.4 專案結構

```
youbook/
├── package.json
├── server.js        # 主伺服器檔案
├── database.js     # 資料庫設定
└── blog.db         # SQLite 資料庫（自動產生）
```

---

## 第二章：資料庫設計

### 2.1 資料庫初始化

建立 `database.js`：

```javascript
const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./blog.db');

db.serialize(() => {
  // 用戶資料表
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
  
  // 貼文資料表
  db.run(`
    CREATE TABLE IF NOT EXISTS posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      content TEXT NOT NULL,
      author_id INTEGER,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (author_id) REFERENCES users(id)
    )
  `);
});

module.exports = db;
```

### 2.2 資料表說明

| 資料表 | 用途 | 欄位 |
|--------|------|------|
| users | 儲存用戶資訊 | id, username, password, created_at |
| posts | 儲存貼文 | id, title, content, author_id, created_at |

### 2.3 新增互動功能資料表

```javascript
// 回應資料表
db.run(`
  CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
  )
`);

// 喜歡資料表
db.run(`
  CREATE TABLE IF NOT EXISTS likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
  )
`);

// 轉貼資料表
db.run(`
  CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
  )
`);
```

**練習題 2.1**：為每個資料表畫出 ER 圖，標明主鍵、外鍵和關聯性。

---

## 第三章：Express 伺服器基礎

### 3.1 建立第一個伺服器

建立 `server.js`：

```javascript
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello Youbook!');
});

app.listen(3000, () => {
  console.log('Server running at http://localhost:3000');
});
```

### 3.2 中間件（Middleware）

Express 使用中間件來處理請求：

```javascript
// 解析 JSON 和 URL 編碼的請求體
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Session 管理
const session = require('express-session');
app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 }
}));
```

### 3.3 路由（Routes）

路由是用戶訪問的 URL 對應的處理函數：

```javascript
app.get('/path', (req, res) => {
  // 處理 GET 請求
});

app.post('/path', (req, res) => {
  // 處理 POST 請求
});

app.delete('/path', (req, res) => {
  // 處理 DELETE 請求
});
```

**練習題 3.1**：建立一個 `/about` 路由，返回「這是一個社群網站」。

---

## 第四章：用戶系統

### 4.1 密碼加密

使用 bcrypt 來安全地儲存密碼：

```javascript
const bcrypt = require('bcryptjs');

// 密碼雜湊
bcrypt.hash(password, 10, (err, hash) => {
  // 儲存 hash 到資料庫
});

// 密碼比對
bcrypt.compare(inputPassword, storedHash, (err, match) => {
  if (match) {
    // 密碼正確
  }
});
```

### 4.2 註冊功能

```javascript
app.post('/register', (req, res) => {
  const { username, password } = req.body;
  
  bcrypt.hash(password, 10, (err, hash) => {
    db.run('INSERT INTO users (username, password) VALUES (?, ?)', 
      [username, hash], (err) => {
        // 處理錯誤或成功
      });
  });
});
```

### 4.3 登入功能

```javascript
app.post('/login', (req, res) => {
  const { username, password } = req.body;
  
  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    bcrypt.compare(password, user.password, (err, match) => {
      if (match) {
        req.session.userId = user.id;
        req.session.username = user.username;
        res.redirect('/');
      }
    });
  });
});
```

### 4.4 Session 保護

建立登入驗證中介層：

```javascript
function requireLogin(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
}

// 使用方式
app.get('/my', requireLogin, (req, res) => {
  // 只有登入才能訪問
});
```

**練習題 4.1**：實作登出功能，清除 session 並重新導向到登入頁面。

---

## 第五章：貼文系統

### 5.1 發布貼文

```javascript
app.post('/posts', requireLogin, (req, res) => {
  const { content } = req.body;
  const authorId = req.session.userId;
  
  db.run('INSERT INTO posts (title, content, author_id) VALUES (?, ?, ?)',
    [content.substring(0, 50), content, authorId], (err) => {
      res.redirect('/my');
    });
});
```

### 5.2 查詢貼文

```javascript
// 查詢所有貼文（關聯用戶名稱）
db.all(`
  SELECT posts.*, users.username 
  FROM posts 
  LEFT JOIN users ON posts.author_id = users.id 
  ORDER BY created_at DESC
`, [], (err, rows) => {
  // rows 是陣列
});

// 查詢單一貼文
db.get('SELECT * FROM posts WHERE id = ?', [postId], (err, row) => {
  // row 是物件
});
```

### 5.3 刪除貼文

```javascript
app.delete('/post/:id', requireLogin, (req, res) => {
  const postId = req.params.id;
  const userId = req.session.userId;
  
  db.run('DELETE FROM posts WHERE id = ? AND author_id = ?',
    [postId, userId], (err) => {
      res.json({ success: true });
    });
});
```

**練習題 5.1**：實作編輯貼文功能。

---

## 第六章：互動功能

### 6.1 回應功能

```javascript
// 新增回應
app.post('/post/:id/comment', requireLogin, (req, res) => {
  const postId = req.params.id;
  const { content } = req.body;
  const authorId = req.session.userId;
  
  db.run('INSERT INTO comments (post_id, author_id, content) VALUES (?, ?, ?)',
    [postId, authorId, content], (err) => {
      res.redirect(`/post/${postId}`);
    });
});

// 查詢回應
db.all('SELECT comments.*, users.username FROM comments LEFT JOIN users ON comments.author_id = users.id WHERE post_id = ? ORDER BY created_at DESC', [postId], (err, rows) => {
  // 處理回應列表
});
```

### 6.2 喜歡功能

```javascript
// 切換喜歡狀態
app.post('/post/:id/like', requireLogin, (req, res) => {
  const postId = req.params.id;
  const userId = req.session.userId;
  
  // 檢查是否已經喜歡
  db.get('SELECT id FROM likes WHERE post_id = ? AND user_id = ?',
    [postId, userId], (err, row) => {
      if (row) {
        // 已喜歡，移除
        db.run('DELETE FROM likes WHERE post_id = ? AND user_id = ?', [postId, userId]);
      } else {
        // 未喜歡，新增
        db.run('INSERT INTO likes (post_id, user_id) VALUES (?, ?)', [postId, userId]);
      }
    });
});

// 計算喜歡數
db.get('SELECT COUNT(*) as count FROM likes WHERE post_id = ?', [postId], (err, row) => {
  const likeCount = row.count;
});
```

### 6.3 轉貼功能

轉貼功能的實作方式與喜歡類似，使用 `shares` 資料表記錄。

**練習題 6.1**：實作轉貼功能並顯示轉貼數。

---

## 第七章：前端頁面

### 7.1 HTML 模板

使用 Template Literals 建立 HTML：

```javascript
const layout = (title, content) => `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>
    /* CSS 樣式 */
  </style>
</head>
<body>
  ${content}
</body>
</html>`;
```

### 7.2 頁面結構

常見的頁面配置：
- **側邊欄**：導航選單、用戶資訊
- **主內容區**：貼文列表、發布表單
- **樣式**：使用深色主題（參考 Twitter/Threads 風格）

### 7.3 動態內容渲染

使用 map 函數渲染貼文列表：

```javascript
const postsHtml = posts.map(post => `
  <div class="post">
    <div class="post-header">
      <span class="username">${post.username}</span>
      <span class="time">${new Date(post.created_at).toLocaleString()}</span>
    </div>
    <div class="post-content">${post.content}</div>
  </div>
`).join('');
```

### 7.4 表單處理

```html
<form method="post" action="/posts">
  <textarea name="content" placeholder="在想什麼？"></textarea>
  <button type="submit">發布</button>
</form>
```

**練習題 7.1**：為發布表單加入字數限制和剩餘字數顯示。

---

## 第八章：實務考量

### 8.1 安全性

- **SQL Injection**：使用參數化查詢而非字串拼接
- **密碼儲存**：永遠使用 bcrypt 雜湊密碼
- **Session 安全**：設定適當的 cookie 選項

### 8.2 效能優化

- 資料庫索引：為常用查詢欄位建立索引
- 非同步處理：避免阻塞事件循環
- 快取策略：考慮快取常用查詢結果

### 8.3 錯誤處理

```javascript
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something went wrong!');
});
```

---

## 習題總覽

| 章節 | 練習題 | 說明 |
|------|--------|------|
| 2 | 練習題 2.1 | 畫出資料表 ER 圖 |
| 3 | 練習題 3.1 | 建立 /about 路由 |
| 4 | 練習題 4.1 | 實作登出功能 |
| 5 | 練習題 5.1 | 實作編輯貼文 |
| 6 | 練習題 6.1 | 實作轉貼功能 |
| 7 | 練習題 7.1 | 加入字數限制 |

---

## 參考資源

- [Node.js 官方文檔](https://nodejs.org/docs/)
- [Express 官方文檔](https://expressjs.com/)
- [SQLite 教程](https://www.sqlite.org/docs.html)
- [bcrypt 文檔](https://www.npmjs.com/package/bcryptjs)

---

*本教學手冊適用於網站設計課程，建議學生完成每個練習後再進行下一章。*