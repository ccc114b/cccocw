#!/bin/bash

echo "=== 死碼消除 (Dead Code Elimination) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat dead_code_elimination.c
echo ""

echo "--- 編譯產生未優化 IR (-O0) ---"
clang -S -emit-llvm -O0 -o dead_code_elimination_O0.ll dead_code_elimination.c
echo "產生 dead_code_elimination_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat dead_code_elimination_O0.ll
echo ""

echo "--- 編譯產生已優化 IR (-O3) ---"
clang -S -emit-llvm -O3 -o dead_code_elimination_O3.ll dead_code_elimination.c
echo "產生 dead_code_elimination_O3.ll"
echo ""

echo "--- 已優化 IR (-O3) ---"
cat dead_code_elimination_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o dead_code_elimination dead_code_elimination.c
./dead_code_elimination
echo ""

echo "=== 完成 ==="