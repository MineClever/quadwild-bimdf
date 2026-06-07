# pyside2_binary_ui_plan

Task ID: `pyside2_binary_ui`
Task Name: `PySide2 二进制图形界面`
Overall Status: In Progress
Current Phase: `M1 - 设计`

## 目标
为已构建的 `quadwild.exe` 与 `quad_from_patches.exe` 提供一个可运行的 PySide2 图形界面，用于选择输入文件、配置参数、设置输出目录并启动处理流程。

## 范围
纳入范围：
- 使用 Python 2/3 兼容语法编写 UI 脚本
- 使用 PySide2 构建桌面界面
- 支持选择二进制路径、输入网格、配置文件、可选 `.sharp` / `.rosy` 文件与输出目录
- 支持运行 `quadwild`、运行 `quad_from_patches`，以及串联执行两步流程
- 在界面中显示执行命令、日志与产物位置

不纳入范围：
- 改写 C++ 二进制的参数协议
- 增加新的核心算法参数解析
- 打包 Python 运行时或 PySide2 安装器

## 已确认决策
- Plan 文档继续优先使用中文。
- UI 本身使用 Python 2/3 兼容语法，但默认依赖 PySide2。
- 由于二进制默认把产物写到输入文件同目录，UI 需要通过复制输入与辅助文件到输出目录工作区来实现“自定义输出路径”。
- UI 应默认探测 `release/windows/quadwild.exe` 与 `release/windows/quad_from_patches.exe`。

## 里程碑拆分
- `M1 - 设计`: 梳理 CLI 参数、输出命名与工作目录策略。
- `M2 - 实现`: 编写 PySide2 UI、任务执行逻辑与日志展示。
- `M3 - 验证`: 做语法检查、入口检查和基础运行验证。
- `M4 - 收尾`: 更新任务记录并同步主索引。

## 风险与注意点
- PySide2 通常不支持 Python 2，但代码语法仍可保持 Python 2/3 兼容。
- 长时间运行任务需要避免阻塞 UI 主线程。
- 输出目录中可能已有同名结果，需要谨慎处理覆盖策略。

## 依赖
- `windows_build_bat_setup`

## 后续动作
- 实现带后台线程执行、日志回传和输出目录工作区复制逻辑的 UI。
- 增加启动脚本，方便直接打开界面。
