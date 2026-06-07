# pyside2_binary_ui_done_plan

Task ID: `pyside2_binary_ui`

## 当前完成状态
- [x] 建立任务计划文件
- [x] 编写 PySide2 UI 脚本
- [x] 增加可运行入口
- [x] 完成验证并收尾

## 完成日志
- 2026-06-07：读取二进制入口参数、输出命名方式和发布目录，确定 UI 包装策略。
- 2026-06-07：实现 `scripts/quadwild_ui.py`，支持 `quadwild`、`quad_from_patches` 与串联完整流程。
- 2026-06-07：增加 `Run_QuadWild_UI.bat` 作为启动入口。
- 2026-06-07：加入 `PySide2` 优先、`PySide6` 兼容回退的导入策略。
- 2026-06-07：完成 `py_compile` 语法检查，并做模块导入级验证。

## 实现说明
UI 脚本提供以下能力：

- 选择 `quadwild.exe`、`quad_from_patches.exe` 二进制路径
- 选择 `quadwild` 输入网格、`quad_from_patches` 输入网格、`.sharp`、`.rosy`、预处理配置和主配置
- 设置输出根目录与任务子目录
- 选择三种工作流：仅 `quadwild`、仅 `quad_from_patches`、完整串联流程
- 在后台线程执行二进制，实时显示日志与命令预览
- 通过工作目录复制策略把输出稳定写入用户指定目录
- 启动时优先使用 `PySide2`，如其导入失败则自动回退到 `PySide6`

## 验证说明
- 已通过 `python -m py_compile scripts\\quadwild_ui.py`。
- 已通过 `python -c "import scripts.quadwild_ui as ui; print(ui.QT_BINDING)"` 做模块导入级验证。
- 当前环境中 `PySide2` 可被优先导入，但导入过程伴随本地 NumPy 兼容警告；脚本已具备 `PySide6` 回退逻辑。
- 未做完整 GUI 交互式人工点击验证，因为当前会话不适合进行桌面交互。

## 遗留问题
- 若本机 `PySide2` 环境异常但未抛出真正的导入失败，仍会优先使用 `PySide2`，其行为依赖本地 Python/Qt 环境质量。

## 收尾状态
已关闭。
