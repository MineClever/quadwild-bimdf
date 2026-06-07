# xfield_tracer_localization_and_fix_plan

Task ID: `xfield_tracer_localization_and_fix`
Task Name: `xfield_tracer 本地化与 tracing 修复`
Overall Status: In Progress
Current Phase: `M1 - 设计`

## 目标
将 `libs/xfield_tracer` 从 git submodule 改为仓库内本地维护代码，并直接在本地代码上修复 tracing 阶段的 `invalid map<K, T> key` 异常中断问题。

## 范围
纳入范围：
- 移除 `libs/xfield_tracer` 的 submodule 关系。
- 将其内容转为主仓库普通目录追踪。
- 在本地 `xfield_tracer` 代码中恢复 tracing 异常隔离修复。
- 完成相关构建验证。

不纳入范围：
- 修改其他 `libs/` 下无关 submodule。

## 依赖
- `tracing_failure_reassessment`
- `submodule_edit_constraint`
