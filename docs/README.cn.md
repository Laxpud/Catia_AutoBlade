# CATIA AutoBlade

[English](../README.md) | [简体中文](README.cn.md)

CATIA AutoBlade 是一个 Windows 命令行工具，用于根据翼型点云和沿展向的截面参数，在 CATIA V5 中创建三维叶片模型。程序通过 CATIA COM 自动化接口完成建模，并同时导出原生 `CATPart` 文件和 STEP 模型。

## 当前状态

项目目前处于可工作的早期原型阶段。单翼型流程已经在 CATIA P3 V5-6R2020 环境中成功运行。旧版单翼型批处理仍按翼型与截面参数做笛卡尔积；包含 `airfoil` 列的截面文件则独立定义一个多翼型叶片任务。

逐截面翼型解析、输入校验、唯一基准几何复用和截面选择已经实现。使用三种不同点数翼型的 89 截面样例已在 CATIA P3 V5-6R2020 中完成 Loft、实体封闭、CATPart 保存和 STEP AP242 导出。

稳定单翼型和展向多翼型里程碑均已完成。剩余的工程一致性工作见 [TODO.md](../TODO.md)。

## 功能范围

CATIA AutoBlade 当前提供：

- 根据 CSV 点云创建翼型样条；
- 按截面选择翼型并复用唯一基准几何；
- 截面缩放、平移和扭转；
- 尖后缘和钝后缘处理；
- 带导引线的 Loft 曲面及封闭实体；
- CATIA 原生格式和 STEP 导出；
- 单模型和批处理 CLI 流程。

它不是通用翼型编辑器、气动求解器或跨平台 CAD 后端。

## 环境要求

- Windows
- Python 3.14 或更高版本
- CATIA V5，并且 COM 自动化接口可用
- 使用 [`uv`](https://docs.astral.sh/uv/) 执行文档中的环境管理流程

项目已在 CATIA P3 V5-6R2020 中使用；其他 CATIA V5 版本尚未列为经过验证的环境。

## 安装

```powershell
uv sync
uv pip install -e .
```

## 快速开始

列出可用输入文件：

```powershell
uv run autoblade list
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

创建规划后的批处理任务；旧版截面文件使用所选翼型组合，每个多翼型截面文件只运行一次：

```powershell
uv run autoblade batch --airfoil sc1095.csv
```

为 `create` 或 `batch` 增加 `--interactive` 可通过交互提示选择输入。生成文件使用 `config.toml` 中的目录和命名模板；显式 `--output` 会覆盖配置输出目录。

独立入口接受与对应子命令相同的选项：

```powershell
uv run autoblade-create --airfoil sc1095.csv --section section_params-1.csv
uv run autoblade-batch --airfoil sc1095.csv
```

## 输入概览

默认情况下，翼型 CSV 放在 `input/airfoils/`，截面参数 CSV 放在 `input/section_params/`；两个位置均可配置。坐标、单位、点序、必需字段和当前校验限制见[输入数据格式](input-formats.md)。

## 文档

- [技术文档索引](index.md)
- [架构说明](architecture.md)
- [输入数据格式](input-formats.md)
- [运行时配置](configuration.md)
- [自动化测试](testing.md)
- [活动任务与验收条件](../TODO.md)

## 开发检查

自动化测试使用 COM fake，不要求安装或运行 CATIA：

```powershell
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
```

## 许可证

[MIT](../LICENSE)
