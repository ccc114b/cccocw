"""
ACL - AI Communication Language
AI 通讯语言规格
"""

ACL_SPEC = """
# ACL (AI Communication Language): 結構化溝通格式

## ACL 指令集

### 1. <write> - 寫入檔案
格式: <write file="檔名">內容</write>

範例:
<write file="main.py">
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def hello():
    return {"message": "Hello World"}
</write>

### 2. <shell> - 執行命令
格式: <shell>命令</shell>

範例:
<shell>pip install fastapi</shell>

### 3. <read> - 讀取檔案
格式: <read file="檔名"></read>

範例:
<read file="main.py"></read>

### 4. <ask> - 詢問問題
格式: <ask>問題1？\n問題2？\n問題3？</ask>

範例:
<ask>
1. 請問需要支援用戶登入功能嗎？
2. 請問需要支援文章分類嗎？
3. 請問需要支援評論功能嗎？
</ask>

## 重要規則
1. 執行者沒有檔案系統權限
2. 所有檔案操作必須透過 ACL 標籤
3. 用繁體中文回覆
"""

# ACL 指令说明
ACL_WRITE = '<write file="檔名">內容</write>'
ACL_SHELL = '<shell>命令</shell>'
ACL_READ = '<read file="檔名"></read>'
ACL_ASK = '<ask>問題</ask>'
