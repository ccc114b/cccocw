# tensorgpt 擴充測試計劃

## 測試策略

使用 `cargo test` 執行測試，参考現有 `main.rs` 中的 gradient test 模式。

---

## 1. Tensor 模組測試

### 1.1 基本運算測試 (現有)

```rust
#[test]
fn test_add_grad() { ... }

#[test]
fn test_mul_grad() { ... }

#[test]
fn test_relu_grad() { ... }

#[test]
fn test_log_grad() { ... }

#[test]
fn test_exp_grad() { ... }

#[test]
fn test_pow_grad() { ... }
```

### 1.2 新增運算測試

```rust
#[test]
fn test_matmul_grad() { ... }
// 驗證: y = Wx, dy/dW = dy * x^T, dy/dx = W^T * dy

#[test]
fn test_softmax_grad() { ... }
// 驗證: softmax + cross_entropy backward = logits - labels

#[test]
fn test_rmsnorm_grad() { ... }
// 驗證: RMSNorm 的梯度計算

#[test]
fn test_cross_entropy_grad() { ... }
// 驗證: CrossEntropy loss 的梯度

#[test]
fn test_tanh_grad() { ... }

#[test]
fn test_sigmoid_grad() { ... }
```

### 1.3 優化器測試

```rust
#[test]
fn test_adam_update() { ... }
// 驗證 Adam 更新參數的正確性
// 確認 lr 衰減、bias correction 正確運作
```

---

## 2. NN 模組測試

### 2.1 層結構測試

```rust
#[test]
fn test_linear_forward() { ... }
// 驗證矩陣乘法輸出正確

#[test]
fn test_linear_backward() { ... }
// 驗證梯度傳播到權重與輸入

#[test]
fn test_rmsnorm_forward() { ... }
// 驗證 RMSNorm 輸出

#[test]
fn test_rmsnorm_backward() { ... }
```

### 2.2 注意力機制測試

```rust
#[test]
fn test_multihead_attention_forward() { ... }
// 驗證 Q、K、V 計算與 attention 输出

#[test]
fn test_multihead_attention_causal() { ... }
// 驗證 causal mask (未來位置不 attending)

#[test]
fn test_multihead_attention_backward() { ... }
```

### 2.3 MLP 測試

```rust
#[test]
fn test_mlp_forward() { ... }
// 驗證 fc1 -> relu -> fc2

#[test]
fn test_mlp_backward() { ... }
```

### 2.4 GPTBlock 測試

```rust
#[test]
fn test_gpt_block_forward() { ... }
// 驗證完整 block: attn + mlp + residual

#[test]
fn test_gpt_block_backward() { ... }
```

---

## 3. GPT 模組測試

### 3.1 模型初始化測試

```rust
#[test]
fn test_gpt_init() { ... }
// 驗證參數數量正確

#[test]
fn test_gpt_embedding_dims() { ... }
// 驗證 embedding dimension 正確
```

### 3.2 前向傳播測試

```rust
#[test]
fn test_gpt_forward_single_token() { ... }
// 單一 token 前向傳播

#[test]
fn test_gpt_forward_multi_token() { ... }
// 多 token (block_size) 前向傳播

#[test]
fn test_gpt_logits_shape() { ... }
// 驗證輸出 logits 維度為 vocab_size
```

### 3.3 訓練測試

```rust
#[test]
fn test_gpt_training_step() { ... }
// 驗證一步訓練: forward -> loss -> backward -> update

#[test]
fn test_gpt_loss_decreases() { ... }
// 驗證 loss 隨訓練下降
```

### 3.4 推理測試

```rust
#[test]
fn test_gpt_inference_bos() { ... }
// 驗證從 BOS 開始生成

#[test]
fn test_gpt_inference_stops_at_bos() { ... }
// 驗證遇到 BOS 停止生成

#[test]
fn test_gpt_inference_temperature() { ... }
// 驗證不同 temperature 輸出不同
```

---

## 4. 整合測試

### 4.1 簡單資料測試

```rust
#[test]
fn test_train_on_simple_text() { ... }
// 用簡短文字訓練，驗證模型能學習
```

### 4.2 中文資料測試

```rust
#[test]
fn test_train_on_chinese() { ... }
// 使用 _data/input.txt 訓練
// 驗證 loss 收斂
```

### 4.3 端到端測試

```rust
#[test]
fn test_full_pipeline() { ... }
// 載入資料 -> tokenizer -> 訓練 -> 生成 -> 驗證輸出不為空
```

---

## 測試資料來源

- 現有測試使用簡單 scalar 值
- 新測試使用 small tensor 驗證矩陣運算
- 整合測試使用 `_data/input.txt`

---

## 執行測試

```bash
cargo test
```

---

## 優先順序

1. **高優先**: 基本運算 + Adam (確保核心正確)
2. **中優先**: Linear + RMSNorm + MLP (基礎層)
3. **中優先**: Attention (GPT 核心)
4. **低優先**: GPT 完整流程 + 推理
5. **最低**: 整合測試 (需手動驗證輸出品質)
