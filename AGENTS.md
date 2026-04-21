# CCC114B Course Repository

Course materials for 陳鍾誠. Static content deployed via GitHub Pages on push to `main`.

## Directory Structure

```
├── _code/nn/agent/  # Agent projects (v5-agent-class through v7-agent-session)
├── _doc/            # Documentation
├── _wiki/           # LLM Wiki knowledge base (has its own AGENTS.md)
├── 系統程式/         # Flat structure only
├── 計算機結構/       # Flat structure only
├── 演算法/          # Flat structure only
├── 機器學習/        # Flat structure only
├── 網頁設計/        # Flat structure only
└── 軟體工程/        # Flat structure only
```

**Critical**: Category folders use **flat structure** — `.py` and `.md` files directly in the folder. No nested subdirectories.

## Key Commands

```bash
# Remove node_modules and target directories
./clean_garbage.sh

# Run agent project (from its directory)
python main.py
```

## Subproject AGENTS.md Files

- `_wiki/AGENTS.md` — LLM Wiki operation guide
- `_code/nn/agent/v7-agent-session/AGENTS.md` — Latest agent (Plan/Exec/Eval mode)
- `_code/nn/agent/v5-agent-class/AGENTS.md` — Previous agent version

## GitHub Pages Deployment

Push to `main` → GitHub Pages (entire repo served statically, no build step).

## Git Notes

- `.gitignore` excludes `bin/` but **keeps** `src/bin/`
- Run tests from subproject directories

## Machine Learning Methods

Documented in `_wiki/機器學習/` (flat structure):

| Method | File | Type |
|--------|------|------|
| KNN | `K-近鄰.md` | Supervised |
| Naive Bayes | `樸素貝葉斯.md` | Supervised |
| Decision Tree | `決策樹.md` | Supervised |
| Random Forest | `隨機森林.md` | Supervised |
| SVM | `支持向量機.md` | Supervised |
| K-Means | `K-均值.md` | Unsupervised |
| PCA | `主成分分析.md` | Unsupervised |
| Linear Regression | `線性回歸.md` | Regression |
| Neural Network | `神經網路.md` | Deep Learning |
| CNN | `卷積神經網路.md` | Deep Learning |
| Transformer | `Transformer.md` | Deep Learning |
