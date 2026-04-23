#!/usr/bin/env bash
# =============================================================================
# test_eliza.sh  —  Multi-round dialogue test for eliza.py (English version)
# Usage: bash test_eliza.sh
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ELIZA="$SCRIPT_DIR/eliza.py"
PASS=0
FAIL=0
TOTAL=0

# ANSI colours
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

# --------------------------------------------------------------------------
# run_test <test_name> <input_text> <expected_pattern (grep -E)>
#   Sends one line to eliza.py and checks the response matches the pattern.
# --------------------------------------------------------------------------
run_test() {
    local name="$1"
    local input="$2"
    local pattern="$3"

    TOTAL=$((TOTAL + 1))

    # Feed the input followed by "quit" so the program exits cleanly.
    response=$(printf '%s\nquit\n' "$input" | python3 "$ELIZA" 2>/dev/null \
               | grep -v -E "^(-{2,}|Welcome|Type 'quit'|Hello\.|^$|Good-bye|Thank you)" \
               | head -1)

    if echo "$response" | grep -qE "$pattern"; then
        echo -e "  ${GREEN}PASS${RESET}  [$name]"
        echo -e "        Input   : $input"
        echo -e "        Response: $response"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${RESET}  [$name]"
        echo -e "        Input   : $input"
        echo -e "        Response: $response"
        echo -e "        Expected pattern: $pattern"
        FAIL=$((FAIL + 1))
    fi
    echo ""
}

# --------------------------------------------------------------------------
# run_conversation <test_name> <newline-separated input block>
#   Runs a full multi-turn conversation and prints the whole transcript.
# --------------------------------------------------------------------------
run_conversation() {
    local name="$1"
    local inputs="$2"

    echo -e "${CYAN}━━━ Conversation: $name ━━━${RESET}"
    printf '%s\n' "$inputs" | python3 "$ELIZA" 2>/dev/null \
        | grep -v -E "^-{2,}$"
    echo ""
}

# =============================================================================
echo -e "${YELLOW}"
echo "╔══════════════════════════════════════════════╗"
echo "║        ELIZA (English) — Test Suite          ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${RESET}"

# --- Pre-flight check --------------------------------------------------------
if [[ ! -f "$ELIZA" ]]; then
    echo -e "${RED}ERROR: eliza.py not found at $ELIZA${RESET}"
    exit 1
fi

# =============================================================================
echo -e "${YELLOW}▶ Section 1: Pattern-matching unit tests${RESET}"
echo ""

run_test "I need …"        "I need some help"         "need|help"
run_test "I am …"          "I am very sad"            "feel|long|come"
run_test "I'm …"           "I'm feeling lost"         "feel|enjoy|tell"
run_test "I feel …"        "I feel anxious"           "feel|often|usually"
run_test "Why can't I …"   "Why can't I be happy"     "should|could|don't know"
run_test "Why don't you …" "Why don't you help me"    "really|eventually|want"
run_test "mother keyword"  "My mother never listens"  "mother"
run_test "computer keyword" "You are just a computer" "talking|strange|feel"
run_test "Question mark"   "Are you real?"            "ask|consider|answer|lies|tell"
run_test "Default fallback" "blah blah blah"          "tell me more|elaborate|family|feel|say|see|interesting"

# =============================================================================
echo -e "${YELLOW}▶ Section 2: Full multi-turn conversations${RESET}"
echo ""

# Conversation A — Feeling overwhelmed
run_conversation "Feeling overwhelmed" \
"I feel overwhelmed
I need some rest
Why can't I relax
I am exhausted
quit"

# Conversation B — Family tension
run_conversation "Family tension" \
"My mother always criticises me
I am tired of arguing
I feel like nobody understands me
Why don't you listen to me
quit"

# Conversation C — Identity & questions
run_conversation "Identity & curiosity" \
"Are you a real therapist?
I'm not sure who I am
I need direction in life
Why can't I make decisions
quit"

# =============================================================================
echo -e "${YELLOW}▶ Section 3: Edge cases${RESET}"
echo ""

run_test "Empty-ish input (spaces)"  "   "            "tell|elaborate|feel|see|interesting|say"
run_test "ALL CAPS input"            "I AM ANGRY"     "feel|long|come"
run_test "Trailing punctuation"      "I need help!"   "need|help"
run_test "quit exits gracefully"     "quit"           "Thank you|Good-bye|\\\$150"

# =============================================================================
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Results: ${GREEN}$PASS passed${RESET}  /  ${RED}$FAIL failed${RESET}  /  $TOTAL total"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

[[ $FAIL -eq 0 ]] && exit 0 || exit 1
