# smooth_openmp_design_and_dependency_policy_plan

Task ID: `smooth_openmp_design_and_dependency_policy`
Task Name: `smooth OpenMP 设计与依赖策略约束更新`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
为 `components/quad_from_patches/smooth_mesh.h` 形成一份可落地的 OpenMP 改造设计文档，同时把“允许从 GitHub 以 submodule 形式引入依赖、优先避免重复造轮子”的约束写入仓库规则。

## 范围
纳入范围：
- 输出 `smooth_mesh.h` 的 OpenMP 改造设计图。
- 更新 `AGENTS.md` 中的依赖策略约束。

不纳入范围：
- 实施 OpenMP 代码改造。
- 实际新增任何 GitHub submodule 依赖。

## 依赖
- `runtime_log_parallel_hotspot_assessment`
- `submodule_edit_constraint`
