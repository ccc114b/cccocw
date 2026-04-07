# Kubernetes

Kubernetes (K8s) 是容器編排平台。

## 核心概念

- **Pod**: 最小部署單元
- **Deployment**: 管理 Pod 部署與副本
- **Service**: 網路服務暴露
- **ConfigMap**: 設定管理
- **Secret**: 敏感資料管理

## 使用方式

```bash
# 部署應用
kubectl apply -f deployment.yaml

# 查看 Pod
kubectl get pods

# 擴展副本
kubectl scale deployment myapp --replicas=5
```

## Deployment 範例

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
```

## 相關概念

- [Docker](../工具/Docker.md)
- [雲端技術](../概念/雲端技術.md)