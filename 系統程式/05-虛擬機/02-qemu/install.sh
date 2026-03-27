#!/bin/bash

set -e

echo "=== 安裝 RISC-V 開發工具 ==="
echo ""

check_command() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1 已安裝"
        return 0
    else
        echo "✗ $1 未安裝"
        return 1
    fi
}

echo "=== 1. 檢查 Homebrew ==="
if ! command -v brew &> /dev/null; then
    echo "安裝 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✓ Homebrew 已安裝"
fi

echo ""
echo "=== 2. 檢查 RISC-V 工具鏈 ==="

check_command riscv64-unknown-elf-gcc || brew install --force riscv-gnu-toolchain

echo ""
echo "=== 3. 檢查 Spike 模擬器 ==="

check_command spike || brew install --force riscv-isa-sim

echo ""
echo "=== 4. 檢查 RISC-V Proxy Kernel ==="

check_command pk || brew install --force riscv-pk

echo ""
echo "=== 5. 檢查 QEMU ==="

if command -v qemu-riscv64 &> /dev/null; then
    echo "✓ qemu-riscv64 (user-mode) 已安裝"
elif command -v qemu-system-riscv64 &> /dev/null; then
    echo "⚠ qemu-system-riscv64 已安裝，但 user-mode 未編譯"
    echo "  如需 qemu-riscv64，請從源碼編譯："
    echo "  brew install --build-from-source qemu"
else
    echo "安裝 QEMU..."
    brew install --force qemu
fi

echo ""
echo "=== 6. 驗證安裝 ==="

echo ""
echo "編譯器："
riscv64-unknown-elf-gcc --version | head -1

echo ""
echo "模擬器："
spike --version 2>&1 | head -1

echo ""
echo "=== 安裝完成 ==="
echo ""
echo "快速測試："
echo "  1. 編譯: riscv64-unknown-elf-gcc -o factorial factorial.c -lc"
echo "  2. 執行: spike \$(brew --prefix)/Cellar/riscv-pk/main/riscv64-unknown-elf/bin/pk factorial"
echo ""
echo "或使用 test.sh: ./test.sh"
