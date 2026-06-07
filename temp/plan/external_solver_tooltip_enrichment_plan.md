# external_solver_tooltip_enrichment_plan

Task ID: `external_solver_tooltip_enrichment`
Task Name: `外部求解器参数提示补强`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
基于仓库内实际配置与源码语义，补充 `scripts/quadwild_ui.py` 中外部求解器参数的 tooltip，使其说明每个参数的真实作用、常见影响和推荐调参方式。

## 范围
纳入范围：
- 盘点 `flow_solver` 与 `satsuma_solver` UI 字段。
- 结合默认 JSON 配置和本地源码使用方式补充字段说明。
- 更新 UI 中对应 tooltip 文案。

不纳入范围：
- 修改外部求解器本体算法逻辑。
- 修改任何 `libs/` 下的 submodule 文件。

## 依赖
- `ui_parameter_separation_and_help`
- `ui_preview_init_and_pyside_fallback_fix`
