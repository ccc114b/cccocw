# TCP-IP協定

TCP/IP 是網際網路的基礎協定。

## 協定層次

```
應用層     │ HTTP, DNS, SSH, FTP
傳輸層     │ TCP, UDP
網路層     │ IP, ICMP, ARP
連結層    │ Ethernet, WiFi
```

## TCP 特性

### 三向交握

```
客戶端 → SYN → 伺服器
客戶端 ← SYN-ACK ← 伺服器
客戶端 → ACK → 伺服器
```

### 四向揮手

```
客戶端 → FIN → 伺服器
客戶端 ← ACK ← 伺服器
客戶端 ← FIN ← 伺服器
客戶端 → ACK → 伺服器
```

### 流量控制

- **滑動視窗**: 調整傳送速率
- **壅塞控制**: 避免網路過載

## IP 位址

- IPv4: 32-bit 位址
- IPv6: 128-bit 位址

## 相關概念

- [網路](../概念/網路.md)
- [HTTP](../主題/HTTP.md)