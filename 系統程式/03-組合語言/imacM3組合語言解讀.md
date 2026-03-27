# iMac M3 (ARM64) 組合語言解讀

## 簡介

本文以 `factorial(5)` 為例，說明在 Apple M3 晶片（ARM64 架構）上的組合語言結構，以及編譯過程中資訊的喪失與保留。

## 1. 編譯流程

```
factorial.c (C 程式碼)
    │
    ├─> clang -S -O0 → factorial.s (組合語言)
    │
    └─> clang -c -O0 → factorial.o (目的檔)
                              │
                              └─> objdump -d → 反組譯
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

## 3. ARM64 組合語言結構

### 3.1 暫存器 naming

| 暫存器 | 用途 |
|--------|------|
| x0-x7 | 函數參數（第1-8個參數） |
| w0-w7 | x0-x7 的 32-bit 版本 |
| x30 (lr) | 連結暫存器（返回位址） |
| x29 (fp) | 框架暫存器（Frame Pointer） |
| sp | 堆疊指標 |
| x0 | 返回值 |

### 3.2 factorial 函數分析

```assembly
_factorial:
    sub     sp, sp, #32          ; 分配 32 bytes 堆疊空間
    stp     x29, x30, [sp, #16]  ; 保存 fp, lr（16-byte Folded Spill）
    add     x29, sp, #16         ; 設定 frame pointer
    str     w0, [sp, #8]         ; 保存參數 n 到堆疊
```

**堆疊 frame 配置（factorial）：**

```
高地址
┌─────────────────────┐
│   舊的 fp (x29)     │  ← x29 指向這裡
├─────────────────────┤
│   返回位址 (lr)     │
├─────────────────────┤
│   參數 n            │  ← [sp, #8]
├─────────────────────┤
│   區域變數 result   │  ← [x29, #-4] = [sp, #20]
├─────────────────────┤
│   臨時變數          │  ← [sp, #4]
├─────────────────────┤
│   padding           │
├─────────────────────┤
│   保留              │
└─────────────────────┘
           ↓ sp 遞增
低地址
```

**遞迴呼叫的堆疊成長過程：**

```
呼叫 factorial(5) 時：
Frame 5:  [sp-32] → 存放 n=5, 計算 5 * factorial(4)
Frame 4:  [sp-64] → 存放 n=4, 計算 4 * factorial(3)
Frame 3:  [sp-96] → 存放 n=3, 計算 3 * factorial(2)
Frame 2:  [sp-128] → 存放 n=2, 計算 2 * factorial(1)
Frame 1:  [sp-160] → n<=1, 直接返回 1
```

**遞迴返回過程：**
```
Frame 1 返回 1
Frame 2: 2 * 1 = 2 返回
Frame 3: 3 * 2 = 6 返回
Frame 4: 4 * 6 = 24 返回
Frame 5: 5 * 24 = 120 返回
```

### 3.3 關鍵指令說明

| 指令 | 說明 |
|------|------|
| `sub sp, sp, #32` | 分配堆疊空間（向低地址生長） |
| `stp x29, x30, [sp, #16]` | 儲存 fp 和 lr |
| `ldp x29, x30, [sp, #16]` | 恢復 fp 和 lr |
| `add sp, sp, #32` | 釋放堆疊空間 |
| `str w0, [sp, #8]` | 儲存參數 |
| `ldur w0, [x29, #-4]` | 以 frame pointer 存取區域變數 |
| `bl _factorial` | 函數呼叫（會自動將返回位址存入 lr） |
| `ret` | 返回（使用 lr 中的位址） |

## 4. 目的檔 objdump 分析

### 4.1 factorial.o objdump 輸出

```
factorial.o:	file format mach-o arm64

Disassembly of section __TEXT,__text:

0000000000000000 <ltmp0>:
       0: d10083ff     	sub	sp, sp, #0x20
       4: a9017bfd     	stp	x29, x30, [sp, #0x10]
       8: 910043fd     	add	x29, sp, #0x10
       c: b9000be0     	str	w0, [sp, #0x8]
      10: b9400be8     	ldr	w8, [sp, #0x8]
      14: 71000508     	subs	w8, w8, #0x1
      18: 1a9fd7e8     	cset	w8, gt
      1c: 370000a8     	tbnz	w8, #0x0, 0x30 <ltmp0+0x30>
      ...
```

### 4.2 喪失的資訊（無 -g 參數）

編譯後的目的檔或執行檔中，以下資訊**完全喪失**：

1. **函數名稱**：符號被 strip，只剩 `<ltmp0>` 等臨時名稱
2. **變數名稱**：無法得知 `n`, `result` 等名稱
3. **參數名稱**：無法得知參數是什麼
4. **原始碼行號**：無法對應到原始碼行
5. **資料類型資訊**：無法得知 `int`、`char` 等型別
6. **原始碼結構**：if/else、迴圈等結構資訊完全消失
7. **區域變數位置**：無法得知 `[x29, #-4]` 對應哪個變數

## 5. 使用 -g 參數保留的資訊

### 5.1 編譯方式

```bash
clang -g -O0 -o factorial_debug factorial.c
```

### 5.2 DWARF 除錯資訊

使用 `-g` 參數編譯後，會產生 DWARF（Debugging With Attributed Record Formats）格式的除錯資訊，儲存在 `.debug_info` 區段中：

```
DW_TAG_subprogram
    DW_AT_low_pc    (0x0000000100003ed4)
    DW_AT_high_pc   (0x0000000100003f38)
    DW_AT_name      ("factorial")
    DW_AT_decl_file ("/.../factorial.c")
    DW_AT_decl_line (3)
    DW_AT_type      (0x00000063 "int")

DW_TAG_formal_parameter
    DW_AT_location  (DW_OP_breg31 WSP+8)
    DW_AT_name      ("n")
    DW_AT_decl_line (3)
    DW_AT_type      (0x00000063 "int")

DW_TAG_variable
    DW_AT_location  (DW_OP_fbreg -8)
    DW_AT_name      ("result")
    DW_AT_decl_line (11)
    DW_AT_type      (0x00000063 "int")
```

### 5.3 -g 保留的資訊

| 資訊類型 | 說明 |
|----------|------|
| 原始碼檔名 | `/Users/.../factorial.c` |
| 行號對應 | 函數在第 3 行、參數在第 3 行、變數在第 11 行 |
| 函數名稱 | `factorial`, `main` |
| 參數名稱 | `n` |
| 區域變數名稱 | `result` |
| 資料型別 | `int`, `char` 等 |
| 堆疊位置 | `DW_OP_fbreg -8` 表示在 frame base 減 8 的位置 |
| Frame Base | `DW_AT_frame_base (DW_OP_reg29 W29)` 使用 x29 作為框架指標 |

### 5.4 -g 仍然喪失的資訊

即使使用 `-g`，以下資訊仍然**無法完全恢復**：

1. **註解**：原始碼中的註解完全消失
2. **巨集展開**：#define 巨集已展開，無法恢復原始巨集形式
3. **編譯期運算**：編譯器最佳化後的常數運算結果
4. **除錯中可能改變的行為**：-O0 與 -O2 的行為差異

## 6. LLVM 工具使用總覽

| 工具 | 用途 |
|------|------|
| `clang -S` | 產生組譯檔（.s） |
| `clang -c` | 編譯目的檔（.o） |
| `clang -g` | 加入除錯資訊 |
| `objdump -d` | 反組譯目的檔 |
| `dwarfdump` | 查看 DWARF 除錯資訊 |
| `file` | 查看檔案格式 |

## 7. 結論

1. **編譯過程喪失資訊**：從 C 到組合語言，型別、變數名稱、程式結構完全消失
2. **組合語言保留運算逻辑**：運算流程、控制流（branch）仍完整存在
3. **目的檔只剩機械碼**：符號表被移除後，無法對應回原始碼
4. **-g 參數保留除錯資訊**：透過 DWARF 格式，可以在除錯器中恢复變數名稱、原始碼行號等資訊
5. **ARM64 堆疊成長方向**：向低地址成長，frame pointer (x29) 用於存取區域變數
6. **遞迴呼叫與堆疊**：每次遞迴都會分配新的 stack frame，保存參數與返回位址
