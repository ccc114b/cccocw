# API

API (Application Programming Interface) 是軟體間溝通的介面。

## REST API

```javascript
// RESTful 路由
GET    /users      # 取得使用者列表
GET    /users/1    # 取得 ID 為 1 的使用者
POST   /users      # 新增使用者
PUT    /users/1    # 更新使用者
DELETE /users/1    # 刪除使用者
```

## JSON 格式

```json
{
    "name": "John",
    "age": 30,
    "email": "john@example.com",
    "skills": ["JavaScript", "Python"]
}
```

## Fetch API

```javascript
// GET
fetch('/api/users')
    .then(res => res.json())
    .then(data => console.log(data));

// POST
fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'John' })
});
```

## GraphQL

```graphql
query {
    user(id: 1) {
        name
        email
        posts {
            title
        }
    }
}
```

## 相關概念

- [RESTful](RESTful.md)
- [JavaScript](JavaScript.md)