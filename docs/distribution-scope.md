# 首个可分发版本的范围与支持策略

本文固定 AutoBlade 首个可分发版本的目标用户、交付渠道、支持基线和外部依赖边界。这里的“支持”只表示项目会针对已验证组合维护和排查缺陷，不表示提供 CATIA、许可证、操作系统或企业级服务承诺。

## 目标用户与使用边界

首个可分发版本定义为面向内部或受控协作团队的 `v0.x` 预览 wheel。目标用户是已经使用 CATIA V5 开展叶片建模、能够使用 PowerShell、Python 和 `uv`、并能自行检查 CATIA 特征树与导出结果的工程人员或自动化维护者。

首个预览版本不面向以下场景：

- 没有 Python 环境、要求图形安装器或独立 EXE 的普通桌面用户；
- 没有 CATIA V5 本体、适用许可证或可用 COM 注册环境的机器；
- 要求在 Linux、macOS、Windows on ARM 或无交互桌面服务器上生成最终 CAD 模型；
- 需要 NX、FreeCAD、OpenCascade 等其他 CAD 后端或稳定插件 API 的集成方；
- 需要气动求解、通用翼型编辑、计算集群调度或发布级 SLA 的工作流。

## 分发路线

首个可分发制品是内部预览 wheel，而不是公共 PyPI 包或独立 EXE。仓库已经提供
显式构建清单、外部工作区初始化、全新环境安装冒烟、真实 CATIA 候选验证和内部
发布 manifest 工具；某个具体版本只有在干净标签提交上生成完整制品集后才成为
受支持的内部交付物。没有标签、SHA-256 或验证记录的临时 wheel 仍属于开发产物。

| 阶段 | 状态 | 制品与渠道 | 进入下一阶段的条件 |
| --- | --- | --- | --- |
| 源码预览 | 开发支持 | 从受控 Git 仓库 checkout，使用 `uv` 创建环境并执行命令 | 继续通过统一仓库检查 |
| 内部 wheel | 受控发布流程已定义 | 整体提供 wheel、sdist、说明、SHA-256、manifest 和验证记录 | 每个标签候选均完成全新环境与真实 CATIA 回归 |
| 发布候选 | 后续验证 | GitHub Release 附带 wheel、sdist、校验和与说明；TestPyPI 只验证索引安装链路 | 版本、回滚、凭据和重复构建流程稳定 |
| 公共发布 | 尚未决定 | 公共 PyPI | 有明确外部用户、名称可用且支持成本可承担 |
| 独立 EXE | 延后评估 | Windows one-folder 或安装包 | 已确认目标用户确实不能使用 Python/`uv` |

GitHub Release、TestPyPI 和公共 PyPI 在完成对应发布里程碑前都不是当前安装渠道。不得在 README、包元数据或对外说明中把计划中的渠道描述成已经可用。

## 预览支持基线

当前只对下表组合做预览支持承诺。支持范围不是根据依赖元数据推断出来的；没有列出的版本和架构均视为未验证，而不是默认兼容。表中的 Windows build 和 Python 补丁版本是当前验证点，支持范围则以同一行的 Windows 和 Python 系列为准。

| 组成 | 预览支持范围 | 验证证据 |
| --- | --- | --- |
| 操作系统 | Windows 11 x64 | 开发环境于 2026-08-08 报告 build `10.0.26200.8875`、`AMD64` |
| Python | CPython 3.14.x x64 | 开发与自动化环境于 2026-08-08 使用 Python `3.14.4` |
| CATIA Python 桥接 | `pywin32` 311 | 锁文件和当前虚拟环境均使用 311；该版本提供 CPython 3.14 wheel |
| CAD | CATIA P3 V5-6R2020 | 2026-08-07 完成 89 截面多翼型 Loft、`CloseSurface`、CATPart 保存和 STEP AP242 导出 |
| CATIA 运行条件 | 可启动独占 `CATIA.Application` 的已注册 COM Automation 环境，并具有建模和导出所需许可证 | 2026-08-11 候选 wheel 回归完成 CATPart 关键特征、STEP 固体 BREP 和零新增 `CNEXT` 检查 |

`pyproject.toml` 已将 `requires-python` 固定为 `>=3.14,<3.15`，声明 Windows 与
Linux classifier，并只在 Windows 上要求 `pywin32==311`。Linux 声明目前只覆盖
wheel 安装、核心导入和无 CAD 规划路径，不扩大真实建模支持矩阵。Windows 10、
Windows on ARM、Python 3.15 及更高版本、其他 `pywin32` 或 CATIA V5 版本只有在
记录验证结果后才能加入支持范围。

## 包标识、作者与版本来源

- 规范 distribution 和 Python namespace 均为 `autoblade`；不提供旧
  `catia_autoblade` shim。旧 `catia-autoblade` 与新包共存时程序会明确要求先
  卸载旧包。公共 PyPI 名称可用性与注册尚未评估，也不是当前渠道。
- `pyproject.toml` 的 `authors` 保留现有包联系人 `Laxpud <mi.shore@foxmail.com>`；MIT `LICENSE` 独立记录版权人为 `YangFan`。包联系人和版权声明承担不同角色，本次不把两者推断为同一身份，也不擅自改写版权归属。
- 唯一版本源是 `src/autoblade/__init__.py` 的 `__version__`。`autoblade --version`、wheel、sdist 和当前提交上的版本标签由 `scripts/validate_distribution.py` 交叉校验；仓库目前尚无发布标签，正式标签检查必须显式使用 `-RequireTag`。

## 分发物与外部依赖边界

源码或 wheel 只负责交付 AutoBlade 的 Python 代码、包元数据和
`autoblade init` 明确纳入清单的不可变示例和已审计翼型目录资源。Hatchling wheel 只包含
`autoblade` 包与这些资源；sdist 使用显式白名单交付重建 wheel 所需的
源码、测试、锁文件、许可证、构建脚本、文档和版本化回归输入。产物校验会拒绝
输出、缓存、虚拟环境、日志、CATPart、STEP、绝对开发机路径和未知归档根目录。

Python 包管理器可以根据包元数据安装 `pywin32`、Typer、Questionary、Pydantic
和 Tomlkit，但这些 Python 依赖不提供 CATIA 能力。工作区始终由用户在
`site-packages` 外显式初始化；安装、升级或卸载包不会删除配置、输入和输出。

以下内容必须由使用者或其组织另行安装、授权和维护，不属于本项目分发物：

- Windows 和受支持的 CPython；
- `uv` 或其他安装工具；
- CATIA V5 本体、修订包、配置和许可证；
- CATIA COM 服务器注册、桌面会话、用户权限及企业安全策略；
- 用户自己的 `config.toml`、翼型、截面参数、输出模型和失败现场；
- 第三方格式验证器、归档、备份、签名和许可证服务器基础设施。

安装 Python 依赖成功不代表 CATIA 环境可用。真实建模前仍需验证 COM 初始化、CATIA 启动、许可证、输出目录写入以及 CATPart/STEP 导出。

## 首个预览版本承诺的能力

首个预览版本只承诺已经由当前自动化测试和真实 CATIA 回归覆盖的能力：

- `create` 从一个明确的六列模板加显式翼型，或一个自包含多翼型截面文件，生成一个叶片任务；
- `batch` 对多个已经闭合输入引用的模型定义逐项执行，不做隐式笛卡尔积；
- `sweep` 只对显式选择的翼型与六列模板生成笛卡尔积，并支持无 CATIA dry-run；
- 在启动 CATIA 前完成 CSV、跨文件引用、后缘拓扑和输出冲突校验；
- 创建尖后缘或钝后缘翼型、变换截面、带前后缘导引线的 Loft 和封闭实体；
- 保存 CATPart、导出 STEP、报告稳定退出码，并在成功或失败路径清理独占 CATIA 会话；
- 保持单翼型、多翼型、密集点云、不同点数翼型和零位移版本化样例的既有回归结果。

第二 CAD 后端、跨平台 CATIA 建模、插件系统和独立 EXE 当前仍不是已发布能力；
只有实现并形成独立验证证据后才能进入支持范围。

## 支持范围变更规则

新增支持组合时，应同时记录 Windows build、CPU 架构、Python、`pywin32`、CATIA 版本/配置、验证日期、代表输入、CATPart/STEP 结果和进程清理结果。仅通过单元测试、依赖解析或成功导入模块，不能把新的 CATIA 组合标记为已支持。

安装和升级步骤见[安装、工作区与升级](installation.md)，标签、验证记录、制品集
和回滚门槛见[内部 preview 发布与回滚](releasing.md)。
