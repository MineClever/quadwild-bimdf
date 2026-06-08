# mesh_extension_case_fix_plan

Task ID: `mesh_extension_case_fix`
Task Name: `输入网格扩展名大小写兼容修复`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
修复 `quadwild` 对输入网格扩展名大小写敏感的问题，确保 UI 或手工调用传入 `.OBJ`、`.PLY`、`.OFF` 时能够正常进入加载流程，并避免后续阶段因前置输出缺失产生级联失败。

## 范围
纳入范围：
- 定位并修复 `quadwild` 共享网格加载路径中的扩展名判断问题。
- 评估并补齐与该问题直接相关的入口兼容性处理。
- 完成受影响目标的定向构建验证。

不纳入范围：
- 重构整套文件命名约定。
- 修改 `libs/` 下受保护 submodule。
- 改动与本次失败无关的 UI 流程设计。

## 依赖
- `json_config_system_migration`
- `pyside2_binary_ui`

## 里程碑
### M1 - 设计
- 根据用户运行日志确认失败发生在输入网格加载前置校验。
- 定位共享加载逻辑与相关入口的大小写敏感假设。

### M2 - 实现
- 在共享加载逻辑中改为大小写无关的扩展名判定。
- 仅在必要时补充入口侧兼容处理，避免重复修补。

### M3 - 验证
- 构建受影响目标。
- 复核 `.OBJ` 输入至少能够越过原始 `Wrong mesh filename` 失败点。

### M4 - 收尾
- 更新完成记录。
- 回写 `temp/plan/plan.md` 总索引状态。

## 结果
- 已在共享网格加载逻辑中支持大小写无关扩展名识别。
- 已修复 `quadwild` 与 `quad_from_patches` 的输入加载失败退出码，避免 UI 将失败误判为成功。
- 已完成 `build/windows-default` 定向重建，并将修复后的二进制同步到 `release/windows/`。
