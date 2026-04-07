# Docker

Docker 是輕量級的容器化技術。

## 基本概念

- **映像檔 (Image)**: 唯讀範本
- **容器 (Container)**: 映像檔的執行個體
- **倉庫 (Registry)**: 存放映像檔

## 使用方式

```bash
# 建構映像檔
docker build -t myapp .

# 執行容器
docker run -p 8080:80 myapp
```

## Dockerfile

```dockerfile
FROM ubuntu:20.04
RUN apt-get update
COPY . /app
WORKDIR /app
CMD ["python3", "app.py"]
```

## 相關概念

- [雲端技術](../概念/雲端技術.md)
- [Kubernetes](../工具/Kubernetes.md)