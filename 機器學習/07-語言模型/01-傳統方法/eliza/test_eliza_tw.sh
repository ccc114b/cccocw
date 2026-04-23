#!/usr/bin/env bash
# =============================================================================
# test_eliza_tw.sh  —  多輪對話測試腳本 for eliza_tw.py（中文版）
# 使用方式：bash test_eliza_tw.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELIZA="$SCRIPT_DIR/eliza_tw.py"
PASS=0
FAIL=0
TOTAL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

# --------------------------------------------------------------------------
# run_test <名稱> <輸入> <預期 grep -E 模式>
#   擷取 ELIZA 的第一個非離開語回應，比對是否符合模式。
# --------------------------------------------------------------------------
run_test() {
    local name="$1"
    local input="$2"
    local pattern="$3"

    TOTAL=$((TOTAL + 1))

    response=$(printf '%s\n再見\n' "$input" | python3 "$ELIZA" 2>/dev/null \
               | grep "ELIZA：" \
               | grep -v -E "歡迎|再見|掰掰|希望今天|保重|有需要隨時" \
               | head -1 \
               | sed 's/.*ELIZA：//')

    if echo "$response" | grep -qE "$pattern"; then
        echo -e "  ${GREEN}通過${RESET}  [$name]"
        echo -e "        輸入：$input"
        echo -e "        回應：$response"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}失敗${RESET}  [$name]"
        echo -e "        輸入：$input"
        echo -e "        回應：${response:-（無回應）}"
        echo -e "        預期符合：$pattern"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# --------------------------------------------------------------------------
# run_test_exit <名稱> <輸入離開詞> <預期模式>
#   專門用來測試離開詞；不過濾離開回應。
# --------------------------------------------------------------------------
run_test_exit() {
    local name="$1"
    local input="$2"
    local pattern="$3"

    TOTAL=$((TOTAL + 1))

    response=$(printf '%s\n' "$input" | python3 "$ELIZA" 2>/dev/null \
               | grep "ELIZA：" \
               | tail -1 \
               | sed 's/.*ELIZA：//')

    if echo "$response" | grep -qE "$pattern"; then
        echo -e "  ${GREEN}通過${RESET}  [$name]"
        echo -e "        輸入：$input"
        echo -e "        回應：$response"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}失敗${RESET}  [$name]"
        echo -e "        輸入：$input"
        echo -e "        回應：${response:-（無回應）}"
        echo -e "        預期符合：$pattern"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# --------------------------------------------------------------------------
# run_test_no_crash <名稱> <輸入>
#   只驗證程式不崩潰（exit code = 0），適合空白輸入等邊界情境。
# --------------------------------------------------------------------------
run_test_no_crash() {
    local name="$1"
    local input="$2"

    TOTAL=$((TOTAL + 1))

    printf '%s\n再見\n' "$input" | python3 "$ELIZA" 2>/dev/null
    local ec=$?

    if [[ $ec -eq 0 ]]; then
        echo -e "  ${GREEN}通過${RESET}  [$name]  （程式正常結束，exit code=0）"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}失敗${RESET}  [$name]  （exit code=$ec，程式異常）"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# --------------------------------------------------------------------------
# run_conversation <名稱> <多行輸入>
#   執行完整多輪對話並印出完整對話紀錄。
# --------------------------------------------------------------------------
run_conversation() {
    local name="$1"
    local inputs="$2"

    echo -e "${CYAN}━━━ 對話情境：$name ━━━${RESET}"
    printf '%s\n' "$inputs" | python3 "$ELIZA" 2>/dev/null \
        | grep -v -E "^=+$|^-+$|^$"
    echo ""
}

# =============================================================================
echo -e "${YELLOW}"
echo "╔══════════════════════════════════════════════╗"
echo "║      ELIZA 中文版（eliza_tw.py）測試套件     ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

if [[ ! -f "$ELIZA" ]]; then
    echo -e "${RED}錯誤：找不到 $ELIZA${RESET}"
    exit 1
fi

# =============================================================================
echo -e "${YELLOW}▶ 第一節：模式比對單元測試${RESET}"
echo ""

run_test "我需要…"         "我需要幫助"         "需要|幫助|確定|會|得到"
run_test "我覺得…"         "我覺得很難過"       "覺得|感受|時候|讓你|告訴"
run_test "我感到…"         "我感到孤單"         "感到|久|時候|為什麼|常常"
run_test "我是…"           "我是學生"           "學生|感受|多久|想法|來找"
run_test "我想…"           "我想放棄"           "為什麼|如果|一直|改變"
run_test "我喜歡…"         "我喜歡音樂"         "為什麼|特別|告訴"
run_test "我討厭…"         "我討厭考試"         "為什麼|什麼時候|感受"
run_test "我為什麼不能…"   "我為什麼不能快樂"   "應該|如果|為什麼|阻止"
run_test "你為什麼不…"     "你為什麼不幫我"     "真的|最終|覺得"
run_test "家人關鍵字"       "我媽媽很嚴格"       "家人|關係|感受|今天"
run_test "電腦關鍵字"       "你只是個AI"         "電腦|說我|奇怪|感受|不同"
run_test "問句"             "你覺得我怎麼了？"   "為什麼|自己|答案|你覺得"
run_test "謝謝"             "謝謝你"             "不客氣|高興|樂意"
run_test "預設回應"         "今天天氣真好"       "說|感受|嗎|然後|意思|告訴|為什麼"

# =============================================================================
echo -e "${YELLOW}▶ 第二節：完整多輪對話情境${RESET}"
echo ""

run_conversation "學業壓力" \
"我覺得壓力好大
我需要休息
我是高三生
我為什麼不能好好放鬆
我討厭考試
再見"

run_conversation "人際關係困擾" \
"我感到很孤單
我想交到真心朋友
你為什麼不懂我
我媽媽說我太內向
我覺得沒有人理解我
再見"

run_conversation "自我認同與迷惘" \
"我是誰？
我不知道我想要什麼
我想找到人生目標
我覺得自己很迷茫
謝謝你聽我說
再見"

# =============================================================================
echo -e "${YELLOW}▶ 第三節：邊界條件測試${RESET}"
echo ""

run_test_no_crash  "空白輸入不崩潰"        "   "
run_test           "句尾有句號"            "我需要幫助。"    "需要|幫助|確定|會|得到"
run_test           "句尾有驚嘆號"          "我覺得好開心！"  "覺得|感受|時候|讓你|告訴"
run_test_exit      "再見 — 離開詞"         "再見"            "再見|掰掰|希望|保重|隨時"
run_test_exit      "拜拜 — 離開詞"         "拜拜"            "再見|掰掰|希望|保重|隨時"
run_test_exit      "quit — 英文離開詞"     "quit"            "再見|掰掰|希望|保重|隨時"

# =============================================================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  結果：${GREEN}$PASS 通過${RESET}  /  ${RED}$FAIL 失敗${RESET}  /  共 $TOTAL 項"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
