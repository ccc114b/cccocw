"""
generate.py
===========
用 sklearn 分類器做「接龍文字生成」，概念和 GPT 相同：

  GPT 的生成原理：
    1. 給定一段 prompt（前綴）
    2. 預測下一個字的「機率分布」
    3. 從分布中「抽樣」一個字（不一定取最高機率，這樣才有創意）
    4. 把新字加到序列尾端，回到步驟 2
    5. 重複直到產生 <EOS> 或達到最大長度

  這裡用 LogisticRegression 取代 Transformer，其餘流程完全相同。

  抽樣策略（對應 GPT 的 temperature / top-k sampling）：
    - temperature > 1 → 機率分布更平坦，輸出更多樣（有創意但可能亂）
    - temperature < 1 → 機率分布更尖銳，輸出更保守（接近 greedy）
    - temperature = 1 → 原始機率
    - top_k           → 只從機率最高的 k 個字中抽樣

執行方式：
    python generate.py tw.txt
"""

import sys
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter

# ── 參數設定 ──────────────────────────────────────────────
CORPUS_FILE  = "tw.txt"
CONTEXT_SIZE = 2      # 用前幾個字預測下一個字（n-gram 階數）
MAX_GEN_LEN  = 30     # 最多生成幾個字
TEMPERATURE  = 1.0    # 抽樣溫度（越高越有創意）
TOP_K        = 5      # 只從前 K 個候選字中抽樣（0 = 不限制）
RANDOM_STATE = 42
# ──────────────────────────────────────────────────────────


# ════════════════════════════════════════════════════════════
#  語料 & 訓練
# ════════════════════════════════════════════════════════════

def load_corpus(filepath: str) -> list[str]:
    """讀取語料，每行視為一句，句尾插入 <EOS>。"""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()
    chars = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            chars.extend(list(line))
            chars.append("<EOS>")
    return chars


def build_samples(chars: list[str], context_size: int):
    """滑動視窗：(前 N 字) → 下一個字。"""
    X_raw, y = [], []
    for i in range(len(chars) - context_size):
        context = " ".join(chars[i : i + context_size])
        X_raw.append(context)
        y.append(chars[i + context_size])
    return X_raw, y


def train(corpus_file: str, context_size: int):
    """讀取語料 → 建樣本 → 訓練 → 回傳 (vectorizer, clf)。"""
    print(f"[1/3] 讀取語料：{corpus_file}")
    chars = load_corpus(corpus_file)
    vocab = Counter(c for c in chars if not c.startswith("<"))
    print(f"      {len(chars)} 個字元，{len(vocab)} 種不同字")

    print(f"[2/3] 建立樣本（context_size={context_size}）…")
    X_raw, y = build_samples(chars, context_size)
    print(f"      {len(X_raw)} 筆樣本，{len(set(y))} 個目標類別")

    vectorizer = CountVectorizer(analyzer="word", token_pattern=r"\S+")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_raw, y, test_size=0.1, random_state=RANDOM_STATE
    )
    X_train = vectorizer.fit_transform(X_train_raw)
    X_test  = vectorizer.transform(X_test_raw)

    print("[3/3] 訓練 LogisticRegression…")
    clf = LogisticRegression(max_iter=1000, solver="lbfgs", C=5.0,
                             random_state=RANDOM_STATE)
    clf.fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"      測試集準確率：{acc:.2%}\n")

    return vectorizer, clf


# ════════════════════════════════════════════════════════════
#  抽樣函式（對應 GPT 的 temperature + top-k sampling）
# ════════════════════════════════════════════════════════════

def sample_next(context_chars: list[str],
                vectorizer, clf,
                temperature: float = 1.0,
                top_k: int = 0) -> tuple[str, list[tuple[str, float]]]:
    """
    給定 context_chars（長度 = context_size），
    回傳 (抽樣結果, top-5 候選清單)。

    temperature sampling：
        logit_i = log(p_i) / temperature
        softmax → 重新抽樣
    """
    context_str = " ".join(context_chars)
    try:
        X = vectorizer.transform([context_str])
    except Exception:
        return "<EOS>", []

    proba  = clf.predict_proba(X)[0]          # 原始機率
    classes = clf.classes_

    # ── top-k 篩選（先取前 k 個，其餘歸零）
    if top_k and top_k < len(proba):
        top_idx = np.argsort(proba)[::-1][:top_k]
        mask = np.zeros_like(proba)
        mask[top_idx] = proba[top_idx]
        proba = mask

    # ── temperature scaling
    log_p = np.log(np.clip(proba, 1e-10, None)) / temperature
    log_p -= log_p.max()                       # 數值穩定
    exp_p = np.exp(log_p)
    exp_p /= exp_p.sum()                       # softmax

    # ── 抽樣
    chosen_idx = np.random.choice(len(classes), p=exp_p)
    chosen     = classes[chosen_idx]

    # ── top-5 候選（供顯示）
    top5_idx = np.argsort(exp_p)[::-1][:5]
    top5 = [(classes[i], float(exp_p[i])) for i in top5_idx]

    return chosen, top5


# ════════════════════════════════════════════════════════════
#  生成（接龍）
# ════════════════════════════════════════════════════════════

def generate(prompt: str,
             vectorizer, clf,
             context_size: int,
             max_len:     int   = MAX_GEN_LEN,
             temperature: float = TEMPERATURE,
             top_k:       int   = TOP_K,
             verbose:     bool  = False) -> str:
    """
    GPT 式自回歸生成：
      將 prompt 的最後 context_size 個字當初始 context，
      不斷預測→追加→更新 context，直到 <EOS> 或達到 max_len。
    """
    # 初始化 context
    seed_chars = list(prompt)
    if len(seed_chars) >= context_size:
        context = seed_chars[-context_size:]
    else:
        context = ["<PAD>"] * (context_size - len(seed_chars)) + seed_chars

    generated = list(prompt)   # 保留完整輸出（含 prompt）

    if verbose:
        print(f"\n  prompt ：「{prompt}」")
        print(f"  context：{context}")
        print(f"  {'步驟':<4} {'預測字':<6} {'機率':<8} 前5候選")
        print(f"  {'─'*55}")

    for step in range(max_len):
        char, top5 = sample_next(context, vectorizer, clf, temperature, top_k)

        if verbose:
            cand_str = "  ".join(f"{c}({p:.0%})" for c, p in top5)
            print(f"  {step+1:<4} 「{char}」   {top5[0][1]:.2%}   {cand_str}")

        if char == "<EOS>":
            break

        generated.append(char)
        # 更新滑動視窗（和 GPT 的 KV-cache 概念相同）
        context = context[1:] + [char]

    return "".join(generated)


# ════════════════════════════════════════════════════════════
#  互動介面
# ════════════════════════════════════════════════════════════

HELP = """
指令說明：
  直接輸入文字      → 以該文字為 prompt 生成
  /temp <數字>      → 調整 temperature（預設 1.0）
  /topk <數字>      → 調整 top-k（0 = 不限，預設 5）
  /len  <數字>      → 調整最大生成長度（預設 30）
  /n    <數字>      → 一次生成幾條（預設 1）
  /v                → 切換 verbose（顯示每步預測細節）
  /demo             → 跑一組示範生成
  /help             → 顯示此說明
  q                 → 離開
"""

DEMO_PROMPTS = ["小貓", "天上", "今天", "早上", "春天", "我", "山上"]


def run_demo(vectorizer, clf, context_size):
    print("\n── 示範生成 ──────────────────────────────────────")
    for prompt in DEMO_PROMPTS:
        result = generate(prompt, vectorizer, clf, context_size,
                          max_len=20, temperature=0.8, top_k=5, verbose=False)
        print(f"  [{prompt}] → {result}")
    print("──────────────────────────────────────────────────")


def interactive(vectorizer, clf, context_size: int):
    temp    = TEMPERATURE
    top_k   = TOP_K
    max_len = MAX_GEN_LEN
    n_gen   = 1
    verbose = False

    print("\n" + "═" * 54)
    print("  sklearn 接龍生成器  （類 GPT 自回歸生成）")
    print("═" * 54)
    print(f"  temperature={temp}  top_k={top_k}  max_len={max_len}")
    print("  輸入 /help 查看指令，輸入 q 離開")
    print("═" * 54)

    run_demo(vectorizer, clf, context_size)

    while True:
        try:
            raw = input("\nprompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye!")
            break

        if not raw:
            continue
        if raw.lower() == "q":
            print("bye!")
            break
        if raw == "/help":
            print(HELP)
            continue
        if raw == "/demo":
            run_demo(vectorizer, clf, context_size)
            continue
        if raw == "/v":
            verbose = not verbose
            print(f"  verbose = {verbose}")
            continue

        # 參數調整指令
        try:
            if raw.startswith("/temp "):
                temp = float(raw.split()[1])
                print(f"  temperature → {temp}")
                continue
            if raw.startswith("/topk "):
                top_k = int(raw.split()[1])
                print(f"  top_k → {top_k}")
                continue
            if raw.startswith("/len "):
                max_len = int(raw.split()[1])
                print(f"  max_len → {max_len}")
                continue
            if raw.startswith("/n "):
                n_gen = int(raw.split()[1])
                print(f"  n_gen → {n_gen}")
                continue
        except (ValueError, IndexError):
            print("  參數格式錯誤，請重試")
            continue

        # 生成
        print()
        for i in range(n_gen):
            if n_gen > 1:
                print(f"  [{i+1}/{n_gen}]", end=" ")
            result = generate(raw, vectorizer, clf, context_size,
                              max_len=max_len, temperature=temp,
                              top_k=top_k, verbose=verbose)
            if not verbose:
                print(f"  {result}")
            else:
                print(f"\n  ▶ 生成結果：{result}")

        print(f"\n  （temperature={temp}, top_k={top_k}, max_len={max_len}）")


# ════════════════════════════════════════════════════════════
#  主程式
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    np.random.seed(RANDOM_STATE)

    corpus_file = sys.argv[1] if len(sys.argv) > 1 else CORPUS_FILE
    vectorizer, clf = train(corpus_file, CONTEXT_SIZE)
    interactive(vectorizer, clf, CONTEXT_SIZE)