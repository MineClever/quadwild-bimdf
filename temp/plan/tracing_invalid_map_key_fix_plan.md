# tracing_invalid_map_key_fix_plan

Task ID: `tracing_invalid_map_key_fix`
Task Name: `Tracing 阶段 invalid map key 异常隔离修复`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
修复 `quadwild` 在 tracing 子 patch 阶段因 `invalid map<K, T> key` 直接中断的问题，至少保证局部异常不会导致整批任务失败，并补充足够的日志用于后续深挖根因。

## 范围
纳入范围：
- 定位异常触发的大致代码路径。
- 在 subpatch tracing 级别增加异常隔离与日志。
- 重建并验证 `quadwild` 可执行文件。

不纳入范围：
- 全面重写 `xfield_tracer` 的 patch tracing 算法。
- 重新设计 tracing 参数或 UI 交互。

## 依赖
- `json_bool_parser_fix`
