```sh
(venv) cccuser@cccimacdeiMac 01-LLVM_IR_ASM % ./test.sh
========================================
LLVM IR -> Assembly 編譯流程示範
機器: arm64 (Apple M1/M2/M3)
範例: factorial(5) = 120
========================================

=== 1. C 程式碼 (factorial.c) ===
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    printf("factorial(5) = %d\n", result);
    return 0;
}

=== 2. 編譯 C -> LLVM IR (.ll) ===
命令: clang -S -emit-llvm -O0 factorial.c -o factorial.ll
產生: factorial.ll

--- LLVM IR 內容 ---
; ModuleID = 'factorial.c'
source_filename = "factorial.c"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128"
target triple = "arm64-apple-macosx15.0.0"

@.str = private unnamed_addr constant [19 x i8] c"factorial(5) = %d\0A\00", align 1

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @factorial(i32 noundef %0) #0 {
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  store i32 %0, ptr %3, align 4
  %4 = load i32, ptr %3, align 4
  %5 = icmp sle i32 %4, 1
  br i1 %5, label %6, label %7

6:                                                ; preds = %1
  store i32 1, ptr %2, align 4
  br label %13

7:                                                ; preds = %1
  %8 = load i32, ptr %3, align 4
  %9 = load i32, ptr %3, align 4
  %10 = sub nsw i32 %9, 1
  %11 = call i32 @factorial(i32 noundef %10)
  %12 = mul nsw i32 %8, %11
  store i32 %12, ptr %2, align 4
  br label %13

13:                                               ; preds = %7, %6
  %14 = load i32, ptr %2, align 4
  ret i32 %14
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @main() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  store i32 0, ptr %1, align 4
  %3 = call i32 @factorial(i32 noundef 5)
  store i32 %3, ptr %2, align 4
  %4 = load i32, ptr %2, align 4
  %5 = call i32 (ptr, ...) @printf(ptr noundef @.str, i32 noundef %4)
  ret i32 0
}

declare i32 @printf(ptr noundef, ...) #1

attributes #0 = { noinline nounwind optnone ssp uwtable(sync) "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+crc,+dotprod,+fp-armv8,+fp16fml,+fullfp16,+lse,+neon,+ras,+rcpc,+rdm,+sha2,+sha3,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #1 = { "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+crc,+dotprod,+fp-armv8,+fp16fml,+fullfp16,+lse,+neon,+ras,+rcpc,+rdm,+sha2,+sha3,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 15, i32 2]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 8, !"PIC Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 1}
!4 = !{i32 7, !"frame-pointer", i32 1}
!5 = !{!"Apple clang version 16.0.0 (clang-1600.0.26.6)"}

=== 3. 從 IR 產生目標檔 (.bc) ===
命令: clang -c -emit-llvm factorial.c -o factorial.bc
產生: factorial.bc (bitcode)
factorial.bc: LLVM bitcode, wrapper

=== 4. 編譯 C -> ARM64 Assembly (.s) ===
命令: clang -S -arch arm64 factorial.c -o factorial_arm64.s
產生: factorial_arm64.s

--- ARM64 Assembly 內容 ---
        .section        __TEXT,__text,regular,pure_instructions
        .build_version macos, 15, 0     sdk_version 15, 2
        .globl  _factorial                      ; -- Begin function factorial
        .p2align        2
_factorial:                             ; @factorial
        .cfi_startproc
; %bb.0:
        sub     sp, sp, #32
        stp     x29, x30, [sp, #16]             ; 16-byte Folded Spill
        add     x29, sp, #16
        .cfi_def_cfa w29, 16
        .cfi_offset w30, -8
        .cfi_offset w29, -16
        str     w0, [sp, #8]
        ldr     w8, [sp, #8]
        subs    w8, w8, #1
        cset    w8, gt
        tbnz    w8, #0, LBB0_2
        b       LBB0_1
LBB0_1:
        mov     w8, #1                          ; =0x1
        stur    w8, [x29, #-4]
        b       LBB0_3
LBB0_2:
        ldr     w8, [sp, #8]
        str     w8, [sp, #4]                    ; 4-byte Folded Spill
        ldr     w8, [sp, #8]
        subs    w0, w8, #1
        bl      _factorial
        ldr     w8, [sp, #4]                    ; 4-byte Folded Reload
        mul     w8, w8, w0
        stur    w8, [x29, #-4]
        b       LBB0_3
LBB0_3:
        ldur    w0, [x29, #-4]
        ldp     x29, x30, [sp, #16]             ; 16-byte Folded Reload
        add     sp, sp, #32
        ret
        .cfi_endproc
                                        ; -- End function
        .globl  _main                           ; -- Begin function main
        .p2align        2
_main:                                  ; @main
        .cfi_startproc
; %bb.0:
        sub     sp, sp, #48
        stp     x29, x30, [sp, #32]             ; 16-byte Folded Spill
        add     x29, sp, #32
        .cfi_def_cfa w29, 16
        .cfi_offset w30, -8
        .cfi_offset w29, -16
        mov     w8, #0                          ; =0x0
        stur    w8, [x29, #-12]                 ; 4-byte Folded Spill
        stur    wzr, [x29, #-4]
        mov     w0, #5                          ; =0x5
        bl      _factorial
        stur    w0, [x29, #-8]
        ldur    w9, [x29, #-8]
                                        ; implicit-def: $x8
        mov     x8, x9
        mov     x9, sp
        str     x8, [x9]
        adrp    x0, l_.str@PAGE
        add     x0, x0, l_.str@PAGEOFF
        bl      _printf
        ldur    w0, [x29, #-12]                 ; 4-byte Folded Reload
        ldp     x29, x30, [sp, #32]             ; 16-byte Folded Reload
        add     sp, sp, #48
        ret
        .cfi_endproc
                                        ; -- End function
        .section        __TEXT,__cstring,cstring_literals
l_.str:                                 ; @.str
        .asciz  "factorial(5) = %d\n"

.subsections_via_symbols

=== 5. IR -> ASM 對應說明 ===
IR 指令                  | ARM64 組合語言
------------------------|----------------------------------
%0 = alloca i32         | str w0, [sp, #8]    (參數存入堆疊)
%4 = load i32, ptr %3   | ldr w8, [sp, #8]   (載入局部變數)
%5 = icmp sle i32 %4, 1 | subs w8, w8, #1; cset w8, gt
br i1 %5                | tbnz w8, #0, LBB0_2 (條件分支)
store i32 1, ptr %2     | mov w8, #1; stur w8, [x29, #-4]
%10 = sub nsw i32 %9, 1| subs w0, w8, #1
%11 = call @factorial   | bl _factorial
%12 = mul nsw i32 %8,%11| mul w8, w8, w0
ret i32 %14             | ldur w0, [x29, #-4]; ret

=== 6. .ll 到 bytecode 轉換 ===
.ll (文字格式 IR) -> bytecode (二進位) 轉換:

1. .ll 檔案: 人類可讀的文字格式 LLVM IR
2. bytecode: 二進位壓縮格式 (.bc)

使用 llvm-as 工具轉換:
  llvm-as factorial.ll -o factorial.bc
  
使用 llvm-dis 反向轉換:
  llvm-dis factorial.bc -o factorial.ll

說明: 
- .ll 使用 ASCII 表示，包含所有指令的易讀文字
- .bc 是二進位格式，檔案更小，適合 linking
- clang -c -emit-llvm 會直接產生 .bc 格式

=== 7. 編譯並執行 ===
命令: clang factorial.c -o factorial && ./factorial
factorial(5) = 120

========================================
完成! 所有檔案已產生:
-rwxr-xr-x@ 1 cccuser  staff  33480 Mar 27 17:32 factorial
-rw-r--r--@ 1 cccuser  staff   2084 Mar 27 17:32 factorial_arm64.s
-rw-r--r--@ 1 cccuser  staff   3088 Mar 27 17:32 factorial.bc
-rw-r--r--@ 1 cccuser  staff   2443 Mar 27 17:32 factorial.ll
========================================
```