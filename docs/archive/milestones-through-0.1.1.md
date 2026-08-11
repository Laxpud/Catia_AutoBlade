# 已完成里程碑：截至 0.1.1

本文归档原 `TODO.md` 中已经完成或已被当前架构取代的计划，保留关键验收证据，避免历史记录继续挤占活动任务清单。当前工作以根目录 [`TODO.md`](../../TODO.md) 为准，稳定契约以 [`docs/index.md`](../index.md) 所列专题文档为准。

## 稳定单翼型建模链路

- [x] 建立英文 README、中文翻译、技术文档索引和活动任务清单。
- [x] 修复 `autoblade-create` 和 `autoblade-batch` 兼容入口，并使其参数和退出行为与主命令一致。
- [x] 让 `config.toml` 成为输入目录、输出目录、作者和输出命名模板的运行时来源；CLI 显式值可覆盖配置。
- [x] 在异常路径可靠释放 CATIA 文档、独占应用和 COM 状态，且批处理失败不会遗留隐藏实例。
- [x] 在启动 CATIA 前完成 CSV schema、数值、截面数量和翼型点序校验，并报告文件、行号和字段。
- [x] 建立不依赖 CATIA 的自动化测试基线，使用 fake/mock 隔离 COM。
- [x] 解决密集翼型点云的几何精度冲突。
  - 2026-08-05 复现：1000 点翼型可以创建点特征，但基准样条或后续 Loft 会因 CATIA 精度和理论前缘闭合点偏差失败。
  - 修复：Python 领域统一使用 m，只在 CATIA Automation 边界换算为 mm；从实际截面曲线的 `Extremum` 中以 `Near` 选取唯一前缘点，不再把理论坐标作为 Loft 闭合点。
  - 验收：300 点、1000 点以及 260 点钝后缘案例均完成 Loft 和实体封闭，实际前缘点到所属截面的距离为 `0 mm`。

## 展向多翼型

- [x] 固定七列截面文件的 `airfoil` 数据契约：逐行填写配置翼型目录内的精确 CSV basename，不允许路径、继承或 CLI 后备覆盖。
- [x] 规范版本化输入命名，并纳入 89 截面多翼型回归样例及其三个翼型引用。
- [x] 先构造 `BladeInputPlan`，去重读取唯一翼型并校验整片叶片的后缘拓扑，再进入 CATIA。
- [x] 每个截面按 `airfoil_filename` 选择基准曲线；重复翼型只创建一次 CATIA 基准几何。
- [x] 固定不同点数翼型的 Loft 策略，不要求预先重采样。
  - 2026-08-07 在 CATIA P3 V5-6R2020 中使用 300、253、249 点三个翼型完成 89 截面 Loft、`CloseSurface`、CATPart 保存和 STEP AP242 导出。
  - STEP 包含闭合实体 BREP，命令结束后没有新增残留 `CNEXT` 进程。

## 命令、输入和回归资产契约

- [x] 固定 `create`、`batch` 和未来 `sweep` 的职责：`create` 生成一个明确任务，`batch` 执行 N 个已闭合模型，参数组合只属于未来显式 `sweep`。
- [x] 六列截面模板在非交互 `create` 中必须显式传入 `--airfoil`；七列自包含文件拒绝后备翼型。
- [x] 统一进程退出码：成功为 `0`，领域或执行失败为 `1`，Typer 用法错误为 `2`，用户中断为 `130`。
- [x] 新增 `docs/cli.md`，集中记录参数、交互行为、预览、覆盖规则和退出码。
- [x] 无参数 `autoblade` 在真实 TTY 中进入循环菜单；非 TTY 显示帮助并以 `2` 退出。
- [x] 在 `input/README.md` 中划分示例、真实 CATIA 回归和 pytest 夹具；预期失败 CSV 不进入运行时扫描目录。
- [x] 建立单元、Parser/Planner、mock CATIA 和真实 CATIA 四层回归边界。

## Planner、Job、Executor 与 Adapter 边界

- [x] 引入 `BladeBuildJob` 和 `BuildResult`，由 Planner 在执行前闭合输入、输出和建模选项。
- [x] `create`、`batch` 共享 `core.executor`；单个批任务失败不会阻断后续任务，全部结果都会被保留。
- [x] `batch` 不再执行隐式笛卡尔积。五个六列模板绑定一个显式翼型时精确生成五个稳定排序任务，同批输出冲突在执行前失败。
- [x] CATIA 会话、几何特征、m→mm 换算、保存和导出集中到 `adapters/cad/catia/`；`core` 不直接导入 `pythoncom` 或 `win32com`。
- [x] 顶层包、Parser、Planner 和几何模块可在不加载 COM 的解释器中导入；不可用后端抛出 `CatiaBackendUnavailableError`。

原计划中的独立 `BladeDefinition` 名称已由当前 `BladeInputPlan` 加 `BladeBuildJob` 契约取代，暂不为同一数据再增加并行领域对象。Linux/macOS CI 也不作为当前 Windows/CATIA 产品的 preview wheel 发布阻塞项；现有测试只承诺核心导入和预检逻辑不加载 COM，不承诺跨平台建模。旧 Python 导入路径继续通过薄兼容层转发，在出现真实移除需求前不单独安排弃用迁移。

## 分发工程基础

- [x] 明确首个可分发版本面向受控工程团队，目标制品是内部 `v0.x` preview wheel；公共 PyPI、独立 EXE、`sweep` 和第二 CAD 后端均不是首版承诺。
- [x] 固定已验证支持基线为 Windows 11 x64、CPython 3.14.x x64、`pywin32` 311 和 CATIA P3 V5-6R2020，并明确 CATIA、许可证及 COM 注册属于外部依赖。
- [x] 统一 `pyproject.toml`、`uv.lock` 和运行环境元数据；唯一版本源为 `src/catia_autoblade/__init__.py`。
- [x] 新增 `autoblade --version`，交叉校验源码版本、Git 标签、wheel 和 sdist 元数据。
- [x] 建立 `scripts/check.ps1` 与 Windows GitHub Actions 检查入口，统一执行冻结依赖同步、pytest、Ruff、Hatchling 构建和产物元数据校验。

后续仍需完成工作区初始化、明确构建清单、安装后冒烟、发布/回滚、配置迁移和环境诊断；这些任务保留在根目录 `TODO.md`。
