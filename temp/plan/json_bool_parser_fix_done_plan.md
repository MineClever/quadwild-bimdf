# json_bool_parser_fix_done_plan

Task ID: `json_bool_parser_fix`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 修复 C++ 布尔解析
- [x] 修复 UI 字段类型
- [x] 修复 UI 二进制路径解析
- [x] 完成验证并收尾

## 完成日志
- 2026-06-08：根据失败任务目录中的 `quadwild_config.json` 和 `quadwild/functions.cpp` 定位到 `useFlowSolver` 被错误地按 `int` 生成、按 `bool` 解析，导致进程异常终止。
- 2026-06-08：通过直接运行 `build/windows-default/Build/bin/Release/quadwild.exe` 复现并确认，JSON 配置在修复后已能成功导入，流程可进入 remesh 与 tracing。
- 2026-06-08：进一步确认 UI 默认调用的是仓库内较旧的 `release/windows/quadwild.exe`，而不是更新后的 `build` 产物；已改为运行时自动解析并优先选择最新可执行文件。

## 实现说明
- `quadwild/functions.cpp` 将 `useFlowSolver` 改为使用布尔解析辅助函数。
- `components/quad_from_patches/main.cpp` 同步修复 `useFlowSolver` 的布尔解析。
- `quadwild/quadwild.cpp` 与 `components/quad_from_patches/main.cpp` 将顶层异常捕获扩展为 `std::exception`，便于输出更多错误信息。
- `scripts/quadwild_ui.py` 将 `useFlowSolver` 表单字段从 `int` 改为 `bool`。
- `scripts/quadwild_ui.py` 新增仓库内二进制候选扫描与最新版本优先逻辑，并在运行日志中提示自动切换。

## 验证说明
- `python -m py_compile scripts\\quadwild_ui.py` 通过。
- 通过 Python 导入检查确认 `preferred_repo_binary('quadwild.exe')` 与 `normalize_binary_path('.\\release\\windows\\quadwild.exe', 'quadwild.exe')` 都解析到 `build/windows-default/Build/bin/Release/quadwild.exe`。
- 直接运行新的 `build/windows-default/Build/bin/Release/quadwild.exe`，日志确认配置成功导入，并继续执行到 tracing 阶段；说明当前失败点已不在 JSON 解析阶段。
- `cmake --build build\\windows-default --config Release --target quadwild quad_from_patches` 最终通过；中途发现此前诊断残留进程会锁定 `quadwild.exe`，清理后可正常链接。

## 收尾状态
已完成。
