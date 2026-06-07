# pipeline_multithreading_assessment_done_plan

Task ID: `pipeline_multithreading_assessment`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成架构与执行路径盘点
- [x] 完成多线程可行性评估
- [x] 完成收尾

## 完成日志
- 2026-06-08：开始评估当前 UI 驱动的二进制流水线是否值得整体改为多线程，以及哪些阶段存在真实并行空间。
- 2026-06-08：确认 `scripts/quadwild_ui.py` 当前只是用 `QThread` 承载外部进程执行，核心计算仍由 `quadwild.exe` 与 `quad_from_patches.exe` 串行完成。
- 2026-06-08：确认 `quadwild` 内部阶段顺序是 `remeshAndField -> trace -> quadrangulate`，`quad_from_patches` 内部顺序是 `quadrangulationFromPatches -> smoothing -> save`，存在强数据依赖，不能简单并行化整个单次流程。
- 2026-06-08：确认当前 CMake 路径没有启用活跃的 OpenMP / 线程并行配置；旧 `.pro` 文件里保留了 `-fopenmp` 痕迹，但并未反映到当前实际构建链。

## 实现说明
- 当前 UI 的工作线程仅用于避免界面阻塞，不会让求解更快；其执行模型是顺序遍历 `command_specs` 并依次启动外部进程。
- `full_pipeline` 模式下，`quad_from_patches` 依赖 `quadwild` 生成的 `*_rem_p0.obj` 与相关 sidecar，因此单个任务的两大阶段天然串行。
- 单模型加速的真正机会主要在算法热点内部，例如 `BatchProcess`、`trace`、`quadrangulationFromPatches`、`MultiCostraintSmooth`，但这意味着需要深入改动现有 C++ / 依赖库，并验证线程安全。
- 最低风险、最高性价比的并行方式不是“把整个程序改成多线程”，而是：
  1. 多任务并行：多个输入模型各跑一套独立流程。
  2. 只对耗时热点做阶段内并行。
  3. 若后端求解器本身支持并行，优先利用求解器级并行而不是外层重复造线程。

## 验证说明
- 已检查 `scripts/quadwild_ui.py` 的执行顺序与线程边界。
- 已检查 `quadwild/quadwild.cpp`、`quadwild/functions.cpp`、`components/quad_from_patches/main.cpp` 的阶段调用顺序。
- 已检查当前构建树中的并行相关痕迹，确认活跃 CMake 路径没有显式线程/`OpenMP` 接入。

## 收尾状态
已完成。
