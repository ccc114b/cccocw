# DevOps

DevOps 結合開發與維運，提升交付效率與品質。

## 核心實踐

1. **自動化**: 減少人為錯誤
2. **持續交付**: 快速可靠發布
3. **監控**: 即時了解系統狀態
4. **協作**: 開發與維運團隊合作

## CI/CD

```
原始碼 → 建構 → 測試 → 部署 → 生產
   ↑                      │
   └────── 回饋 ───────────┘
```

## 常見工具

| 類別 | 工具 |
|------|------|
| CI/CD | Jenkins, GitHub Actions, GitLab CI |
| 容器 | Docker, Kubernetes |
| 監控 | Prometheus, Grafana |
| 日誌 | ELK Stack, Loki |
| 雲端 | AWS, GCP, Azure |

## Infrastructure as Code

```yaml
# Terraform
resource "aws_instance" "web" {
    ami           = "ami-12345"
    instance_type = "t2.micro"
    tags = {
        Name = "web-server"
    }
}
```

## 相關概念

- [持續整合](持續整合.md)
- [持續部署](持續部署.md)
- [Docker](../系統程式/Docker.md)