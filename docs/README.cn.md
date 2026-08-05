# CATIA AutoBlade

[English](../README.md) | [简体中文](README.cn.md)

CATIA AutoBlade 是一个 Windows 命令行工具，用于根据翼型点云和沿展向的截面参数，在 CATIA V5 中创建三维叶片模型。程序通过 CATIA COM 自动化接口完成建模，并同时导出原生 `CATPart` 文件和 STEP 模型。

## 当前状态

项目目前处于可工作的早期原型阶段。单翼型流程已经在 CATIA P3 V5-6R2020 环境中成功运行；批处理支持对翼型文件和截面参数文件执行笛卡尔积组合建模。

当前实现要求一片叶片的所有截面使用同一个翼型。较新输入数据中出现的可选 `airfoil` 列尚未用于逐截面选择翼型。

当前里程碑是在扩展几何模型之前，使现有单翼型流程可重复、可配置并具备可靠的资源清理。活动任务和验收条件见 [TODO.md](../TODO.md)。

## 功能范围

CATIA AutoBlade 当前提供：

- 根据 CSV 点云创建翼型样条；
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

创建所有选定组合：

```powershell
uv run autoblade batch --airfoil sc1095.csv
```

为 `create` 或 `batch` 增加 `--interactive` 可通过交互提示选择输入。未指定 `--output` 时，生成文件写入 `output/`。

独立入口接受与对应子命令相同的选项：

```powershell
uv run autoblade-create --airfoil sc1095.csv --section section_params-1.csv
uv run autoblade-batch --airfoil sc1095.csv
```

## 输入概览

翼型 CSV 放在 `input/airfoils/`，截面参数 CSV 放在 `input/section_params/`。坐标、单位、点序、必需字段和当前校验限制见[输入数据格式](input-formats.md)。

## 文档

- [技术文档索引](index.md)
- [架构说明](architecture.md)
- [输入数据格式](input-formats.md)
- [活动任务与验收条件](../TODO.md)

## 许可证

[MIT](../LICENSE)
