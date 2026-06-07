# ui_preview_init_and_pyside_fallback_fix_done_plan

Task ID: `ui_preview_init_and_pyside_fallback_fix`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成 UI 初始化缺陷修复
- [x] 完成验证与收尾

## 完成日志
- 2026-06-08：收到用户反馈，`PySide2` 导入失败时会打印内部 traceback，同时 `QuadWildWindow` 在刷新 JSON 预览时缺少 `flow_solver_json_preview` 属性导致窗口初始化失败。
- 2026-06-08：开始检查 `scripts/quadwild_ui.py` 的 UI 构建顺序、外部求解器预览控件绑定，以及配置变更回调的触发时机。
- 2026-06-08：为 `QuadWildWindow` 增加四个预览控件属性的显式初始化，并在 `refresh_json_previews()` 中加入空值保护，避免窗口构建早期刷新时触发 `AttributeError`。
- 2026-06-08：调整 Qt 绑定导入逻辑，对 `PySide2` 的失败尝试临时静默 `stderr`，在失败后再平滑回退到 `PySide6`。

## 实现说明
- `build_config_group()` 现在能为 `flow_solver` 与 `satsuma_solver` 正确绑定独立预览控件，避免外部求解器 JSON 预览仍然走主配置控件路径。
- `QuadWildWindow.__init__()` 中预先声明 `quadwild_json_preview`、`qfp_json_preview`、`flow_solver_json_preview`、`satsuma_solver_json_preview`，确保任意早期回调都不会命中未定义属性。
- `refresh_json_previews()` 在控件尚未创建时直接跳过对应刷新项，从而把初始化顺序问题降级为安全空操作。
- Qt 绑定导入逻辑优先尝试 `PySide2`，若失败则不再向终端泄露内部导入栈，而是继续回退到 `PySide6`。

## 验证说明
- `python -m py_compile scripts\\quadwild_ui.py` 通过。
- `python -c "import sys; sys.path.insert(0, '.'); import scripts.quadwild_ui as ui; print(ui.QT_BINDING)"` 通过，当前环境结果为 `PySide2`。

## 收尾状态
已完成。
