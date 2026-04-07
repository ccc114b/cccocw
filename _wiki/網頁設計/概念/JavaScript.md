# JavaScript

JavaScript 是網頁的程式語言，實現互動功能。

## 基本語法

```javascript
// 變數
let x = 5;
const y = 10;

// 函數
function greet(name) {
    return `Hello, ${name}!`;
}

// 箭頭函數
const add = (a, b) => a + b;

// 類別
class Person {
    constructor(name) {
        this.name = name;
    }
    greet() {
        console.log(`Hello, ${this.name}`);
    }
}
```

## DOM 操作

```javascript
// 選擇元素
const el = document.querySelector('#app');

// 修改內容
el.textContent = 'New content';

// 新增元素
const newEl = document.createElement('div');
el.appendChild(newEl);

// 事件
el.addEventListener('click', () => {
    console.log('Clicked!');
});
```

## 非同步

```javascript
// Promise
fetch('/api/data')
    .then(res => res.json())
    .then(data => console.log(data));

// Async/Await
async function loadData() {
    const res = await fetch('/api/data');
    const data = await res.json();
    return data;
}
```

## 相關概念

- [HTML](../概念/HTML.md)
- [前端框架](../主題/前端框架.md)
- [API](../概念/API.md)