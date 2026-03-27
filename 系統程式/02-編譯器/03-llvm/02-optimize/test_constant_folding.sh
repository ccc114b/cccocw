#!/bin/bash

echo "=== 常數折疊 (Constant Folding) 測試 ==="
echo ""

echo "--- 原始碼 ---"
cat constant_folding.c
echo ""

echo "--- 編譯產生未優化 IR ---"
clang -S -emit-llvm -O0 -o constant_folding_O0.ll constant_folding.c
echo "產生 constant_folding_O0.ll"
echo ""

echo "--- 未優化 IR (-O0) ---"
cat constant_folding_O0.ll
echo ""

echo "--- 編譯產生已優化 IR ---"
clang -S -emit-llvm -O3 -o constant_folding_O3.ll constant_folding.c
echo "產生 constant_folding_O3.ll"
echo ""

echo "--- 已優化 IR (O3) ---"
cat constant_folding_O3.ll
echo ""

echo "--- 編譯並執行 ---"
clang -O3 -o constant_folding constant_folding.c
./constant_folding
echo ""

echo "=== 完成 ==="