```sh
=== LLVM 工具鏈測試：factorial(5) = 120 ===

--- 1. 顯示原始碼 ---
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int main() {
    int result = factorial(5);
    printf("factorial(5) = %d\n", result);
    return 0;
}
--- 2. 編譯產生 LLVM IR ---
產生 factorial.ll

--- 3. 顯示 LLVM IR ---
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

--- 4. 編譯產生目的檔 ---
產生 factorial.o

--- 5. 反組譯目的檔 (otool) ---
factorial.o:
(__TEXT,__text) section
_factorial:
0000000000000000	sub	sp, sp, #0x20
0000000000000004	stp	x29, x30, [sp, #0x10]
0000000000000008	add	x29, sp, #0x10
000000000000000c	str	w0, [sp, #0x8]
0000000000000010	ldr	w8, [sp, #0x8]
0000000000000014	subs	w8, w8, #0x1
0000000000000018	cset	w8, gt
000000000000001c	tbnz	w8, #0x0, 0x30
0000000000000020	b	0x24
0000000000000024	mov	w8, #0x1
0000000000000028	stur	w8, [x29, #-0x4]
000000000000002c	b	0x54
0000000000000030	ldr	w8, [sp, #0x8]
0000000000000034	str	w8, [sp, #0x4]
0000000000000038	ldr	w8, [sp, #0x8]
000000000000003c	subs	w0, w8, #0x1
0000000000000040	bl	_factorial
0000000000000044	ldr	w8, [sp, #0x4]
0000000000000048	mul	w8, w8, w0
000000000000004c	stur	w8, [x29, #-0x4]
0000000000000050	b	0x54
0000000000000054	ldur	w0, [x29, #-0x4]
0000000000000058	ldp	x29, x30, [sp, #0x10]
000000000000005c	add	sp, sp, #0x20
0000000000000060	ret
_main:
0000000000000064	sub	sp, sp, #0x30
0000000000000068	stp	x29, x30, [sp, #0x20]
000000000000006c	add	x29, sp, #0x20
0000000000000070	mov	w8, #0x0
0000000000000074	stur	w8, [x29, #-0xc]
0000000000000078	stur	wzr, [x29, #-0x4]
000000000000007c	mov	w0, #0x5
0000000000000080	bl	0x80
0000000000000084	stur	w0, [x29, #-0x8]
0000000000000088	ldur	w9, [x29, #-0x8]
000000000000008c	mov	x8, x9
0000000000000090	mov	x9, sp
0000000000000094	str	x8, [x9]
0000000000000098	adrp	x0, 0 ; 0x0
000000000000009c	add	x0, x0, #0x0
00000000000000a0	bl	0xa0
00000000000000a4	ldur	w0, [x29, #-0xc]
00000000000000a8	ldp	x29, x30, [sp, #0x20]
00000000000000ac	add	sp, sp, #0x30
00000000000000b0	ret

--- 6. Mach-O 標頭資訊 ---
factorial.o:
Mach header
      magic  cputype cpusubtype  caps    filetype ncmds sizeofcmds      flags
 0xfeedfacf 16777228          0  0x00           1     4        440 0x00002000

--- 7. Load Commands ---
factorial.o:
Load command 0
      cmd LC_SEGMENT_64
  cmdsize 312
  segname 
   vmaddr 0x0000000000000000
   vmsize 0x0000000000000108
  fileoff 472
 filesize 264
  maxprot 0x00000007
 initprot 0x00000007
   nsects 3
    flags 0x0
Section
  sectname __text
   segname __TEXT
      addr 0x0000000000000000
      size 0x00000000000000b4
    offset 472
     align 2^2 (4)
    reloff 736
    nreloc 4
     flags 0x80000400
 reserved1 0
 reserved2 0
Section
  sectname __cstring
   segname __TEXT
      addr 0x00000000000000b4
      size 0x0000000000000013
    offset 652
     align 2^0 (1)
    reloff 0
    nreloc 0
     flags 0x00000002
 reserved1 0
 reserved2 0
Section
  sectname __compact_unwind
   segname __LD
      addr 0x00000000000000c8
      size 0x0000000000000040
    offset 672
     align 2^3 (8)
    reloff 768
    nreloc 2
     flags 0x02000000
 reserved1 0
 reserved2 0
Load command 1
      cmd LC_BUILD_VERSION
  cmdsize 24
 platform 1
    minos 15.0
      sdk 15.2
   ntools 0
Load command 2
     cmd LC_SYMTAB
 cmdsize 24
  symoff 784
   nsyms 7
  stroff 896
 strsize 56
Load command 3
            cmd LC_DYSYMTAB
        cmdsize 80
      ilocalsym 0
      nlocalsym 4
     iextdefsym 4
     nextdefsym 2
      iundefsym 6
      nundefsym 1
         tocoff 0
           ntoc 0
      modtaboff 0
        nmodtab 0
   extrefsymoff 0
    nextrefsyms 0
 indirectsymoff 0
  nindirectsyms 0
      extreloff 0
        nextrel 0
      locreloff 0
        nlocrel 0

--- 8. 符號表 ---
0000000000000000 T _factorial
0000000000000064 T _main
                 U _printf
00000000000000b4 s l_.str
0000000000000000 t ltmp0
00000000000000b4 s ltmp1
00000000000000c8 s ltmp2

--- 9. 重定位資訊 ---
factorial.o:
Relocation information (__TEXT,__text) 4 entries
address  pcrel length extern type    scattered symbolnum/value
000000a0 1     2      1      2       0         6
0000009c 0     2      1      4       0         1
00000098 1     2      1      3       0         1
00000080 1     2      1      2       0         4
Relocation information (__LD,__compact_unwind) 2 entries
address  pcrel length extern type    scattered symbolnum/value
00000020 0     3      0      0       0         1
00000000 0     3      0      0       0         1

--- 10. 連結並執行 ---
執行結果：
factorial(5) = 120

=== 完成 ===
```