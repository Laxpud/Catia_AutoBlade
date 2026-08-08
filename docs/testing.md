# 自动化测试

项目的 `pytest` 基线不依赖已安装或正在运行的 CATIA。核心导入、CSV、Planner 和坐标测试不需要 `pywin32`；完整测试矩阵在 Windows 上运行，并用 fake 或 mock 隔离所有 COM 应用创建。

## 运行命令

常规开发和发布前检查统一使用一个入口：

```powershell
pwsh -File scripts/check.ps1
```

该脚本按顺序执行冻结锁文件同步、pytest、Ruff、Hatchling wheel/sdist 构建和实际产物 `METADATA`/`PKG-INFO` 校验。`.github/workflows/checks.yml` 在 Windows CI 中调用同一脚本，不维护另一套命令。正式版本标签构建还应使用：

```powershell
pwsh -File scripts/check.ps1 -RequireTag
```

`-RequireTag` 要求当前提交存在与 `src/catia_autoblade/__init__.py` 相同的 `0.1.1` 或 `v0.1.1` 标签。普通开发检查允许尚未打标签，但发现不一致的版本标签仍会失败。

排查单个阶段时可分别使用 `uv run --extra dev pytest -q`、`uv run --extra dev ruff check src tests scripts`、`uv build` 和 `uv run python scripts/validate_distribution.py`。这些命令是诊断入口，完整验收仍以 `scripts/check.ps1` 为准。

## 分层回归策略

| 层级 | 自动化范围 | 能发现的问题 | 不能替代的检查 |
| --- | --- | --- | --- |
| 单元层 | m/mm 单位、旋转、缩放、平移、零位移和输出命名 | 数学顺序、符号、单位边界和纯函数回归 | CATIA 特征是否可更新 |
| Parser / Planner 层 | CSV schema、跨文件引用闭合、`BladeBuildJob` 列表和输出冲突 | 缺文件、非法字段、任务数量、隐式组合和 COM 前失败 | Loft 的真实几何质量 |
| mock CATIA 层 | 唯一基准几何复用、调用顺序、异常清理和批任务隔离 | COM 编排、重复创建、资源泄漏路径 | CATIA 内核的样条、Loft、`CloseSurface` 结果 |
| 真实 CATIA 层 | 版本化代表输入的人工冒烟与回归 | 几何内核、特征树、实体封闭、格式导出和真实进程残留 | 不进入默认 `pytest`，不能作为低成本提交前检查 |

pytest 专用预期失败数据不得放入 `input/` 扫描目录。当前小型测试全部使用 `tmp_path` 构造；未来出现跨模块共享的大型固定夹具时再创建 `tests/fixtures/`。版本化输入的分类和推荐命令见 [`input/README.md`](../input/README.md)。

## 覆盖范围

| 测试模块 | 主要契约 |
| --- | --- |
| `test_input_validation.py` | 翼型和截面 CSV 解析、schema、数值、点序、行号与字段错误定位 |
| `test_input_plan.py` | 单/多翼型模式、受限路径解析、唯一读取、后缘拓扑和 COM 前失败 |
| `test_job_planner.py` | `BladeBuildJob` 输入闭合、稳定排序、无笛卡尔积、输出冲突和共享 Executor |
| `test_repository_inputs.py` | 版本化输入命名、89 行多翼型样例、引用完整性与唯一翼型顺序 |
| `test_geometry_math.py` | m/mm 边界、截面缩放以及旋转→缩放→平移顺序 |
| `test_multi_airfoil_geometry.py` | 唯一 CATIA 基准几何创建和逐截面引用编排 |
| `test_platform_boundary.py` | 核心无 COM 导入、全新解释器导入和不可用 CATIA 后端能力错误 |
| `test_runtime_config.py` | 配置路径、文件扫描、CLI 输出覆盖和输出命名 |
| `test_cli.py` | 主命令、独立入口、长短选项与参数分派 |
| `test_catia_lifecycle.py` | COM 初始化、文档关闭、应用退出、异常清理和批处理隔离 |

`tests/conftest.py` 在已安装 `pywin32` 时禁止调用真实 `win32com.client.Dispatch` 和 `DispatchEx`。如果未来新增代码绕过 mock 并尝试启动 CATIA，测试会立即失败，而不是在开发机上留下隐藏进程。静态与全新解释器测试同时阻止核心层重新引入 COM 导入。

预览支持组合及验证日期维护在[分发范围与支持策略](distribution-scope.md)的兼容性表中。仅有 pytest 通过不能扩大 CATIA 支持矩阵。

## 自动化与真实 CATIA 的边界

自动化测试验证 Python 领域逻辑、参数契约和 COM 生命周期编排，但不会验证 CATIA 的样条拟合、Loft 或 `CloseSurface` 几何结果。涉及真实几何内核的回归仍需使用代表性输入执行 CLI，并检查：

- `.CATPart` 和 `.stp` 均成功生成；
- CATIA 特征树和实体几何符合预期；
- 命令结束后没有新增的 `CNEXT` 进程残留。

真实 CATIA 冒烟测试不属于默认 `pytest` 套件，以免自动化检查依赖许可证、桌面会话或特定 CATIA 版本。每次人工回归至少记录：

```text
date:
command:
Windows / Python / pywin32:
CATIA version and configuration:
input model:
CATPart result:
STEP result and topology:
feature-tree / geometry observations:
new CNEXT processes after exit:
```

2026-08-07 已使用 CATIA P3 V5-6R2020 对 `section_params-multi-airfoil.csv` 执行真实回归：三个不同点数翼型完成 89 截面 Loft 和实体封闭，CATPart 与 STEP AP242 均成功输出；STEP 包含闭合实体 BREP，命令结束后没有残留 `CNEXT` 进程。详细记录见[展向多翼型设计](multi-airfoil-design.md)。
