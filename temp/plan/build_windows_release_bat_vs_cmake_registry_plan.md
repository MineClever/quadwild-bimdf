# build_windows_release_bat_vs_cmake_registry_plan

Task ID: `build_windows_release_bat_vs_cmake_registry`
Task Name: `Build_Windows_Release.bat 自动读取 VS 注册表 CMake 环境`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
改进 `Build_Windows_Release.bat`，优先从 Visual Studio 安装注册表中自动定位自带 CMake，再回退到系统 `PATH`，避免依赖硬编码绝对路径。

## 范围
纳入范围：
- 通过注册表读取 Visual Studio 安装根目录
- 自动拼出 VS 自带 `cmake.exe` 路径并校验可用性
- 保留现有的 `PATH` 回退逻辑
- 更新计划索引与完成记录

不纳入范围：
- 改动 CMakeLists 或核心 C++ 代码
- 修改 Windows 构建产物收集逻辑
- 引入新的第三方工具

## 已确认决策
- 先查 Visual Studio 注册表，再查系统 `PATH`
- 优先使用现有 VS 安装中的 CMake，而不是额外下载的 CMake
- 当注册表或目标文件不可用时，脚本必须明确回退或报错

## 里程碑拆分
- `M1 - 设计`: 确认注册表键、回退顺序与失败处理。
- `M2 - 实现`: 修改批处理脚本并同步计划文件。
- `M3 - 验证`: 检查脚本语法并进行最小化执行验证。
- `M4 - 收尾`: 记录结果并同步主索引状态。

## 风险与注意点
- 不同 Visual Studio 版本和安装类型可能对应不同的注册表值。
- 64 位与 32 位注册表视图可能不一致，需要兼容查询。
- 本机若未安装 Visual Studio，自带 CMake 路径应自然回退到 `PATH`。

## 依赖
- `windows_build_bat_setup`
