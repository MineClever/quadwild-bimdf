# build_windows_release_bat_vs_cmake_registry_done_plan

Task ID: `build_windows_release_bat_vs_cmake_registry`

## 当前完成状态
- [x] 为任务建立计划文件
- [x] 更新 `Build_Windows_Release.bat`
- [x] 验证注册表探测与回退逻辑
- [x] 回写主计划索引并完成收尾

## 完成日志
- 2026-06-08：新增任务计划文件并同步到主计划索引，明确目标是把 `Build_Windows_Release.bat` 的 VS CMake 路径从硬编码改为注册表自动探测。
- 2026-06-08：将脚本改为优先从 `HKLM\SOFTWARE\Microsoft\VisualStudio\17.0\Setup\rdbgwiz` 等注册表位置反推 VS 安装根，再构造 `Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe`；同时保留 `SxS\VS7` 与 `PATH` 回退。
- 2026-06-08：实际执行 `cmd /c Build_Windows_Release.bat` 验证脚本可正常启动并进入构建流程；当前机器未安装 VS 自带 CMake 组件，因此脚本按预期回退到 `PATH` 中的 `cmake`，后续配置阶段仍受仓库现有 CMake 兼容性问题影响而失败。
- 2026-06-08：在第一轮完成记录基础上重新打开任务，补充从 Visual Studio 卸载注册表 `InstallLocation` 读取安装根目录的逻辑，以覆盖 `H:\Program Files\Microsoft Visual Studio\2022\Community` 这类实际安装路径。
- 2026-06-08：最终改为优先用 PowerShell 读取 VS 卸载注册表中的 `InstallLocation`，并成功命中 `H:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe`。
- 2026-06-08：实际执行 `cmd /c Build_Windows_Release.bat`，脚本成功完成配置、编译和产物收集，输出 `Build complete`。

## 实现说明
- `Build_Windows_Release.bat` 现在会先尝试从 Visual Studio 注册表中定位安装根，再拼接 bundled CMake 路径。
- 若注册表命中但目标 `cmake.exe` 不存在，脚本会继续尝试旧的 `SxS\VS7` 路径，最后再回退到系统 `PATH`。
- 这样可以兼容不同 VS 安装布局，同时去掉了硬编码绝对路径。
- 目前优先级是：PowerShell 读取卸载注册表 `InstallLocation` > `Setup\\rdbgwiz` 兼容探测 > `SxS\\VS7` 旧路径 > 系统 `PATH`。

## 验证说明
- 运行 `cmd /c Build_Windows_Release.bat`，脚本成功打印仓库根目录、构建配置与 CMake 选择结果。
- 在当前机器上，脚本已命中 VS 自带 CMake，显示完整路径 `H:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe`。
- 本次执行成功完成配置、编译和产物收集，`release/windows/` 已更新。

## 遗留问题
- 构建过程仍会输出仓库内若干第三方 CMake 警告，但不影响 Windows Release 流程完成。

## 收尾状态
- 已完成。
