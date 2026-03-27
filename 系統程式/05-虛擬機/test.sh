#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "=== 編譯 C 程式 ==="
riscv64-unknown-elf-gcc -o factorial factorial.c -lc
echo "編譯完成: factorial"

echo ""
echo "=== 使用 Spike 模擬器執行 ==="
echo "執行: spike pk factorial"
spike /opt/homebrew/Cellar/riscv-pk/main/riscv64-unknown-elf/bin/pk factorial

echo ""
echo "=== 執行完成 ==="
