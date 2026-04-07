# WebSocket

WebSocket 實現雙向即時通訊，適合聊天室、即時更新等場景。

## 與 HTTP 的比較

| 特性 | HTTP | WebSocket |
|------|------|-----------|
| 方向 | 請求-回應 | 雙向 |
| 連線 | 每次新建 | 持續 |
| 狀態 | 無狀態 | 有狀態 |

## 客戶端

```javascript
const ws = new WebSocket('ws://localhost:8080');

ws.onopen = () => {
    console.log('Connected');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

ws.send(JSON.stringify({
    type: 'message',
    content: 'Hello'
}));

ws.onclose = () => {
    console.log('Disconnected');
};
```

## 伺服端 (Node.js)

```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws) => {
    ws.on('message', (message) => {
        // 廣播給所有客戶端
        wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    });
});
```

## 相關概念

- [後端開發](主題/後端開發.md)
- [HTTP](02-系統程式/主題/HTTP.md)