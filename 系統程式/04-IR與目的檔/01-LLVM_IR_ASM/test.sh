#!/bin/bash

set -e

echo "========================================"
echo "LLVM IR -> Assembly 編譯流程示範"
echo "機器: arm64 (Apple M1/M2/M3)"
echo "範例: factorial(5) = 120"
echo "========================================"

# Step 1: 顯示 C 程式碼
echo ""
echo "=== 1. C 程式碼 (factorial.c) ==="
cat factorial.c

# Step 2: 編譯 C 到 LLVM IR (.ll)
echo ""
echo "=== 2. 編譯 C -> LLVM IR (.ll) ==="
echo "命令: clang -S -emit-llvm -O0 factorial.c -o factorial.ll"
clang -S -emit-llvm -O0 factorial.c -o factorial.ll
echo "產生: factorial.ll"
echo ""
echo "--- LLVM IR 內容 ---"
cat factorial.ll

# Step 3: 從 IR 產生目標檔 (可選)
echo ""
echo "=== 3. 從 IR 產生目標檔 (.bc) ==="
echo "命令: clang -c -emit-llvm factorial.c -o factorial.bc"
clang -c -emit-llvm factorial.c -o factorial.bc
echo "產生: factorial.bc (bitcode)"
file factorial.bc

# Step 4: 產生 ARM64 組合語言
echo ""
echo "=== 4. 編譯 C -> ARM64 Assembly (.s) ==="
echo "命令: clang -S -arch arm64 factorial.c -o factorial_arm64.s"
clang -S -arch arm64 factorial.c -o factorial_arm64.s
echo "產生: factorial_arm64.s"
echo ""
echo "--- ARM64 Assembly 內容 ---"
cat factorial_arm64.s

# Step 5: 顯示 IR 到 ASM 對應說明
echo ""
echo "=== 5. IR -> ASM 對應說明 ==="
cat << 'EOF'
IR 指令                  | ARM64 組合語言
------------------------|----------------------------------
%0 = alloca i32         | str w0, [sp, #8]    (參數存入堆疊)
%4 = load i32, ptr %3   | ldr w8, [sp, #8]   (載入局部變數)
%5 = icmp sle i32 %4, 1 | subs w8, w8, #1; cset w8, gt
br i1 %5                | tbnz w8, #0, LBB0_2 (條件分支)
store i32 1, ptr %2     | mov w8, #1; stur w8, [x29, #-4]
%10 = sub nsw i32 %9, 1| subs w0, w8, #1
%11 = call @factorial   | bl _factorial
%12 = mul nsw i32 %8,%11| mul w8, w8, w0
ret i32 %14             | ldur w0, [x29, #-4]; ret
EOF

echo ""
echo "=== 6. .ll 到 bytecode 轉換 ==="
cat << 'EOF'
.ll (文字格式 IR) -> bytecode (二進位) 轉換:

1. .ll 檔案: 人類可讀的文字格式 LLVM IR
2. bytecode: 二進位壓縮格式 (.bc)

使用 llvm-as 工具轉換:
  llvm-as factorial.ll -o factorial.bc
  
使用 llvm-dis 反向轉換:
  llvm-dis factorial.bc -o factorial.ll

說明: 
- .ll 使用 ASCII 表示，包含所有指令的易讀文字
- .bc 是二進位格式，檔案更小，適合 linking
- clang -c -emit-llvm 會直接產生 .bc 格式
EOF

# Step 6: 編譯並執行
echo ""
echo "=== 7. 編譯並執行 ==="
echo "命令: clang factorial.c -o factorial && ./factorial"
clang factorial.c -o factorial
./factorial

echo ""
echo "========================================"
echo "完成! 所有檔案已產生:"
ls -la *.ll *.bc *.s factorial 2>/dev/null
echo "========================================"
