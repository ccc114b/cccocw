#!/bin/bash

echo "=== 迴圈展開 (Loop Unrolling) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat loop_unrolling.c
echo ""

echo "--- 編譯產生未優化 IR (-O0) ---"
clang -S -emit-llvm -O0 -o loop_unrolling_O0.ll loop_unrolling.c
echo "產生 loop_unrolling_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat loop_unrolling_O0.ll
echo ""

echo "--- 編譯產生已優化 IR (-O3) ---"
clang -S -emit-llvm -O3 -o loop_unrolling_O3.ll loop_unrolling.c
echo "產生 loop_unrolling_O3.ll"
echo ""

echo "--- 已優化 IR (-O3) ---"
cat loop_unrolling_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o loop_unrolling loop_unrolling.c
./loop_unrolling
echo ""

echo "=== 完成 ==="