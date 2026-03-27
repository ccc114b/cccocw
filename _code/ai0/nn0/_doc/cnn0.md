# cnn0.py 數學原理說明

本文件詳細說明 `cnn0.py` 模組中實現的 CNN（Convolutional Neural Network，卷積神經網路）模型背後的數學原理。

## 目錄

1. [CNN 概述](#cnn-概述)
2. [卷積層 (Conv2d)](#卷積層-conv2d)
3. [池化層 (MaxPool2d)](#池化層-maxpool2d)
4. [全連接層 (Linear)](#全連接層-linear)
5. [激活函數](#激活函數)
6. [權重初始化](#權重初始化)
7. [CNN 模型架構](#cnn-模型架構)
8. [梯度流動與反向傳播](#梯度流動與反向傳播)

---

## CNN 概述

卷積神經網路（CNN）是處理網格結構數據（如圖像）的核心架構。與全連接網路相比，CNN 的優勢：

1. **局部連接**：每個神經元只連接輸入的局部區域
2. **權重共享**：同一卷積核在整個輸入上共享
3. **平移不變性**：對輸入的平移具有魯棒性
4. **層次化特徵提取**：逐層提取從簡單到複雜的特徵

---

## 卷積層 (Conv2d)

### 概念介紹

卷積層使用**卷積核**（或稱**濾波器**）在輸入圖像上滑動，進行局部特徵提取。

### 數學定義

對於輸入 $x \in \mathbb{R}^{C_{in} \times H \times W}$ 和卷積核 $w \in \mathbb{R}^{C_{out} \times C_{in} \times k_h \times k_w}$：

$$y_{c_{out}, i, j} = b_{c_{out}} + \sum_{c_{in}=1}^{C_{in}} \sum_{k_h=0}^{K_h-1} \sum_{k_w=0}^{K_w-1} x_{c_{in}, i+k_h, j+k_w} \cdot w_{c_{out}, c_{in}, k_h, k_w}$$

其中：
- $C_{in}$: 輸入通道數
- $C_{out}$: 輸出通道數
- $K_h, K_w$: 卷積核尺寸
- $b$: 偏置

### 輸出尺寸計算

$$H_{out} = H_{in} - K_h + 1$$
$$W_{out} = W_{in} - K_w + 1$$

### 本模組實現

```python
class Conv2d:
    def __init__(self, in_channels, out_channels, kernel_size):
        self.in_c = in_channels
        self.out_c = out_channels
        self.ks = kernel_size
        
        # 權重維度: [out_channels][in_channels][kernel_size][kernel_size]
        self.w = [[[[Value(random.uniform(-bound, bound)) for _ in range(kernel_size)]
                    for _ in range(kernel_size)]
                   for _ in range(in_channels)]
                  for _ in range(out_channels)]
        # 偏置: [out_channels]
        self.b = [Value(0.0) for _ in range(out_channels)]

    def __call__(self, x):
        C, H, W = len(x), len(x[0]), len(x[0][0])
        out_H = H - self.ks + 1
        out_W = W - self.ks + 1

        out = []
        for oc in range(self.out_c):
            out_c_map = []
            for i in range(out_H):
                row = []
                for j in range(out_W):
                    val = self.b[oc]
                    for ic in range(self.in_c):
                        for ki in range(self.ks):
                            for kj in range(self.ks):
                                val = val + x[ic][i+ki][j+kj] * self.w[oc][ic][ki][kj]
                    row.append(val)
                out_c_map.append(row)
            out.append(out_c_map)
        return out
```

### 卷積的可視化理解

```
輸入 (5x5)          卷積核 (3x3)         輸出 (3x3)
+---+---+---+---+---+
| 1 | 2 | 3 | 4 | 5 |     +---+---+---+
+---+---+---+---+---+     | a | b | c |
| 6 | 7 | 8 | 9 |10 |  *  | d | e | f |  =  局部特徵
+---+---+---+---+---+     | g | h | i |
|11 |12 |13 |14 |15 |     +---+---+---+
+---+---+---+---+---+
|16 |17 |18 |19 |20 |
+---+---+---+---+---+
|21 |22 |23 |24 |25 |
+---+---+---+---+---+

卷積核在每個位置進行 element-wise 乘法並求和
```

---

## 池化層 (MaxPool2d)

### 目的

池化層（Pooling）的主要作用：
1. **降低維度**：減少特徵圖的空間尺寸
2. **提取主要特徵**：保留最顯著的特征
3. **增加感受野**：讓後續層看到更大範圍
4. **提供平移不變性**：輕微的平移不會改變輸出

### Max Pooling 數學定義

對於輸入 $x \in \mathbb{R}^{C \times H \times W}$，核大小 $K$，步幅 $S$：

$$y_{c, i, j} = \max_{k_h \in [0, K)} \max_{k_w \in [0, K)} x_{c, i \cdot S + k_h, j \cdot S + k_w}$$

### 輸出尺寸計算

$$H_{out} = \left\lfloor \frac{H_{in}}{S} \right\rfloor$$
$$W_{out} = \left\lfloor \frac{W_{in}}{S} \right\rfloor$$

### 本模組實現

```python
class MaxPool2d:
    def __init__(self, kernel_size=2, stride=2):
        self.ks = kernel_size
        self.stride = stride

    def __call__(self, x):
        C, H, W = len(x), len(x[0]), len(x[0][0])
        out_H = H // self.stride
        out_W = W // self.stride

        out = []
        for c in range(C):
            out_c_map = []
            for i in range(out_H):
                row = []
                for j in range(out_W):
                    pool_vals = []
                    for ki in range(self.ks):
                        for kj in range(self.ks):
                            pool_vals.append(x[c][i*self.stride + ki][j*self.stride + kj])
                    max_v = max(pool_vals, key=lambda v: v.data)
                    row.append(max_v)
                out_c_map.append(row)
            out.append(out_c_map)
        return out
```

### Max Pooling 的自動微分

Max Pooling 的反向傳播有一個重要特性：**梯度只流向最大值的位置**。

```python
# 選擇數值最大的 Value 節點
# 這會自動將梯度導向該節點，完美實現 Max Pooling 自動微分！
max_v = max(pool_vals, key=lambda v: v.data)
```

數學上：
$$\frac{\partial L}{\partial x_{i,j}} = \begin{cases} 
\frac{\partial L}{\partial y_{i',j'}} & \text{if } (i,j) = \arg\max(\text{pool window}) \\
0 & \text{otherwise}
\end{cases}$$

這正是 max 函數的偏導數特性。

---

## 全連接層 (Linear)

### 數學定義

$$y = W \cdot x + b$$

- $W \in \mathbb{R}^{out\_features \times in\_features}$: 權重矩陣
- $x \in \mathbb{R}^{in\_features}$: 輸入向量
- $b \in \mathbb{R}^{out\_features}$: 偏置向量
- $y \in \mathbb{R}^{out\_features}$: 輸出向量

每個輸出元素的計算：
$$y_i = b_i + \sum_{j=1}^{in\_features} w_{ij} \cdot x_j$$

### 本模組實現

```python
class Linear:
    def __init__(self, in_features, out_features):
        self.in_f = in_features
        self.out_f = out_features
        bound = math.sqrt(6.0 / in_features)
        self.w = [[Value(random.uniform(-bound, bound)) for _ in range(in_features)] 
                  for _ in range(out_features)]
        self.b = [Value(0.0) for _ in range(out_features)]

    def __call__(self, x):
        out = []
        for i in range(self.out_f):
            val = self.b[i]
            for j in range(self.in_f):
                val = val + x[j] * self.w[i][j]
            out.append(val)
        return out
```

---

## 激活函數

### ReLU (Rectified Linear Unit)

本模組使用 ReLU 作為激活函數：

$$\text{ReLU}(x) = \max(0, x)$$

$$\frac{d}{dx}\text{ReLU}(x) = \begin{cases} 1 & \text{if } x > 0 \\ 0 & \text{if } x \leq 0 \end{cases}$$

### 程式碼實現

```python
x = [[[v.relu() for v in row] for row in c_map] for c_map in x]
```

### ReLU 的優勢

1. **計算高效**：只需要比較操作
2. **緩解梯度消失**：正區間梯度恆為 1
3. **稀疏激活性**：會使部分神經元輸出為 0
4. **生物學合理性**：與神經元的「全有或全無」特性相似

---

## 權重初始化

### He Uniform 初始化

本模組使用 He Uniform 初始化（又稱 Kaiming Uniform），這是為 ReLU 激活函數設計的：

```python
fan_in = in_channels * kernel_size * kernel_size
bound = math.sqrt(6.0 / fan_in)
self.w = [[[Value(random.uniform(-bound, bound)) for _ in range(kernel_size)]
            for _ in range(kernel_size)]
           for _ in range(in_channels)]
          for _ in range(out_channels)]
```

### 數學推導

對於 ReLU 及其變體，權重的方差應為：
$$\text{Var}(W) = \frac{2}{fan_{in}}$$

均勻分佈在 $[-limit, limit]$ 之間，其中：
$$limit = \sqrt{\frac{6}{fan_{in}}}$$

### 為什麼需要初始化？

- **過小初始化**：梯度會在層間，指數級衰减（梯度消失）
- **過大初始化**：梯度會在層間爆炸（梯度爆炸）
- **合適的初始化**：保持信號和梯度的合理範圍

---

## CNN 模型架構

### 模型結構

```python
class CNN:
    def __init__(self):
        # 假設輸入影像經過了降採樣，尺寸為 1x14x14
        # 卷積後: 4x12x12
        self.conv1 = Conv2d(in_channels=1, out_channels=4, kernel_size=3)
        # 池化後: 4x6x6
        self.pool1 = MaxPool2d(kernel_size=2, stride=2)
        # 全連接映射到 10 個類別 (0~9)
        self.fc1 = Linear(in_features=4 * 6 * 6, out_features=10)
```

### 完整前向傳播

```python
def __call__(self, x):
    # 1. 卷積層
    x = self.conv1(x)
    
    # 2. ReLU 激活
    x = [[[v.relu() for v in row] for row in c_map] for c_map in x]
    
    # 3. 池化層
    x = self.pool1(x)
    
    # 4. Flatten (展平)
    x_flat = []
    for c_map in x:
        for row in c_map:
            x_flat.extend(row)
            
    # 5. 全連接層
    out = self.fc1(x_flat)
    return out
```

### 資料流示意

```
輸入圖像 (1, 14, 14)
    ↓
卷積層 Conv2d(1→4, kernel=3)
    ↓
特徵圖 (4, 12, 12)
    ↓
ReLU 激活
    ↓
MaxPool2d(kernel=2, stride=2)
    ↓
特徵圖 (4, 6, 6)
    ↓
Flatten
    ↓
向量 (144)
    ↓
全連接層 Linear(144→10)
    ↓
輸出 logits (10)
```

### 各層參數數量

| 層 | 參數計算 | 參數數量 |
|----|----------|----------|
| Conv2d | $4 \times 1 \times 3 \times 3 + 4$ | 40 |
| Linear | $144 \times 10 + 10$ | 1450 |
| **總計** | | **1490** |

---

## 梯度流動與反向傳播

### CNN 反向傳播的特殊性

CNN 的反向傳播需要處理：

1. **卷積層**：梯度需要「反卷積」操作
2. **池化層**：梯度只流向最大值位置
3. **展平操作**：梯度均勻分配給每個元素

### 利用 nn0.py 的自動微分

本模組完全依賴 `nn0.py` 的 `Value` 類別來處理梯度：

```python
from nn0 import Value
```

所有運算（乘法、加法、ReLU）都通過 `Value` 類別的運算符重載完成，自動構建計算圖並執行反向傳播。

### 梯度流動示意

```
輸出 Loss
    ↑
全連接層梯度 (1490 個參數的梯度)
    ↑
Flatten (恆等映射)
    ↑
MaxPool2d 梯度 (只有最大值位置有梯度)
    ↑
ReLU 梯度 (ReLU'(x) * 上層梯度)
    ↑
Conv2d 梯度 (4×3×3×1 + 4 個參數的梯度)
    ↑
輸入梯度
```

---

## 總結

`cnn0.py` 實現了一個完整的手寫數字識別 CNN 模型，包含：

1. **卷積層 (Conv2d)**：通過局部連接和權重共享提取圖像特徵
2. **池化層 (MaxPool2d)**：降低維度並提供平移不變性，利用自動微分實現梯度路由
3. **ReLU 激活**：高效的非線性變換
4. **全連接層 (Linear)**：將特徵映射到類別空間
5. **He Uniform 初始化**：為 ReLU 設計的權重初始化策略
6. **展平操作**：將 2D 特徵圖轉換為 1D 向量

這個實現保留了 CNN 的核心思想，通過 `nn0.py` 的自動微分引擎處理所有梯度計算，展示了 CNN 的數學原理在實際代碼中的體現。
