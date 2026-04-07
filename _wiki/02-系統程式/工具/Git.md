# Git

Git 是分散式版本控制系統。

## 基本概念

- **Repository**: 專案儲存庫
- **Commit**: 快照記錄
- **Branch**: 分支
- **Merge**: 合併

## 基本指令

```bash
# 初始化
git init

# 克隆
git clone url

# 提交
git add .
git commit -m "message"

# 分支
git branch feature
git checkout feature

# 合併
git merge feature
```

## 工作流程

```
工作目錄 → 暫存區 → 儲存庫
  add        commit
```

## 相關概念

- [版本控制](主題/版本控制.md)