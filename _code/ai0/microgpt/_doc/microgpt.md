# MicroGPT 數學原理

本文档说明 `microgpt.py` 背后的数学原理。

## 1. 語言建模基礎

語言建模的目標是學習一個概率分佈 $P(\text{sequence})$，使得模型能夠根據前面的 token 預測下一個 token。具體而言，給定一個 token 序列 $t_1, t_2, \ldots, t_n$，語言模型學習：

$$P(t_{i+1} | t_1, \ldots, t_i)$$

microgpt 採用 **因果語言模型**（Causal Language Model）架構，只使用前面的上下文預測下一個 token。

## 2. Tokenizer

microgpt 使用 **字符級別的 tokenizer**。將所有文檔中的唯一字符收集起來，每個字符對應一個唯一的 token ID：

$$\text{vocab} = \{c_0, c_1, \ldots, c_{V-1}\}$$

其中 $V$ 是詞彙表大小。此外，添加了一個特殊的 **BOS**（Beginning of Sequence）token作為序列的開頭標記。

對於一個字符串 "hello"，tokenize 後變為：

$$[ \text{BOS}, \text{'h'}, \text{'e'}, \text{'l'}, \text{'l'}, \text{'o'}, \text{BOS} ]$$

## 3. 嵌入層

### Token 嵌入

每個 token ID 對應一個 $d_{\text{model}}$ 維的向量：

$$\text{emb}(t) \in \mathbb{R}^{d_{\text{model}}}$$

在 microgpt 中，$d_{\text{model}} = n_{\text{embd}} = 16$。

### 位置嵌入

 Transformer 本身不包含位置資訊，因此需要添加位置嵌入：

$$\text{pos\_emb}(p) \in \mathbb{R}^{d_{\text{model}}}$$

其中 $p$ 是位置索引，範圍為 $0$ 到 $block\_size - 1$。

### 輸入表示

最終輸入是 token 嵌入和位置嵌入的和：

$$x = \text{emb}(t) + \text{pos\_emb}(p)$$

## 4. RMSNorm

RMSNorm（Root Mean Square Normalization）是一種簡化的 Layer Normalization：

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot \gamma$$

其中

$$\text{RMS}(x) = \sqrt{\frac{1}{d} \sum_{i=1}^{d} x_i^2 + \epsilon}$$

在 microgpt 中，$\epsilon = 1e-5$，並且 $\gamma$ 設為 $1$（隱式地通過可學習參數省略實現）。

數學上，RMSNorm 可以寫成：

$$y_i = \frac{x_i}{\sqrt{\frac{1}{d}\sum_j x_j^2 + \epsilon}}$$

## 5. 多頭注意力

### 線性投影

對於輸入 $x \in \mathbb{R}^{d_{\text{model}}}$，計算 Query、Key、Value：

$$Q = W_Q \cdot x, \quad K = W_K \cdot x, \quad V = W_V \cdot x$$

其中 $W_Q, W_K, W_V \in \mathbb{R}^{d_{\text{model}} \times d_{\text{model}}}$ 是可學習的權重矩陣。

### 分頭處理

將 $Q, K, V$ 拆分為 $h$ 個頭：

$$Q = [Q_0, Q_1, \ldots, Q_{h-1}], \quad K = [K_0, K_1, \ldots, K_{h-1}], \quad V = [V_0, V_1, \ldots, V_{h-1}]$$

每個頭的維度是 $d_{\text{head}} = d_{\text{model}} / h$。

### 縮放點積注意力

對於每個頭，計算注意力分數：

$$\text{attention\_logits}_t = \frac{Q \cdot K_t}{\sqrt{d_{\text{head}}}}$$

使用 softmax 轉換為概率分佈：

$$\text{attention\_weights} = \text{softmax}(\text{attention\_logits})$$

### 注意力輸出

每個頭的輸出是價值的加權平均：

$$\text{head\_out}_j = \sum_{t} \text{attention\_weights}_t \cdot V_t[j]$$

所有頭的輸出拼接後，再通過一個輸出投影：

$$\text{attention\_output} = W_O \cdot \text{concat}(\text{head\_out}_0, \ldots, \text{head\_out}_{h-1})$$

### 殘差連接

注意力模塊的輸出通過殘差連接添加到輸入：

$$x_{\text{out}} = x_{\text{in}} + \text{attention\_output}$$

## 6. 前饋網絡（MLP）

Transformer 的前饋網絡由兩個線性層組成：

$$\text{FFN}(x) = W_{fc2} \cdot \text{Act}(W_{fc1} \cdot x)$$

其中激活函數在 microgpt 中是 **ReLU**：

$$\text{ReLU}(x) = \max(0, x)$$

第一層將維度從 $d_{\text{model}}$ 擴展到 $4 \cdot d_{\text{model}}$，第二層再縮回到 $d_{\text{model}}$。

同樣使用殘差連接：

$$x_{\text{out}} = x_{\text{in}} + \text{FFN}(x_{\text{in}})$$

## 7. 損失函數

### 交叉熵損失

對於每個位置 $pos$，模型輸出對下一個 token 的 logit：

$$\text{logits}_t = f_\theta(\text{context})$$

轉換為概率：

$$P_t = \frac{e^{\text{logits}_t}}{\sum_i e^{\text{logits}_i}}$$

對於目標 token $y$，交叉熵損失為：

$$\mathcal{L} = -\log(P_y)$$

### 總損失

對於整個序列的平均損失：

$$\mathcal{L}_{\text{total}} = \frac{1}{N} \sum_{pos=1}^{N} -\log(P_{y_{pos}})$$

其中 $N$ 是序列長度。

## 8. 反向傳播與自動微分

microgpt 實現了一個簡單的 **自動微分系統**（Autograd）。每個 `Value` 對象記錄：
- `data`：前向傳播的數值
- `grad`：反向傳播的梯度
- `_children`：計算圖中的子節點
- `_local_grads`：當前節點對每個子節點的局部導數

### 前向傳播

每個運算（如加法、乘法、指數、對數）都創建新的 Value 節點，並記錄局部梯度。

例如，對於乘法 $z = x \cdot y$：

$$\frac{\partial z}{\partial x} = y, \quad \frac{\partial z}{\partial y} = x$$

### 反向傳播

使用拓撲排序反向遍歷計算圖：

$$ \frac{\partial \mathcal{L}}{\partial v} = \sum_{c \in \text{children}(v)} \frac{\partial \mathcal{L}}{\partial c} \cdot \frac{\partial c}{\partial v} $$

從損失函數的梯度為 $1$ 開始，反向傳播直到所有參數。

## 9. Adam 優化器

Adam（Adaptive Moment Estimation）結合了動量（ Momentum）和 RMSProp 的優點：

### 計算梯度的一階矩估計（動量）：

$$m_t = \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot g_t$$

### 計算梯度的二階矩估計：

$$v_t = \beta_2 \cdot v_{t-1} + (1 - \beta_2) \cdot g_t^2$$

### 偏差校正：

$$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1 - \beta_2^t}$$

### 參數更新：

$$\theta_t = \theta_{t-1} - \eta_t \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$$

在 microgpt 中：
- $\beta_1 = 0.85$
- $\beta_2 = 0.99$
- $\epsilon = 1e-8$
- 學習率使用線性衰減：$\eta_t = \eta_{\text{initial}} \cdot (1 - t / T)$

## 10. 推理與採樣

### 溫度採樣

在生成新 token 時，使用溫度參數控制分佈的銳度：

$$\text{logits}_{\text{scaled}} = \frac{\text{logits}}{T}$$

其中 $T$ 是溫度參數（microgpt 中 $T = 0.5$）。

- 當 $T \to 0$：趨於確定性，選擇最高概率的 token
- 當 $T \to 1$：趨於均勻分佈，生成更具多樣性的文本
- 當 $T > 1$：增加隨機性，生成更具創意但可能不合語法的文本

### 貪心採樣

選擇概率最高的 token：

$$\text{token} = \arg\max_i P_i$$

### 隨機採樣

根據概率分佈隨機選擇 token：

$$\text{token} \sim P(\cdot)$$

microgpt 使用 `random.choices` 根據概率加權隨機選擇。

## 11. 總結

microgpt 實現了一個完整的神經語言模型訓練流程：

1. **數據處理**：字符級 tokenization
2. **模型前向**：嵌入 → Transformer 層 → 輸出 logit
3. **損失計算**：交叉熵損失
4. **梯度計算**：自動微分
5. **參數更新**：Adam 優化器
6. **文本生成**：溫度採樣

這個極簡實現展示了深度學習的核心數學原理，包括：
- 矩陣運算
- 非線性激活函數
- 歸一化技術
- 注意力機制
- 梯度下降與優化算法