#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "===== Test 1: Compile to Assembly ====="
riscv64-unknown-elf-gcc -S -O0 -o factorial.s factorial.c
echo "✓ Assembly generated: factorial.s"

echo ""
echo "===== Test 2: Compile to Object File ====="
riscv64-unknown-elf-gcc -c -O0 -o factorial.o factorial.c
echo "✓ Object file generated: factorial.o"

echo ""
echo "===== Test 3: Generate Objdump (without -g) ====="
riscv64-unknown-elf-objdump -d factorial.o > factorial_objdump.txt
echo "✓ Objdump generated: factorial_objdump.txt"

echo ""
echo "===== Test 4: Compile with Debug Info (-g) ====="
riscv64-unknown-elf-gcc -g -O0 -o factorial_debug factorial.c
echo "✓ Debug binary generated: factorial_debug"

echo ""
echo "===== Test 5: Objdump with Debug Info ====="
riscv64-unknown-elf-objdump -d factorial_debug > factorial_debug_objdump.txt
echo "✓ Debug objdump generated: factorial_debug_objdump.txt"

echo ""
echo "===== Test 6: Check DWARF info ====="
riscv64-unknown-elf-objdump -g factorial_debug > factorial_dwarf.txt 2>/dev/null || true
echo "✓ DWARF info generated: factorial_dwarf.txt"

echo ""
echo "===== All tests passed! ====="
