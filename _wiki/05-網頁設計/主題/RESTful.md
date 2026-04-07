# RESTful

RESTful 是一種 API 設計風格，基於 REST 原則。

## 原則

1. **客戶端-伺服器分離**
2. **無狀態**: 伺服器不儲存客戶端狀態
3. **可快取**: 响应可標記為可快取
4. **分層系統**: 支援中介層
5. **統一介面**: 資源導向

## URL 設計

```
GET    /api/products          # 取得產品列表
GET    /api/products/123      # 取得單一產品
POST   /api/products          # 新增產品
PUT    /api/products/123      # 更新產品
PATCH  /api/products/123      # 部分更新
DELETE /api/products/123      # 刪除產品

GET    /api/products/123/reviews  # 產品的評論
```

## HTTP 狀態碼

| 狀態碼 | 意義 |
|--------|------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 500 | Server Error |

## 相關概念

- [API](概念/API.md)
- [後端開發](主題/後端開發.md)