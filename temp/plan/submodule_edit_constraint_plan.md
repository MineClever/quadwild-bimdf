# submodule_edit_constraint_plan

Task ID: `submodule_edit_constraint`
Task Name: `禁止修改 submodule 约束落地`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
撤回当前对 submodule 工作树的本地修改，并把“默认不修改 submodule”加入仓库级 agent 约束。

## 范围
纳入范围：
- 撤回 `libs/xfield_tracer` 中本轮引入的本地修改。
- 更新 `AGENTS.md` 约束说明。
- 同步计划系统记录。

不纳入范围：
- 修改主仓库非 submodule 文件中的功能逻辑。
- 更新 submodule 指针版本。

## 依赖
- `tracing_invalid_map_key_fix`
