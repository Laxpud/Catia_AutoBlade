# 项目任务清单

本文件只记录尚未完成的活动工作、优先级和可验证的完成标准。已完成的计划见 [`docs/archive/`](docs/archive/)，其中包括[截至 0.1.1 的里程碑](docs/archive/milestones-through-0.1.1.md)和 [`v0.2.0` 内部 preview wheel 里程碑](docs/archive/internal-preview-wheel-0.2.0.md)；稳定技术契约见 [`docs/index.md`](docs/index.md)。

## 执行与维护规则

- 默认从当前里程碑中第一个未完成任务开始，除非用户指定其他任务。
- 任务的全部验收条件满足后，标记为 `[x]`，并记录完成日期和验证证据；部分完成时保持 `[ ]`。
- 当前里程碑的任务和完成条件全部通过后，将其归档到 `docs/archive/`，并把下一里程碑提升为当前里程碑。
- 验证不足时不得标记完成，也不得降低验收条件。

## 当前状态（2026-08-11）

- 单翼型、展向多翼型、`create`/`batch`、Planner/Executor、CATIA Adapter、COM 清理和无 CATIA 自动化测试基线均已完成。
- `v0.2.0` 内部 preview wheel 已在标签提交 `1d479ff84a9b8e68abfa830a64cd37f42a4f6ce1` 上完成全量检查、非 editable 安装冒烟和真实 CATIA 回归，并生成版本说明、验证记录、SHA-256 与内部发布清单。
- 当前目标是增加职责独立的显式参数扫描 `sweep`；公共 PyPI、独立 EXE 和第二 CAD 后端仍不在当前范围内。

建议执行顺序：先固定 `SweepPlanner` 的输入选择和任务排序，再建立稳定清单与 dry-run，最后接入独立 `sweep` 命令；组合规划测试不得启动 CATIA。

## 当前里程碑：显式参数扫描 `sweep`

- [x] 增加独立的 `sweep` 命令和 `SweepPlanner`，承接显式设计变量组合。（2026-08-12：完成重复 `--airfoil`/`--section`、交互多选、airfoil-major 稳定笛卡尔积、完整预览和共享 Executor 接入；`tests/test_sweep.py` 覆盖 2 × 5 精确生成 10 个任务及额外文件隔离。）
  - 首版只组合用户显式选择的六列截面模板与显式选择的翼型；含 `airfoil` 列的自包含文件不参与外部翼型组合。
  - 验收：2 个翼型与 `section_params-1.csv` 至 `section_params-5.csv` 精确生成 10 个稳定排序的 `BladeBuildJob`，并有不启动 CATIA 的 Planner 自动化测试。
  - 验收：输入目录中额外文件不能静默增加任务；执行前展示选择范围、组合数量、完整任务预览和输出冲突。

- [x] 为扫描任务固定最小组合与清单契约。（2026-08-12：完成 schema version 1 JSON 清单、稳定任务 ID、完整输出路径和 `--dry-run` Executor 前返回；CATIA Builder 未加入组合逻辑。）
  - 首版只实现 Cartesian product；只有出现明确需求后才增加 `zip`、全局缩放、桨距或尖部形状等设计变量。
  - 验收：Planner 输出可序列化为稳定清单，用于 dry-run、黄金任务列表回归和未来调度；CATIA Builder 不包含组合逻辑。

### 当前里程碑完成条件

- [x] `sweep` 只组合显式选择的输入，任务数量和稳定顺序均有自动化回归。（2026-08-12：`tests/test_sweep.py`）
- [x] 任务清单可序列化并能在不启动 CATIA 的 dry-run 中完整展示。（2026-08-12：真实 CLI 2 × 2 dry-run 与自动化零 Executor 断言通过。）
- [x] `create` 和 `batch` 的既有职责、任务语义与回归保持不变。（2026-08-12：全量 136 项无 CATIA 测试通过。）
- [ ] `pwsh -File scripts/check.ps1` 在干净工作区通过。
  - 2026-08-12：当前含既有未提交“真实示例”改动的工作区已通过 136 项测试、Ruff、wheel/sdist、非 editable wheel 冒烟和分发元数据验证；仍需在本轮改动提交后的干净工作区复跑，满足字面验收条件后再归档里程碑。

## 后续里程碑：真实示例与内置翼型目录

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
