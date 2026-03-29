# ACLCoder - 规格书 v0.1

## 概述

ACLCoder 是一个使用 ACL (AI Communication Language) 通讯协议的 AI 代码生成工具。

**核心组件：**
- AICommander - 指挥官，负责回答问题、提供建议
- AIExecutor - 执行者，负责生成代码、执行任务

**不包含：** AIL 框架（独立项目）

---

## ACL 通讯协议

### 指令格式

| 指令 | 格式 | 说明 |
|------|------|------|
| write | `<write file="檔名">內容</write>` | 写入文件 |
| shell | `<shell>命令</shell>` | 执行命令 |
| read | `<read file="檔名"></read>` | 读取文件 |
| ask | `<ask>問題</ask>` | 询问问题 |
| answer | `<answer>回覆</answer>` | 回复 |
| result | `<result>結果</result>` | 结果回报 |

### 沟通流程

```
Commander (人類) → 任務 → Executor
Executor → <ask> → Commander
Commander → <answer> → Executor  
Executor → <write> → 檔案系統
```

---

## 核心组件

### 1. AICommander

**职责：**
- 回答执行者的规格问题
- 提供技术建议
- 辅助决策

**输入：** 执行者的问题 + 项目上下文
**输出：** 建议/答案

### 2. AIExecutor

**职责：**
- 接收任务
- 分析任务需求
- 询问规格问题（使用 ACL）
- 生成代码（使用 ACL）
- 执行文件操作

**输入：** 任务描述
**输出：** 生成的代码文件

---

## 架构设计

```
┌─────────────────────────────────────────────────┐
│                  ACLCoder                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────┐      ┌──────────────────┐     │
│  │  Commander  │ ←──→ │    Executor       │     │
│  │  (AI 回答)   │      │  (AI 生成代码)    │     │
│  └─────────────┘      └──────────────────┘     │
│         ↑                      ↑                │
│         │                      │                │
│  ┌──────┴──────────────────────┴──────┐       │
│  │           ACL Parser                 │       │
│  │  (解析 <write>, <ask>, <shell>...)  │       │
│  └──────────────────────────────────────┘       │
│                      ↑                           │
│                      │                           │
│  ┌──────────────────┴──────────────────┐     │
│  │           File System / Shell          │     │
│  └───────────────────────────────────────┘     │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 文件结构

```
aclcoder/
├── _doc/
│   └── SPEC.md              # 本规格书
├── src/
│   └── aclcoder/
│       ├── __init__.py
│       ├── executor.py       # AIExecutor + AICommander
│       ├── acl_parser.py     # ACL 解析器
│       └── cli.py            # 命令行入口
├── pyproject.toml            # PyPI 配置
└── README.md
```

---

## 使用方式

### 命令行

```bash
# 从任务文本生成代码
aclcoder "建立一个 blog 系统"

# 从 .acl 任务文件
aclcoder task.acl

# 指定输出目录
aclcoder "任务" -o ./output
```

### Python API

```python
from aclcoder import AIExecutor

executor = AIExecutor(root_dir="./output")
await executor.run("建立一个 blog 系统")
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-03-29 | 初始规格，无 AIL 框架 |
