# Verilog

Verilog 是一種硬體描述語言 (HDL)，用於設計數位電路。

## 基本語法

```verilog
module and_gate (
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
```

## 資料類型

- **wire**: 連接訊號
- **reg**: 暫存器（可儲存值）
- **integer**: 整數
- **parameter**: 參數

## 建模層次

- **行為級**: 描述功能
- **暫存器傳遞級 (RTL)**: 描述資料流與暫存器
- **閘級**: 描述邏輯閘

## 相關概念

- [數位邏輯](../概念/數位邏輯.md)
- [CPU架構](../概念/CPU架構.md)