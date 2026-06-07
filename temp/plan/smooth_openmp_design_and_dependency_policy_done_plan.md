# smooth_openmp_design_and_dependency_policy_done_plan

Task ID: `smooth_openmp_design_and_dependency_policy`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成 OpenMP 设计文档
- [x] 完成仓库约束更新
- [x] 完成收尾

## 完成日志
- 2026-06-08：开始为 `smooth_mesh.h` 输出 OpenMP 改造设计，并同步更新依赖引入策略约束。
- 2026-06-08：新增 `docs/openmp_smoothing_design.md`，按 `SmoothSharpFeatures()`、`SmoothInternal()`、`BackProjectStepPositions()` 的数据流边界给出 OpenMP 改造顺序与风险说明。
- 2026-06-08：更新 `AGENTS.md`，明确允许在确有必要时优先从 GitHub 以 submodule 形式引入成熟依赖，而不是重复造轮子。

## 实现说明
- OpenMP 设计文档优先强调 two-phase gather/apply 改造，而不是直接对共享写入循环套 `parallel for`。
- 设计文档把 `smooth_mesh.h` 里的并行化目标分成三层：
  - 立即可试的安全顶点循环
  - 需要轻度重构的顶点写回步骤
  - 需要线程私有缓冲与归并的 `BackProjectStepPositions()`
- 仓库约束补充为：若需要第三方能力，优先复用成熟上游库；用户明确允许以 Git submodule 形式从 GitHub 引入依赖，但前提是确认确有必要且优于仓库内重复实现。

## 验证说明
- 已核对文档与约束文件落盘：
  - `docs/openmp_smoothing_design.md`
  - `AGENTS.md`
  - `temp/plan/plan.md`

## 收尾状态
已完成。
