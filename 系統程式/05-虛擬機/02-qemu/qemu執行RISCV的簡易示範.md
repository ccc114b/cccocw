# QEMU 執行 RISC-V 程式簡易示範

> 注意：macOS Homebrew QEMU 預設只提供 system-mode，不含 user-mode。本文使用 Spike 模擬器代替 QEMU user-mode 進行示範。

## 環境

- **編譯器**：riscv64-unknown-elf-gcc
- **模擬器**：Spike (RISC-V ISA Simulator) + pk (Proxy Kernel)
- **目標**：計算 5! = 120

## 程式碼

```c
// factorial.c
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

## 編譯與執行流程

### 1. 編譯 C 程式

```bash
riscv64-unknown-elf-gcc -o factorial factorial.c -lc
```

- `-o factorial`：輸出檔名為 factorial
- `-lc`：連結 C 標準程式庫

編譯結果是 **ELF 格式的可執行檔**：

```
factorial: ELF 64-bit LSB executable, UCB RISC-V, RVC, double-float ABI
```

### 2. 使用模擬器執行

```bash
spike pk factorial
```

輸出：
```
bbl loader
factorial(5) = 120
```

## 原理說明

### 為什麼不能直接執行目的檔？

1. **目的檔（.o）**：只包含機器碼和符號，還需要與程式庫鏈接
2. **可執行檔（ELF）**：完整的程式，包含入口點（_start）和所有依賴

### 什麼是 Spike？

Spike 是 RISC-V 的開源模擬器，包含兩部分：

1. **pk (Proxy Kernel)**：代理核心
   - 處理系統呼叫（syscall）
   - 提供基本執行環境

2. **Spike 模擬器**
   - 模擬 RISC-V CPU 指令
   - 載入並執行 ELF 檔

### 執行流程

```
factorial.c
    ↓ riscv64-unknown-elf-gcc
factorial (ELF for RISC-V)
    ↓
spike pk factorial
    ↓
┌─────────────────────────────┐
│   Spike 模擬器 (RISC-V CPU)  │
│   ┌─────────────────────┐   │
│   │  Proxy Kernel (pk)  │   │
│   │  - 處理 syscalls   │   │
│   │  - 程式載入器      │   │
│   └─────────────────────┘   │
│   ┌─────────────────────┐   │
│   │  factorial 程式     │   │
│   │  factorial(5)=120  │   │
│   └─────────────────────┘   │
└─────────────────────────────┘
```

### QEMU user-mode vs Spike

| 特性 | QEMU user-mode | Spike |
|------|----------------|-------|
| 用途 | 跨平台執行 | 軟體模擬 |
| 效能 | 接近原生 | 較慢 |
| 適用場景 | 開發測試 | 偵錯/教學 |

## 自動化測試

```bash
./test.sh
```

輸出：
```
=== 編譯 C 程式 ===
編譯完成: factorial

=== 使用 Spike 模擬器執行 ===
執行: spike pk factorial
bbl loader
factorial(5) = 120

=== 執行完成 ===
```

## 檔案清單

- `factorial.c` - C 原始碼
- `factorial` - 編譯後的 RISC-V ELF 可執行檔
- `test.sh` - 自動化編譯與執行腳本

## 常見問題

### Q: QEMU 不能執行嗎？

A: 可以，但需要：
- QEMU user-mode (`qemu-riscv64`)
- Linux RISC-V 工具鏈（riscv64-linux-gnu-gcc）

macOS Homebrew 預設只提供 system-mode。

### Q: 為什麼需要 Proxy Kernel (pk)？

A: Spike 只模擬 CPU，無法處理系統呼叫。pk 提供基本的作業系統介面，讓程式可以呼叫 printf 等函式。

## 參考資源

- [Spike RISC-V Simulator](https://github.com/riscv-software-src/riscv-isa-sim)
- [RISC-V Proxy Kernel](https://github.com/riscv-software-src/riscv-pk)
- [RISC-V GNU Compiler Toolchain](https://github.com/riscv-collab/riscv-gnu-toolchain)
