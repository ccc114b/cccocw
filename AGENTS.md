# CCC114B Course Repository

Course materials for 陳鍾誠. Static content deployed via GitHub Pages on push to `main`.

## Directory Structure

```
├── _code/nn/agent/  # Standalone projects (v0-chat through v5-agent-class)
├── _doc/            # Documentation
├── _wiki/           # LLM Wiki knowledge base
├── 系統程式/         # Flat structure only
├── 計算機結構/       # Flat structure only
├── 演算法/          # Flat structure only
├── 機器學習/        # Flat structure only
├── 網頁設計/        # Flat structure only
└── 軟體工程/        # Flat structure only
```

**Critical**: Category folders require **flat structure** — `.py` and `.md` files directly in the folder. No nested subdirectories.

## Key Commands

```bash
./clean_garbage.sh    # Remove node_modules and target directories
```

## Subproject AGENTS.md Files

Each project has its own instructions:
- `_wiki/AGENTS.md` — LLM Wiki operation guide
- `_code/nn/agent/v5-agent-class/AGENTS.md` — Current Ollama agent project
- `_code/nn/agent/v4-agent-context/AGENTS.md` — Previous agent version

## GitHub Pages Deployment

Push to `main` → GitHub Pages (entire repo served statically, no build step).

## Git Notes

- `.gitignore` excludes `bin/` but **keeps** `src/bin/`
- Run tests from subproject directories
