# ui_preview_init_and_pyside_fallback_fix_plan

Task ID: `ui_preview_init_and_pyside_fallback_fix`
Task Name: `UI 预览初始化与 PySide 回退修复`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
修复 `scripts/quadwild_ui.py` 在外部求解器预览区初始化阶段的属性缺失异常，并让 Qt 绑定加载在 `PySide2` 失败时更安静地回退到 `PySide6`。

## 范围
纳入范围：
- 修复 `flow_solver_json_preview` / `satsuma_solver_json_preview` 相关初始化问题。
- 为 JSON 预览刷新流程增加安全保护，避免窗口构建早期触发属性错误。
- 改善 `PySide2` 导入失败时的回退体验，避免把失败栈直接暴露给终端用户。

不纳入范围：
- 修改 `quadwild.exe` 或 `quad_from_patches.exe` 的 C++ 配置解析逻辑。
- 修改任何 `libs/` 下的 submodule 文件。

## 依赖
- `ui_parameter_separation_and_help`
- `submodule_edit_constraint`
