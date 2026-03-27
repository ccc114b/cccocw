#!/bin/bash

echo "=== 內聯展開 (Inlining) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat inlining.c
echo ""

echo "--- 編譯產生未優化 IR (-O0) ---"
clang -S -emit-llvm -O0 -o inlining_O0.ll inlining.c
echo "產生 inlining_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat inlining_O0.ll
echo ""

echo "--- 編譯產生已優化 IR (-O3) ---"
clang -S -emit-llvm -O3 -o inlining_O3.ll inlining.c
echo "產生 inlining_O3.ll"
echo ""

echo "--- 已優化 IR (-O3) ---"
cat inlining_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o inlining inlining.c
./inlining
echo ""

echo "=== 完成 ==="