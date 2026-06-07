# submodule_edit_constraint_done_plan

Task ID: `submodule_edit_constraint`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 撤回 submodule 本地修改
- [x] 写入禁止修改 submodule 约束
- [x] 完成收尾记录

## 完成日志
- 2026-06-08：用户明确要求避免修改 `tracer_interface.h` 等来自 submodule 的文件，并将该规则写入仓库约束。
- 2026-06-08：已撤回 `libs/xfield_tracer/tracing/tracer_interface.h` 的本地修改，submodule 工作树恢复干净状态。
- 2026-06-08：已在 `AGENTS.md` 中加入“`libs/` 下 submodule 默认只读，除非用户显式要求，否则不得修改”的约束。

## 实现说明
- 使用 submodule 自身的 git 工作树回滚 `tracing/tracer_interface.h`。
- 在 `AGENTS.md` 的 `Agent Workflow Constraints` 段落补充 submodule 只读规则。

## 验证说明
- `git -C libs/xfield_tracer status --short` 返回空，确认 submodule 内已无本地修改。
- 根仓库 `git status --short` 不再显示 `m libs/xfield_tracer`，确认未残留 submodule 工作树变更。

## 收尾状态
已完成。
