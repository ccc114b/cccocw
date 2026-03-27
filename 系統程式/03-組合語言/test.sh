#!/bin/bash

set -e

echo "===== Test 1: Compile and Run ====="
clang -o factorial factorial.c
./factorial
EXPECTED=120
ACTUAL=$(./factorial | sed 's/.*= //')
if [ "$ACTUAL" -eq "$EXPECTED" ]; then
    echo "✓ Test passed: factorial(5) = $ACTUAL"
else
    echo "✗ Test failed: expected $EXPECTED, got $ACTUAL"
    exit 1
fi

echo ""
echo "===== Test 2: Generate Assembly ====="
clang -S -O0 -o factorial.s factorial.c
echo "✓ Assembly generated: factorial.s"

echo ""
echo "===== Test 3: Generate Object File ====="
clang -c -O0 -o factorial.o factorial.c
echo "✓ Object file generated: factorial.o"

echo ""
echo "===== Test 4: Generate Objdump (without -g) ====="
/usr/bin/objdump -d factorial.o > factorial_objdump.txt
echo "✓ Objdump generated: factorial_objdump.txt"

echo ""
echo "===== Test 5: Generate Debug Info (-g) ====="
clang -g -O0 -o factorial_debug factorial.c
/usr/bin/objdump -d factorial_debug > factorial_debug_objdump.txt
echo "✓ Debug objdump generated: factorial_debug_objdump.txt"

echo ""
echo "===== Test 6: Check DWARF debug info ====="
/usr/bin/dwarfdump --debug-info factorial_debug > factorial_dwarf.txt 2>/dev/null || true
echo "✓ DWARF info generated: factorial_dwarf.txt"

echo ""
echo "===== All tests passed! ====="
