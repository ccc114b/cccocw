Planner 應該有能力啟動 Executor 和 Evaluator ，但是當 Planner 想要啟動這些 session 中的 Agent 時，有兩種模式

1. 自動模式： Planner 可以直接啟動 Agnet ，不需要使用者修改確認
2. 控管模式： Planner 需要使用者確認（並可能修改指令）後，才啟動 Agent (也可能否決）

所以

1. 請讓 Planner 知道並有能力啟動 Agent (Executor, Evaluator)
2. 請設定『自動或控管』模式，在控管模式下， Planner 會下指令給 CLI ，讓使用者修改確認後再送出

