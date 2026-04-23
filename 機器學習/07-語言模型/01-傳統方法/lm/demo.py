"""
train_predict.py
================
用 sklearn 分類器示範「字級語言模型」：
  給定前 N 個字（context），預測下一個字。

資料來源：tw.txt（繁體中文短句）

流程：
  1. 讀取語料，切成「字」序列
  2. 滑動視窗產生 (context → next_char) 樣本
  3. 用 CountVectorizer 把 context 轉成詞頻向量（特徵）
  4. 訓練 LogisticRegression 分類器
  5. 評估準確率
  6. 互動式預測：輸入前綴，輸出預測下一個字 + top-5 候選
"""

import re
import sys
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from collections import Counter

# ── 參數設定 ──────────────────────────────────────────────
CORPUS_FILE = "tw.txt"   # 語料檔案路徑
CONTEXT_SIZE = 2         # 用前幾個字來預測下一個字
TEST_SIZE    = 0.1       # 測試集比例
RANDOM_STATE = 42
TOP_K        = 5         # 預測時顯示前 K 個候選字
# ──────────────────────────────────────────────────────────


def load_corpus(filepath: str) -> list[str]:
    """讀取語料，回傳字元列表（去除空白與標點）。"""
    with open(filepath, encoding="utf-8") as f:
        text = f.read()

    # 每行視為一個句子，句尾加特殊符號 <EOS> 讓模型學到句子邊界
    chars = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        chars.extend(list(line))
        chars.append("<EOS>")   # 句尾標記

    return chars


def build_samples(chars: list[str], context_size: int):
    """
    滑動視窗產生樣本。
    X_raw : list[str]  — 每筆樣本是「前 context_size 個字」串成一個字串
    y     : list[str]  — 每筆標籤是「下一個字」
    """
    X_raw, y = [], []
    for i in range(len(chars) - context_size):
        context = " ".join(chars[i : i + context_size])   # 字與字用空格隔開
        next_ch = chars[i + context_size]
        X_raw.append(context)
        y.append(next_ch)
    return X_raw, y


def build_and_train(X_raw, y):
    """
    向量化 + 訓練分類器。
    回傳 (vectorizer, clf, X_test_raw, y_test)。
    """
    # ── 特徵：把「前 N 個字」當成 bag-of-characters，
    #    analyzer="word" 且每個「詞」是單一漢字（已用空格分隔）
    vectorizer = CountVectorizer(analyzer="word", token_pattern=r"\S+")

    X_raw_train, X_raw_test, y_train, y_test = train_test_split(
        X_raw, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    X_train = vectorizer.fit_transform(X_raw_train)
    X_test  = vectorizer.transform(X_raw_test)

    # ── 分類器：LogisticRegression（支援多類別）
    clf = LogisticRegression(
        max_iter=1000,
        solver="lbfgs",
        C=5.0,
        random_state=RANDOM_STATE,
    )
    clf.fit(X_train, y_train)

    # ── 評估
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n[評估] 測試集準確率：{acc:.2%}  ({len(y_test)} 筆樣本)")

    return vectorizer, clf, X_raw_test, y_test


def predict_next(prefix: str, vectorizer, clf,
                 context_size: int, top_k: int = TOP_K) -> list[tuple[str, float]]:
    """
    給定一段前綴字串，預測下一個字（top-k 候選 + 機率）。
    若前綴字數不足 context_size，左側補 <PAD>。
    """
    chars = list(prefix)

    # 取最後 context_size 個字當 context
    if len(chars) >= context_size:
        context_chars = chars[-context_size:]
    else:
        pad = ["<PAD>"] * (context_size - len(chars))
        context_chars = pad + chars

    context_str = " ".join(context_chars)

    try:
        X = vectorizer.transform([context_str])
    except Exception:
        return []

    proba = clf.predict_proba(X)[0]
    classes = clf.classes_

    # 取機率最高的 top_k
    top_indices = np.argsort(proba)[::-1][:top_k]
    return [(classes[i], proba[i]) for i in top_indices]


def interactive_demo(vectorizer, clf, context_size: int):
    """互動式預測介面。"""
    print("\n" + "=" * 50)
    print("互動預測模式（輸入 'q' 離開）")
    print(f"  輸入前 {context_size} 個字（或更多），模型預測下一個字")
    print("=" * 50)

    while True:
        prefix = input("\n請輸入前綴：").strip()
        if prefix.lower() == "q":
            print("bye!")
            break
        if not prefix:
            continue

        candidates = predict_next(prefix, vectorizer, clf, context_size)
        if not candidates:
            print("  （無法預測，context 中可能包含訓練時未見的字）")
            continue

        print(f"  前綴：「{prefix}」  →  預測下一個字：")
        for rank, (ch, prob) in enumerate(candidates, 1):
            bar = "█" * int(prob * 30)
            print(f"    {rank}. 「{ch}」  {prob:.2%}  {bar}")


def show_corpus_stats(chars: list[str]):
    """顯示語料基本統計。"""
    non_special = [c for c in chars if not c.startswith("<")]
    freq = Counter(non_special)
    print(f"\n[語料統計]")
    print(f"  總字元數（含標記）：{len(chars)}")
    print(f"  不重複字元數      ：{len(freq)}")
    print(f"  最常見的前 10 個字：")
    for ch, cnt in freq.most_common(10):
        print(f"    「{ch}」 出現 {cnt} 次")


def show_sample_predictions(vectorizer, clf, context_size: int):
    """展示幾個固定範例的預測結果。"""
    examples = ["小貓", "天上", "我喜", "今天", "早上"]
    print("\n[示範預測]")
    for prefix in examples:
        candidates = predict_next(prefix, vectorizer, clf, context_size)
        if candidates:
            top1 = candidates[0][0]
            top_str = "、".join(f"{c}({p:.0%})" for c, p in candidates[:3])
            print(f"  「{prefix}」→ 最佳：「{top1}」｜前3：{top_str}")


# ── 主程式 ────────────────────────────────────────────────
if __name__ == "__main__":
    corpus_file = sys.argv[1] if len(sys.argv) > 1 else CORPUS_FILE

    print(f"讀取語料：{corpus_file}")
    chars = load_corpus(corpus_file)
    show_corpus_stats(chars)

    print(f"\n建立樣本（context_size={CONTEXT_SIZE}）…")
    X_raw, y = build_samples(chars, CONTEXT_SIZE)
    print(f"  共 {len(X_raw)} 筆樣本，{len(set(y))} 個不同標籤（目標字）")

    print("\n訓練 LogisticRegression 分類器…")
    vectorizer, clf, X_raw_test, y_test = build_and_train(X_raw, y)

    show_sample_predictions(vectorizer, clf, CONTEXT_SIZE)

    # 互動模式
    interactive_demo(vectorizer, clf, CONTEXT_SIZE)