# CSS

CSS (Cascading Style Sheets) 用於控制網頁的外觀與排版。

## 基本語法

```css
/* 選擇器 */
h1 {
    color: blue;
    font-size: 24px;
}

/* 類別 */
.highlight {
    background-color: yellow;
}

/* ID */
#header {
    position: fixed;
}
```

## 版面配置

### Flexbox

```css
.container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 10px;
}
```

### Grid

```css
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
}
```

## 響應式設計

```css
@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }
}
```

## 相關概念

- [HTML](../概念/HTML.md)
- [響應式設計](../主題/響應式設計.md)