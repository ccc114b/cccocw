# GitHub Flavored Markdown 數學公式指南

本文件說明在 GitHub 上撰寫 Markdown 時，數學公式的呈現方式與注意事項。

## 目錄

1. [GitHub 數學公式支援](#github-數學公式支援)
2. [行內公式](#行內公式)
3. [區塊公式](#區塊公式)
4. [LaTeX 數學符號](#latex-數學符號)
5. [常見問題與解決方案](#常見問題與解決方案)
6. [排版建議](#排版建議)

---

## GitHub 數學公式支援

### 支援程度

GitHub README 和 Issue 對數學公式的支援如下：

| 環境 | 數學公式支援 |
|------|--------------|
| GitHub README (.md) | ✅ 支援（使用 LaTeX） |
| GitHub Issue | ✅ 支援 |
| GitHub PR | ✅ 支援 |
| GitHub Gist | ✅ 支援 |

### 啟用方式

在 GitHub 上，數學公式通過 MathJax 或 KaTeX 渲染，無需額外設定。只需使用 `$...$` 或 `$$...$$` 語法。

---

## 行內公式

### 語法

使用單個 `$` 包圍公式：

```markdown
這是行內公式：$E = mc^2$
```

### 呈現效果

這是行內公式：$E = mc^2$

### 適用場景

- 簡短的變數或符號
- 嵌入句子中的小型表達式
- 單行文字中的數學符號

### 範例

```markdown
損失函數為 $L = -\log(p_{target})$
```

呈現：損失函數為 $L = -\log(p_{target})$

---

## 區塊公式

### 語法

使用雙重 `$` 包圍公式：

```markdown
$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$
```

### 呈現效果

$$
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
$$

### 適用場景

- 複雜的多行公式
- 需要獨立展示的推導過程
- 較長的數學表達式

### 範例

```markdown
$$
\hat{m}_t = \frac{m_t}{1 - \beta_1^t}
$$
```

呈現：
$$
\hat{m}_t = \frac{m_t}{1 - \beta_1^t}
$$

---

## LaTeX 數學符號

### 基本運算符

| 數學意義 | LaTeX 語法 | 呈現 |
|----------|-----------|------|
| 加減 | `a \pm b` | $a \pm b$ |
| 乘號（點） | `a \cdot b` | $a \cdot b$ |
| 乘號（叉） | `a \times b` | $a \times b$ |
| 除號 | `a / b` 或 `\frac{a}{b}` | $a / b$ 或 $\frac{a}{b}$ |
| 等於 | `=` | $=$ |
| 不等於 | `\neq` | $\neq$ |
| 大於/小於 | `>`, `<`, `\geq`, `\leq` | $>$, $<$, $\geq$, $\leq$ |

### 分數與根號

| 數學意義 | LaTeX 語法 | 呈現 |
|----------|-----------|------|
| 分數 | `\frac{a}{b}` | $\frac{a}{b}$ |
| 平方根 | `\sqrt{x}` | $\sqrt{x}$ |
| n次方根 | `\sqrt[n]{x}` | $\sqrt[n]{x}$ |
| 指數 | `a^{n}` | $a^{n}$ |
| 下標 | `a_{i}` | $a_{i}$ |

### 希臘字母

| 字母 | LaTeX 語法 | 呈現 |
|------|-----------|------|
| alpha | `\alpha` | $\alpha$ |
| beta | `\beta` | $\beta$ |
| gamma | `\gamma`, `\Gamma` | $\gamma$, $\Gamma$ |
| delta | `\delta`, `\Delta` | $\delta$, $\Delta$ |
| epsilon | `\epsilon` | $\epsilon$ |
| theta | `\theta`, `\Theta` | $\theta$, $\Theta$ |
| lambda | `\lambda`, `\Lambda` | $\lambda$, $\Lambda$ |
| mu | `\mu` | $\mu$ |
| sigma | `\sigma`, `\Sigma` | $\sigma$, $\Sigma$ |
| phi | `\phi`, `\Phi` | $\phi$, $\Phi$ |
| omega | `\omega`, `\Omega` | $\omega$, $\Omega$ |

### 運算符號

| 數學意義 | LaTeX 語法 | 呈現 |
|----------|-----------|------|
| 求和 | `\sum_{i=1}^{n}` | $\sum_{i=1}^{n}$ |
| 積分 | `\int_{a}^{b}` | $\int_{a}^{b}$ |
| 極限 | `\lim_{x \to \infty}` | $\lim_{x \to \infty}$ |
| 連乘 | `\prod_{i=1}^{n}` | $\prod_{i=1}^{n}$ |
| 絕對值 | `|x|` 或 `\lvert x \rvert` | $|x|$ |

### 特殊符號

| 數學意義 | LaTeX 語法 | 呈現 |
|----------|-----------|------|
| 無限 | `\infty` | $\infty$ |
| 偏導數 | `\partial` | $\partial$ |
| 梯度 | `\nabla` | $\nabla$ |
| 屬於 | `\in` | $\in$ |
| 包含 | `\subset`, `\subseteq` | $\subset$, $\subseteq$ |
| 屬於 | `\forall` | $\forall$ |
| 存在 | `\exists` | $\exists$ |
| 空格 | `\,` `\:` `\quad` | 不同大小的空格 |

### 矩陣

```markdown
$$
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
$$
```

呈現：
$$
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
$$

### 分段函數

```markdown
$$
\text{ReLU}(x) = \begin{cases}
1 & \text{if } x > 0 \\
0 & \text{if } x \leq 0
\end{cases}
$$
```

呈現：
$$
\text{ReLU}(x) = \begin{cases}
1 & \text{if } x > 0 \\
0 & \text{if } x \leq 0
\end{cases}
$$

---

## 常見問題與解決方案

### 問題 1：公式不渲染

**原因**：使用了不支援的語法或特殊字元衝突

**解決方案**：
- 確保使用正確的 `$` 或 `$$` 語法
- 檢查是否有未轉義的 `_` 或 `^`（應使用 `\_` 或 `\^`）

### 問題 2：下標/上標在行內公式中顯示錯誤

**原因**：行內公式中多個字元需要用大括號包裹

**錯誤**：
```markdown
$x_i = 1$  <!-- 正確 -->
$x_i+1 = 2$  <!-- 錯誤：+1 不會顯示為下標 -->
```

**正確**：
```markdown
$x_i + 1 = 2$  <!-- 正確 -->
$x_{i+1} = 2$  <!-- 正確：i+1 作為下標 -->
```

### 問題 3：與 Markdown 語法衝突

**原因**：`*`, `_`, `\` 等字元在 Markdown 和 LaTeX 中都有特殊意義

**解決方案**：
- 在文字中使用 `\*`, `\_`, `\\` 轉義
- 在公式中正常使用，GitHub 會正確渲染

### 問題 4：公式中顯示文字

**解決方案**：使用 `\text{文字}` 或 `\mathrm{文字}`

```markdown
$\text{Hello World}$
```

呈現：$\text{Hello World}$

### 問題 5：大型公式換行

**解決方案**：

```markdown
$$
\begin{aligned}
f(x) &= x^2 + 2x + 1 \\
    &= (x + 1)^2
\end{aligned}
$$
```

呈現：
$$
\begin{aligned}
f(x) &= x^2 + 2x + 1 \\
    &= (x + 1)^2
\end{aligned}
$$

---

## 排版建議

### 1. 公式與文字的間距

- 行內公式與文字之間自動有間距
- 區塊公式前後建議空一行

```markdown
這是文字。

$$
公式
$$

這是另一段文字。
```

### 2. 公式編號

GitHub Markdown 不支援自動公式編號。可手動編號：

```markdown
$$
E = mc^2 \tag{1}
$$
```

### 3. 引用公式

使用 `(\#)` 語法引用：

```markdown
如公式 $(\#1)$ 所示...
```

### 4. 代碼區塊中的公式

如果要在程式碼區塊中顯示 LaTeX 語法（而非渲染），可使用一般程式碼區塊：

```python
# 這是程式碼，不是公式
# \frac{a}{b} 會直接顯示，不會渲染
```

### 5. 避免的写法

| 不推薦 | 推薦 |
|--------|------|
| `$$x^2$$`（行內使用雙$） | `$x^2$` |
| `$a b$`（缺少運算符） | `$a \cdot b$` |
| `x_i=1`（下標未包大括） | `$x_i=1$` 或 `$x_{i}=1$` |

---

## 快速查詢表

### 常用公式範例

```markdown
# 鏈式法則
$\frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx}$

# Softmax
$\text{Softmax}(x)_i = \frac{e^{x_i}}{\sum_j e^{x_j}}$

# Sigmoid
$\sigma(x) = \frac{1}{1 + e^{-x}}$

# 矩陣乘法
$(AB)_{ij} = \sum_k A_{ik} \cdot B_{kj}$

# 交叉熵
$L = -\sum_i y_i \log(\hat{y}_i)$

# 歐拉公式
$e^{i\pi} + 1 = 0$
```

---

## 總結

1. **行內公式**：使用單 `$...$`
2. **區塊公式**：使用雙 `$$...$$`
3. **複雜結構**：使用 `\begin{}` 環境
4. **文字說明**：使用 `\text{}`
5. **轉義**：Markdown 特殊字元在公式外需要轉義

遵循以上原則，即可在 GitHub 上正確呈現數學公式。
