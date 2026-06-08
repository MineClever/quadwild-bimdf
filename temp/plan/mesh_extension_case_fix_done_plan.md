# mesh_extension_case_fix_done_plan

Task ID: `mesh_extension_case_fix`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 完成代码修复
- [x] 完成构建验证
- [x] 完成收尾记录

## 完成日志
- 2026-06-08：根据用户提供的 UI 运行日志，确认 `quadwild` 在读取 `S.OBJ` 时输出 `Wrong mesh filename`，随后 `quad_from_patches` 因缺失 `S_rem_p0.obj` 发生级联失败。
- 2026-06-08：定位到共享 `LoadTriMesh()` 通过 `find(".obj") / find(".ply") / find(".off")` 做大小写敏感判断，导致 `.OBJ` 输入被直接拒绝。
- 2026-06-08：补充大小写无关扩展名识别，并修复两个可执行文件在输入加载失败时错误使用 `exit(0)` 的问题。
- 2026-06-08：完成 `quadwild` 与 `quad_from_patches` 的 Release 定向构建，并验证 `release/windows/quadwild.exe` 可用同一份 `S.OBJ` 进入 remesh 阶段。

## 实现说明
- 在 `components/field_computation/triangle_mesh_type.h` 中对输入文件名做小写归一化，再进行 `.ply`、`.obj`、`.off` 判定，从而兼容 `.OBJ` 等大写扩展名。
- 在 `quadwild/quadwild.cpp` 中将输出前缀提取改为基于最后一个 `.`，并把网格加载失败从 `exit(0)` 改为返回 `1`，同时输出具体文件名。
- 在 `components/quad_from_patches/main.cpp` 中将输入网格加载失败改为返回 `1` 并走标准错误输出，避免 UI 误判执行成功。

## 验证说明
- `cmake --build build\\windows-default --config Release --target quadwild quad_from_patches` 通过。
- 使用 `build/windows-default/Build/bin/Release/quadwild.exe` 对 `ui_runs/full_S_OBJ_20260608_201840/S.OBJ` 进行 15 秒限时运行，确认日志已越过原始失败点并输出 `Loaded 77108 faces and 38553 vertices`。
- 使用缺失输入路径运行 `quadwild`，确认退出码为 `1`，且输出 `Wrong mesh filename: ...missing.OBJ`。
- 使用缺失输入路径运行 `quad_from_patches`，确认退出码为 `1`，且输出 `Error loading mesh from file ...missing_rem_p0.obj`。
- 将验证通过的 `quadwild.exe` 与 `quad_from_patches.exe` 同步覆盖到 `release/windows/` 后，再次对 `release/windows/quadwild.exe` 做短时运行复核，确认 UI 实际使用路径也已生效。

## 收尾状态
已完成。
