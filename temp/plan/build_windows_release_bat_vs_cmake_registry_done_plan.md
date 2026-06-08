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

## 实现说明
- `Build_Windows_Release.bat` 现在会先尝试从 Visual Studio 注册表中定位安装根，再拼接 bundled CMake 路径。
- 若注册表命中但目标 `cmake.exe` 不存在，脚本会继续尝试旧的 `SxS\VS7` 路径，最后再回退到系统 `PATH`。
- 这样可以兼容不同 VS 安装布局，同时去掉了硬编码绝对路径。

## 验证说明
- 运行 `cmd /c Build_Windows_Release.bat`，脚本成功打印仓库根目录、构建配置与 CMake 选择结果。
- 在当前机器上，脚本未命中 VS 自带 CMake，因此显示 `CMake executable: cmake` 并按预期走回退逻辑。
- 后续 CMake 配置失败来自仓库现有的最低版本兼容性问题，与本次批处理脚本修改无关。

## 遗留问题
- 当前机器没有安装可用的 VS bundled CMake，因此无法在本机复现实例级“注册表命中 -> 使用 VS CMake”的完整链路。

## 收尾状态
- 已完成。
