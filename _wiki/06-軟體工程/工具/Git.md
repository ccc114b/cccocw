# Git

Git 是分散式版本控制系統，廣泛用於軟體開發。

## 基本概念

- **Repository**: 專案儲存庫
- **Commit**: 變更快照
- **Branch**: 分支
- **Merge**: 合併
- **Pull Request**: 請求合併

## 常用指令

```bash
# 初始化
git init
git clone url

# 提交
git add .
git commit -m "message"

# 分支
git branch -M main
git checkout -b feature

# 遠端
git remote add origin url
git push -u origin main
git pull

# 查看
git status
git log --graph --oneline
git diff
```

## Git Flow

```
main ←─────── production
  ↑
develop ←─── integration
  ↑
feature ←── new feature
  ↑
hotfix ←── bug fix
```

## 相關概念

- [版本控制](概念/版本控制.md)
- [持續整合](主題/持續整合.md)