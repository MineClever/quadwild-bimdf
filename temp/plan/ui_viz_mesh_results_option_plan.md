# ui_viz_mesh_results_option_plan

Task ID: `ui_viz_mesh_results_option`
Task Name: `UI 添加 viz_mesh_results 可选可视化导出`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
在 UI 中新增一个可选项，让用户可以选择使用 `viz_mesh_results.exe` 对流程中的中间结果进行可视化导出，便于检查 `.rosy`、sharp、patch 等关联结果。

## 范围
纳入范围：
- 在 UI 中增加开关与 `viz_mesh_results.exe` 路径配置。
- 在合适的流程节点调用 `viz_mesh_results.exe`。
- 更新预览、设置保存和验证逻辑。

不纳入范围：
- 修改 `viz_mesh_results.exe` 本体行为。
- 改动无关 UI 页面结构。

## 依赖
- `pyside2_binary_ui`
- `xfield_tracer_localization_and_fix`
