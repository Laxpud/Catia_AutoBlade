# 项目任务清单

本文件只记录尚未完成的活动工作、优先级和可验证的完成标准。已完成的计划见 [`docs/archive/`](docs/archive/)，其中包括[截至 0.1.1 的里程碑](docs/archive/milestones-through-0.1.1.md)、[`v0.2.0` 内部 preview wheel 里程碑](docs/archive/internal-preview-wheel-0.2.0.md)、[显式参数扫描 `sweep` 里程碑](docs/archive/explicit-parameter-sweep.md)和[真实示例与内置翼型目录里程碑](docs/archive/real-example-and-airfoil-library.md)；稳定技术契约见 [`docs/index.md`](docs/index.md)。

## 执行与维护规则

- 默认从当前里程碑中第一个未完成任务开始，除非用户指定其他任务。
- 任务的全部验收条件满足后，标记为 `[x]`，并记录完成日期和验证证据；部分完成时保持 `[ ]`。
- 当前里程碑的任务和完成条件全部通过后，将其归档到 `docs/archive/`，并把下一里程碑提升为当前里程碑。
- 验证不足时不得标记完成，也不得降低验收条件。

## 当前状态（2026-08-12）

- 单翼型、展向多翼型、`create`/`batch`、Planner/Executor、CATIA Adapter、COM 清理和无 CATIA 自动化测试基线均已完成。
- `v0.2.0` 内部 preview wheel 已在标签提交 `1d479ff84a9b8e68abfa830a64cd37f42a4f6ce1` 上完成全量检查、非 editable 安装冒烟和真实 CATIA 回归，并生成版本说明、验证记录、SHA-256 与内部发布清单。
- 显式参数扫描 `sweep` 已在提交 `ba7e647` 完成，具备稳定 Cartesian product、JSON 清单和无 CATIA dry-run；提交后的干净工作区通过 136 项测试、Ruff、构建、安装冒烟和分发校验。
- 真实示例与内置翼型目录里程碑已完成；来源授权、实现范围、命名评估和验证证据见[归档记录](docs/archive/real-example-and-airfoil-library.md)。
- 用户确认项目尚未大规模使用后，已把用户可见集合从 `section_params` 直接迁移为 `blade_sections`；当前配置 schema 为 `3.0.0`，`sweep` 清单 schema 为 version 2，并通过 140 项测试、Ruff、构建、隔离安装冒烟和分发校验。破坏性边界和旧工作区操作见[命名迁移记录](docs/blade-sections-migration.md)。
- 当前没有无条件活动里程碑。公共 PyPI、独立 EXE 和第二 CAD 后端仍不在当前范围内；以下方向只有在对应触发条件成立后才提升为当前里程碑。

## 当前计划：条件性长期方向

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
