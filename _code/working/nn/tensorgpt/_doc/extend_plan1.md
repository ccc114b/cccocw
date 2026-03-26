# tensorgpt 擴充規劃

## 參考來源

參考 `nn/nn0py/` 下的 Python 實作：
- `nn0.py` - autograd 引擎 + Adam 優化器
- `gpt0.py` - GPT 模型架構
- `examples/test_gpt0.py` - 訓練範例

## 專案結構

```
nn/tensorgpt/
├── Cargo.toml
├── _data/
│   └── input.txt (chinese.txt)
├── _doc/
│   └── extend_plan1.md
└── src/
    ├── main.rs           # 現有 tensor + autograd
    ├── tensor.rs          # 擴充為 tensor 模組
    ├── nn.rs              # 神經網路元件
    └── gpt.rs             # GPT 模型 + train/inference
```

## 擴充模組

### 1. tensor 模組 (src/tensor.rs)

擴充現有 autograd 引擎：

- `Value` 結構：支援向量/矩陣運算 (使用 ArrayD<f64>)
- 新增運算：
  - `matmul` - 矩陣乘法
  - `softmax` - 數值穩定 softmax
  - `rmsnorm` - RMS Normalization
  - `cross_entropy` - Cross-Entropy Loss
  - `tanh`, `sigmoid` - 其他 activation functions
- `Adam` 優化器：支援參數更新與 learning rate 衰減

### 2. nn 模組 (src/nn.rs)

神經網路元件：

- `Linear`: 線性層 `y = Wx + b`
- `RMSNorm`: RMS 正規化
- `MultiHeadAttention`: 多頭注意力機制
- `MLP`: 前饋網路 (fc1 -> relu -> fc2)
- `GPTBlock`: 一層 Transformer 區塊

### 3. gpt 模組 (src/gpt.rs)

GPT 模型與訓練：

- `GPT`: 完整模型 (embedding + n_layer × GPTBlock + lm_head)
- `train()`: 訓練迴圈
- `inference()`: 文字生成 (temperature sampling)

### 4. main.rs

- 載入 `_data/input.txt`
- Tokenizer: 字元級編碼 (char-level)
- 建立模型、訓練、生成樣本

## GPT 模型架構

參考 nn0py/gpt0.py，GPT 結構如下：

```
Token Embedding (wte) + Position Embedding (wpe)
    │
    ▼
┌─────────────────────────────────────┐
│  GPTBlock (× n_layer)                │
│  ├── RMSNorm                        │
│  ├── MultiHeadAttention             │
│  │   ├── Q, K, V (linear)           │
│  │   ├── scaled dot-product         │
│  │   ├── softmax                    │
│  │   └── output linear              │
│  ├── Residual                       │
│  ├── RMSNorm                        │
│  ├── MLP (fc1 -> relu -> fc2)       │
│  └── Residual                       │
└─────────────────────────────────────┘
    │
    ▼
Linear (lm_head) -> logits
```

## 訓練流程

1. 載入文字資料
2. 建立字元表 (vocab)
3. 初始化 GPT 模型參數
4. 建立 Adam 優化器
5. 訓練迴圈：forward -> loss -> backward -> optimizer.step()
6. 推理：给定 BOS token，逐 token 生成直到遇到 BOS

## 下一步

按照此規劃實作各模組，最終目標：
- 訓練 tensorgpt 在 chinese.txt 上
- 產生樣本輸出文字
