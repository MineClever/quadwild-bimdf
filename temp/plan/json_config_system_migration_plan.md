# json_config_system_migration_plan

Task ID: `json_config_system_migration`
Task Name: `全量 JSON 配置系统迁移`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
彻底放弃当前基于 `txt` 的运行配置格式，把 `quadwild`、`quad_from_patches` 和 Python UI 的配置读写统一切换到 `json`，并将现有默认配置文件全部转换为 JSON。

## 范围
纳入范围：
- 修改 `quadwild` 的配置读取逻辑，改为 JSON。
- 修改 `quad_from_patches` 的配置读取与调试导出逻辑，改为 JSON。
- 把现存默认 `txt` 配置迁移为 `.json` 文件，并更新代码中的默认路径与帮助信息。
- 更新 `scripts/quadwild_ui.py`，让 UI 默认读写 JSON 配置文件与工作目录内的阶段配置。
- 同步更新仓库文档中的运行示例。

不纳入范围：
- 重构核心算法参数语义。
- 设计新的远程配置协议。
- 强制把所有外部 sidecar 文件都改为 JSON。

## 已确认决策
- Plan 文档继续优先中文。
- 本次迁移目标是彻底弃用 `txt` 作为运行配置格式，不保留双格式运行入口。
- UI 仍允许直接编辑原始配置文本，但文本内容变为 JSON。
- 默认配置文件优先沿用原有目录结构与命名语义，只把扩展名迁移为 `.json`。

## 里程碑拆分
- `M1 - 设计`: 清点所有 `txt` 配置入口、默认文件与文档引用，确定 JSON 结构。
- `M2 - 实现`: 完成 C++ / UI / 默认配置文件迁移。
- `M3 - 验证`: 完成 Python 语法检查和 Windows 构建验证。
- `M4 - 收尾`: 回写任务记录并同步主索引。

## 风险与注意点
- `quadwild` 与 `quad_from_patches` 现有配置字段并不完全同构，迁移时要保证共享字段含义一致。
- JSON 迁移后，默认值来源必须明确，否则 UI 默认值与二进制默认值可能漂移。
- 发布目录如果只覆盖不清理，会残留旧的 `.txt` 配置，因此打包脚本也需要同步修正。

## 依赖
- `configurable_pipeline_and_ui_tabs`
- `ui_serialized_config_assessment`

## 后续动作
- 如果本次迁移完成后仍需要更强的字段级校验，可再把 JSON 文本编辑器升级为结构化表单。
- 如果后续还要继续做 UI 表单化，建议把当前 JSON 文本区再抽象为共享 schema，而不是继续复制字段名。
