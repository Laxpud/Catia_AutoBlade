# 真实示例与内置翼型目录里程碑

本记录归档 2026-08-12 完成的“真实示例与内置翼型目录”里程碑。该里程碑
建立可公开再分发的真实教学示例、独立的已审计翼型目录及其版本边界，并完成
`section_params` 用户可见命名的兼容迁移评估。

## 可分发真实示例

- [x] 使用 `input/section_params/section_params-multi-airfoil.csv` 对应的真实桨叶参数，
  替换 wheel 中原先人工构造的两截面示例。
- [x] `autoblade init --with-examples` 只复制 `example-section-params.csv` 及其引用的
  `airfoil1_sharp.csv`、`airfoil2_sharp.csv`、`airfoil3_sharp.csv`，不复制维护者回归
  资产。
- [x] 截面参数和三个翼型均完成来源、授权、脱敏边界、修改记录、点数和 SHA-256
  审计；作者为 Hannnk，维护者已取得作者直接再分发授权。
- [x] 初始化资源与仓库输入逐记录内容一致，并通过固定 LF 获得跨平台可复现摘要。

来源身份、授权范围、修改说明和逐文件摘要见[真实示例数据审计](../example-data-audit.md)。

## 独立内置翼型目录

- [x] 在 wheel 中建立独立 `catia_autoblade/resources/airfoil_library/`，首版只纳入
  三个来源与再分发授权明确的 Hannnk 翼型。
- [x] `manifest.json` 使用稳定 ID，并记录来源、授权、是否修改、修改说明、点数和
  实际分发 SHA-256；初始化器在写用户工作区前校验清单、包内文件集合和摘要。
- [x] `autoblade init --with-airfoil-library` 显式复制完整已审计目录，不复制截面示例；
  与 `--with-examples` 并用时对共同翼型去重。
- [x] 受管理文件遵守覆盖保护；安装、升级或卸载 wheel 不修改已经复制到外部工作区
  的用户数据。
- [x] 未审计的 `sc1095*`、`sd7032_sharp`、`naca0012_sharp` 和 1,000 点密集回归
  资产继续留在 wheel 目录之外。

清单语义、初始化行为和资产排除边界见[内置翼型目录](../airfoil-library.md)。

## 版本与拆包边界

- [x] 内置目录随 `catia-autoblade` 包版本发布，不建立独立数据版本；清单
  `schema_version` 只表示清单结构。
- [x] 同一包版本的目录内容由 wheel、精确条目集合和逐文件 SHA-256 共同固定。
- [x] 增加、修改或删除翼型必须同步来源授权、数据校验、未发布说明和适用的真实
  CATIA 回归。
- [x] 只有数据更新节奏明显独立、分发体积显著增长或许可证需要隔离时，才重新评估
  拆分独立数据包。

## `section_params` 命名评估

- [x] 盘点工作区目录、配置 schema、CLI 与初始化行为、Python API、`sweep` JSON、
  输出命名和历史工作区记录。
- [x] 确认 `blade_sections` 更适合作为文件集合概念，但当前版本继续保留
  `input/section_params/`、`paths.section_params_dir` 和全部既有接口。
- [x] 未来方案要求配置 schema 与 Python 别名兼容、每次命令至多一次警告、显式且
  可回滚的工作区目录迁移，以及至少一个完整 preview 发布周期。
- [x] CLI `--section`、输出模板 `{section}`/`{blade}`、单行 `section`、既有 CSV
  basename 和历史记录不随集合目录改名。

完整影响面和分阶段方案见[`section_params` 命名迁移评估](../blade-sections-migration.md)。

归档后维护者确认项目尚未大规模使用，原先的兼容期建议被直接迁移决定取代；当前
契约和旧工作区操作以[`section_params` → `blade_sections` 命名迁移](../blade-sections-migration.md)
为准。本节保留原结论，用于说明里程碑完成时的决策历史。

## 验证证据

- [x] 2026-08-12 通过 138 项 pytest 和 Ruff。
- [x] wheel 与 sdist 构建、分发内容校验以及全新非 editable wheel 安装冒烟通过；
  冒烟分别覆盖示例工作区和仅内置翼型目录工作区。
- [x] 自动化覆盖示例依赖、完整目录、两种初始化选项并用、清单与包资源双向一致、
  摘要、点数和受管理文件覆盖保护。
- [x] 2026-08-07 已在 CATIA P3 V5-6R2020 使用同一 89 截面记录和三个翼型完成 Loft、
  `CloseSurface`、CATPart 与 STEP AP242 输出，命令结束后没有残留 `CNEXT` 进程。
- [x] 命名评估使用仓库级检索覆盖源代码、测试、配置、脚本、当前文档和归档；本里程碑
  未移动用户数据或实施破坏性命名变更。

真实 CATIA 回归没有因打包目录调整重复执行：本里程碑复制的数值记录与上述已验证输入
逐记录一致，新增行为位于初始化、清单校验和分发边界，均由无 COM 自动化与安装冒烟
覆盖。
