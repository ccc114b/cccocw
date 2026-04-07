# Linux系統呼叫

Linux 系統呼叫是使用者空間應用程式與 Linux 核心溝通的介面。

## 常見系統呼叫

### 行程管理

| 系統呼叫 | 功能 |
|----------|------|
| fork() | 建立新行程 |
| exec() | 執行新程式 |
| wait() | 等待子行程 |
| exit() | 終止行程 |
| getpid() | 取得行程 ID |

### 檔案操作

| 系統呼叫 | 功能 |
|----------|------|
| open() | 開啟檔案 |
| read() | 讀取資料 |
| write() | 寫入資料 |
| close() | 關閉檔案 |
| lseek() | 移動檔案指標 |

### 網路

| 系統呼叫 | 功能 |
|----------|------|
| socket() | 建立 Socket |
| bind() | 綁定位址 |
| listen() | 監聽連線 |
| accept() | 接受連線 |
| connect() | 連線至伺服器 |

## 使用方式

```c
#include <unistd.h>

int fd = open("/path/file", O_RDONLY);
read(fd, buffer, size);
close(fd);
```

## 相關概念

- [作業系統](概念/作業系統.md)
- [行程與執行緒](主題/行程與執行緒.md)