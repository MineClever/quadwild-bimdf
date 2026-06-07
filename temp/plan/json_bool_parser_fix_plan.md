# json_bool_parser_fix_plan

Task ID: `json_bool_parser_fix`
Task Name: `JSON 布尔字段解析与 UI 二进制路径修复`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
修复 UI 生成的 JSON 配置在 `quadwild` / `quad_from_patches` 中触发的布尔字段解析崩溃，并修复 UI 优先调用仓库中过期 `release` 二进制的问题。

## 范围
纳入范围：
- 修复 `useFlowSolver` 等布尔字段的 C++ JSON 解析逻辑。
- 修复 UI 中对应字段控件类型，避免继续输出数值型布尔。
- 改善 CLI 异常输出，避免再次只看到退出码。
- 修复 UI 的可执行文件选择逻辑，优先使用仓库内最新构建产物。

不纳入范围：
- 重新设计全部参数 schema。
- 修改 quadrangulation 算法行为。

## 依赖
- `json_config_system_migration`
- `ui_json_form_parameterization`
