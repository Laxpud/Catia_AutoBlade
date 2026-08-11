# 项目任务清单

本文件只记录尚未完成的活动工作、优先级和可验证的完成标准。已经完成或被当前架构取代的计划见 [`docs/archive/milestones-through-0.1.1.md`](docs/archive/milestones-through-0.1.1.md)，稳定技术契约见 [`docs/index.md`](docs/index.md)。

## 执行与维护规则

- 默认从当前里程碑中第一个未完成任务开始，除非用户指定其他任务。
- 任务的全部验收条件满足后，标记为 `[x]`，并记录完成日期和验证证据；部分完成时保持 `[ ]`。
- 当前里程碑的任务和完成条件全部通过后，将其归档到 `docs/archive/`，并把下一里程碑提升为当前里程碑。
- 验证不足时不得标记完成，也不得降低验收条件。

## 当前状态（2026-08-11）

- 单翼型、展向多翼型、`create`/`batch`、Planner/Executor、CATIA Adapter、COM 清理和无 CATIA 自动化测试基线均已完成。
- `scripts/check.ps1` 已能执行冻结依赖同步、pytest、Ruff、wheel/sdist 构建和产物元数据校验。
- 工作区初始化、可审计构建、非 editable 安装冒烟、配置迁移、环境诊断和内部发布工具已经实现；仓库仍无发布标签或已批准内部制品集。
- 2026-08-11 的 dirty-worktree 候选 wheel 已在支持基线上完成 89 截面真实 CATIA 回归；最终提交和标签必须重新生成干净验证记录后才能发布。
- 当前目标是把本里程碑改动提交并在唯一版本标签上生成内部 `v0.x` preview 制品集，不把公共 PyPI、独立 EXE、`sweep` 或第二 CAD 后端纳入首版阻塞项。

建议执行顺序：工作区初始化 → 构建清单 → 安装产物冒烟 → 内部发布流程；配置迁移和环境诊断可在前三项接口稳定后并行推进。

## 当前里程碑：可安装的内部 preview wheel

### P0：工作区初始化与配置发现

- [x] 增加 `autoblade init`，让已安装的 wheel 能创建独立、可编辑的建模工作区。
  - 验收：命令只在显式目标目录创建 `config.toml`、`input/airfoils/`、`input/section_params/` 和 `output/`，并可选择复制最小示例。
  - 验收：已存在文件默认不覆盖；只有显式 `--force` 或交互确认才允许替换，并在执行前展示受影响路径。
  - 验收：明确并测试配置发现优先级，覆盖显式配置路径、当前工作区配置、用户级配置和内置默认值；不得因启动目录不同而静默读取错误工作区。
  - 验收：包内只保存不可变模板资源；用户配置、输入和输出始终位于 `site-packages` 之外，安装、升级和卸载不得删除用户工作区。
  - 验收：新增 CLI、配置路径、无配置、重复初始化和只读目标目录测试，不启动真实 CATIA。
  - 实现记录（2026-08-11）：显式目标初始化会预览全部计划，只覆盖 `--force` 或交互确认的受管理模板；wheel 资源与用户工作区隔离。全新安装冒烟已从包资源创建工作区并完成输入预检和 fake Builder 执行。

### P0：可审计的构建内容

- [x] 固定 Hatchling wheel 与 sdist 文件清单，避免构建结果受本地临时文件影响。
  - 验收：在 `pyproject.toml` 中明确 wheel/sdist 的 include 与 exclude；输出、失败快照、缓存、虚拟环境、私有/客户数据和未授权的未跟踪输入不得进入产物。
  - 验收：wheel 只包含运行代码和 `autoblade init` 所需的不可变资源；sdist 包含重建 wheel 所需的源码、测试、许可证、锁文件和构建配置。
  - 验收：自动列出并检查 wheel/sdist 内容；从干净 checkout 或版本标签构建时，同一源码与版本产生一致的文件集合。
  - 验收：`uv build` 和 `scripts/validate_distribution.py` 均成功，产物内不存在仓库本地绝对路径或相对 README 链接。
  - 实现记录（2026-08-11）：Hatchling wheel 固定为 `src/catia_autoblade`，sdist 明确列出重建来源与版本化输入；校验器拒绝禁止目录、CAD/日志产物和本地绝对路径，并生成排序内容清单。候选 wheel 为 44 个文件，sdist 为 103 个文件。

### P0：安装后冒烟与真实产物验证

- [x] 为非 editable 安装增加全新环境冒烟测试。
  - 前置：`autoblade init` 和构建文件清单已经稳定。
  - 验收：在干净 Windows/CPython 3.14 虚拟环境中从 wheel 安装，验证 `autoblade`、`autoblade-create`、`autoblade-batch` 的 `--help`、`--version` 和退出码。
  - 验收：测试明确排除仓库源码路径和已有 `.venv`，证明导入和命令入口来自已安装 wheel。
  - 验收：执行 `autoblade init` 后，`list`、`config show`、输入预检和 mock 建模路径均能运行。
  - 验收：发布候选 wheel 使用至少一个代表性输入完成真实 CATIA 冒烟，并记录 CATPart、STEP、特征树和 `CNEXT` 清理结果。
  - 实现记录（2026-08-11）：`scripts/check.ps1` 每次构建后创建独立 CPython 3.14 环境并安装 wheel，验证三个入口、初始化工作区、配置、输入和 mock 建模。`0.2.0` 候选 wheel 的显式真实回归使用 89 截面多翼型输入生成 7,689,114 字节 CATPart 和 1,022,363 字节 STEP，关键特征、固体 BREP 与零新增 `CNEXT` 均通过。

### P1：版本、内部发布与回滚

- [x] 建立可重复的内部 preview 发布流程。
  - 验收：明确 `v0.x` 版本规则；`__version__`、Git 标签、Release Notes、wheel 和 sdist 版本保持一致。
  - 验收：发布前检查工作区状态、完整仓库检查、产物内容、全新环境安装和真实 CATIA 验证记录；任一证据缺失时不得把产物标为可用 preview。
  - 验收：内部交付物包含 wheel、sdist、版本说明、已验证环境和 SHA-256，且能从对应标签重新构建。
  - 验收：定义失败与回滚步骤，不留下重复标签、版本号相同但内容不同的产物或含糊的部分发布。
  - 验收：GitHub Release、TestPyPI 和公共 PyPI 作为后续渠道单独晋级，不作为首个内部 wheel 的完成条件。
  - 实现记录（2026-08-11）：新增版本说明、真实验证 JSON 模板和 `prepare_internal_release.py`；只有干净标签提交、完整检查、安装冒烟、真实 CATIA 证据和零残留进程同时满足时才生成 SHA-256 与内部发布 manifest。失败、重复版本和回滚规则见 `docs/releasing.md`。

### P1：配置 schema 演进与用户数据保护

- [x] 定义升级和配置 schema 迁移策略。
  - 验收：`AppConfig.version` 参与兼容性判断；至少用一个历史配置样例验证直接读取或迁移路径。
  - 验收：明确未知字段、废弃字段和未来版本配置的警告/失败规则，并覆盖自动化测试。
  - 验收：升级前后配置、输入和输出路径保持稳定；迁移操作可预览、可备份且不会静默覆盖用户文件。
  - 验收：只有出现真实迁移需求时才增加独立 `config migrate` 命令，当前不为假设场景提前建立复杂迁移框架。
  - 实现记录（2026-08-11）：配置 schema 升为 `2.0.0`，修复真实 `1.0.0` 历史路径双重 `input` 前缀；旧配置只在内存读取，显式 `config migrate --apply` 才会在摘要校验后备份并原子替换。未来版本、未知字段、登记废弃字段和预览后并发修改均安全失败。

### P1：安装环境诊断与分发文档

- [x] 增加 `autoblade doctor` 和对应安装文档。
  - 验收：诊断 Windows、Python、`pywin32`、CATIA COM 注册/初始化能力、配置来源、输入目录和输出写权限，并生成可复制的摘要。
  - 验收：诊断过程不得连接、退出或破坏用户已经打开的 CATIA 会话；任何需要启动独占实例的深度检查都必须显式确认并保证清理。
  - 验收：新增安装与发布文档，覆盖源码、内部 wheel、升级、卸载、工作区初始化、CATIA 前置条件、常见失败和维护者发布步骤。
  - 验收：中英文 README 只展示已经受支持渠道的最短路径，不提前宣传规划中的公共发布能力。
  - 实现记录（2026-08-11）：`doctor` 只读 CATIA ProgID 注册并配对线程 COM 初始化，不 Dispatch 应用；当前机器的 Windows、Python 3.14.4、pywin32 311、COM、注册、配置和目录检查均通过，CATIA 版本保留人工确认警告。新增安装与内部发布文档，中英文 README 同步内部 wheel 边界。

### 当前里程碑完成条件

- [ ] `pwsh -File scripts/check.ps1` 在干净工作区通过。
- [x] 从候选 wheel 创建全新环境并完成非 editable 安装冒烟。
- [x] `autoblade init` 创建的工作区可完成输入发现、配置读取和代表模型预检。
- [x] 候选 wheel 在已记录的支持基线上完成真实 CATIA 建模、CATPart/STEP 导出和进程清理。
- [ ] 内部发布产物、版本说明、SHA-256、验证记录和回滚步骤齐全且可追溯到同一 Git 标签。

## 后续里程碑：显式参数扫描 `sweep`

- [ ] 增加独立的 `sweep` 命令和 `SweepPlanner`，承接显式设计变量组合。
  - 首版只组合用户显式选择的六列截面模板与显式选择的翼型；含 `airfoil` 列的自包含文件不参与外部翼型组合。
  - 验收：2 个翼型与 `section_params-1.csv` 至 `section_params-5.csv` 精确生成 10 个稳定排序的 `BladeBuildJob`，并有不启动 CATIA 的 Planner 自动化测试。
  - 验收：输入目录中额外文件不能静默增加任务；执行前展示选择范围、组合数量、完整任务预览和输出冲突。

- [ ] 为扫描任务固定最小组合与清单契约。
  - 首版只实现 Cartesian product；只有出现明确需求后才增加 `zip`、全局缩放、桨距或尖部形状等设计变量。
  - 验收：Planner 输出可序列化为稳定清单，用于 dry-run、黄金任务列表回归和未来调度；CATIA Builder 不包含组合逻辑。

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
