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
| `pyside2_binary_ui` | PySide2 二进制图形界面 | In Progress | M1 - 设计 | `windows_build_bat_setup` | [pyside2_binary_ui_plan.md](./pyside2_binary_ui_plan.md) | [pyside2_binary_ui_done_plan.md](./pyside2_binary_ui_done_plan.md) |

## 依赖说明
新任务在开始实质执行前必须先登记到该表。如果任务依赖其他任务，必须在这里和任务计划文件中同时记录。

## 维护规则
更新顺序是强制的：

1. Update `<task>_plan.md`.
2. Update `<task>_done_plan.md`.
3. Sync the summary state back into `plan.md`.

不要在 `plan.md` 中堆积实现细节。
