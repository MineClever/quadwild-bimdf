# ui_parameter_separation_and_help_plan

Task ID: `ui_parameter_separation_and_help`
Task Name: `UI 参数拆分与字段提示完善`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
按 `quadwild.exe` 与 `quad_from_patches.exe` 实际读取的参数重构 UI，避免两阶段参数混杂，并为每个参数补充作用与用法提示。

## 范围
纳入范围：
- 盘点两阶段真实读取的配置键。
- 重构 UI 表单分组与展示结构。
- 为每个配置字段补充提示信息。

不纳入范围：
- 修改二进制的底层参数解析逻辑。
- 修改 submodule 内容。

## 依赖
- `ui_json_form_parameterization`
- `json_bool_parser_fix`
