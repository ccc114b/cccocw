
* https://github.com/deusyu/harness-engineering
* [Harness Engineering：如何构建高效的AI编码智能体](https://zhuanlan.zhihu.com/p/2019061294423126127)
    * https://github.com/opendev-to/opendev

* [当模型够强，Agent 为什么还是频繁翻车？一文讲透 2026 最火 AI 工程概念：Harness Engineering](https://www.youtube.com/watch?v=Xq-s_hAjADw)
    * planner => generator => evaluator



* https://www.threads.com/@ryota.vl/post/DWxpTpREfgf?hl=en
    * Agent = Model + Harness

ryota.vl => 測試工程師

這週 Anthropic 和 OpenAI 幾乎同一週發表了各自關於 Harness Engineering 的文章，整個 AI 社區炸了。有人說這是 AI 工程的第三次範式轉移，有人說這不過是給舊概念換了個新名字。
同一週，Martin Fowler 的網站也發了一篇文章，換了一個更樸素的說法在講同一件事：怎麼把資深工程師腦中的判斷力編碼成 AI 可執行的指令。
兩篇放在一起讀，對測試工程師的啟示很直接：不管你叫它 Harness Engineering 還是 Encoding Team Standards，核心都是同一件事——設計 Agent 的運行環境。而「設計驗證方式」是其中最關鍵的一環。


指令的四個組成元素：Role（設定視角）、Context Requirements（需要什麼資訊）、Categorized Standards（分成 must follow / should follow / nice to have）、Output Format（確保不同人跑出來的結果可比較）。這四個元素適用於 generation、refactoring、security check、code review 等所有 AI 互動場景。