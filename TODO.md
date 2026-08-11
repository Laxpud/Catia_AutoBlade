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

- [ ] 增加独立的 `sweep` 命令和 `SweepPlanner`，承接显式设计变量组合。
  - 首版只组合用户显式选择的六列截面模板与显式选择的翼型；含 `airfoil` 列的自包含文件不参与外部翼型组合。
  - 验收：2 个翼型与 `section_params-1.csv` 至 `section_params-5.csv` 精确生成 10 个稳定排序的 `BladeBuildJob`，并有不启动 CATIA 的 Planner 自动化测试。
  - 验收：输入目录中额外文件不能静默增加任务；执行前展示选择范围、组合数量、完整任务预览和输出冲突。

- [ ] 为扫描任务固定最小组合与清单契约。
  - 首版只实现 Cartesian product；只有出现明确需求后才增加 `zip`、全局缩放、桨距或尖部形状等设计变量。
  - 验收：Planner 输出可序列化为稳定清单，用于 dry-run、黄金任务列表回归和未来调度；CATIA Builder 不包含组合逻辑。

### 当前里程碑完成条件

- [ ] `sweep` 只组合显式选择的输入，任务数量和稳定顺序均有自动化回归。
- [ ] 任务清单可序列化并能在不启动 CATIA 的 dry-run 中完整展示。
- [ ] `create` 和 `batch` 的既有职责、任务语义与回归保持不变。
- [ ] `pwsh -File scripts/check.ps1` 在干净工作区通过。

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
