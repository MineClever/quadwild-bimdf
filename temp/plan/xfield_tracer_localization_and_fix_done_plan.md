# xfield_tracer_localization_and_fix_done_plan

Task ID: `xfield_tracer_localization_and_fix`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成 submodule 本地化
- [x] 完成 tracing 修复
- [x] 完成验证与收尾

## 完成日志
- 2026-06-08：开始将 `libs/xfield_tracer` 从 submodule 转为本地维护代码，并同步处理 tracing 崩溃修复。
- 2026-06-08：移除 `.gitmodules` 中 `libs/xfield_tracer` 的 submodule 声明，删除工作树中的 `libs/xfield_tracer/.git` 链接文件，并将 `libs/xfield_tracer` 作为主仓库普通目录加入索引追踪。
- 2026-06-08：更新 `AGENTS.md`，明确 `libs/xfield_tracer` 现在是允许直接维护的本地代码例外，不再受“默认禁止修改 submodule”约束。
- 2026-06-08：在 `libs/xfield_tracer/tracing/tracer_interface.h` 的 `SolveSubPatches()` 中恢复按 partition 的异常隔离逻辑；当 `TraceSubPatch()` 抛出异常时，记录 `[WARN] TraceSubPatch failed for partition ...` 并继续处理剩余 partition。
- 2026-06-08：完成 `quadwild` 与 `cli_trace` 的重建，并使用现有 `Mesh_rem` 中间产物成功复现验证：`cli_trace.exe` 不再因 `invalid map<K, T> key` 整体失败，而是完成 tracing 并输出单 partition 警告。

## 实现说明
- `xfield_tracer` 的 Git 形态已从 gitlink 改为普通目录追踪，因此后续对其代码的维护将和主仓库其它源码一致。
- tracing 修复采用最小侵入策略：只在 `SolveSubPatches()` 内部按 partition 捕获异常，不改变成功路径的 tracing 行为。
- 外层 `quadwild/trace.cpp` 仍保持简洁桥接层；真正的“继续处理剩余 partition”能力必须位于 `xfield_tracer` 内部，这次已在本地化后的代码上恢复。

## 验证说明
- `git submodule status` 已确认不再列出 `libs/xfield_tracer`。
- 构建验证：
  - `H:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe --build build\windows-default --config Release --target quadwild cli_trace`
  - `quadwild.exe` 构建成功
  - `cli_trace.exe` 构建成功
- 运行验证：
  - `build\windows-default\Build\bin\Release\cli_trace.exe D:\_Code_Here\Git\quadwild-bimdf\ui_runs\full_Mesh_obj_20260608_023916\Mesh_rem`
  - 结果为 `exit code 0`
  - tracing 全流程完成，末尾输出：
    - `[WARN] TraceSubPatch failed for partition 4049 with 139 faces: invalid map<K, T> key`
    - `success.`

## 收尾状态
已完成。
