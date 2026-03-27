#!/bin/bash

echo "=== 強度折減 (Strength Reduction) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat strength_reduction.c
echo ""

echo "--- 編譯產生未優化 IR (-O0) ---"
clang -S -emit-llvm -O0 -o strength_reduction_O0.ll strength_reduction.c
echo "產生 strength_reduction_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat strength_reduction_O0.ll
echo ""

echo "--- 編譯產生已優化 IR (-O3) ---"
clang -S -emit-llvm -O3 -o strength_reduction_O3.ll strength_reduction.c
echo "產生 strength_reduction_O3.ll"
echo ""

echo "--- 已優化 IR (-O3) ---"
cat strength_reduction_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o strength_reduction strength_reduction.c
./strength_reduction
echo ""

echo "=== 完成 ==="