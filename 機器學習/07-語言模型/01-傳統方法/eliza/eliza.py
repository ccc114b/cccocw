import re
import random

# 1. 視角轉換字典 (Reflections)
# 作用：將使用者的第一人稱轉換為機器人的第二人稱，反之亦然。
reflections = {
    "i": "you",
    "i am": "you are",
    "i was": "you were",
    "i'd": "you would",
    "i've": "you have",
    "i'll": "you will",
    "my": "your",
    "are": "am",
    "you've": "I have",
    "you'll": "I will",
    "your": "my",
    "yours": "mine",
    "you": "I",
    "me": "you"
}

# 2. 規則與回應模板 (Psychobabble)
# 格式：[正規表達式模式, [回應清單]]
# {0} 會被替換成使用者輸入中被 () 捕捉到並經過視角轉換的文字。
psychobabble = [
    [r'I need (.*)',
     ["Why do you need {0}?",
      "Would it really help you to get {0}?",
      "Are you sure you need {0}?"]],
    [r'Why don\'t you (.*)',
     ["Do you really think I don't {0}?",
      "Perhaps eventually I will {0}.",
      "Do you really want me to {0}?"]],
    [r'Why can\'t I (.*)',
     ["Do you think you should be able to {0}?",
      "If you could {0}, what would you do?",
      "I don't know -- why can't you {0}?"]],
    [r'I am (.*)',
     ["Did you come to me because you are {0}?",
      "How long have you been {0}?",
      "How do you feel about being {0}?"]],
    [r'I\'m (.*)',
     ["How does being {0} make you feel?",
      "Do you enjoy being {0}?",
      "Why do you tell me you're {0}?"]],
    [r'I feel (.*)',
     ["Good, tell me more about these feelings.",
      "Do you often feel {0}?",
      "When do you usually feel {0}?"]],
    [r'(.*) mother(.*)',
     ["Tell me more about your mother.",
      "What was your relationship with your mother like?",
      "How do you feel about your mother?",
      "How does this relate to your feelings today?"]],
    [r'(.*) computer(.*)',
     ["Are you really talking about me?",
      "Does it seem strange to talk to a computer?",
      "How do computers make you feel?"]],
    [r'(.*)\?',
     ["Why do you ask that?",
      "Please consider whether you can answer your own question.",
      "Perhaps the answer lies within yourself?",
      "Why don't you tell me?"]],
    [r'quit',
     ["Thank you for talking with me.",
      "Good-bye.",
      "Thank you, that will be $150. Have a good day!"]],
    # 預設回應（當所有規則都沒對上時）
    [r'(.*)',
     ["Please tell me more.",
      "Let's change focus a bit... Tell me about your family.",
      "Can you elaborate on that?",
      "Why do you say that?",
      "I see.",
      "Very interesting.",
      "How does that make you feel?"]]
]

def reflect(fragment):
    """處理代詞的轉換（例如：my 變成 your）"""
    tokens = fragment.lower().split()
    for i, token in enumerate(tokens):
        if token in reflections:
            tokens[i] = reflections[token]
    return ' '.join(tokens)

def analyze(statement):
    """分析使用者的輸入並回傳 ELIZA 的回應"""
    for pattern, responses in psychobabble:
        # 使用正規表達式進行不區分大小寫的比對
        match = re.match(pattern, statement.rstrip(".!"), re.IGNORECASE)
        if match:
            response = random.choice(responses)
            # 如果回應模板中有 {0}，則將擷取到的文字進行代詞轉換後填入
            if '{0}' in response:
                return response.format(reflect(match.group(1)))
            else:
                return response
    return "I don't understand."

def main():
    print("-" * 50)
    print("Welcome to ELIZA.")
    print("Type 'quit' to exit.")
    print("-" * 50)
    print("Hello. How are you feeling today?")
    
    while True:
        try:
            statement = input("\n> ")
            response = analyze(statement)
            print(response)
            
            if statement.lower().strip() == "quit":
                break
        except (KeyboardInterrupt, EOFError):
            print("\nGood-bye.")
            break

if __name__ == "__main__":
    main()