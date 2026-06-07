# external_solver_tooltip_enrichment_done_plan

Task ID: `external_solver_tooltip_enrichment`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成参数含义盘点
- [x] 完成 tooltip 更新
- [x] 完成验证与收尾

## 完成日志
- 2026-06-08：开始针对外部求解器 UI 字段补强 tooltip，重点补充“实际作用”和“推荐设置方式”。
- 2026-06-08：结合 `config/main_config/flow_virtual_simple.json`、`config/satsuma/lemon.json` 与 `libs/quadretopology/quadretopology/qr_flow.cpp`、`libs/satsuma/src/libsatsuma/Extra/Highlevel.cc`、`libs/satsuma/src/libsatsuma/Solvers/BiMDFDoubleCover.cc` 盘点各字段的真实行为。
- 2026-06-08：将 Flow Solver 与 Satsuma Solver 所有 UI 字段的 tooltip 扩充为“作用 + 调大/调小影响 + 推荐默认/建议区间”的说明。

## 实现说明
- `paired_half_target`、`paired_resolve_new_targets` 以及 `paired_initial` / `paired_resolve` 各权重和目标形式，现在明确说明它们如何参与 paired 边目标拆分与二轮修正。
- `double_cover.max_deviation`、`evening_mode`、`method`、`refine_with_matching`、`refinement_maxdev_*`、`deviation_limit` 等字段，现在明确说明它们属于 double-cover 近似还是 refinement 阶段，以及推荐默认值和何时提高/降低。
- 本次仅更新 `scripts/quadwild_ui.py` 中外部求解器字段说明，不修改任何 submodule 源码。

## 验证说明
- `python -m py_compile scripts\\quadwild_ui.py` 通过。

## 收尾状态
已完成。
