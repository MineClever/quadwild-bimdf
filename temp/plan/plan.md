# 主计划索引

## 用途
该目录是仓库级工程任务计划系统。`plan.md` 只维护总索引；具体计划与执行记录必须放在任务文件中。

## 命名规则
任务 ID 仍使用稳定的小写 ASCII 下划线命名，例如 `planning_system_bootstrap`。每个任务必须同时具备：

- `<task>_plan.md`
- `<task>_done_plan.md`

除非任务明确要求英文，Plan 文档的标题、状态、里程碑说明、进展记录优先使用中文。

## 里程碑定义
- `M1 - 设计`: 明确范围、假设、影响面。
- `M2 - 实现`: 完成代码或文档变更。
- `M3 - 验证`: 完成构建、测试或其他验证。
- `M4 - 收尾`: 汇总结果并回写总索引。

## 任务表
| Task ID | Task Name | Status | Current Phase | Dependencies | Plan File | Done File |
| --- | --- | --- | --- | --- | --- | --- |
| `planning_system_bootstrap` | 计划系统初始化 | Done | M4 - 收尾 | None | [planning_system_bootstrap_plan.md](./planning_system_bootstrap_plan.md) | [planning_system_bootstrap_done_plan.md](./planning_system_bootstrap_done_plan.md) |
| `windows_build_bat_setup` | Windows 一键构建脚本 | Done | M4 - 收尾 | `planning_system_bootstrap` | [windows_build_bat_setup_plan.md](./windows_build_bat_setup_plan.md) | [windows_build_bat_setup_done_plan.md](./windows_build_bat_setup_done_plan.md) |
| `pyside2_binary_ui` | PySide2 二进制图形界面 | Done | M4 - 收尾 | `windows_build_bat_setup` | [pyside2_binary_ui_plan.md](./pyside2_binary_ui_plan.md) | [pyside2_binary_ui_done_plan.md](./pyside2_binary_ui_done_plan.md) |
| `square_topology_assessment` | 方格拓扑逼近评估 | Done | M4 - 收尾 | `pyside2_binary_ui` | [square_topology_assessment_plan.md](./square_topology_assessment_plan.md) | [square_topology_assessment_done_plan.md](./square_topology_assessment_done_plan.md) |
| `configurable_pipeline_and_ui_tabs` | 流水线可配置化与 UI Tab 重构 | Done | M4 - 收尾 | `pyside2_binary_ui` | [configurable_pipeline_and_ui_tabs_plan.md](./configurable_pipeline_and_ui_tabs_plan.md) | [configurable_pipeline_and_ui_tabs_done_plan.md](./configurable_pipeline_and_ui_tabs_done_plan.md) |
| `ui_serialized_config_assessment` | UI 序列化配置评估 | Done | M4 - 收尾 | `configurable_pipeline_and_ui_tabs` | [ui_serialized_config_assessment_plan.md](./ui_serialized_config_assessment_plan.md) | [ui_serialized_config_assessment_done_plan.md](./ui_serialized_config_assessment_done_plan.md) |
| `json_config_system_migration` | 全量 JSON 配置系统迁移 | Done | M4 - 收尾 | `configurable_pipeline_and_ui_tabs`, `ui_serialized_config_assessment` | [json_config_system_migration_plan.md](./json_config_system_migration_plan.md) | [json_config_system_migration_done_plan.md](./json_config_system_migration_done_plan.md) |
| `ui_json_form_parameterization` | UI 参数表单化与总览输入同步 | Done | M4 - 收尾 | `json_config_system_migration` | [ui_json_form_parameterization_plan.md](./ui_json_form_parameterization_plan.md) | [ui_json_form_parameterization_done_plan.md](./ui_json_form_parameterization_done_plan.md) |
| `json_bool_parser_fix` | JSON 布尔字段解析与 UI 二进制路径修复 | Done | M4 - 收尾 | `json_config_system_migration`, `ui_json_form_parameterization` | [json_bool_parser_fix_plan.md](./json_bool_parser_fix_plan.md) | [json_bool_parser_fix_done_plan.md](./json_bool_parser_fix_done_plan.md) |
| `tracing_invalid_map_key_fix` | Tracing 阶段 invalid map key 异常隔离修复 | Done | M4 - 收尾 | `json_bool_parser_fix` | [tracing_invalid_map_key_fix_plan.md](./tracing_invalid_map_key_fix_plan.md) | [tracing_invalid_map_key_fix_done_plan.md](./tracing_invalid_map_key_fix_done_plan.md) |
| `qfp_smoothing_progress_log_fix` | quad_from_patches smoothing 日志误导修复 | Done | M4 - 收尾 | `json_bool_parser_fix` | [qfp_smoothing_progress_log_fix_plan.md](./qfp_smoothing_progress_log_fix_plan.md) | [qfp_smoothing_progress_log_fix_done_plan.md](./qfp_smoothing_progress_log_fix_done_plan.md) |
| `submodule_edit_constraint` | 禁止修改 submodule 约束落地 | Done | M4 - 收尾 | `tracing_invalid_map_key_fix` | [submodule_edit_constraint_plan.md](./submodule_edit_constraint_plan.md) | [submodule_edit_constraint_done_plan.md](./submodule_edit_constraint_done_plan.md) |
| `track_build_windows_release_bat` | 将 Build_Windows_Release.bat 纳入 Git 跟踪 | Done | M4 - 收尾 | `windows_build_bat_setup` | [track_build_windows_release_bat_plan.md](./track_build_windows_release_bat_plan.md) | [track_build_windows_release_bat_done_plan.md](./track_build_windows_release_bat_done_plan.md) |
| `ui_parameter_separation_and_help` | UI 参数拆分与字段提示完善 | Done | M4 - 收尾 | `ui_json_form_parameterization`, `json_bool_parser_fix` | [ui_parameter_separation_and_help_plan.md](./ui_parameter_separation_and_help_plan.md) | [ui_parameter_separation_and_help_done_plan.md](./ui_parameter_separation_and_help_done_plan.md) |
| `ui_preview_init_and_pyside_fallback_fix` | UI 预览初始化与 PySide 回退修复 | Done | M4 - 收尾 | `ui_parameter_separation_and_help`, `submodule_edit_constraint` | [ui_preview_init_and_pyside_fallback_fix_plan.md](./ui_preview_init_and_pyside_fallback_fix_plan.md) | [ui_preview_init_and_pyside_fallback_fix_done_plan.md](./ui_preview_init_and_pyside_fallback_fix_done_plan.md) |
| `external_solver_tooltip_enrichment` | 外部求解器参数提示补强 | Done | M4 - 收尾 | `ui_parameter_separation_and_help`, `ui_preview_init_and_pyside_fallback_fix` | [external_solver_tooltip_enrichment_plan.md](./external_solver_tooltip_enrichment_plan.md) | [external_solver_tooltip_enrichment_done_plan.md](./external_solver_tooltip_enrichment_done_plan.md) |
| `pipeline_multithreading_assessment` | 整程序多线程提速可行性评估 | Done | M4 - 收尾 | `configurable_pipeline_and_ui_tabs`, `submodule_edit_constraint` | [pipeline_multithreading_assessment_plan.md](./pipeline_multithreading_assessment_plan.md) | [pipeline_multithreading_assessment_done_plan.md](./pipeline_multithreading_assessment_done_plan.md) |
| `single_model_hotspot_parallel_assessment` | 单模型热点并行与 OpenMP 可行性评估 | Done | M4 - 收尾 | `pipeline_multithreading_assessment`, `submodule_edit_constraint` | [single_model_hotspot_parallel_assessment_plan.md](./single_model_hotspot_parallel_assessment_plan.md) | [single_model_hotspot_parallel_assessment_done_plan.md](./single_model_hotspot_parallel_assessment_done_plan.md) |
| `runtime_log_parallel_hotspot_assessment` | 基于实际运行日志的并行热点评估 | In Progress | M1 - 设计 | `single_model_hotspot_parallel_assessment`, `submodule_edit_constraint` | [runtime_log_parallel_hotspot_assessment_plan.md](./runtime_log_parallel_hotspot_assessment_plan.md) | [runtime_log_parallel_hotspot_assessment_done_plan.md](./runtime_log_parallel_hotspot_assessment_done_plan.md) |
| `smooth_openmp_design_and_dependency_policy` | smooth OpenMP 设计与依赖策略约束更新 | Done | M4 - 收尾 | `runtime_log_parallel_hotspot_assessment`, `submodule_edit_constraint` | [smooth_openmp_design_and_dependency_policy_plan.md](./smooth_openmp_design_and_dependency_policy_plan.md) | [smooth_openmp_design_and_dependency_policy_done_plan.md](./smooth_openmp_design_and_dependency_policy_done_plan.md) |
| `smooth_openmp_phase1_implementation` | smooth OpenMP 第一阶段实现 | Done | M4 - 收尾 | `smooth_openmp_design_and_dependency_policy`, `submodule_edit_constraint` | [smooth_openmp_phase1_implementation_plan.md](./smooth_openmp_phase1_implementation_plan.md) | [smooth_openmp_phase1_implementation_done_plan.md](./smooth_openmp_phase1_implementation_done_plan.md) |
| `tracing_failure_reassessment` | Tracing 失败回归复核 | Done | M4 - 收尾 | `submodule_edit_constraint`, `json_bool_parser_fix` | [tracing_failure_reassessment_plan.md](./tracing_failure_reassessment_plan.md) | [tracing_failure_reassessment_done_plan.md](./tracing_failure_reassessment_done_plan.md) |
| `xfield_tracer_localization_and_fix` | xfield_tracer 本地化与 tracing 修复 | In Progress | M1 - 设计 | `tracing_failure_reassessment`, `submodule_edit_constraint` | [xfield_tracer_localization_and_fix_plan.md](./xfield_tracer_localization_and_fix_plan.md) | [xfield_tracer_localization_and_fix_done_plan.md](./xfield_tracer_localization_and_fix_done_plan.md) |

## 依赖说明
新任务在开始实质执行前必须先登记到该表。如果任务依赖其他任务，必须在这里和任务计划文件中同时记录。

## 维护规则
更新顺序是强制的：

1. Update `<task>_plan.md`.
2. Update `<task>_done_plan.md`.
3. Sync the summary state back into `plan.md`.

不要在 `plan.md` 中堆积实现细节。
