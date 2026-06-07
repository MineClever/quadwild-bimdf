# ui_serialized_config_assessment_plan

Task ID: `ui_serialized_config_assessment`
Task Name: `UI 序列化配置评估`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
评估是否适合把当前项目的全部配置改为 UI 可直接编辑的结构，并把现有 `txt` 配置文件作为序列化后的持久化格式，由 UI 直接读写。

## 范围
纳入范围：
- 评估现有 `txt` 配置格式是否足以承载 UI 状态
- 评估 `quadwild` 与 `quad_from_patches` 的解析逻辑是否适合统一
- 评估 UI 直接绑定配置字段的实现复杂度、风险与推荐拆分

不纳入范围：
- 实际实现新的配置系统
- 改写配置文件格式
- 增加新的运行参数

## 已确认决策
- 评估基于当前代码，不泛化到外部系统。
- 输出以“是否值得做、怎么做更稳”为主。

## 里程碑拆分
- `M1 - 设计`: 定义评估边界与涉及文件。
- `M2 - 实现`: 梳理当前 UI、txt 配置与 C++ 解析逻辑。
- `M3 - 验证`: 交叉比对 UI 已支持和未支持的配置项。
- `M4 - 收尾`: 输出评估结论与建议顺序。

## 风险与注意点
- 当前 txt 配置是弱结构化文本，不是强 schema。
- “全部配置 UI 化”很容易把 UI 复杂度推高。

## 依赖
- `configurable_pipeline_and_ui_tabs`

## 后续动作
- 如果结论成立，下一步应先定义统一 schema，再让 UI 与 txt 双向映射。
