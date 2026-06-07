# single_model_hotspot_parallel_assessment_plan

Task ID: `single_model_hotspot_parallel_assessment`
Task Name: `单模型热点并行与 OpenMP 可行性评估`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
围绕单个模型处理流程，评估当前仓库中哪些热点阶段适合做阶段内并行，尤其是是否适合用 OpenMP 直接提速，以及这样做的限制、风险和优先级。

## 范围
纳入范围：
- 盘点单模型主流程中的热点阶段。
- 评估 OpenMP 对各热点阶段的适配性。
- 区分可在主仓库内实施的并行化与会落入 submodule 的并行化。

不纳入范围：
- 直接修改算法实现。
- 修改任何 `libs/` 下的 submodule 文件。

## 依赖
- `pipeline_multithreading_assessment`
- `submodule_edit_constraint`
