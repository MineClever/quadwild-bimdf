# windows_build_bat_setup_plan

Task ID: `windows_build_bat_setup`
Task Name: `Windows 一键构建脚本`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
为本项目增加一个可直接执行的 `.bat`，在 Windows 下完成配置、编译、收集产物，并输出可运行二进制目录。

## 范围
纳入范围：
- 增加新的 Windows 批处理构建脚本
- 复用仓库现有 CMake/CI 的 Windows 构建路径
- 在脚本中整理 `quadwild`、`quad_from_patches` 与运行所需 `config/`
- 更新计划系统与 agent 规则，使 Plan 默认优先中文

不纳入范围：
- 增加新的 CMake target
- 修改核心算法代码
- 处理非 Windows 平台的一键脚本

## 已确认决策
- 任务计划内容优先使用中文。
- Windows 构建优先尝试 CI 使用的 `ClangCl` 路径。
- 若本地没有 `ClangCl`，脚本需要提供可用的回退路径，而不是静默失败。
- 产物应收集到独立目录，便于直接运行与分发。

## 里程碑拆分
- `M1 - 设计`: 确定脚本行为、输出目录与失败回退策略。
- `M2 - 实现`: 新增 `.bat` 并更新相关计划约束。
- `M3 - 验证`: 检查脚本语法、关键命令与产物路径。
- `M4 - 收尾`: 回写完成记录并同步主索引状态。

## 风险与注意点
- 本地 Windows 环境可能缺少 `ClangCl` 或 Visual Studio 生成器。
- 第三方依赖较多，首次配置时间可能较长。
- 不同生成器的输出目录结构可能不同，需要脚本兼容处理。

## 依赖
- `planning_system_bootstrap`

## 后续动作
- 如果后续需要更安静的日志输出，可继续把默认生成器配置日志也转存到文件。
- 如果需要分发压缩包，可在脚本末尾追加打包步骤。
