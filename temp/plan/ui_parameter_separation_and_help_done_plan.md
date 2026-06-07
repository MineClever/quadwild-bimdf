# ui_parameter_separation_and_help_done_plan

Task ID: `ui_parameter_separation_and_help`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成参数盘点与 UI 拆分
- [x] 为字段补充提示
- [x] 完成验证与收尾

## 完成日志
- 2026-06-08：确认 `quadwild/functions.cpp` 与 `components/quad_from_patches/main.cpp` 的实际读取参数集合并不完全相同，现有 UI 需要按真实使用范围重新分组。
- 2026-06-08：按真实读取范围重构 `scripts/quadwild_ui.py` 的字段分组，区分“预处理与场 / 共享量化目标 / 求解器 / 约束策略 / 仅 QuadWild 后处理 / 外部求解器”。
- 2026-06-08：为所有配置字段以及主要执行字段补充 tooltip，说明作用、适用阶段和基本用法。

## 实现说明
- `quadwild` 页只保留 `quadwild.exe` 实际读取的参数，并显式保留其独有的 `do_remesh`、`sharp_feature_thr`、`chartSmoothingIterations`、`quadrangulation*`、`feasibilityFix`。
- `quad_from_patches` 页只保留 `quad_from_patches.exe` 实际读取的参数，不再混入 `quadwild` 专属字段。
- 配置表单从单一长表切换为按 section 分组的多个 `QGroupBox`，并在每个字段 spec 上新增 `help` 文本供 UI tooltip 使用。

## 验证说明
- `python -m py_compile scripts\\quadwild_ui.py` 通过。
- 关键代码位置已确认：字段分组和帮助文本位于 `scripts/quadwild_ui.py` 的 `QUADWILD_FORM_FIELDS`、`QFP_FORM_FIELDS` 与 `apply_field_help()`。

## 收尾状态
已完成。
