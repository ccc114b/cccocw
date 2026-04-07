# HTTP

HTTP 是無狀態的請求/回應協定。

## 請求格式

```
GET /path HTTP/1.1
Host: example.com
User-Agent: Mozilla/5.0
Accept: text/html

```

## 回應格式

```
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 123

<html>...</html>
```

## 請求方法

| 方法 | 說明 |
|------|------|
| GET | 取得資源 |
| POST | 提交資料 |
| PUT | 更新資源 |
| DELETE | 刪除資源 |

## 狀態碼

| 狀態碼 | 說明 |
|--------|------|
| 200 | OK |
| 301 | 永久轉向 |
| 302 | 暫時轉向 |
| 404 | 找不到 |
| 500 | 伺服器錯誤 |

## 相關概念

- [TCP-IP協定](../主題/TCP-IP协定.md)
- [網路](../概念/網路.md)