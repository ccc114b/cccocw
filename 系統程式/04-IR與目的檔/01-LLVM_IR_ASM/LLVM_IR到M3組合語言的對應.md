# LLVM IR 到 ARM64 (Apple M系列晶片) 組合語言的對應

## 環境說明

- 機器架構: arm64 (Apple M1/M2/M3)
- 作業系統: macOS 15.5
- 編譯器: Apple clang 16.0.0
- 範例: `factorial(5) = 120`

## 編譯流程

```
C 程式碼        LLVM IR (.ll)      ARM64 ASM (.s)     可執行檔
factorial.c  →  factorial.ll  →  factorial.s    →  factorial
                   ↓
              bytecode (.bc)
```

## 範例程式

```c
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    printf("factorial(5) = %d\n", result);
    return 0;
}
```

## LLVM IR 分析

產生的 IR 如下 (以 `-O0` 產生，保持原始結構):

```llvm
define i32 @factorial(i32 noundef %0) {
  %2 = alloca i32, align 4          ; 為傳回值配置空間
  %3 = alloca i32, align 4          ; 為參數 n 配置空間
  store i32 %0, ptr %3, align 4     ; 儲存參數到局部變數
  %4 = load i32, ptr %3, align 4    ; 載入 n 的值
  %5 = icmp sle i32 %4, 1          ; 比較 n <= 1
  br i1 %5, label %6, label %7      ; 條件分支

6:                                   ; then: return 1
  store i32 1, ptr %2, align 4
  br label %13

7:                                   ; else: return n * factorial(n-1)
  %8 = load i32, ptr %3, align 4
  %9 = load i32, ptr %3, align 4
  %10 = sub nsw i32 %9, 1
  %11 = call i32 @factorial(i32 %10)
  %12 = mul nsw i32 %8, %11
  store i32 %12, ptr %2, align 4
  br label %13

13:                                  ; 合併點
  %14 = load i32, ptr %2, align 4
  ret i32 %14
}
```

## IR 到 ARM64 組合語言對應

### 1. 函式 prologue/epilogue

| IR 動作 | ARM64 組合語言 |
|---------|----------------|
| 配置堆疊框架 | `sub sp, sp, #32` (分配 32 bytes) |
| 保存暫存器 | `stp x29, x30, [sp, #16]` |
| 建立 frame pointer | `add x29, sp, #16` |
| 恢復堆疊 | `add sp, sp, #32` |
| 返回 | `ret` |

### 2. 變數存取

| IR 指令 | ARM64 組合語言 | 說明 |
|---------|----------------|------|
| `store i32 %0, ptr %3` | `str w0, [sp, #8]` | 參數 w0 存入堆疊 |
| `load i32, ptr %3` | `ldr w8, [sp, #8]` | 從堆疊載入到暫存器 |

### 3. 運算指令

| IR 指令 | ARM64 組合語言 | 說明 |
|---------|----------------|------|
| `sub nsw i32 %9, 1` | `subs w0, w8, #1` | 減法 (設條件旗標) |
| `mul nsw i32 %8, %11` | `mul w8, w8, w0` | 乘法 |
| `add i32` | `add w8, w8, w0` | 加法 |

### 4. 比較與分支

| IR 指令 | ARM64 組合語言 | 說明 |
|---------|----------------|------|
| `icmp sle i32 %4, 1` | `subs w8, w8, #1` + `cset w8, gt` | 比較 n <= 1 |
| `br i1 %5` | `tbnz w8, #0, LBB0_2` | 測試位元並分支 |

### 5. 函式呼叫

| IR 指令 | ARM64 組合語言 | 說明 |
|---------|----------------|------|
| `call i32 @factorial` | `bl _factorial` |  Branch with Link |
| 參數傳遞 | `mov w0, #5` | 參數放入 w0 暫存器 |
| 返回值 | `w0` 暫存器 | 返回值在 w0 |

### 6. 返回值處理

| IR 指令 | ARM64 組合語言 | 說明 |
|---------|----------------|------|
| `ret i32 %14` | `ldur w0, [x29, #-4]` + `ret` | 載入返回值並返回 |

## 完整對應表

```
LLVM IR 指令                    ARM64 組合語言
─────────────────────────────────────────────────────
%result = alloca i32           str wN, [sp, #offset]
%result = load i32, ptr %ptr  ldr wN, [sp, #offset]
store i32 %val, ptr %ptr      str wN, [sp, #offset]
%result = add i32 %a, %b      add wN, wM, wK
%result = sub i32 %a, %b      sub wN, wM, wK
%result = mul i32 %a, %b      mul wN, wM, wK
%result = icmp slt i32 %a, %b cmp + cset
br i1 %cond, label %t, label %f tbnz/tbz
call @func(args)              bl _func
ret i32 %val                  mov w0, wN; ret
```

## .ll 到 bytecode 轉換

### 格式說明

| 格式 | 副檔名 | 說明 |
|------|--------|------|
| .ll | LLVM IR (文字) | 人類可讀，包含所有指令的 ASCII 表示 |
| .bc | Bytecode (二進位) | 機器可讀的壓縮格式，適合 linking |

### 轉換工具

```bash
# .ll -> .bc (文字到二進位)
llvm-as factorial.ll -o factorial.bc

# .bc -> .ll (二進位到文字)
llvm-dis factorial.bc -o factorial.ll

# 直接產生 bytecode
clang -c -emit-llvm factorial.c -o factorial.bc
```

### 格式差異

```
.ll 檔案 (factorial.ll):
  define i32 @factorial(i32 noundef %0) {
    %2 = alloca i32, align 4
    ...

.bc 檔案 (factorial.bc):
  ▒▒▒▒ LLVM BC ▒▒▒▒▒▒▒▒▒... (二進位內容)
  file: LLVM bitcode, wrapper
```

## ARM64 暫存器使用慣例

| 暫存器 | 用途 | 保存性 |
|--------|------|--------|
| w0/w1 | 參數與返回值 | caller-saved |
| w2-w7 | 額外參數 | caller-saved |
| w8-w18 | 暫時計算 | caller-saved |
| w19-w28 | 保存的暫存器 | callee-saved |
| x29 (fp) | Frame Pointer | callee-saved |
| x30 (lr) | Link Register | caller-saved |
| sp | Stack Pointer | 系統保留 |

## 執行結果

```
$ clang factorial.c -o factorial
$ ./factorial
factorial(5) = 120
```

## 結論

LLVM IR 是一種中介表示 (Intermediate Representation)，它：
1. **與語言無關**: 可從 C/C++/Rust 等語言產生
2. **與目標無關**: IR 本身不指定目標架構
3. **可優化**: LLVM 可在 IR 層級進行優化
4. **可後端編譯**: 透過 llc 可編譯到各類目標架構 (x86, ARM, RISC-V 等)

本範例展示從 C → LLVM IR → ARM64 Assembly 的完整對應過程，清楚呈現高階語言如何轉換為低階組合語言的對應關係。
