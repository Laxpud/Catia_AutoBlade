# CATIA AutoBlade

[English](../README.md) | [简体中文](README.cn.md)

CATIA AutoBlade 是一个 Windows 命令行工具，用于根据翼型点云和沿展向的截面参数，在 CATIA V5 中创建三维叶片模型。程序通过 CATIA COM 自动化接口完成建模，并同时导出原生 `CATPart` 文件和 STEP 模型。

## 当前状态

项目目前处于可工作的早期原型阶段。单翼型流程已经在 CATIA P3 V5-6R2020 环境中成功运行。六列截面文件是需要显式绑定一个翼型的模板；包含 `airfoil` 列的截面文件则独立定义一个自包含多翼型模型。批处理为每个选中的截面定义创建一个任务，不执行隐式参数组合。独立的 `sweep` 流程只对用户显式选择的翼型和六列模板执行笛卡尔积。

逐截面翼型解析、输入校验、唯一基准几何复用和截面选择已经实现。使用三种不同点数翼型的 89 截面样例已在 CATIA P3 V5-6R2020 中完成 Loft、实体封闭、CATPart 保存和 STEP AP242 导出。

稳定单翼型和展向多翼型里程碑均已完成。仓库现已提供可审计的 wheel/sdist 清单、外部工作区初始化、全新环境 wheel 冒烟、配置迁移保护、环境诊断和带门槛的内部发布流程。某个具体 wheel 只有作为带标签、SHA-256 和真实 CATIA 验证证据的完整制品集交付时才属于受支持内部版本。目前不支持公共包索引或独立可执行程序。边界见[分发范围与支持策略](distribution-scope.md)。

## 功能范围

CATIA AutoBlade 当前提供：

- 根据 CSV 点云创建翼型样条；
- 按截面选择翼型并复用唯一基准几何；
- 截面缩放、平移和扭转；
- 尖后缘和钝后缘处理；
- 带导引线的 Loft 曲面及封闭实体；
- CATIA 原生格式和 STEP 导出；
- 单模型、非组合式批处理和显式参数扫描 CLI 流程；
- 稳定 JSON 扫描清单以及不启动 CATIA 的 dry-run。

它不是通用翼型编辑器、气动求解器或跨平台 CAD 后端。

## 环境要求

- Windows 11 x64
- CPython 3.14 x64；当前已验证解释器为 Python 3.14.4
- `pywin32` 311
- CATIA P3 V5-6R2020，并且 COM 自动化接口和所需许可证可用
- 使用 [`uv`](https://docs.astral.sh/uv/) 执行文档中的环境管理流程

这是当前唯一经过验证的预览支持基线。其他 Windows、Python、`pywin32`、处理器架构和 CATIA 组合均属于未验证范围，不会被默认视为受支持。CATIA 本体、许可证和 COM 注册环境是外部前置条件，不包含在本项目中。证据与渠道边界见[分发范围与支持策略](distribution-scope.md)。

可在 Windows 上通过 WinGet 安装 `uv`：

```powershell
winget install --id=astral-sh.uv -e
```

## 安装

经过授权的内部预览制品通过版本化 wheel 直接安装。安装前应核对随制品提供的 SHA-256：

```powershell
uv venv .venv --python 3.14
uv pip install --python .venv\Scripts\python.exe .\catia_autoblade-0.2.0-py3-none-any.whl
.\.venv\Scripts\Activate.ps1
autoblade init C:\Engineering\blade-workspace --with-examples
```

`--with-examples` 会把已验证的 89 截面多翼型真实桨叶示例及其引用的三个翼型复制到外部工作区。

当前不支持公共 PyPI 安装。维护者从源码 checkout 开发时使用：

```powershell
uv sync
uv pip install -e .
```

完整的安装、工作区、升级、卸载和回滚流程见[安装、工作区与升级](installation.md)。

## 快速开始

在交互终端中打开菜单：

```powershell
uv run autoblade
```

脚本调用可先列出可用输入文件：

```powershell
uv run autoblade list
```

在不启动或连接 CATIA 的前提下诊断安装环境：

```powershell
uv run autoblade doctor
```

创建一个叶片：

```powershell
uv run autoblade create --airfoil sc1095.csv --section section_params-1.csv
```

不传后备 `--airfoil`，直接创建仓库中的多翼型样例：

```powershell
uv run autoblade create --section section_params-multi-airfoil.csv
```

建模失败时可使用 `--keep-failed-part` 保留 `*_failed.CATPart` 以便排查。

构建扫描到的所有截面定义；显式翼型统一绑定六列模板，自包含文件保留逐截面引用：

```powershell
uv run autoblade batch --airfoil sc1095.csv
```

在不启动 CATIA 的前提下预览一个显式 2 × 2 笛卡尔积：

```powershell
uv run autoblade sweep --airfoil sc1095.csv --airfoil sd7032_sharp.csv `
  --section section_params-1.csv --section section_params-2.csv --dry-run
```

详细参数、交互行为、独立兼容入口、任务预览、覆盖规则和退出码见 [CLI 参考](cli.md)。

## 输入概览

默认情况下，翼型 CSV 放在 `input/airfoils/`，截面参数 CSV 放在 `input/section_params/`；两个位置均可配置。坐标、单位、点序、必需字段和当前校验限制见[输入数据格式](input-formats.md)。

## 文档

- [技术文档索引](index.md)
- [CLI 参考](cli.md)
- [设计原则](design-principles.md)
- [架构说明](architecture.md)
- [输入数据格式](input-formats.md)
- [运行时配置](configuration.md)
- [安装、工作区与升级](installation.md)
- [分发范围与支持策略](distribution-scope.md)
- [内部 preview 发布与回滚](releasing.md)
- [自动化测试](testing.md)
- [活动任务与验收条件](../TODO.md)

## 开发检查

自动化测试使用 COM fake，不要求安装或运行 CATIA：

```powershell
pwsh -File scripts/check.ps1
```

该统一入口执行 pytest、Ruff、wheel/sdist 构建和分发元数据校验；单项诊断及版本标签检查见[自动化测试](testing.md)。

## 许可证

[MIT](../LICENSE)
