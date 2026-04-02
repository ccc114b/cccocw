#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Testing agent0.py security mechanism ==="
echo ""

TEST_DIR="test_allowed_dir"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR"
echo "test content" > testfile.txt

run_agent() {
    printf "$1\n/quit\n" | python3 agent0.py 2>&1 &
    PID=$!
    sleep 12
    kill $PID 2>/dev/null || true
    wait $PID 2>/dev/null || true
}

echo "=== Test 1: Access /etc (should be blocked) ==="
RESULT=$(run_agent "cat /etc/passwd")
if echo "$RESULT" | grep -qi "Security error\|denied\|cannot access\|violate\|security restriction\|only.*current"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "$RESULT" | head -15
fi
echo ""

echo "=== Test 2: Access ~/.bashrc (should be blocked) ==="
RESULT=$(run_agent "cat ~/.bashrc")
if echo "$RESULT" | grep -qi "Security error\|denied\|cannot access\|violate\|security restriction"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "$RESULT" | head -15
fi
echo ""

echo "=== Test 3: Path traversal (should be blocked) ==="
RESULT=$(run_agent "cat ../../../etc/passwd")
if echo "$RESULT" | grep -qi "Security error\|denied\|cannot access\|violate\|security restriction"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "$RESULT" | head -15
fi
echo ""

echo "=== Test 4: Access /tmp (should be blocked) ==="
RESULT=$(run_agent "cat /tmp/test")
if echo "$RESULT" | grep -qi "Security error\|denied\|cannot access\|violate\|security restriction\|only.*current"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "$RESULT" | head -15
fi
echo ""

echo "=== Test 5: Access relative path in allowed dir (should work) ==="
RESULT=$(run_agent "cat testfile.txt")
if echo "$RESULT" | grep -q "test content"; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
    echo "$RESULT" | head -15
fi
echo ""

echo "=== Test 6: Create file in allowed dir (should work) ==="
printf "echo hello > newfile.txt\n/quit\n" | python3 agent0.py > /dev/null 2>&1 &
PID=$!
sleep 5
kill $PID 2>/dev/null || true
wait $PID 2>/dev/null || true
if [ -f "newfile.txt" ] && grep -q "hello" newfile.txt; then
    echo "✓ PASS"
else
    echo "✗ FAIL"
fi
echo ""

rm -rf "$TEST_DIR" testfile.txt newfile.txt
echo "=== Tests completed ==="