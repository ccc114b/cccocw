Thinking: 测试通过了！现在我可以告诉用户如何使用这个参数。
完成！现在可以这样使用：
# 默认 headless 模式（不显示浏览器）
./test.sh
# 显示浏览器窗口
./test.sh --no-headless
# 只运行 e2e 测试
python3 test/e2e/test_browser.py --no-headless
python3 test/e2e/test_browser.py --headless
参数说明：
- --headless 或不指定：后台运行（默认）
- --no-headless：显示浏览器窗口
