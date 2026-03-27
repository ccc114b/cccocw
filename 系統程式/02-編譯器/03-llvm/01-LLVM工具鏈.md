# LLVM 工具鏈：從原始碼到目的檔的完整旅程

> 以 factorial(5) = 120 為例，介紹 clang/LLVM 編譯流程與目的檔格式

## 環境

- **系統**: macOS Sonoma 14.5 (arm64)
- **編譯器**: Apple clang version 16.0.0 (clang-1600.0.26.6)
- **目標架構**: arm64-apple-darwin

---

## 1. 原始碼：factorial.c

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

這是一個遞迴計算階乘的程式。`factorial(5)` 會計算 5 × 4 × 3 × 2 × 1 = 120。

---

## 2. 編譯流程概述

```
factorial.c  ──(clang -S -emit-llvm)──>  factorial.ll
                                     │
                                     └──(clang -c)──>  factorial.o
```

- **`.c`**: C 原始碼
- **`.ll`**: LLVM IR (Intermediate Representation) 中間表示
- **`.o`**: 目的檔 (Object File)，此處為 Mach-O 格式

---

## 3. 生成 LLVM IR

使用 `-S -emit-llvm` 產生人類可讀的 LLVM IR：

```bash
clang -S -emit-llvm -o factorial.ll factorial.c
```

### 實際產生的 IR (factorial.ll)

```
; ModuleID = 'factorial.c'
source_filename = "factorial.c"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128"
target triple = "arm64-apple-macosx15.0.0"

@.str = private unnamed_addr constant [19 x i8] c"factorial(5) = %d\0A\00", align 1

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @factorial(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 %0, ptr %3, align 4
  %4 = load i32, ptr %3, align 4
  %5 = icmp sle i32 %4, 1
  br i1 %5, label %6, label %7

6:                                                ; preds = %1
  store i32 1, ptr %2, align 4
  br label %13

7:                                                ; preds = %1
  %8 = load i32, ptr %3, align 4
  %9 = load i32, ptr %3, align 4
  %10 = sub nsw i32 %9, 1
  %11 = call i32 @factorial(i32 noundef %10)
  %12 = mul nsw i32 %8, %11
  store i32 %12, ptr %2, align 4
  br label %13

13:                                               ; preds = %7, %6
  %14 = load i32, ptr %2, align 4
  ret i32 %14
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  %3 = call i32 @factorial(i32 noundef 5)
  store i32 %3, ptr %2, align 4
  %4 = load i32, ptr %2, align 4
  %5 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %4)
  ret i32 0
}

declare i32 @printf(ptr noundef, ...) #1
```

### IR 語法解讀

| 語法 | 意義 |
|------|------|
| `@factorial` | 函數符號 (全域) |
| `@main` | 主函數符號 |
| `@.str` | 全域字串常數 |
| `i32` | 32 位元整數 |
| `%0`, `%2` | 本地變數 (虛擬暫存器) |
| `icmp sle` | 有號小於或等於比較 |
| `br` | 無條件分支 |
| `call` | 函數呼叫 |
| `mul nsw` | 乘法 (no signed wrap) |
| `ret` | 返回 |
| `alloca` | 堆疊配置 |
| `load`/`store` | 記憶體存取 |
| `noundef` | 無未定義假設 |
| `align 4` | 4 位元組對齊 |

IR 是 SSA (Static Single Assignment) 形式，每個變數只能賦值一次。

---

## 4. 生成目的檔

使用 `-c` 編譯為目的檔 (不進行連結)：

```bash
clang -c -o factorial.o factorial.c
```

---

## 5. 反組譯：從目的檔到組合語言

### 5.1 使用 otool 反組譯

```bash
otool -tV factorial.o
```

輸出：

```
factorial.o:
(__TEXT,__text) section
_factorial:
0000000000000000	sub	sp, sp, #0x20
0000000000000004	stp	x29, x30, [sp, #0x10]
0000000000000008	add	x29, sp, #0x10
000000000000000c	str	w0, [sp, #0x8]
0000000000000010	ldr	w8, [sp, #0x8]
0000000000000014	subs	w8, w8, #0x1
0000000000000018	cset	w8, gt
000000000000001c	tbnz	w8, #0x0, 0x30
0000000000000020	b	0x24
0000000000000024	mov	w8, #0x1
0000000000000028	stur	w8, [x29, #-0x4]
000000000000002c	b	0x54
0000000000000030	ldr	w8, [sp, #0x8]
0000000000000034	str	w8, [sp, #0x4]
0000000000000038	ldr	w8, [sp, #0x8]
000000000000003c	subs	w0, w8, #0x1
0000000000000040	bl	_factorial
0000000000000044	ldr	w8, [sp, #0x4]
0000000000000048	mul	w8, w8, w0
000000000000004c	stur	w8, [x29, #-0x4]
0000000000000050	b	0x54
0000000000000054	ldur	w0, [x29, #-0x4]
0000000000000058	ldp	x29, x30, [sp, #0x10]
000000000000005c	add	sp, sp, #0x20
0000000000000060	ret
_main:
0000000000000064	sub	sp, sp, #0x30
0000000000000068	stp	x29, x30, [sp, #0x20]
000000000000006c	add	x29, sp, #0x20
0000000000000070	mov	w8, #0x0
0000000000000074	stur	w8, [29, #-0xc]
0000000000000078	stur	wzr, [x29, #-0x4]
000000000000007c	mov	w0, #0x5
0000000000000080	bl	0x80
0000000000000084	stur	w0, [x29, #-0x8]
0000000000000088	ldur	w9, [x29, #-0x8]
000000000000008c	mov	x8, x9
0000000000000090	mov	x9, sp
0000000000000094	str	x8, [x9]
0000000000000098	adrp	x0, 0 ; 0x0
000000000000009c	add	x0, x0, #0x0
00000000000000a0	bl	0xa0
00000000000000a4	ldur	w0, [x29, #-0xc]
00000000000000a8	ldp	x29, x30, [sp, #0x20]
00000000000000ac	add	sp, sp, #0x30
00000000000000b0	ret
```

### 5.2 組合語言解讀

| ARM64 指令 | 意義 |
|------------|------|
| `sub sp, sp, #0x20` | 配置堆疊框架 |
| `stp x29, x30, [sp, #0x10]` | 儲存 frame pointer 與 link register |
| `add x29, sp, #0x10` | 設定 frame pointer |
| `cmp/subs` | 比較與減法 |
| `cset w8, gt` | 若大於則設 w8 = 1 |
| `tbnz w8, #0x0, 0x30` | 若 w8 != 0 則跳躍 |
| `bl _factorial` | 呼叫遞迴函數 |
| `mul w8, w8, w0` | 乘法運算 |
| `ret` | 返回 |

---

## 6. 目的檔格式：Mach-O

macOS 使用 **Mach-O** (Mach Object) 格式。

### 6.1 檢視 Mach-O 標頭

```bash
otool -h factorial.o
```

```
factorial.o:
Mach header
      magic  cputype cpusubtype  caps    filetype ncmds sizeofcmds      flags
 0xfeedfacf 16777228          0  0x00           1     4        440 0x00002000
```

| 欄位 | 值 | 意義 |
|------|-----|------|
| magic | 0xfeedfacf | Mach-O 64-bit (arm64) |
| cputype | 16777228 (0x0100000c) | ARM64 |
| filetype | 1 | 可執行檔類型 (OBJECT) |
| ncmds | 4 | Load commands 數量 |

### 6.2 檢視載入命令 (Load Commands)

```bash
otool -l factorial.o
```

主要 Load Commands：

```
Load command 0
      cmd LC_SEGMENT_64
  cmdsize 312
  segname 
   vmaddr 0x0000000000000000
   vmsize 0x0000000000000108
  fileoff 472
 filesize 264
  maxprot 0x00000007
 initprot 0x00000007
   nsects 3
    flags 0x0
Section
  sectname __text
   segname __TEXT
      addr 0x0000000000000000
      size 0x00000000000000b4
    offset 472
     align 2^2 (4)
    reloff 736
    nreloc 4
     flags 0x80000400
 reserved1 0
 reserved2 0
Section
  sectname __cstring
   segname __TEXT
      addr 0x00000000000000b4
      size 0x0000000000000013
    offset 652
    ...
```

### 6.3 Mach-O 結構圖

```
┌─────────────────────┐
│  Mach Header (64-bit)│  固定的標頭資訊 (24 bytes)
├─────────────────────┤
│   Load Commands     │  告知系統如何載入檔案
│   - LC_SEGMENT_64   │  段區定義
│   - LC_BUILD_VERSION│  編譯器版本
│   - LC_SYMTAB       │  符號表
│   - LC_DYSYMTAB     │  動態符號表
├─────────────────────┤
│   Section Data      │  實際的程式碼/資料
│   (__text)         │  程式碼
│   (__cstring)      │  字串常數
│   (__compact_unwind)│ 例外處理資訊
├─────────────────────┤
│   Symbol Table      │  符號表
├─────────────────────┤
│   String Table      │  字串表
└─────────────────────┘
```

### 6.4 重要 Load Commands 說明

| Load Command | 用途 |
|---------------|------|
| `LC_SEGMENT_64` | 定義段區 (segment)，如 `__TEXT`、`__DATA` |
| `LC_BUILD_VERSION` | 指定目標平台版本 |
| `LC_SYMTAB` | 符號表位置 |
| `LC_DYSYMTAB` | 動態符號表 |

### 6.5 段區 (Sections)

| 段區 | 內容 |
|------|------|
| `__TEXT,__text` | 程式碼 |
| `__TEXT,__cstring` | C 字串常數 |
| `__LD,__compact_unwind` | 例外處理/堆疊回溯資訊 |

---

## 7. 符號表分析

### 7.1 檢視符號表

```bash
nm factorial.o
```

```
0000000000000000 T _factorial
0000000000000064 T _main
                 U _printf
00000000000000b4 s l_.str
0000000000000000 t ltmp0
00000000000000b4 s ltmp1
00000000000000c8 s ltmp2
```

### 7.2 符號類型說明

| 符號 | 類型 | 意義 |
|------|------|------|
| `_factorial` | T | 定義於 __TEXT 的函數符號 |
| `_main` | T | 定義於 __TEXT 的主函數 |
| `_printf` | U | 未定義 (undefined)，需連結時解析 |
| `l_.str` | s | 區域 static 字串 |
| `ltmp0`, `ltmp1` | t | 區域暫時符號 |

---

## 8. 重定位資訊

目的檔中尚未完成連結的位址需要重定位資訊。

```bash
otool -r factorial.o
```

```
Relocation information (__TEXT,__text) 4 entries
address  pcrel length extern type    scattered symbolnum/value
000000a0 1     2      1      2       0         6
0000009c 0     2      1      4       0         1
00000098 1     2      1      3       0         1
00000080 1     2      1      2       0         4
```

### 重定位類型說明

| type | 意義 |
|------|------|
| 2 | branch (分支) |
| 3 | branch with link (如 bl) |
| 4 | pointer (指標) |

---

## 9. 完整編譯與執行

### 9.1 連結並執行

```bash
clang -o factorial factorial.c
./factorial
```

輸出：

```
factorial(5) = 120
```

### 9.2 使用 LLVM 工具鏈逐步編譯

```bash
# 產生 IR
clang -S -emit-llvm -o factorial.ll factorial.c

# 產生目的檔
clang -c -o factorial.o factorial.c

# 連結 (使用系統連結器)
ld factorial.o -o factorial -lSystem

# 執行
./factorial
```

---

## 10. 總結

本篇文章展示了使用 clang/LLVM 工具鏈編譯 C 程式碼的完整流程：

1. **原始碼 (`.c`)**: C 語言程式碼
2. **IR (`.ll`)**: 平台無關的中間表示，適用於最佳化與跨平台編譯
3. **目的檔 (`.o`)**: 特定目標架構的機器碼 (此處為 arm64 Mach-O)

目的檔格式 Mach-O 包含：
- **Mach Header**：檔案基本資訊
- **Load Commands**：載入指示
- **Section Data**：實際程式碼與資料
- **Symbol/String Tables**：符號與字串表

LLVM IR 是連接前端與後端的橋樑，也是現代編譯器架構 (如 Clang、Rust、Swift) 的核心。

---

## 附錄：測試腳本

執行 `test.sh` 可重現本篇文章的所有輸出：

```bash
./test.sh
```