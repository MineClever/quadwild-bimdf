# smooth_mesh.h OpenMP Design

## 目标
针对 `components/quad_from_patches/smooth_mesh.h` 的 `MultiCostraintSmooth()` 设计一条低风险 OpenMP 改造路径，优先优化单模型流程中最重的 `smooth` 阶段，而不是一次性并行化整个 quad 流水线。

## 当前热点结构
`MultiCostraintSmooth()` 每轮迭代包含两个主要子阶段：

1. `SmoothSharpFeatures()`
2. `SmoothInternal()`

真实运行日志显示 `smooth` 占 `quad_from_patches` 总时间的绝大多数，因此这里是单模型提速的第一目标。

## 并行化原则
- 只并行“读旧状态、算新目标、最后统一写回”的步骤。
- 不并行直接修改 mesh 拓扑、邻接关系或共享动态容器的步骤。
- 每轮迭代保持语义不变：先完成 sharp，再完成 internal。
- 首选 OpenMP 的 `parallel for`，但前提是先改成 two-phase gather/apply 数据流。

## 阶段拆分
### A. `SmoothSharpFeatures()`
当前流程：
1. `LaplacianPos()` 计算 `TargetPos`
2. 写回 sharp 顶点位置
3. `ClosestPointEMesh()` 将 sharp 顶点投回 feature edge

建议改造：
- 保持步骤顺序不变。
- 将“写回 sharp 顶点位置”和“投回 feature edge”拆成两个顶点级循环，并对 `ProjSharp && !BlockedV[i]` 的顶点集合做 OpenMP 并行。
- `ClosestPointEMesh()` 只读 `EdgeM`，天然适合并行；先建立 `sharpVertexIndices`，避免在并行循环里反复判断状态。

风险：
- `LaplacianPos()` 内部对 `TargetPos` / `NumPos` 有共享累加，不能直接并行；需要后续单独改为线程私有缓冲或边列表归并。

### B. `SmoothInternal()`
当前流程：
1. `LaplacianPos()` 或 `TemplatePos()` 生成 `TargetPosSmooth`
2. 写回 surface 顶点
3. 循环 `back_proj_steps` 次执行 `BackProjectStepPositions()`
4. 最后对每个 surface 顶点做一次 `GetClosestFaceBase()` 投影

建议改造优先级：

#### B1. 先并行“最终最近面投影”
- 这是最安全的第一刀。
- 每个顶点独立读取 `TriGrid` / `TriM` 并写回自身位置。
- 可直接改为 `#pragma omp parallel for schedule(static)`。

#### B2. 再并行“surface 顶点位置写回”
- `TargetPosSmooth[i]` 和 `TargetPosBackProj[i]` 已经按顶点索引组织。
- 写回 `PolyM.vert[i].P()` 时每个线程只写一个顶点，可并行。

#### B3. 最后重构 `BackProjectStepPositions()`
这是收益最大但改动也最大的部分。当前问题：
- `GetMovingPointOnSurface()` 会往 `VertMove[IndexV]`、`VertWeight[IndexV]` 里 `push_back`，存在共享写竞争。

建议改成：
1. 预先收集 `surfaceTriVertexIndices`
2. 每线程维护本地贡献缓冲：`localMove[index]`、`localWeight[index]`
3. 并行遍历三角网格表面顶点，累计到线程本地缓冲
4. 线程结束后做一次串行归并
5. 统一生成 `TargetMov` 与 `TargetPos`

这样 `BackProjectStepPositions()` 才适合 OpenMP。

## 不建议第一阶段并行的内容
- `GetProjectionBasis()`：包含大量集合、映射、重复插入检查和 feature 分类，收益不确定，先不动。
- `LaplacianPos()` / `LaplacianEdgePos()`：当前是共享累加模型，必须先改数据结构再谈并行。
- 任何会修改面邻接、边界或拓扑的数据流。

## 实施顺序
1. 构建系统接入 OpenMP，但默认可关闭。
2. 仅并行 `SmoothInternal()` 的最终最近面投影和两处顶点写回。
3. 并行 `SmoothSharpFeatures()` 的 sharp 顶点写回与 edge 投影。
4. 重构 `BackProjectStepPositions()` 为线程私有 gather/apply。
5. 若收益仍不足，再评估 `LaplacianPos()` 的边贡献归并化改造。

## 构建建议
- 在根 `CMakeLists.txt` 中显式 `find_package(OpenMP)`。
- 只给 `components/quad_from_patches` 相关目标链接 OpenMP。
- 通过 CMake 选项控制开关，例如 `QUADWILD_ENABLE_OPENMP_SMOOTHING=ON`。

## 预期收益
- 第一阶段只做安全顶点循环并行，预计是中等收益。
- 真正的大头在 `BackProjectStepPositions()` 重构后才可能明显下降。
- 若机器核数充足，`smooth` 阶段存在显著多核利用空间；但要先通过 profiling 验证具体哪个子步骤最重。
