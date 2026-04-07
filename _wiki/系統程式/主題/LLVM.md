# LLVM

LLVM 是一個功能強大的編譯器框架。

## 組成部分

1. **LLVM IR**: 中間表示式
2. **clang**: C/C++ 編譯器前端
3. **優化通道**: 各種最佳化 pass
4. **後端**: 生成多種目標架構

## LLVM IR 語法

```llvm
; 函數定義
define i32 @add(i32 %a, i32 %b) {
    %result = add i32 %a, %b
    ret i32 %result
}
```

## 常見最佳化

- 常數折疊 (Constant Folding)
- 死碼消除 (Dead Code Elimination)
- 內聯 (Inlining)
- 迴圈展開 (Loop Unrolling)

## 相關概念

- [編譯器](../概念/編譯器.md)