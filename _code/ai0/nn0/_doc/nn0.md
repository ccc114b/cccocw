# nn0.py 數學原理說明

本文件詳細說明 `nn0.py` 模組中實現的自動微分引擎與優化器背後的數學原理。

## 目錄

1. [自動微分 (Automatic Differentiation)](#自動微分-automatic-differentiation)
2. [Value 類別與反向傳播](#value-類別與反向傳播)
3. [Adam 優化器](#adam-優化器)
4. [損失函數與激活函數](#損失函數與激活函數)
5. [矩陣運算](#矩陣運算)

---

## 自動微分 (Automatic Differentiation)

### 為什麼需要自動微分？

在神經網路訓練中，我們需要計算損失函數相對於每個參數的梯度，以進行梯度下降優化。傳統的數值微分（Numerical Differentiation）精度低且計算量大；符號微分（Symbolic Differentiation）則可能產生複雜的表達式。自動微分（Autograd）結合了兩者的優點，能夠精確且高效地計算梯度。

### 前向模式 vs 反向模式

自動微分有兩種主要模式：

| 模式 | 計算方式 | 適用場景 |
|------|----------|----------|
| 前向模式 (Forward Mode) | 從輸入到輸出計算導數 | 輸入維度少、輸出維度多的情況 |
| **反向模式 (Reverse Mode)** | 從輸出到輸入計算導數 | 輸入維度多、輸出維度少的情況 ← **本模組採用** |

神經網路通常有大量參數但損失是單一標量，因此反向模式（反向傳播）是最佳選擇。

---

## Value 類別與反向傳播

### Value 節點的設計

`nn0.py` 中的 `Value` 類別是自動微分的核心。每個 `Value` 節點儲存：
- `data`: 實際數值
- `grad`: 梯度值（初始為 0）
- `_children`: 子節點（構成計算圖的節點）
- `_local_grads`: 局部梯度（相對於每個子節點的偏導數）

### 計算圖的構建

當執行運算時（如 `+`、`*`），自動構建計算圖：

```python
def __add__(self, other):
    other = other if isinstance(other, Value) else Value(other)
    return Value(self.data + other.data, (self, other), (1, 1))
```

這裡的 `(1, 1)` 表示：
- ∂(a+b)/∂a = 1
- ∂(a+b)/∂b = 1

### 鏈式法則 (Chain Rule)

反向傳播的核心是鏈式法則。對於複合函數 f(g(x))：
$$\frac{df}{dx} = \frac{df}{dg} \cdot \frac{dg}{dx}$$

在程式碼中，通過 `_local_grads` 儲存每個局部導數，然後在反向傳播時累乘：

```python
def backward(self):
    # ... 建立拓撲排序 ...
    for v in reversed(topo):
        for child, local_grad in zip(v._children, v._local_grads):
            child.grad += local_grad * v.grad
```

這正是鏈式法則的實現：∂L/∂child = ∂L/∂parent × ∂parent/∂child

---

### 各運算的梯度公式

#### 加法 (Addition)
$$f(a, b) = a + b$$
$$\frac{\partial f}{\partial a} = 1, \quad \frac{\partial f}{\partial b} = 1$$

程式碼體現：
```python
return Value(self.data + other.data, (self, other), (1, 1))
```

#### 乘法 (Multiplication)
$$f(a, b) = a \cdot b$$
$$\frac{\partial f}{\partial a} = b, \quad \frac{\partial f}{\partial b} = a$$

程式碼體現：
```python
return Value(self.data * other.data, (self, other), (other.data, self.data))
```

#### 冪函數 (Power)
$$f(a) = a^n$$
$$\frac{\partial f}{\partial a} = n \cdot a^{n-1}$$

程式碼體現：
```python
def __pow__(self, other):
    return Value(self.data**other, (self,), (other * self.data**(other - 1),))
```

#### 指數函數 (Exponential)
$$f(a) = e^a$$
$$\frac{\partial f}{\partial a} = e^a$$

程式碼體現：
```python
def exp(self):
    return Value(math.exp(self.data), (self,), (math.exp(self.data),))
```

#### 對數函數 (Logarithm)
$$f(a) = \ln(a)$$
$$\frac{\partial f}{\partial a} = \frac{1}{a}$$

程式碼體現：
```python
def log(self):
    return Value(math.log(self.data), (self,), (1 / self.data,))
```

#### ReLU 激活函數
$$\text{ReLU}(a) = \max(0, a)$$
$$\frac{\partial \text{ReLU}}{\partial a} = \begin{cases} 1 & \text{if } a > 0 \\ 0 & \text{if } a \leq 0 \end{cases}$$

程式碼體現：
```python
def relu(self):
    return Value(max(0, self.data), (self,), (float(self.data > 0),))
```

---

## Adam 優化器

### 傳統梯度下降的問題

標準梯度下降使用固定學習率：
$$\theta_{t+1} = \theta_t - \eta \cdot \nabla L(\theta_t)$$

問題：
1. 學習率難以設定（太大震盪，太小收斂慢）
2. 所有參數使用相同學習率
3. 容易陷入局部最小值

### Adam 的核心思想

Adam（Adaptive Moment Estimation）結合了兩個主要改進：

1. **動量 (Momentum)**: 累積過去梯度的方向，類似物理中的動量
2. **自適應學習率 (Adaptive Learning Rate)**: 每個參數根據梯度歷史調整學習率

### Adam 的數學推導

#### 第一步：計算梯度

$$\nabla L(\theta_t) = g_t$$

#### 第二步：更新一階矩估計（動量）

$$m_t = \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot g_t$$

這類似於指數移動平均，$\beta_1$ 通常設為 0.9。

#### 第三步：更新二階矩估計（梯度平方）

$$v_t = \beta_2 \cdot v_{t-1} + (1 - \beta_2) \cdot g_t^2$$

這記錄了梯度平方的累積，用於調整學習率。

#### 第四步：偏差修正

由於 m₀ 和 v₀ 初始為 0，在早期會低估這些值。修正公式：

$$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}$$
$$\hat{v}_t = \frac{v_t}{1 - \beta_2^t}$$

#### 第五步：參數更新

$$\theta_{t+1} = \theta_t - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \varepsilon}$$

其中 $\varepsilon = 10^{-8}$ 是防止除零的常數。

### 程式碼實現

```python
def step(self, lr_override=None):
    self.step_count += 1
    lr = lr_override if lr_override is not None else self.lr
    for i, p in enumerate(self.params):
        # 一階矩估計
        self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * p.grad
        # 二階矩估計
        self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * p.grad ** 2
        # 偏差修正
        m_hat = self.m[i] / (1 - self.beta1 ** self.step_count)
        v_hat = self.v[i] / (1 - self.beta2 ** self.step_count)
        # 參數更新
        p.data -= lr * m_hat / (v_hat ** 0.5 + self.eps)
        p.grad = 0
```

### 學習率線性衰減

為了在訓練後期精細調整，學習率隨時間線性衰減：

$$\eta_t = \eta_0 \cdot \left(1 - \frac{t}{T}\right)$$

其中 $t$ 是當前步數，$T$ 是總步數。

---

## 損失函數與激活函數

### Softmax 函數

Softmax 將 logits 轉換為機率分布：

$$\text{Softmax}(x)_i = \frac{e^{x_i}}{\sum_{j} e^{x_j}}$$

**數值穩定性問題**：當 x_i 很大時，e^{x_i} 可能溢出。

**解決方案**：減去最大值 M
$$\text{Softmax}(x)_i = \frac{e^{x_i - M}}{\sum_{j} e^{x_j - M}}$$

其中 $M = \max(x)$，這不會改變結果，因為：
$$\frac{e^{x_i - M}}{\sum_j e^{x_j - M}} = \frac{e^{x_i}/e^M}{\sum_j e^{x_j}/e^M} = \frac{e^{x_i}}{\sum_j e^{x_j}}$$

### 交叉熵損失 (Cross-Entropy Loss)

對於分類問題：
$$L = -\log(p_{target})$$

直接使用 logits 計算可以避免 softmax 的數值問題：
$$L = \log\left(\sum_i e^{x_i - M}\right) - (x_{target} - M)$$

這稱為 **Log-Sum-Exp 技巧**。

### RMS Normalization

RMS Norm 是 Layer Norm 的簡化版本，計算成本更低：

$$\text{RMS}(x) = \sqrt{\frac{1}{n} \sum_{i=1}^{n} x_i^2 + \varepsilon}$$

$$\text{RMSNorm}(x)_i = \frac{x_i}{\text{RMS}(x)} \cdot \gamma_i$$

本模組中省略了可學習的 $\gamma$ 和 $\beta$：
```python
def rmsnorm(x):
    ms = sum(xi * xi for xi in x) / len(x)
    scale = (ms + 1e-5) ** -0.5
    return [xi * scale for xi in x]
```

---

## 矩陣運算

### 線性層 (Linear Layer)

$$y = W \cdot x + b$$

其中：
- $W \in \mathbb{R}^{n_{out} \times n_{in}}$ 是權重矩陣
- $x \in \mathbb{R}^{n_{in}}$ 是輸入向量
- $b \in \mathbb{R}^{n_{out}}$ 是偏置向量
- $y \in \mathbb{R}^{n_{out}}$ 是輸出向量

每個輸出元素的計算：
$$y_i = \sum_{j=1}^{n_{in}} W_{ij} \cdot x_j + b_i$$

程式碼實現：
```python
def linear(x, w):
    """矩陣乘法：y = W @ x"""
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]
```

---

## 總結

`nn0.py` 實現了一個完整的神經網路訓練框架：

1. **自動微分**：通過構建計算圖並應用鏈式法則，精確計算每個參數的梯度
2. **Adam 優化器**：結合動量與自適應學習率，有效收斂
3. **數值穩定**：通過 Log-Sum-Exp 等技巧避免數值溢出
4. **模組化設計**：每個組件（激活函數、歸一化、損失函數）都可以獨立使用
