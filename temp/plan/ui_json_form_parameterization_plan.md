# ui_json_form_parameterization_plan

Task ID: `ui_json_form_parameterization`
Task Name: `UI 参数表单化与总览输入同步`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
把现有 UI 中的 `QuadWild` / `Quad From Patches` JSON 配置从文本编辑方式迁移为参数表单，让用户直接在界面上编辑所有主要参数；同时保留 JSON 文件作为配置读写格式，并把 `QuadWild` 输入网格入口同步到“总览”Tab。

## 范围
纳入范围：
- 将 `scripts/quadwild_ui.py` 改为“参数控件 <-> JSON 文件”双向读写。
- 为 `QuadWild` 与 `Quad From Patches` 提供完整参数表单、文件加载、文件保存与默认值恢复。
- 在总览 Tab 增加 `QuadWild` 输入网格入口。
- 保留 `QuadWild` Tab 中的输入入口，并让两处入口保持同一份状态。

不纳入范围：
- 改写底层二进制参数协议。
- 修改 C++ 端配置字段集合。
- 将所有参数拆成更复杂的多层 schema 校验系统。

## 已确认决策
- Plan 文档继续优先中文。
- JSON 文件仍作为正式配置交换格式。
- UI 不再以“手工编辑原始 JSON 文本”为主，而是以参数表单为主。
- 由于 Qt 不能把同一个控件实例同时挂载在两个 Tab 中，两处输入入口将共享同一份数据状态并保持实时同步。

## 里程碑拆分
- `M1 - 设计`: 梳理当前 UI 控件、配置字段与同步策略。
- `M2 - 实现`: 完成表单化、文件读写与总览同步入口。
- `M3 - 验证`: 完成 Python 语法检查与模块导入验证。
- `M4 - 收尾`: 回写任务记录并同步主索引。

## 风险与注意点
- 参数较多，若布局组织不当，UI 会迅速变得难用，需要分组显示。
- 旧设置文件里可能仍保存文本配置，需要兼容迁移读取。
- 数组类参数如 `callbackTimeLimit` 与 `callbackGapLimit` 需要定义清晰的界面输入格式。
- Qt 无法把同一个控件实例同时放到两个 Tab 中，因此“总览”和“QuadWild”中的输入入口只能共享同一份状态，而不能是同一个实例对象。

## 依赖
- `json_config_system_migration`
