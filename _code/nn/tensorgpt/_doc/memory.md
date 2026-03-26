# tensorgpt 專案記憶

## 專案目標

建立一個 Rust 專案，從頭實作 GPT 模型，使用自訂的 Tensor+Autograd 系統建构在 ndarray 之上，類似 microgpt.py 的做法。目標是透過從頭建构 autograd 來學習它是如何運作的。

## 專案結構

```
nn/tensorgpt/
├── Cargo.toml           # 依賴: ndarray, rand
└── src/main.rs         # Tensor+Autograd 實作 (目前 gradient tests 通過!)
```

## 目前進度

### 已完成

1. **Tensor 結構** - 使用 `ndarray::ArrayD<f64>`
2. **TensorPool** - 記憶體管理
3. **基本運算**:
   - `add` - 加法
   - `mul` - 乘法
   - `relu` - ReLU  activation
   - `log` - 對數
   - `exp` - 指數
   - `pow` - 幂運算
4. **反向傳播** - 使用拓撲排序
5. **Gradient tests** - 全部 6 個測試通過!

### 待完成

1. 添加更多 GPT 需要的運算 (matmul, softmax, layer norm, embedding)
2. 實作 GPT 模型架構 (embedding, attention, MLP, etc.)
3. 加入優化器 (Adam)
4. 加入訓練迴圈
5. 加入推論/ sampling
6. 使用中文 input.txt 測試

## 參考資源

- `nn/rustgpt/` - 之前的純 Rust 實作 (scalar-by-scalar autograd)
- `nn/nn0c/` - C 實作
- `computer0/ai/nn0/nn0c/` - 較新的 C 實作，輸出較好

## Cargo.toml 內容

```toml
[package]
name = "tensorgpt"
version = "0.1.0"
edition = "2021"

[dependencies]
ndarray = "0.15"
rand = "0.8"
```

## 下一步

繼續在 `src/main.rs` 中添加:
1. `matmul` - 矩陣乘法
2. `softmax` - softmax activation
3. `layer_norm` - Layer Normalization
4. `embedding` - 詞嵌入
5. `tanh`, `sigmoid` - 其他 activation functions

然後實作完整的 GPT 模型架構。
