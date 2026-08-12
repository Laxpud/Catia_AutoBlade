# 项目任务清单

本文件只记录尚未完成的活动工作、优先级和可验证的完成标准。已完成的计划见 [`docs/archive/`](docs/archive/)，其中包括[截至 0.1.1 的里程碑](docs/archive/milestones-through-0.1.1.md)、[`v0.2.0` 内部 preview wheel 里程碑](docs/archive/internal-preview-wheel-0.2.0.md)和[显式参数扫描 `sweep` 里程碑](docs/archive/explicit-parameter-sweep.md)；稳定技术契约见 [`docs/index.md`](docs/index.md)。

## 执行与维护规则

- 默认从当前里程碑中第一个未完成任务开始，除非用户指定其他任务。
- 任务的全部验收条件满足后，标记为 `[x]`，并记录完成日期和验证证据；部分完成时保持 `[ ]`。
- 当前里程碑的任务和完成条件全部通过后，将其归档到 `docs/archive/`，并把下一里程碑提升为当前里程碑。
- 验证不足时不得标记完成，也不得降低验收条件。

## 当前状态（2026-08-12）

- 单翼型、展向多翼型、`create`/`batch`、Planner/Executor、CATIA Adapter、COM 清理和无 CATIA 自动化测试基线均已完成。
- `v0.2.0` 内部 preview wheel 已在标签提交 `1d479ff84a9b8e68abfa830a64cd37f42a4f6ce1` 上完成全量检查、非 editable 安装冒烟和真实 CATIA 回归，并生成版本说明、验证记录、SHA-256 与内部发布清单。
- 显式参数扫描 `sweep` 已在提交 `ba7e647` 完成，具备稳定 Cartesian product、JSON 清单和无 CATIA dry-run；提交后的干净工作区通过 136 项测试、Ruff、构建、安装冒烟和分发校验。
- 当前目标是完成真实示例与内置翼型目录的来源审计、资源边界和真实 CATIA 验收；公共 PyPI、独立 EXE 和第二 CAD 后端仍不在当前范围内。

建议执行顺序：先完成真实示例及其三个依赖翼型的脱敏与来源确认，再建立完整内置翼型目录及清单，最后固定目录版本边界并评估 `section_params` 命名迁移。

已完成的 `sweep` 任务、验收条件和最终验证证据见[归档记录](docs/archive/explicit-parameter-sweep.md)。

## 当前里程碑：真实示例与内置翼型目录

- [ ] 用一套可公开分发的真实桨叶参数替换当前人工构造的两截面示例。
  - 示例数据源已确定为 `input/section_params/section_params-multi-airfoil.csv`；wheel 内以 `example-section-params.csv` 提供，并同时携带其引用的三个翼型。
  - 示例必须完成脱敏和来源确认；入口截面文件采用 `example-...` 前缀，依赖翼型保留可跨示例复用的稳定翼型 ID。它只承担最短教学路径，不混入密集点云、零位移等维护者回归资产。
  - 验收：`autoblade init --with-examples` 生成一个能够直接预检的工作区，并在受支持 CATIA 环境完成 Loft、实体封闭、CATPart 和 STEP 输出。

- [ ] 在 wheel 中建立独立的内置翼型目录，纳入通过来源与再分发许可审计的现有翼型数据。
  - 每个翼型记录稳定 ID、来源、许可证或再分发授权、是否修改、修改说明、点数和 SHA-256；来源或授权不明确的数据不得进入 wheel。
  - `autoblade init --with-examples` 只复制真实示例及其依赖翼型；新增 `--with-airfoil-library` 显式复制完整内置翼型目录，不把 `input/` 下的维护者回归资产整体复制给用户。
  - 验收：wheel 内容清单、全新环境安装冒烟和工作区覆盖保护覆盖全部新增资源；安装、升级和卸载均不修改已经复制到外部工作区的用户数据。

- [ ] 为持续增长的翼型目录固定版本与拆包边界。
  - 短期随 `catia-autoblade` wheel 发布；只有当数据更新明显独立于程序、规模显著增长或许可证需要隔离时，才评估拆分独立数据包。
  - 验收：同一软件版本内置目录可按清单复现；增加、修改或删除翼型都必须经过来源审计、数据校验和发布说明。

- [ ] 评估将用户可见的 `section_params` 命名迁移为 `blade_sections`。
  - `blade_sections` 更准确地表达“一份 CSV 描述一片桨叶的展向截面布置”；内部单行对象仍称 `section`，避免把文件和单个截面混为一谈。
  - 验收：先盘点目录名、配置键、CLI 文案、Python API、输出命名和历史工作区的兼容影响，再设计带警告和迁移期的方案；在兼容方案完成前保留现有 `section_params` 契约，不做破坏性改名。

## 条件性长期方向

- [ ] 仅在确认无 Python 用户的真实需求后评估独立 Windows 可执行程序。
  - 验收：比较 PyInstaller 与 Nuitka，优先验证可诊断的 one-folder 原型及 `pythoncom`、`pywintypes`、`win32com.client`、Questionary 和 Typer 资源完整性。
  - 验收：配置和输入继续作为外部工作区管理，并在没有开发环境的目标 CATIA 机器上验证安装、建模、升级、卸载、杀毒软件影响和可选代码签名。

- [ ] 仅在出现第二个真实建模后端需求时抽象公共 Builder 接口并评估独立分包。
  - 候选方向包括 NX、FreeCAD、OpenCascade 或直接网格输出；当前不创建空 Adapter、插件系统或过早稳定的公共 CAD API。
  - 验收：新后端复用现有已校验任务和后端无关几何契约，平台特有能力保留在各自 Adapter 内。
  - 验收：第二后端落地后再评估平台无关核心包、`catia-autoblade` 与其他 Adapter 包的依赖和发布边界。

## 维护规则

- 完成任务时将其标记为 `[x]`，补充完成日期和可复查证据，例如测试、产物检查或真实 CATIA 记录。
- 一个里程碑全部完成后，将详细记录移入 `docs/archive/`，根 `TODO.md` 只保留简短状态和下一阶段工作。
- 新任务必须给出可验证的验收条件；稳定设计说明进入 `docs/`，不要在 TODO 中长期复制实现细节。
