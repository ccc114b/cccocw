# QEMU

QEMU 是功能強大的開源虛擬機。

## 功能

- 使用者模式: 模擬單一程式
- 系統模式: 模擬完整電腦
- 支援多種 CPU 架構 (x86, ARM, RISC-V, MIPS 等)

## 使用方式

```bash
# 執行 RISC-V 執行檔
qemu-riscv64 -L /path/to/riscv64/sysroot ./hello

# 完整系統模擬
qemu-system-riscv64 \
    -nographic \
    -machine virt \
    -kernel Image
```

## 相關概念

- [虛擬機](../概念/虛擬機.md)