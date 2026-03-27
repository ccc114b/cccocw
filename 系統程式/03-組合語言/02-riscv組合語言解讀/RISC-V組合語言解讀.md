# RISC-V 組合語言解讀

## 簡介

本文以 `factorial(5)` 為例，說明 RISC-V 64-bit 架構（RV64GC）上的組合語言結構，以及編譯過程中資訊的喪失與保留。

## 1. 編譯流程

```
factorial.c (C 程式碼)
    │
    ├─> riscv64-unknown-elf-gcc -S -O0 → factorial.s (組合語言)
    │
    └─> riscv64-unknown-elf-gcc -c -O0 → factorial.o (目的檔)
                              │
                              └─> riscv64-unknown-elf-objdump -d → 反組譯
```

## 2. 原始 C 程式碼

```c
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    printf("factorial(5) = %d\n", result);
    return 0;
}
```

## 3. RISC-V 組合語言結構

### 3.1 暫存器 naming (RV64GC)

| 暫存器 | 別名 | 用途 |
|--------|------|------|
| a0-a7 | - | 函數參數（第1-8個參數），也用於返回值 |
| ra | x1 | 返回位址（Return Address） |
| sp | x2 | 堆疊指標（Stack Pointer） |
| gp | x3 | 全域指標（Global Pointer） |
| tp | x4 | 线程指標（Thread Pointer） |
| s0/fp | x8 | 框架指標（Frame Pointer） |
| s1-x | x9-x | 保存暫存器 |
| t0-t6 | x5-x7, x28-x31 | 臨時暫存器 |

### 3.2 factorial 函數分析

```assembly
factorial:
    addi    sp,sp,-32        ; 分配 32 bytes 堆疊空間
    sd      ra,24(sp)        ; 保存返回位址 (ra)
    sd      s0,16(sp)        ; 保存框架指標 (s0)
    addi    s0,sp,32         ; 設定 frame pointer
    mv      a5,a0            ; a5 = n (參數)
    sw      a5,-20(s0)       ; 儲存區域變數 n
    lw      a5,-20(s0)       ; 載入 n
    sext.w  a4,a5            ; 符號擴展
    li      a5,1             ; a5 = 1
    bgt     a4,a5,.L2        ; if (n > 1) goto .L2
    li      a5,1             ; a5 = 1 (return 1)
    j       .L3              ; goto .L3
.L2:                          ; 遞迴部分
    lw      a5,-20(s0)       ; 載入 n
    addiw   a5,a5,-1         ; a5 = n - 1
    sext.w  a5,a5            ; 符號擴展
    mv      a0,a5            ; a0 = n - 1
    call    factorial        ; 遞迴呼叫
    mv      a5,a0            ; a5 = factorial(n-1)
    lw      a4,-20(s0)       ; 載入 n
    mulw    a5,a4,a5         ; a5 = n * factorial(n-1)
    sext.w  a5,a5            ; 符號擴展
.L3:                          ; 返回
    mv      a0,a5            ; 設定返回值
    ld      ra,24(sp)        ; 恢復 ra
    ld      s0,16(sp)        ; 恢復 s0
    addi    sp,sp,32         ; 釋放堆疊空間
    jr      ra               ; 返回
```

**堆疊 frame 配置（factorial）：**

```
高地址
┌─────────────────────┐
│   舊的 s0 (fp)      │  ← s0 指向這裡 (sp+32)
├─────────────────────┤
│   返回位址 (ra)     │  ← sp+24
├─────────────────────┤
│   (padding)        │
├─────────────────────┤
│   區域變數 n        │  ← s0-20 (sp+12)
├─────────────────────┤
│   (未使用)          │
└─────────────────────┘
           ↓ sp 遞增
低地址
```

### 3.3 關鍵指令說明

| 指令 | 說明 |
|------|------|
| `addi sp,sp,-32` | 分配堆疊空間（向低地址生長） |
| `sd ra,24(sp)` | 儲存返回位址 |
| `sd s0,16(sp)` | 儲存框架指標 |
| `ld ra,24(sp)` | 恢復返回位址 |
| `ld s0,16(sp)` | 恢復框架指標 |
| `addi sp,sp,32` | 釋放堆疊空間 |
| `sw a5,-20(s0)` | 儲存區域變數 |
| `lw a5,-20(s0)` | 載入區域變數 |
| `call factorial` | 函數呼叫（自動儲存 ra） |
| `jr ra` | 返回（使用 ra 中的位址） |

**遞迴呼叫的堆疊成長過程：**

```
呼叫 factorial(5) 時：
Frame 5:  [sp-32] → 存放 n=5, 計算 5 * factorial(4)
Frame 4:  [sp-64] → 存放 n=4, 計算 4 * factorial(3)
Frame 3:  [sp-96] → 存放 n=3, 計算 3 * factorial(2)
Frame 2:  [sp-128] → 存放 n=2, 計算 2 * factorial(1)
Frame 1:  [sp-160] → n<=1, 直接返回 1
```

## 4. 目的檔 objdump 分析

### 4.1 factorial.o objdump 輸出

```
factorial.o:     file format elf64-littleriscv

Disassembly of section .text:

0000000000000000 <factorial>:
   0:	1101                	add	sp,sp,-32
   2:	ec06                	sd	ra,24(sp)
   4:	e822                	sd	s0,16(sp)
   6:	1000                	add	s0,sp,32
   8:	87aa                	mv	a5,a0
   a:	fef42623          	sw	a5,-20(s0)
   e:	fec42783          	lw	a5,-20(s0)
  12:	0007871b          	sext.w	a4,a5
  16:	4785                	li	a5,1
  18:	00e7c463          	blt	a5,a4,20 <.L2>
  1c:	4785                	li	a5,1
  1e:	a005                	j	3e <.L3>

0000000000000020 <.L2>:
  20:	fec42783          	lw	a5,-20(s0)
  24:	37fd                	addw	a5,a5,-1
  26:	2781                	sext.w	a5,a5
  28:	853e                	mv	a0,a5
  2a:	00000097          	auipc	ra,0x0
  2e:	000080e7          	jalr	ra # 2a <.L2+0xa>
  32:	87aa                	mv	a5,a0
  34:	fec42703          	lw	a4,-20(s0)
  38:	02f707bb          	mulw	a5,a4,a5
  3c:	2781                	sext.w	a5,a5

000000000000003e <.L3>:
  3e:	853e                	mv	a0,a5
  40:	60e2                	ld	ra,24(sp)
  42:	6442                	ld	s0,16(sp)
  44:	6105                	add	sp,sp,32
  46:	8082                	ret
```

### 4.2 喪失的資訊（無 -g 參數）

編譯後的目的檔或執行檔中，以下資訊**完全喪失**：

1. **函數名稱**：符號可能被 strip
2. **變數名稱**：無法得知 `n`, `result` 等名稱
3. **參數名稱**：無法得知參數是什麼
4. **原始碼行號**：無法對應到原始碼行
5. **資料類型資訊**：無法得知 `int`、`char` 等型別
6. **原始碼結構**：if/else、迴圈等結構資訊完全消失
7. **區域變數位置**：無法得知 `sw -20(s0)` 對應哪個變數

## 5. 使用 -g 參數保留的資訊

### 5.1 編譯方式

```bash
riscv64-unknown-elf-gcc -g -O0 -o factorial_debug factorial.c
```

### 5.2 DWARF 除錯資訊

使用 `-g` 參數編譯後，會產生 DWARF（Debugging With Attributed Record Formats）格式的除錯資訊。從輸出中可以看到我們程式碼的除錯資訊：

```
DW_TAG_subprogram
    DW_AT_name        : factorial
    DW_AT_decl_file   : factorial.c
    DW_AT_decl_line   : 3
    DW_AT_type        : int

DW_TAG_formal_parameter
    DW_AT_name        : n
    DW_AT_decl_file   : factorial.c
    DW_AT_decl_line   : 3
    DW_AT_type        : int
```

### 5.3 -g 保留的資訊

| 資訊類型 | 說明 |
|----------|------|
| 原始碼檔名 | `factorial.c` |
| 行號對應 | 函數在第 3 行、參數在第 3 行、變數在第 11 行 |
| 函數名稱 | `factorial`, `main` |
| 參數名稱 | `n` |
| 區域變數名稱 | `result` |
| 資料型別 | `int`, `char` 等 |
| 堆疊位置 | 區域變數在 s0-20 的位置 |

### 5.4 -g 仍然喪失的資訊

即使使用 `-g`，以下資訊仍然**無法完全恢復**：

1. **註解**：原始碼中的註解完全消失
2. **巨集展開**：#define 巨集已展開，無法恢復原始巨集形式
3. **編譯期運算**：編譯器最佳化後的常數運算結果

## 6. ARM64 與 RISC-V 比較

| 特性 | ARM64 (Apple M3) | RISC-V (RV64GC) |
|------|------------------|-----------------|
| 框架暫存器 | x29 (fp) | s0 (fp/x8) |
| 連結暫存器 | x30 (lr) | ra (x1) |
| 堆疊指標 | sp | sp (x2) |
| 函數參數 | x0-x7 | a0-a7 |
| 返回指令 | `ret` | `jr ra` |
| 堆疊成長方向 | 向低地址 | 向低地址 |
| 堆疊保存 | `stp x29, x30, [sp, #16]` | `sd ra,24(sp)` |

### 主要差異總覽

1. **暫存器命名**：ARM 使用 x0-x30，RISC-V 使用更彈性的命名（x0-x31 + 別名）
2. **函數呼叫**：ARM 使用 `bl` + `ret`，RISC-V 使用 `call` + `jr ra`
3. **返回位址**：ARM 保存在 lr (x30)，RISC-V 保存在 ra (x1)
4. **框架指標**：兩者都使用，但 RISC-V 明確保存/恢復

## 7. 結論

1. **編譯過程喪失資訊**：從 C 到組合語言，型別、變數名稱、程式結構完全消失
2. **組合語言保留運算逻辑**：運算流程、控制流（branch）仍完整存在
3. **目的檔只剩機械碼**：符號表被移除後，無法對應回原始碼
4. **-g 參數保留除錯資訊**：透過 DWARF 格式，可以在除錯器中恢复變數名稱、原始碼行號等資訊
5. **RISC-V 堆疊成長方向**：向低地址成長，s0 作為框架指標
6. **遞迴呼叫與堆疊**：每次遞迴都會分配新的 stack frame，保存 ra 與 s0、參數、區域變數
7. **工具差異**：使用 `riscv64-unknown-elf-gcc` 和 `riscv64-unknown-elf-objdump`
