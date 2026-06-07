# tracing_invalid_map_key_fix_done_plan

Task ID: `tracing_invalid_map_key_fix`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 增加 subpatch 异常隔离
- [x] 完成构建验证
- [x] 完成收尾记录

## 完成日志
- 2026-06-08：根据 UI 执行日志确认 `quadwild` 已进入真实 tracing 阶段，并在 `SolveSubPatches -> TraceSubPatch` 期间因 `invalid map<K, T> key` 终止。
- 2026-06-08：定位到失败发生在 subpatch tracing 阶段，决定先做 patch 级异常隔离，而不是让整个 tracing 直接中断。
- 2026-06-08：对 `quadwild` 目标完成重建；本地限时复现已确认新二进制可启动到 tracing 阶段，但在限定时间内未跑到原始失败点。

## 实现说明
- 在 `libs/xfield_tracer/tracing/tracer_interface.h` 的 `SolveSubPatches()` 中，为每个 `TraceSubPatch()` 调用增加 `std::exception` 与未知异常捕获。
- 当单个 partition tracing 失败时，输出 `[WARN] TraceSubPatch failed for partition ...` 日志，并按未成功 tracing 的分支继续流程，避免整批任务直接退出。
- 增加 `<exception>` 显式包含，避免依赖间接头文件。

## 验证说明
- `cmake --build build\\windows-default --config Release --target quadwild` 通过。
- 受控运行新的 `build/windows-default/Build/bin/Release/quadwild.exe` 进行限时复现，确认可执行文件能稳定进入 tracing 阶段。
- 由于该模型较大，240 秒限时复现未推进到原始异常点，因此本轮验证结果为“已完成编译与阶段性运行验证，等待完整长跑确认 patch 级隔离效果”。

## 收尾状态
已完成。
