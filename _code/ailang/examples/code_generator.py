"""
AIL 程式碼生成器
讓 Agent 不只返回建議，還能實際建立程式碼檔案
"""

import asyncio
import os
import re
from pathlib import Path
from ailang import Agent, init_openrouter, init_ollama


class CodeGenerator:
    """
    程式碼生成器
    
    功能：
    - 理解需求
    - 生成程式碼
    - 保存到檔案
    """
    
    def __init__(self, output_dir: str = "./generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.coder = Agent("coder")
    
    async def generate(self, task: str, filename: str = None):
        """生成程式碼"""
        
        print(f"\n📝 理解需求: {task}")
        
        # 讓 AI 生成完整程式碼
        prompt = f"""
        請生成一個完整的、可運行的程式碼檔案。
        
        需求: {task}
        
        重要：請把所有程式碼（HTML + CSS + JavaScript）放在一個單一檔案中。
        這樣用戶可以直接打開使用。
        
        請只輸出程式碼，不要有其他說明。
        """
        
        result = await self.coder(task=prompt)
        
        if not result:
            print("❌ Agent 返回空結果")
            return {}
        
        print(f"📄 收到回應 ({len(result)} 字元)")
        
        # 解析程式碼
        files = self._parse_code(result)
        
        # 保存檔案
        saved = []
        for name, code in files.items():
            filepath = self.output_dir / name
            filepath.write_text(code, encoding='utf-8')
            saved.append(str(filepath))
            print(f"✅ 已保存: {filepath}")
        
        return saved
    
    def _parse_code(self, result: str):
        """解析程式碼"""
        files = {}
        
        # 移除思考過程
        result = re.sub(r'Thinking\.\.\.[\s\S]*?done thinking\.', '', result)
        
        # 移除 markdown code block 標記
        result = re.sub(r'^```\w*\n', '', result, flags=re.MULTILINE)
        result = re.sub(r'\n```$', '', result)
        
        # 找 HTML 代碼區塊
        html_pattern = r'(<!DOCTYPE html>[\s\S]*?</html>)'
        html_matches = re.findall(html_pattern, result, re.IGNORECASE)
        
        if html_matches:
            # 取第一個完整的 HTML
            files["app.html"] = html_matches[0].strip()
        else:
            # 如果沒找到完整 HTML，嘗試找 <html> 開頭到 </html> 結尾
            html_match = re.search(r'(<html[\s\S]*?</html>)', result, re.IGNORECASE)
            if html_match:
                files["app.html"] = html_match.group(1).strip()
            else:
                files["app.html"] = result.strip()
        
        return files


class WebAppGenerator:
    """
    網頁應用生成器
    生成完整的 HTML/CSS/JS 應用
    """
    
    def __init__(self, output_dir: str = "./generated"):
        self.output_dir = Path(output_dir)
        self.generator = CodeGenerator(output_dir)
    
    async def generate_weather_app(self):
        """生成天氣查詢應用"""
        
        task = """
        建立一個天氣查詢應用程式：
        - 使用 HTML + CSS + JavaScript
        - 可輸入城市名稱查詢天氣
        - 顯示未來7天天氣
        - 簡潔美觀的 UI 設計
        - 使用 Open-Meteo API (免費，無需 API Key)
        """
        
        files = await self.generator.generate(task, "weather.html")
        return files


async def demo():
    """演示"""
    # 優先使用本地 Ollama
    try:
        init_ollama(model="minimax-m2.5:cloud")
        print("✓ Ollama 初始化成功 (MiniMax M2.5 雲端)")
    except Exception as e:
        print(f"⚠️ Ollama 連接失敗: {e}")
        import os
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if api_key:
            init_openrouter(api_key, model="openrouter/free")
            print("✓ OpenRouter 初始化成功")
    
    print("🌤️  AIL 程式碼生成器")
    print("="*50)
    
    # 生成天氣應用
    generator = WebAppGenerator("./generated")
    files = await generator.generate_weather_app()
    
    print(f"\n📁 已生成 {len(files)} 個檔案")
    for f in files:
        print(f"   - {f}")


if __name__ == "__main__":
    asyncio.run(demo())
