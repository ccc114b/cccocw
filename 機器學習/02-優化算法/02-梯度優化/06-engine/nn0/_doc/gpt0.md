# gpt0.py 數學原理說明

本文件詳細說明 `gpt0.py` 模組中實現的 GPT（Generative Pre-trained Transformer）模型背後的數學原理。

## 目錄

1. [GPT 模型概述](#gpt-模型概述)
2. [Transformer 架構](#transformer-架構)
3. [位置編碼 (Positional Encoding)](#位置編碼-positional-encoding)
4. [自注意力機制 (Self-Attention)](#自注意力機制-self-attention)
5. [多头自注意力 (Multi-Head Attention)](#多头自注意力-multi-head-attention)
6. [前饋神經網路 (Feed-Forward Network)](#前饋神經網路-feed-forward-network)
7. [殘差連接與 RMS Norm](#殘差連接與-rms-norm)
8. [語言模型損失函數](#語言模型損失函數)
9. [訓練與推理](#訓練與推理)

---

## GPT 模型概述

GPT 是一種基於 Transformer 解碼器的語言模型，核心思想是：

1. **預訓練 (Pre-training)**：在大規模文本上學習預測下一個 token
2. **微調 (Fine-tuning)**：在特定任務上進行微調

本實現類似 GPT-2，採用：
- **單向注意力**：只看到前面的 context
- **RMS Norm**：取代 LayerNorm
- **ReLU**：取代 GELU 激活函數
- **無 bias**：移除了所有偏置項

---

## Transformer 架構

### 整體結構

GPT 的前向傳播流程：

```
Input Token → Token Embedding + Positional Embedding
           → RMS Norm
           → [× N Layers]
           │    ├── Multi-Head Self-Attention + Residual
           │    └── Feed-Forward Network + Residual
           → RMS Norm
           → Linear (LM Head)
           → Output Logits
```

每層的數學形式：
$$\text{Output}_l = \text{FFN}\left(\text{Attention}\left(\text{LN}(x_l)\right) + x_l\right) + x_l$$

其中 $x_l$ 是第 $l$ 層的輸入，LN 代表 Layer Normalization（本實現使用 RMS Norm）。

---

## 位置編碼 (Positional Encoding)

### 為什麼需要位置編碼？

Transformer 的自注意力機制是排列等變的（permutation equivariant），即改變輸入順序不會改變輸出。為了讓模型理解序列順序，需要額外添加位置資訊。

### 本實現的方式

本模組使用可學習的位置嵌入（Learned Positional Embedding）：

```python
sd['wpe'] = matrix(self.block_size, self.n_embd)  # 位置編碼矩陣
```

每個位置 pos_id 對應一個 d 維向量，與 token embedding 相加：

```python
x = [t + p for t, p in zip(tok_emb, pos_emb)]
```

### 數學形式

$$\text{Input}_i = \text{TokenEmbedding}(token_i) + \text{PositionEmbedding}(pos_i)$$

---

## 自注意力機制 (Self-Attention)

### 概念介紹

自注意力機制允許序列中的每個位置「注意」序列中的所有其他位置，計算它們之間的相關性（attention）。

### Q, K, V 分解

對於每個輸入向量 $x$，我們計算三個向量：

- **Query (Q)**: 我正在尋找什麼？
- **Key (K)**: 我包含什麼資訊？
- **Value (V)**: 如果匹配，我傳遞什麼？

數學形式：
$$Q = W_Q \cdot x$$
$$K = W_K \cdot x$$
$$V = W_V \cdot x$$

### Attention 計算

標準 Attention（Scaled Dot-Product Attention）：

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_k}}\right) \cdot V$$

其中：
- $d_k$ 是 key 向量的維度
- $\sqrt{d_k}$ 是縮放因子，防止梯度消失

本模組的實現：

```python
q = linear(x, sd[f'layer{li}.attn_wq'])
k = linear(x, sd[f'layer{li}.attn_wk'])
v = linear(x, sd[f'layer{li}.attn_wv'])

attn_logits = [
    sum(q_h[j] * k_h[t][j] for j in range(self.head_dim)) / self.head_dim**0.5
    for t in range(len(k_h))
]
attn_weights = softmax(attn_logits)
head_out = [
    sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h)))
    for j in range(self.head_dim)
]
```

### 數學細節

#### Query-Key 匹配

$$score(q, k) = \frac{q \cdot k}{\sqrt{d_k}}$$

這個分數衡量 query 和 key 的相似度。

#### Softmax 歸一化

$$\alpha_i = \frac{e^{score_i}}{\sum_j e^{score_j}}$$

#### 輸出加權

$$output = \sum_i \alpha_i \cdot v_i$$

這相當於根據 attention weights 對 value 向量進行加權平均。

---

## 多头自注意力 (Multi-Head Attention)

### 為什麼需要多頭？

單一 attention 頭只能學習一種類型的關係。多頭注意力允許模型同時學習多種關係：

- 語法關係
- 語義關係
- 長期依賴
- 局部模式

### 數學形式

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h) \cdot W^O$$

其中每個 head：
$$\text{head}_i = \text{Attention}(Q W_i^Q, K W_i^K, V W_i^V)$$

### 本模組的實現

```python
for h in range(self.n_head):
    hs = h * self.head_dim
    q_h = q[hs:hs + self.head_dim]
    k_h = [ki[hs:hs + self.head_dim] for ki in keys[li]]
    v_h = [vi[hs:hs + self.head_dim] for vi in values[li]]
    # ... 計算單個 head ...
    x_attn.extend(head_out)
```

每個 head 處理維度的一部分，最後拼接在一起。

### 因果注意力（Causal Attention）

GPT 是自回歸模型，只能看到當前位置之前的 tokens。這通過 mask 實現：只允許關注歷史位置。

本模組的 keys 和 values 只包含當前位置之前的 tokens（通過 `keys[li].append(k)` 累積），自然實現了因果注意力。

---

## 前饋神經網路 (Feed-Forward Network)

### 架構

每層 Transformer 還包含一個前饋網路：

```python
x = linear(x, sd[f'layer{li}.mlp_fc1'])  # 擴展維度: d_model -> 4 * d_model
x = [xi.relu() for xi in x]               # ReLU 激活
x = linear(x, sd[f'layer{li}.mlp_fc2'])  # 收縮維度: 4 * d_model -> d_model
```

### 數學形式

$$\text{FFN}(x) = W_2 \cdot \text{ReLU}(W_1 \cdot x + b_1) + b_2$$

本實現省略了 bias：
$$\text{FFN}(x) = W_2 \cdot \text{ReLU}(W_1 \cdot x)$$

維度變化：
- 輸入：$d_{model}$
- 中間：$4 \times d_{model}$（GPT-2 標準）
- 輸出：$d_{model}$

### 為什麼需要 FFN？

Self-Attention 已經可以學習 token 之間的關係，但 FFN 提供了：
1. 額外的非線性變換
2. 更多的模型容量
3. 對每個位置的獨立處理

---

## 殘差連接與 RMS Norm

### 殘差連接 (Residual Connection)

$$y = x + \mathcal{F}(x)$$

優點：
1. 緩解梯度消失問題
2. 允許梯度直接流向更深層
3. 使訓練更深的神經網路成為可能

本模組實現：
```python
x = [a + b for a, b in zip(x, x_residual)]
```

### RMS Norm

RMS Norm（Root Mean Square Normalization）：

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot \gamma$$

其中：
$$\text{RMS}(x) = \sqrt{\frac{1}{n} \sum_{i=1}^{n} x_i^2 + \varepsilon}$$

本模組簡化版本（省略 $\gamma$）：
```python
def rmsnorm(x):
    ms = sum(xi * xi for xi in x) / len(x)
    scale = (ms + 1e-5) ** -0.5
    return [xi * scale for xi in x]
```

### 與 Layer Norm 的比較

| 特性 | Layer Norm | RMS Norm |
|------|------------|----------|
| 計算公式 | 減去均值 | 不減均值 |
| 計算成本 | 較高（需計算均值） | 較低 |
| 效果 | 相當 | 相當 |

---

## 語言模型損失函數

### Next Token Prediction

GPT 的訓練目標是預測下一個 token。給定序列 $(t_1, t_2, \ldots, t_n)$：

$$\mathcal{L} = -\sum_{i=1}^{n-1} \log P(t_{i+1} | t_1, \ldots, t_i)$$

### 交叉熵實現

```python
def cross_entropy(logits, target_id):
    max_val = max(val.data for val in logits)
    exps = [(val - max_val).exp() for val in logits]
    total = sum(exps)
    return total.log() - (logits[target_id] - max_val)
```

數學推導：
$$\text{CrossEntropy}(logits, target) = -\log \frac{e^{logit_{target}}}{\sum_i e^{logit_i}}$$

應用 Log-Sum-Exp 技巧：
$$= \log\left(\sum_i e^{logit_i - M}\right) - (logit_{target} - M)$$

其中 $M = \max_i(logit_i)$

### 多位置損失平均

```python
for pos_id in range(n):
    token_id, target_id = tokens[pos_id], tokens[pos_id + 1]
    logits = model(token_id, pos_id, keys, values)
    probs = softmax(logits)
    loss_t = -probs[target_id].log()
    losses.append(loss_t)
loss = (1 / n) * sum(losses)
```

平均所有位置的損失以獲得最終的訓練信號。

---

## 訓練與推理

### 訓練流程

```python
def gd(model, optimizer, tokens, step, num_steps):
    # 1. 構建 context window
    keys   = [[] for _ in range(model.n_layer)]
    values = [[] for _ in range(model.n_layer)]

    losses = []
    # 2. 對每個位置進行前向傳播
    for pos_id in range(n):
        logits = model(token_id, pos_id, keys, values)
        loss_t = -softmax(logits)[target_id].log()
        losses.append(loss_t)

    # 3. 計算平均損失
    loss = (1 / n) * sum(losses)

    # 4. 反向傳播
    loss.backward()

    # 5. 更新參數（學習率衰減）
    lr_t = optimizer.lr * (1 - step / num_steps)
    optimizer.step(lr_override=lr_t)
```

### 推理流程（文字生成）

```python
def inference(model, uchars, BOS, num_samples=20, temperature=0.5):
    for sample_idx in range(num_samples):
        keys   = [[] for _ in range(model.n_layer)]
        values = [[] for _ in range(model.n_layer)]
        token_id = BOS

        for pos_id in range(model.block_size):
            logits = model(token_id, pos_id, keys, values)
            # Temperature sampling
            probs = softmax([l / temperature for l in logits])
            token_id = random.choices(range(vocab_size), weights=probs)[0]
            if token_id == BOS:
                break
            sample.append(uchars[token_id])
```

### Temperature Sampling

Temperature 控制生成的隨機性：
- **temperature = 0**: 貪心解碼，總是選擇最高概率的 token
- **temperature = 1**: 標準 softmax
- **temperature > 1**: 增加隨機性，分布更均勻

數學形式：
$$P_i = \frac{e^{logit_i / T}}{\sum_j e^{logit_j / T}}$$

---

## 模型參數初始化

### 權重初始化

```python
def _init_params(self, std=0.08):
    def matrix(nout, nin):
        return [[Value(random.gauss(0, std)) for _ in range(nin)]
                for _ in range(nout)]
```

使用高斯分佈初始化，標準差設為 0.08（較小的值）。

### 初始化策略

- **Token Embeddings**: $N(0, 0.08)$
- **Position Embeddings**: $N(0, 0.08)$
- **Query/Key/Value/Output 投影**: $N(0, 0.08)$
- **MLP 權重**: $N(0, 0.08)$
- **LM Head**: $N(0, 0.08)$

---

## 總結

`gpt0.py` 實現了一個完整的小型 GPT 模型，包含：

1. **Transformer 解碼器架構**：單向自注意力 + 前饋網路
2. **可學習的位置編碼**：讓模型理解序列順序
3. **Multi-Head Attention**：同時學習多種關係類型
4. **殘差連接 + RMS Norm**：穩定訓練過程
5. **ReLU 激活函數**：計算高效的非線性
6. **自迴歸生成**：通過因果注意力實現
7. **Temperature Sampling**：控制生成多樣性

這個實現保留了 GPT 的核心思想，儘管規模較小，但數學原理與完整版 GPT-2 完全一致。
