# React

React 是 Facebook 開發的 UI 框架，專注於元件化開發。

## 基本元件

```jsx
import React from 'react';

function Welcome({ name }) {
    return <h1>Hello, {name}!</h1>;
}

// 使用
<Welcome name="John" />
```

## 狀態管理

```jsx
import { useState } from 'react';

function Counter() {
    const [count, setCount] = useState(0);
    return (
        <button onClick={() => setCount(c => c + 1)}>
            Clicked {count} times
        </button>
    );
}
```

## Hooks

```jsx
// 副作用
useEffect(() => {
    fetchData();
}, []);  // 依賴陣列

// 上下文
const value = useContext(MyContext);

// 自訂 Hook
function useCustom() {
    const [state, setState] = useState(null);
    return { state, setState };
}
```

## 生態

- **Next.js**: SSR/SSG 框架
- **Redux**: 狀態管理
- **React Router**: 路由
- **React Native**: 行動應用

## 相關概念

- [前端框架](主題/前端框架.md)
- [JavaScript](概念/JavaScript.md)