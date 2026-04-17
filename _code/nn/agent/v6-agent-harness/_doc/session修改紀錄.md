# session

加入 session 的觀念 (每個 session 有自己的 agent group)

1. 隨時用 /session.new <name> 就可以創建一個新的 session 創建 新的 planner (session name 和 planner name 是一樣的), 系統自動給定 id
    * 當使用 /exec <job_description> 時，會創建新的 Executor 去執行某任務
    * 當使用 /eval <eval_description> 時，會創建新的 Evaluator 去評量目前 Executor 的任務
    * 一個 session 只能有一個 planner ，但是可以有很多 executor 和 evaluator
    * 可以用 /agents 列出目前 session 的所有 agent (1 planner, n executor, m evaluator, m<=n, 沒有下 /eval 指令的 executor, 沒有對應到 evaluator)
2. session 的管理
    * 可以用 /session.list 列出所有的 session (id, name)
    * 可以用 /session <id> 或 /session <name> 去切換 session。


