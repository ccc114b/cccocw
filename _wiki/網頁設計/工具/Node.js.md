# Node.js

Node.js 是基於 Chrome V8 引擎的 JavaScript 執行環境，用於伺服器端開發。

## 基本使用

```javascript
// 讀取檔案
const fs = require('fs');
fs.readFile('file.txt', (err, data) => {
    console.log(data.toString());
});

// HTTP 伺服器
const http = require('http');
http.createServer((req, res) => {
    res.end('Hello World');
}).listen(3000);
```

## npm

```bash
# 初始化專案
npm init -y

# 安裝套件
npm install express

# 全域安裝
npm install -g nodemon

# 執行腳本
npm run dev
```

## Express 框架

```javascript
const express = require('express');
const app = express();

app.get('/api', (req, res) => {
    res.json({ message: 'Hello' });
});

app.listen(3000, () => {
    console.log('Server running');
});
```

## 相關概念

- [後端開發](../主題/後端開發.md)
- [JavaScript](../概念/JavaScript.md)