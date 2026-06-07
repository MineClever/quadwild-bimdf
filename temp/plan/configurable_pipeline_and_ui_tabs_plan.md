# configurable_pipeline_and_ui_tabs_plan

Task ID: `configurable_pipeline_and_ui_tabs`
Task Name: `流水线可配置化与 UI Tab 重构`
Overall Status: In Progress
Current Phase: `M1 - 设计`

## 目标
把 `quadwild` 以及后续 `Quad From Patches` 阶段中的关键硬编码参数改成可配置项，并重构当前 Python UI：使用多个 Tab 组织设置，支持运行状态显示、中断执行、重置默认、任务目录自动生成与手动刷新/编辑。

## 范围
纳入范围：
- 修改 C++ 配置结构和解析逻辑，使 quantization / quadrangulation 关键参数可配置
- 更新默认配置文件，使新配置项可落地
- 重构 `scripts/quadwild_ui.py` 为多 Tab 界面
- 增加取消执行、状态显示、重置默认、任务目录自动生成与手动生成按钮

不纳入范围：
- 更换底层二进制参数协议
- 修改核心优化算法公式
- 做完整桌面人工交互测试

## 已确认决策
- Plan 文档继续优先中文。
- `quadwild` 侧将扩展现有配置格式，而不是新增全新二进制参数接口。
- UI 继续兼容 `PySide2` / `PySide6` 双绑定策略。
- 任务目录默认根据当前工作流和输入网格文件名自动生成，同时保留手动编辑和手动刷新能力。

## 里程碑拆分
- `M1 - 设计`: 确认硬编码参数、UI 结构与状态管理策略。
- `M2 - 实现`: 完成 C++ 配置扩展和 UI 重构。
- `M3 - 验证`: 做构建或静态检查，确认脚本可导入、C++ 可编译。
- `M4 - 收尾`: 回写任务记录并同步主索引。

## 风险与注意点
- `quadwild` 现有配置文件格式较脆弱，扩展时要保持向后兼容。
- Python 2/3 兼容语法下，中断子进程和线程收尾要避免使用较新的语法特性。
- 如果 UI 允许编辑过多参数，布局会迅速失控，因此需要分 Tab 组织。

## 依赖
- `pyside2_binary_ui`

## 后续动作
- 先读取 `quad_from_patches` 的完整配置格式并映射到 `quadwild` 参数结构。
- 再统一重构 UI 的任务执行和状态管理。
