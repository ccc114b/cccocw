# Transformer

Transformer 基於自注意力機制，完全拋棄循環結構，成為 NLP 與 Vision 的核心模型。

## 架構

```
輸入 → 編碼器 → 解碼器 → 輸出
       │         │
       └─ Self-Attention ─┘
```

## 自注意力機制

```python
import torch.nn as nn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        self.attention = nn.MultiheadAttention(d_model, num_heads)
```

計算流程：
1. 輸入分割為 Q, K, V
2. 計算注意力權重: softmax(QKᵀ/√d)
3. 加權求和: V × 注意力權重

## 位置編碼

因為自注意力沒有順序資訊，需要加入位置編碼：

```python
PE(pos, 2i) = sin(pos/10000^(2i/d))
PE(pos, 2i+1) = cos(pos/10000^(2i/d))
```

## 經典模型

- BERT (2018): 雙向編碼器
- GPT (2018-2023): 單向解碼器
- T5 (2019): Encoder-Decoder

## 相關概念

- [循環神經網路](循環神經網路.md)
- [大型語言模型](大型語言模型.md)