# 自动化测试

项目的 `pytest` 基线不依赖已安装或正在运行的 CATIA。测试仍需 Windows 和项目依赖中的 `pywin32`，但所有 COM 应用创建都由 fake 或 mock 隔离。

## 运行命令

直接安装开发依赖并执行测试：

```powershell
uv run --extra dev pytest -q
```

运行静态检查：

```powershell
uv run --extra dev ruff check src tests
```

也可以先执行一次 `uv sync --extra dev`，之后使用 `uv run pytest -q` 和 `uv run ruff check src tests`。

## 覆盖范围

| 测试模块 | 主要契约 |
| --- | --- |
| `test_input_validation.py` | 翼型和截面 CSV 解析、schema、数值、点序、行号与字段错误定位 |
| `test_input_plan.py` | 单/多翼型模式、受限路径解析、唯一读取、后缘拓扑和 COM 前失败 |
| `test_repository_inputs.py` | 版本化输入命名、89 行多翼型样例、引用完整性与唯一翼型顺序 |
| `test_geometry_math.py` | m/mm 边界、截面缩放以及旋转→缩放→平移顺序 |
| `test_multi_airfoil_geometry.py` | 唯一 CATIA 基准几何创建和逐截面引用编排 |
| `test_runtime_config.py` | 配置路径、文件扫描、CLI 输出覆盖和输出命名 |
| `test_cli.py` | 主命令、独立入口、长短选项与参数分派 |
| `test_catia_lifecycle.py` | COM 初始化、文档关闭、应用退出、异常清理和批处理隔离 |

`tests/conftest.py` 在每个测试中禁止调用真实 `win32com.client.Dispatch` 和 `DispatchEx`。如果未来新增代码绕过 mock 并尝试启动 CATIA，测试会立即失败，而不是在开发机上留下隐藏进程。

## 自动化与真实 CATIA 的边界

自动化测试验证 Python 领域逻辑、参数契约和 COM 生命周期编排，但不会验证 CATIA 的样条拟合、Loft 或 `CloseSurface` 几何结果。涉及真实几何内核的回归仍需使用代表性输入执行 CLI，并检查：

- `.CATPart` 和 `.stp` 均成功生成；
- CATIA 特征树和实体几何符合预期；
- 命令结束后没有新增的 `CNEXT` 进程残留。

真实 CATIA 冒烟测试不属于默认 `pytest` 套件，以免自动化检查依赖许可证、桌面会话或特定 CATIA 版本。

2026-08-07 已使用 CATIA P3 V5-6R2020 对 `section_params-multi-airfoil.csv` 执行真实回归：三个不同点数翼型完成 89 截面 Loft 和实体封闭，CATPart 与 STEP AP242 均成功输出；STEP 包含闭合实体 BREP，命令结束后没有残留 `CNEXT` 进程。详细记录见[展向多翼型设计](multi-airfoil-design.md)。
