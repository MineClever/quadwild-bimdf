# tracing_failure_reassessment_plan

Task ID: `tracing_failure_reassessment`
Task Name: `Tracing 失败回归复核`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
复核当前 `quadwild` tracing 阶段再次出现的 `invalid map<K, T> key` 失败，确认是否属于已知回归，并区分可在主仓库处理的部分与需要 submodule 修改的部分。

## 范围
纳入范围：
- 复核当前崩溃日志与现有代码状态。
- 识别失败是否来自此前已撤回的 submodule 修复。
- 给出可行的下一步方案与约束。

不纳入范围：
- 未经确认直接修改 `libs/` 下 submodule。

## 依赖
- `submodule_edit_constraint`
- `json_bool_parser_fix`
