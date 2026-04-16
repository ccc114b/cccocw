UserAgent 一開始是 Plan mode ，打 /exec 後進入 Exec Mode ，此時會將訊息傳遞給 Executor ，等到打 /eval 後進入 Eval Mode，此時會呼叫 Evaluator ， 打 /plan 又回到 plan mode 繼續規劃下一輪，此時會呼叫 Planner

Planner 也要能執行 Shell ，取得磁碟中的訊息，只是其系統提示不同， Planner 通常不負責寫程式。

