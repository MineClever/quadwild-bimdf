# tracing_failure_reassessment_done_plan

Task ID: `tracing_failure_reassessment`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成日志与代码状态复核
- [x] 完成结论与建议
- [x] 完成收尾

## 完成日志
- 2026-06-08：开始复核 tracing 阶段 `invalid map<K, T> key` 回归失败。
- 2026-06-08：确认 `quadwild/trace.cpp` 当前只是直接调用 `RecursiveProcess<TracerType>(...)`，本地桥接层没有局部异常隔离。
- 2026-06-08：确认 `libs/xfield_tracer` submodule 工作树当前为干净状态，之前对 `tracing/tracer_interface.h` 的 `TraceSubPatch()` 异常隔离改动确已撤回。
- 2026-06-08：确认当前再次出现的 `fatal error: invalid map<K, T> key` 与此前已知 tracing 回归点一致；没有 submodule 级异常隔离时，单个 partition 失败会再次中断整个 tracing。

## 实现说明
- 本次未修改代码，只完成状态复核。
- 现有主仓库层面无法等价替代此前的 submodule 修复：如果不在 `xfield_tracer` 内部按 partition 捕获异常，`RecursiveProcess()` 一旦抛出异常，整个 tracing 都会退出。
- 在 `quadwild/trace.cpp` 或 `quadwild` 主程序更外层追加 try/catch 只能把“崩溃退出”变成“优雅失败”，不能实现“跳过坏 partition 并继续 tracing”。

## 验证说明
- 已检查 `quadwild/trace.cpp` 当前调用路径。
- 已检查 `git -C libs\\xfield_tracer status --short`，确认 submodule 工作树干净。
- 已检索仓库当前代码，确认此前 `[WARN] TraceSubPatch failed for partition ...` 的 submodule 级隔离逻辑已不存在。

## 收尾状态
已完成。
