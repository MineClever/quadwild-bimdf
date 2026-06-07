# track_build_windows_release_bat_plan

Task ID: `track_build_windows_release_bat`
Task Name: `将 Build_Windows_Release.bat 纳入 Git 跟踪`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
修复 `.gitignore` 对 `Build_Windows_Release.bat` 的误忽略，让该脚本可以被 Git 正常跟踪。

## 范围
纳入范围：
- 定位忽略规则来源。
- 调整 `.gitignore` 以放行该脚本。
- 验证 Git 状态与忽略判定。

不纳入范围：
- 修改脚本内容本身。
- 执行提交。

## 依赖
- `windows_build_bat_setup`
