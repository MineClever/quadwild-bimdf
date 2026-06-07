# ui_viz_mesh_results_option_done_plan

Task ID: `ui_viz_mesh_results_option`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成功能实现
- [x] 完成验证
- [x] 完成收尾

## 完成日志
- 2026-06-08：开始为 UI 添加 `viz_mesh_results.exe` 可选可视化导出功能。
- 2026-06-08：在总览页新增 `viz_mesh_results.exe` 路径与启用开关，并将该选项接入设置保存、恢复默认、参数校验和命令预览。
- 2026-06-08：在 `ProcessWorker.prepare_workspace_and_commands()` 中新增可选 `viz_mesh_results` 调用逻辑；当 `quadwild` 运行到 tracing 阶段后，自动对 `*_rem.obj` 调用可视化导出。
- 2026-06-08：完成脚本编译与轻量导入验证，确认新功能未破坏 UI 启动。

## 实现说明
- 新增的可视化导出只在 `full_pipeline` 或 `quadwild_only` 且停止步骤为 `2/3` 时执行；若停在 step `1`，UI 会在预览与运行日志中说明已跳过。
- 调用输入使用 `*_rem.obj`，因为 `viz_mesh_results.exe` 会按同名规则查找 `.rosy`、`.sharp`、`_p0.obj`、`_p0.patch` 等 tracing 中间文件。
- `viz_mesh_results.exe` 产出的检查文件是 `.ply`，包括 field / sharp / patch 的可视化网格；本次未修改该工具本体格式。

## 验证说明
- `python -m py_compile scripts\\quadwild_ui.py` 通过。
- `python -c "import sys; sys.path.insert(0, '.'); import scripts.quadwild_ui as ui; print(ui.preferred_repo_binary('viz_mesh_results.exe') or 'MISSING')"` 通过，当前解析到 `release\\windows\\viz_mesh_results.exe`。

## 收尾状态
已完成。
