# LLVM 優化簡介

> 以實際程式展示 clang/LLVM 編譯器的各種優化技術

## 環境

- **系統**: macOS (arm64)
- **編譯器**: Apple clang version 16.0.0
- **目標架構**: arm64-apple-darwin

---

## 優化等級說明

| 等級 | 說明 |
|------|------|
| `-O0` | 無優化，產生符合原始語义的調試資訊 |
| `-O1` | 基本優化 |
| `-O2` | 較高優化 (常用) |
| `-O3` | 最高優化，包含激進優化 |

---

## 1. 常數折疊 (Constant Folding)

### 原始碼

```c
#include <stdio.h>

int fold_constants() {
    int a = 5 * 24;
    int b = 100 - 50;
    int c = 10 / 2;
    int d = 15 + 25;
    return a + b + c + d;
}

int main() {
    int result = fold_constants();
    printf("fold_constants() = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
define i32 @fold_constants() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  store i32 120, ptr %1, align 4    ; 仍儲存結果到記憶體
  store i32 50, ptr %2, align 4
  store i32 5, ptr %3, align 4
  store i32 40, ptr %4, align 4
  %5 = load i32, ptr %1, align 4   ; 從記憶體讀取
  %6 = load i32, ptr %2, align 4
  %7 = add nsw i32 %5, %6
  %8 = load i32, ptr %3, align 4
  %9 = add nsw i32 %7, %8
  %10 = load i32, ptr %4, align 4
  %11 = add nsw i32 %9, %10
  ret i32 %11
}
```

### 已優化 IR (-O3)

```llvm
define i32 @fold_constants() local_unnamed_addr #0 {
  ret i32 215                          ; 直接返回常數結果
}
```

### 優化效果

| 項目 | -O0 | -O3 |
|------|-----|-----|
| 函數呼叫 | 有 | 無 |
| 記憶體操作 | 多次 load/store | 無 |
| 指令數 | ~15 條 | 1 條 |

執行結果：`fold_constants() = 215`

---

## 2. 內聯展開 (Inlining)

### 原始碼

```c
#include <stdio.h>

inline int square(int x) {
    return x * x;
}

inline int cube(int x) {
    return x * x * x;
}

int compute(int a, int b) {
    int s = square(a);
    int c = cube(b);
    return s + c;
}

int main() {
    int result = compute(5, 3);
    printf("compute(5, 3) = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
define i32 @compute(i32 noundef %0, i32 noundef %1) #0 {
  ; ... 參數儲存 ...
  %7 = load i32, ptr %3, align 4
  %8 = call i32 @square(i32 noundef %7)   ; 呼叫 square
  store i32 %8, ptr %5, align 4
  %9 = load i32, ptr %4, align 4
  %10 = call i32 @cube(i32 noundef %9)     ; 呼叫 cube
  store i32 %10, ptr %6, align 4
  ; ...
}

declare i32 @square(i32 noundef)           ; 獨立的 square 函數
declare i32 @cube(i32 noundef)             ; 獨立的 cube 函數
```

### 已優化 IR (-O3)

```llvm
define i32 @compute(i32 noundef %0, i32 noundef %1) local_unnamed_addr #0 {
  %3 = mul nsw i32 %0, %0                  ; inline square(a)
  %4 = mul nsw i32 %1, %1                   ; inline cube part 1
  %5 = mul nsw i32 %4, %1                   ; inline cube part 2
  %6 = add nsw i32 %5, %3                   ; s + c
  ret i32 %6
}
```

### 優化效果

| 項目 | -O0 | -O3 |
|------|-----|-----|
| 函數呼叫 | 2 次 (square, cube) | 0 次 |
| 函數定義 | 3 個 | 1 個 |
| 堆疊框架 | 複雜 | 簡化 |

執行結果：`compute(5, 3) = 52` (5² + 3³ = 25 + 27 = 52)

---

## 3. 死碼消除 (Dead Code Elimination)

### 原始碼

```c
#include <stdio.h>

int dead_code_elimination(int x) {
    if (0) {              // 永遠為 false
        return x + 1;
    }
    return x * 2;
}

int main() {
    int result = dead_code_elimination(10);
    printf("dead_code_elimination(10) = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
define i32 @dead_code_elimination(i32 noundef %0) #0 {
  store i32 %0, ptr %2, align 4
  %3 = load i32, ptr %2, align 4
  %4 = mul nsw i32 %3, 2
  ret i32 %4
}
```

### 已優化 IR (-O3)

```llvm
define i32 @dead_code_elimination(i32 noundef %0) local_unnamed_addr #0 {
  %2 = shl nsw i32 %0, 1              ; x * 2 → x << 1
  ret i32 %2
}
```

### 優化效果

- `if (0)` 區塊完全移除
- `x * 2` 優化為 `x << 1` (強度折減)
- 程式碼精簡至 2 行

執行結果：`dead_code_elimination(10) = 20`

---

## 4. 公共子表達式消除 (CSE)

### 原始碼

```c
#include <stdio.h>

int common_subexpression(int a, int b, int c) {
    int x = (a + b) * c;
    int y = (a + b) + c;
    return x + y;
}

int main() {
    int result = common_subexpression(1, 2, 3);
    printf("common_subexpression(1,2,3) = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
; 第一次計算 a + b
%11 = add nsw i32 %9, %10
%13 = mul nsw i32 %11, %12
store i32 %13, ptr %7, align 4

; 第二次計算 a + b (重複!)
%16 = add nsw i32 %14, %15
%18 = add nsw i32 %16, %17
store i32 %18, ptr %8, align 4
```

### 已優化 IR (-O3)

```llvm
define i32 @common_subexpression(i32 noundef %0, i32 noundef %1, i32 noundef %2) local_unnamed_addr #0 {
  %4 = add nsw i32 %1, %0             ; 只計算一次 (a + b)
  %5 = mul nsw i32 %4, %2             ; x = (a + b) * c
  %6 = add nsw i32 %4, %2             ; y = (a + b) + c (重用 %4)
  %7 = add nsw i32 %6, %5             ; return x + y
  ret i32 %7
}
```

### 優化效果

| 項目 | -O0 | -O3 |
|------|-----|-----|
| `a + b` 計算次數 | 2 次 | 1 次 |
| 指令總數 | 較多 | 較少 |

執行結果：`common_subexpression(1,2,3) = 15` ((1+2)*3 + (1+2)+3 = 9 + 6 = 15)

---

## 5. 迴圈展開 (Loop Unrolling)

### 原始碼

```c
#include <stdio.h>

int loop_unrolling(int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += i;
    }
    return sum;
}

int main() {
    int result = loop_unrolling(8);
    printf("loop_unrolling(8) = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
; 完整的迴圈結構
br label %5
5:
  %6 = load i32, ptr %4, align 4
  %7 = load i32, ptr %2, align 4
  %8 = icmp slt i32 %6, %7
  br i1 %8, label %9, label %16
9:
  %10 = load i32, ptr %4, align 4
  %11 = load i32, ptr %3, align 4
  %12 = add nsw i32 %11, %10
  store i32 %12, ptr %3, align 4
  br label %13
13:
  %14 = load i32, ptr %4, align 4
  %15 = add nsw i32 %14, 1
  store i32 %15, ptr %4, align 4
  br label %5
```

### 已優化 IR (-O3)

```llvm
define i32 @loop_unrolling(i32 noundef %0) local_unnamed_addr #0 {
  %2 = icmp sgt i32 %0, 0
  br i1 %2, label %3, label %13

3:
  %4 = add nsw i32 %0, -1
  %5 = zext i32 %4 to i33
  %6 = add nsw i32 %0, -2
  %7 = zext i32 %6 to i33
  %8 = mul i33 %5, %7                  ; 數學公式展開
  %9 = lshr i33 %8, 1
  %10 = trunc i33 %9 to i32
  %11 = add i32 %10, %0
  %12 = add i32 %11, -1
  br label %13

13:
  %14 = phi i32 [ 0, %1 ], [ %12, %3 ]
  ret i32 %14
}
```

### 優化效果

- 迴圈完全消除，轉為數學公式
- `0 + 1 + 2 + ... + (n-1) = n*(n-1)/2`
- 8*7/2 = 28

執行結果：`loop_unrolling(8) = 28`

---

## 6. 強度折減 (Strength Reduction)

### 原始碼

```c
#include <stdio.h>

int strength_reduction(int n) {
    int result = 0;
    for (int i = 0; i < n; i++) {
        result = result + 16;
    }
    return result;
}

int main() {
    int result = strength_reduction(5);
    printf("strength_reduction(5) = %d\n", result);
    return 0;
}
```

### 未優化 IR (-O0)

```llvm
; 完整迴圈，每次迭代執行 add
%11 = add nsw i32 %10, 16
store i32 %11, ptr %3, align 4
```

### 已優化 IR (-O3)

```llvm
define i32 @strength_reduction(i32 noundef %0) local_unnamed_addr #0 {
  %2 = icmp sgt i32 %0, 0
  %3 = shl i32 %0, 4                   ; n * 16 → n << 4
  %4 = select i1 %2, i32 %3, i32 0
  ret i32 %4
}
```

### 優化效果

| 項目 | -O0 | -O3 |
|------|-----|-----|
| 迴圈迭代 | 5 次 | 0 次 |
| 運算 | 多次加法 | 一次位移 `shl` |
| 複雜度 | O(n) | O(1) |

- `16` = `2⁴`，所以 `n * 16` = `n << 4`
- `5 * 16 = 80`

執行結果：`strength_reduction(5) = 80`

---

## 測試腳本

所有測試腳本位於 `optimize/` 目錄：

```bash
# 常數折疊
./optimize/test_constant_folding.sh

# 內聯展開
./optimize/test_inlining.sh

# 死碼消除
./optimize/test_dead_code_elimination.sh

# 公共子表達式消除
./optimize/test_cse.sh

# 迴圈展開
./optimize/test_loop_unrolling.sh

# 強度折減
./optimize/test_strength_reduction.sh
```

---

## 總結

LLVM 優化pass會分析 IR 並進行多種轉換：

| 優化類型 | 效果 |
|----------|------|
| 常數折疊 | 編譯時計算常數運算式 |
| 內聯展開 | 消除函數呼叫開銷 |
| 死碼消除 | 移除不可達程式碼 |
| CSE | 重用重複計算 |
| 迴圈展開 | 消除迴圈分支 |
| 強度折減 | 用廉价運算替換昂貴運算 |

這些優化大幅提升效能，同時保持語義正確性。