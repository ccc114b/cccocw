#!/bin/bash

echo "=== LLVM 工具鏈測試：factorial(5) = 120 ==="
echo ""

echo "--- 1. 顯示原始碼 ---"
cat factorial.c
echo ""

echo "--- 2. 編譯產生 LLVM IR ---"
clang -S -emit-llvm -o factorial.ll factorial.c
echo "產生 factorial.ll"
echo ""

echo "--- 3. 顯示 LLVM IR ---"
cat factorial.ll
echo ""

echo "--- 4. 編譯產生目的檔 ---"
clang -c -o factorial.o factorial.c
echo "產生 factorial.o"
echo ""

echo "--- 5. 反組譯目的檔 (otool) ---"
otool -tV factorial.o
echo ""

echo "--- 6. Mach-O 標頭資訊 ---"
otool -h factorial.o
echo ""

echo "--- 7. Load Commands ---"
otool -l factorial.o
echo ""

echo "--- 8. 符號表 ---"
nm factorial.o
echo ""

echo "--- 9. 重定位資訊 ---"
otool -r factorial.o
echo ""

echo "--- 10. 連結並執行 ---"
clang -o factorial factorial.c
echo "執行結果："
./factorial
echo ""

echo "=== 完成 ==="