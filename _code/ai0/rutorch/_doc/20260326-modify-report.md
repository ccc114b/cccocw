# rutorch 修改報告 (20260326)

## 問題與修改

### 1. 空 prompt 處理
- **問題**：`prompt = ""` 時，`vocab.encode_lossy("")` 返回空 Vec，導致後續處理錯誤
- **修復**：當 `ids.is_empty()` 時插入預設 token (index 0)

### 2. Greedy Decoding 重複問題
- **問題**：模型生成時持續選擇最高機率的 token，導致輸出重複
- **修復**：加入 repeat window 機制
  - 檢查最近 10 個 token
  - 如果候選 token 在 window 內，選擇次高的

### 3. GPT epochs 參數未傳遞
- **問題**：`demo_char_gpt` 硬編碼 `epochs = 20`，命令行傳入的 epoch 參數無效
- **修復**：修改函數簽名接收 `epochs` 參數

### 4. decode 邊界檢查
- **問題**：`vocab.decode()` 可能存取越界 index
- **修復**：加入 `if i < self.itos.len()` 檢查

## 修改的函數

1. `generate_text` (main.rs:296)
2. `generate_gpt` (main.rs:562)
3. `demo_char_gpt` (main.rs:417)
4. `decode` (text.rs:41)
