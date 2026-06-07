# square_topology_assessment_plan

Task ID: `square_topology_assessment`
Task Name: `方格拓扑逼近评估`
Overall Status: Done
Current Phase: `M4 - 收尾`

## 目标
评估在当前 quadwild-bimdf 项目中，若希望最终生成的四边形网格更靠近目标拓扑方格，应优先调整哪些环节、参数与工作流。

## 范围
纳入范围：
- 阅读当前仓库中的 quadrangulation 入口与量化目标权重
- 识别影响方格规则性、奇异点布局、边长一致性和 chart 拓扑的关键参数
- 给出面向当前项目的建议优先级

不纳入范围：
- 直接修改算法实现
- 提交新的默认参数文件
- 跑批量数据实验

## 已确认决策
- 评估结论必须基于当前代码路径，而不是泛化到其他重网格系统。
- 输出以可操作建议为主，聚焦配置、输入质量和最值得改的代码点。

## 里程碑拆分
- `M1 - 设计`: 确定需要查看的入口、参数和量化实现。
- `M2 - 实现`: 阅读 `quadwild/functions.cpp`、`components/quad_from_patches/main.cpp`、`libs/quadretopology/quadretopology/qr_flow.cpp`。
- `M3 - 验证`: 交叉比对配置文件和实现中的权重用法。
- `M4 - 收尾`: 输出结论并回写计划系统。

## 风险与注意点
- “更像方格”可能指几何更正方，也可能指拓扑更规则，这两者在当前系统中不是同一个旋钮。
- 当前入口有一部分参数被硬编码覆盖，导致单纯改配置文件未必生效。

## 依赖
- `pyside2_binary_ui`

## 后续动作
- 如需落地优化，优先做小规模参数扫描和去硬编码。
