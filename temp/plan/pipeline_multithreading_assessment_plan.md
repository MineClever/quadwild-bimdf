# pipeline_multithreading_assessment_plan

Task ID: `pipeline_multithreading_assessment`
Task Name: `整程序多线程提速可行性评估`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
评估是否可以把当前 QuadWild / Quad From Patches 整体运行流程改为多线程模式，以尽可能提升运行速度，并明确真正有收益的改造方向、风险和优先级。

## 范围
纳入范围：
- 盘点当前 UI 进程、`quadwild.exe`、`quad_from_patches.exe` 的执行边界。
- 识别流程级并行、阶段级并行、算法级并行的可行性差异。
- 给出推荐改造顺序和不建议投入的方向。

不纳入范围：
- 直接修改求解器算法实现。
- 修改任何 `libs/` 下的 submodule 文件。

## 依赖
- `configurable_pipeline_and_ui_tabs`
- `submodule_edit_constraint`
