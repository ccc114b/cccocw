#!/bin/bash

echo "=== 公共子表達式消除 (CSE) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat cse.c
echo ""

echo "--- 編譯產生未優化 IR (-O0) ---"
clang -S -emit-llvm -O0 -o cse_O0.ll cse.c
echo "產生 cse_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat cse_O0.ll
echo ""

echo "--- 編譯產生已優化 IR (-O3) ---"
clang -S -emit-llvm -O3 -o cse_O3.ll cse.c
echo "產生 cse_O3.ll"
echo ""

echo "--- 已優化 IR (-O3) ---"
cat cse_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o cse cse.c
./cse
echo ""

echo "=== 完成 ==="