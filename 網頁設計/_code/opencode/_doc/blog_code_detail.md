# Blog 系統程式碼詳細解說

## 一、專案結構

```
blog/
├── package.json      # 專案設定與依賴
├── database.js       # SQLite 資料庫初始化
├── server.js         # Express 伺服器主程式
└── blog.db            # SQLite 資料庫檔案（自動產生）
```

## 二、資料庫設計（database.js）

### 資料表：users（用戶）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| username | TEXT | 使用者名稱，必須唯一 |
| password | TEXT | 密碼（bcrypt 雜湊後儲存） |
| created_at | DATETIME | 建立時間，預設為 NOW |

### 資料表：posts（貼文）
| 欄位 | 類型 | 說明 |
|------|------|------|
| id | INTEGER | 主鍵，自動遞增 |
| title | TEXT | 標題（取內文前 50 字） |
| content | TEXT | 貼文內容 |
| author_id | INTEGER | 發文者 ID，外鍵關聯 users |
| created_at | DATETIME | 建立時間，預設為 NOW |

## 三、伺服器端（server.js）

### 3.1 初始化設定
```javascript
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(session({...}));
```
- `express.json()` - 解析 JSON 請求體
- `express.urlencoded()` - 解析表單資料
- `express-session` - 管理使用者 sessions

### 3.2 中間件（Middleware）

**用於將 session 資料傳到模板：**
```javascript
app.use((req, res, next) => {
  res.locals.userId = req.session.userId;
  res.locals.username = req.session.username;
  next();
});
```

**登入驗證：**
```javascript
function requireLogin(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
}
```

### 3.3 資料庫操作函式

| 函式 | 功能 |
|------|------|
| getUserPosts(userId, cb) | 取得某用戶的所有貼文 |
| getAllPosts(cb) | 取得所有貼文（JOIN users 表） |
| getUserById(userId, cb) | 依 ID 取得用戶資料 |
| getPost(id, cb) | 取得單篇貼文（含發文者名稱） |
| addPost(content, authorId, cb) | 新增貼文 |
| deletePost(id, userId, cb) | 刪除貼文（需作者本人） |
| findUser(username, cb) | 以帳號查詢用戶 |
| createUser(username, password, cb) | 建立新用戶（密碼雜湊） |

### 3.4 路由說明

| 路徑 | 方法 | 說明 |
|------|------|------|
| `/` | GET | 公共貼文區（需登入） |
| `/my` | GET | 個人貼文區（需登入） |
| `/user/:id` | GET | 查看特定用戶的貼文 |
| `/post/:id` | GET | 查看單篇貼文 |
| `/posts` | POST | 發表新貼文（需登入） |
| `/post/:id` | DELETE | 刪除貼文（需登入且為作者） |
| `/login` | GET/POST | 登入頁面/處理登入 |
| `/register` | GET/POST | 註冊頁面/處理註冊 |
| `/logout` | GET | 登出 |

### 3.5 密碼安全

密碼雜湊流程：
```javascript
// 註冊時
bcrypt.hash(password, 10, (err, hash) => {
  db.run('INSERT INTO users (username, password) VALUES (?, ?)', [username, hash], ...);
});

// 登入時
bcrypt.compare(password, user.password, (err, match) => {
  if (match) { /* 登入成功 */ }
});
```
- 使用 bcrypt 的 cost factor 10 進行雜湊
- 雜湊後的密碼無法還原，即使資料庫外洩也無法取得原始密碼

## 四、介面設計（HTML/CSS）

### 4.1 模板引擎
不使用外部模板引擎，而是透過 JavaScript 模板字串生成 HTML。

### 4.2 共用佈局（layout 函式）
```javascript
const layout = (title, content) => `<!DOCTYPE html>
<html>
<head>
  <title>${title}</title>
  <style>...</style>
</head>
<body>${content}</body>
</html>`;
```

### 4.3 左側邊欄（sidebar 函式）
根據登入狀態顯示不同內容：
- **已登入**：Public、My Posts、用戶頭像、Log out
- **未登入**：Login、Register

### 4.4 Threads 風格樣式
- 深色背景 (#000)
- 灰色分隔線 (#2d2d2d)
- 紫色漸層頭像
- 圓角導航項目
- 響應式最大寬度 700px

## 五、運作流程範例

### 發文流程
1. 瀏覽器 POST /posts（含 session）
2. server 檢查 requireLogin（未登入則轉向 /login）
3. 取得 req.body.content
4. 呼叫 addPost(content, req.session.userId, callback)
5. 寫入 SQLite
6. redirect /my

### 刪除流程
1. 瀏覽器點擊刪除鈕，觸發 JavaScript fetch('/post/:id', {method: 'DELETE'})
2. server 檢查 requireLogin
3. 執行 deletePost(id, userId)（WHERE id=? AND author_id=?）
4. 只能刪除自己的貼文

## 六、安全考量

| 項目 | 處理方式 |
|------|----------|
| SQL Injection | 使用參數化查詢（? 佔位符） |
| 密碼儲存 | bcrypt 雜湊 |
| Session 安全 | secret key + cookie 設定 |
| XSS | 輸出時基本防護（內容直接輸出） |
| 未授權存取 | requireLogin 中間件 |

## 七、啟動方式

```bash
cd blog
npm install   # 首次安裝依賴
npm start     # 啟動伺服器
# 瀏覽 http://localhost:3000
```

首次啟動會自動建立 blog.db 資料庫和資料表。