# c0computer 編譯器發展計劃

## RISC-V 指令集擴展測試計劃

### 已支援的擴展

| 擴展 | 名稱 | 狀態 | 說明 |
|------|------|------|------|
| **RV64I** | 64-bit 基本整數 | ✓ 完成 | add, sub, and, or, xor, slt, sll, sr, load, store, branch, jump |
| **RV64IM** | 乘除法 | ✓ 完成 | mul, mulh, mulhu, div, divu, rem, remu 及 32-bit 版本 |

### 待支援的擴展測試計劃

#### 階段 RVM: M 擴展 (乘法/除法) - 現已完成
- [x] mul, mulh, mulhu, mulw
- [x] div, divu, divw, divuw
- [x] rem, remu, remw, remuw
- 測試檔案: test_arith.c, test_function.c

#### 階段 RVA: A 擴展 (原子操作)
| 優先級 | 指令 | 測試檔案 |
|--------|------|----------|
| 高 | lr.w, sc.w, lr.d, sc.d | test_atomic.c |
| 高 | amoadd.w, amoadd.d | test_atomic.c |
| 中 | amoswap.w, amoswap.d | test_atomic.c |
| 低 | amoand.w, amoor.w, amoxor.w | test_atomic.c |

#### 階段 RVF: F 擴展 (單精度浮點)
| 優先級 | 指令 | 測試檔案 |
|--------|------|----------|
| 高 | fadd.s, fsub.s, fmul.s, fdiv.s | test_float.c |
| 高 | flw, fsw, flw | test_float.c |
| 中 | feq.s, flt.s, fle.s | test_float.c |
| 中 | fcvt.w.s, fcvt.s.w | test_float.c |
| 低 | fsqrt.s, fmax.s, fmin.s | test_float.c |

#### 階段 RVD: D 擴展 (雙精度浮點)
| 優先級 | 指令 | 測試檔案 |
|--------|------|----------|
| 高 | fadd.d, fsub.d, fmul.d, fdiv.d | test_double.c |
| 高 | fld, fsd | test_double.c |
| 中 | fcvt.d.s, fcvt.s.d | test_double.c |
| 低 | fsqrt.d | test_double.c |

#### 階段 RVB: B 擴展 (位元操作)
| 優先級 | 指令 | 測試檔案 |
|--------|------|----------|
| 高 | andn, orn, xnor | test_bitop.c |
| 高 | clz, ctz, pcnt | test_bitop.c |
| 中 | max, maxu, min, minu | test_bitop.c |
| 低 | rol, ror, rori | test_bitop.c |
| 低 | bclr, bset, binv | test_bitop.c |

#### 階段 RVC: C 擴展 (壓縮指令)
- 支援 16-bit 壓縮指令格式
- 需要修改組譯器和解譯器
- 測試: 比較程式大小

#### 階段 RVV: V 擴展 (向量指令)
| 優先級 | 指令類別 | 測試檔案 |
|--------|----------|----------|
| 高 | vsetvl, vle.v, vse.v | test_vector.c |
| 中 | vadd.vv, vsub.vv, vmul.vv | test_vector.c |
| 低 | vload.v, vstore.v | test_vector.c |

### 測試案例建檔

在 `compiler/_data/` 目錄下建立對應測試檔案：

```bash
# 原子操作測試
test_atomic.c      # A 擴展

# 浮點數測試
test_float.c       # F 擴展
test_double.c      # D 擴展

# 位元操作測試
test_bitop.c       # B 擴展

# 向量測試
test_vector.c      # V 擴展

# 更多基礎測試
test_neg.c         # 負數運算
test_divzero.c     # 除以零處理
test_overflow.c    # 溢位處理
test_compare64.c   # 64-bit 比較
test_shift64.c     # 64-bit 移位
```

### 測試執行方式

```bash
# 執行所有測試
./test.sh

# 執行特定擴展測試
make test_atomic
make test_float
make test_double
make test_bitop

# 單一測試
make test_float && ./rv0/rv0vm -e 0x0 _data/test_float.o
```

---

## 發展策略：測試驅動開發 (TDD)

### 核心原則
1. **每次只改動一個小功能**
2. **先寫測試，再實作功能**
3. **確保現有功能不被破壞**（回歸測試）
4. **小步前進，避免大幅重構**

---

## 階段一：鞏固基礎設施

### 1.1 建立自動化測試框架
```
目標：每個禮拜新增測試案例
```

建立 `compiler/_test/` 目錄結構：
```
_test/
  c0c/
    test_arith.c      # 算術運算
    test_logic.c      # 邏輯運算
    test_control.c    # 控制流 (if, for, while)
    test_function.c   # 函數呼叫
    test_pointer.c    # 指標運算
    test_array.c      # 陣列
    test_struct.c     # 結構體
  rv0/
    test_rv_insts.c  # 測試各 RISC-V 指令
```

### 1.2 改進 Makefile
```makefile
# 目標
test:          # 執行所有測試
test_c0c:      # 只測 c0c
test_rv0:      # 只測 rv0
test_regress:  # 執行回歸測試，確保不破壞現有功能
```

### 1.3 為每個元件建立測試腳本
```bash
# 測試流程
1. 編譯測試程式 (c0c 或 clang)
2. 組譯 (rv0as)
3. 執行 (rv0vm)
4. 檢查輸出/回傳值
5. 記錄結果
```

---

## 階段二：完善 RISC-V 虛擬機 (rv0vm)

### 2.1 優先順序（由常用到少用）

| 優先級 | 指令類別 | 具體指令 | 狀態 |
|--------|----------|----------|------|
| 高 | 算術 | add, sub, mul, div, rem, addw, subw, mulw, divw, remw | ✓ 完成 |
| 高 | 邏輯 | and, or, xor, andi, ori, xori | ✓ 完成 |
| 中 | 移位 | sll, srl, sra, sllw, srlw, sraw | ✓ 完成 |
| 中 | 比較 | slt, sltu, slti, sltiu | ✓ 完成 |
| 低 | 載入/儲存 | lbu, lhu, sb, sh | ✓ 完成 |
| 低 | 環境 | ecall, ebreak | ✓ 完成 |

### 2.2 實作步驟
```
每次實作一個指令類別：
1. 找到使用該指令的測試案例
2. 在 rv0vm.c 新增支援
3. 執行測試，確認通過
4. 記錄在 CHANGELOG.md
```

---

## 階段三：完善 RISC-V 組譯器 (rv0as)

### 3.1 需要支援的指令

參考階段 2.1 的指令表，確保每個指令都能被正確組譯。

### 3.2 改進方向
- 支援更多偽指令 (pseudo-instructions)
- 改善錯誤訊息
- 支援更多組譯器指示詞 (directives)

---

## 階段四：完善 c0c 編譯器

### 4.1 當前問題
- c0c → ll0c → rv0as 的管線有問題
- 目前需要用 clang-21 作為替代

### 4.2 發展順序
```
1. 先讓 c0c 輸出正確的 LLVM IR
2. 修復 ll0c 輸出正確的 RISC-V assembly
3. 確保 c0c + ll0c + rv0as + rv0vm 完整管線運作
```

## 階段六：效能與優化

### 6.1 執行效率
- 優化 rv0vm 解譯速度
- 加入 JIT 編譯（進階）

### 6.2 錯誤處理
- 改善編譯器錯誤訊息
- 加入除錯資訊輸出

---

## 開發流程建議

### 每次開發的標準流程
```
1. 選擇一個小功能或修復
2. 找到或建立相關測試案例
3. 確認測試失敗（預期行為）
4. 實作功能
5. 確認測試通過
6. 執行回歸測試
7. 提交變更，記錄在 CHANGELOG
```

### 程式碼品質原則
- **保持簡單** (KISS)
- **不要預先優化** (YAGNI)
- **每次只改一點**
- **寫測試別寫太多**

---

## 短期目標（1-2 週）

1. [x] 建立 `_test/` 目錄結構
2. [x] 新增 10 個基礎測試案例
3. [x] 完善 rv0vm：支援 div, rem, 邏輯運算
4. [x] 完善 rv0as：支援 RV64I + M 完整指令集
5. [x] 建立自動化測試腳本 (test.sh)
6. [ ] 新增 RVA (原子操作) 擴展支援
7. [ ] 新增 RVF/RVD (浮點數) 擴展支援
8. [ ] 新增 RVB (位元操作) 擴展支援

---

## 檔案結構建議

```
compiler/
  _data/           # 測試資料 (.c 檔案)
  _test/           # 自動化測試腳本
  _doc/            # 計劃和文件
  c0/              # c0c 編譯器
    c0c/
      c/           # 測試案例
  ll0/             # ll0c 組譯器
  rv0/             # rv0 工具鏈
    rv0as.c        # 組譯器
    rv0vm.c        # 虛擬機
    rv0objdump.c   # 反組譯器
  Makefile         # 主建置檔
  CHANGELOG.md     # 變更記錄
```

---

## 總結

這個編譯器專案採用 **小步前進、測試驅動** 的方式發展：

1. **不求快，但求穩** - 每次只改一點，確保不破壞現有功能
2. **測試優先** - 先寫測試，再實作功能
3. **記錄變更** - 每個修改都記錄下來
4. **回歸測試** - 每次修改後執行全部測試

按照這個計劃，可以一步一步將編譯器從「能跑」發展到「完整」。
