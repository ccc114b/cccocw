## 階段 1 

現在我們要把 agent0.py 分成幾個模組， main.py, agents.py ，然後 tests/test_reviewer.py 修改後要能通過測試


## 階段 2

現在我們要把 agent0.py 分成幾個模組， main.py, agents.py ，其中 agents.py 中有 Agent Class

這些 Agent 可以分為 Planner, Executor, Evaluator, Guard，每個 agent 都可以透過 read 取得 message, 然後透過 write 對外輸出 message ，Guard 控管 Executor/Evaluator 所要求的 shell 指令是否能執行。

1. Planner 會負責和使用者進行對話，

