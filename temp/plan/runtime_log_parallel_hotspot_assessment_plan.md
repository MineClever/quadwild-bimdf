# runtime_log_parallel_hotspot_assessment_plan

Task ID: `runtime_log_parallel_hotspot_assessment`
Task Name: `基于实际运行日志的并行热点评估`
Overall Status: In Progress
Current Phase: `M1 - 设计`

## 目标
结合用户提供的真实单模型运行日志，进一步评估当前流程的实际热点、潜在并行收益，以及 OpenMP 在这些热点上的优先级。

## 范围
纳入范围：
- 从本次运行日志提取阶段耗时与热点。
- 判断热点是否受 submodule 边界、数据依赖或共享写入限制。
- 给出更贴近当前模型与参数的并行化建议。

不纳入范围：
- 实施代码改造。
- 修改任何 `libs/` 下的 submodule 文件。

## 依赖
- `single_model_hotspot_parallel_assessment`
- `submodule_edit_constraint`
