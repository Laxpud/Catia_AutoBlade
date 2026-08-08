# 项目任务清单

本文件记录当前里程碑和可验收的后续工作。长期技术说明放在 `docs/`，已经完成且需要保留的计划可在未来归档到 `docs/archive/`。

## 已完成里程碑：稳定单翼型建模链路

- [x] 建立英文项目入口、中文翻译、技术文档索引和活动任务清单。
- [x] 修复独立 CLI 入口 `autoblade-create` 和 `autoblade-batch`。
  - 验收：两个命令的 `--help` 均以状态码 0 退出，并且能够解析与主命令一致的参数。
  - 验收：README 中的所有命令示例都可以执行到预期阶段。
- [x] 让 `config.toml` 成为运行时配置来源，而不只是可查看、可编辑的数据文件。
  - 验收：输入目录、输出目录和输出命名模板均由 `ConfigManager` 提供。
  - 验收：CLI 显式参数能够覆盖配置值，且相对路径的解析基准有文档说明和测试。
- [x] 为 CATIA 与 COM 生命周期增加可靠清理。
  - 验收：建模、保存或导出任一步骤抛出异常后，文档和 COM 状态仍会在 `finally` 路径中释放。
  - 验收：批处理失败不会遗留不可见的 CATIA 进程。
- [x] 增加输入数据校验和可定位的错误信息。
  - 验收：缺列、空文件、非法数字、少于两个截面、无效翼型点序都能在启动 CATIA 前失败。
  - 验收：错误信息包含文件路径、字段或行号以及违反的约束。
- [x] 定位并解决密集翼型点云在 CATIA 中的几何精度冲突。
  - 复现记录（2026-08-05）：将 `airfoil1_sharp.csv` 沿原点序线性插值到 1000 点；归一化坐标直接按 mm 创建基准翼型时，最小相邻点距为 `0.0003097902 mm`。1000 个点特征均创建成功，但组装样条后的 `Part.Update()` 失败；原始 300 点、最小相邻点距 `0.0010350515 mm` 的对照组成功。
  - 处理策略：翼型坐标、截面弦长、平移参数和 Python 领域计算统一使用 m；基准翼型弦长为 1 m。仅在 CATIA Automation 边界按其固定接口契约将长度换算为 mm。
  - 验证记录（2026-08-05）：截面参数迁移为 m 后，上述 1000 点样例能够创建基准样条和 26 个变换截面，但仍在 Loft 更新阶段失败；260 点 `sc1095.csv` 可完成 Loft 和实体封闭。
  - 根因记录（2026-08-05）：旧实现将理论前缘坐标经过数值变换后作为独立闭合点。普通 300 点案例中该点到截面的偏差低于 CATIA 显示精度，但 1000 点拟合曲线与理论坐标相差约 `0.001 mm`，因此 Loft 拒绝该闭合点。密集曲线的弦向极值还可能包含多个非连通点，不能直接作为导引样条控制点。
  - 修复记录（2026-08-05）：每个截面先从实际曲线生成前缘方向的 `Extremum`，再以理论前缘作为 `Near` 选择器，从多点极值中取得单一曲线点。300 点、1000 点和 260 点钝后缘案例的 26 个前缘点到所属截面距离均为 `0 mm`，且均完成 Loft 和实体封闭。
  - 手工检查：测试输入现为 `input/airfoils/airfoil1_sharp_dense_1000.csv`；原始成功截面、Loft 失败现场和修复后的完整实体仍按历史名称保存在 `output/repro/AIRFOIL1_sharp_1000_sections.CATPart`、`output/repro/AIRFOIL1_sharp_1000_loft_failure.CATPart` 和 `output/repro/AIRFOIL1_sharp_1000_curve_le_fixed.CATPart`。
  - 验收：代表性约 1000 点翼型能够稳定完成样条、Loft 和实体封闭，且现有低密度翼型的几何与输出不发生非预期变化。
- [x] 建立不依赖 CATIA 的自动化测试基线。
  - 验收：覆盖 CSV 解析、坐标变换、文件扫描、输出命名和 CLI 参数解析。
  - 验收：测试通过 mock 隔离 COM 接口，并能在未安装 CATIA 的环境执行。

## 已完成里程碑：支持展向多翼型

- [x] 确认多翼型截面文件中 `airfoil` 列的正式数据契约。
  - 契约：六列文件保持单翼型兼容；出现 `airfoil` 表头时每个截面都必须填写配置翼型目录下的精确 CSV basename。
  - 契约：切换处不增加数值连续性字段，通过统一坐标系、点序、实际前缘闭合点和前后缘导引线建立 Loft 对齐；首版要求整片叶片后缘拓扑一致。
  - 设计记录：[展向多翼型设计](docs/multi-airfoil-design.md)。
- [x] 规范当前里程碑的输入路径和文件名。
  - 验收：版本化输入使用小写稳定文件名，89 行样例为 `input/section_params/section_params-multi-airfoil.csv`，引用不包含目录分量。
  - 验收：里程碑所需翼型与参数文件在后续提交中一并纳入版本控制，不留下仅本机存在的引用。
- [x] 让每个截面按 `airfoil` 字段选择并复用翼型几何。
  - 验收：当前 89 行组合参数可分别使用 `airfoil1_sharp.csv`、`airfoil2_sharp.csv` 和 `airfoil3_sharp.csv`。
  - 验收：重复翼型只读取和创建一次基准几何，截面顺序严格按 `idx` 校验。
  - 实现记录（2026-08-07）：输入计划完成安全 basename 解析、唯一翼型去重读取、后缘拓扑一致性校验和 COM 前失败；几何编排按 `airfoil_filename` 复用唯一基准曲线。
- [x] 定义不同点数翼型之间的 Loft 稳定性策略。
  - 验收：翼型切换位置的截面对齐、前缘定位和后缘导引规则有技术文档与回归样例。
  - 验收：生成曲面能够成功封闭为实体并导出 `CATPart` 与 STEP。
  - 验证记录（2026-08-07）：CATIA P3 V5-6R2020 使用 300、253、249 点的三个原始翼型完成 89 截面 Loft、`CloseSurface`、CATPart 保存和 STEP AP242 导出，无需重采样；STEP 包含闭合实体 BREP，命令结束后无残留 `CNEXT`。

## 下一阶段：固定模型输入、命令和回归资产契约

- [x] 记录 `create`、`batch` 和未来 `sweep` 的稳定职责，避免继续把批量执行与参数组合混为同一语义。
  - 契约：`create` 接收一个明确模型定义并生成一个 `BladeBuildJob`；`batch` 执行多个已经闭合输入引用的模型定义并生成 N 个任务；`sweep` 显式组合设计变量并生成 N × M × … 个任务。
  - 契约：六列截面文件是需要绑定翼型的几何模板；含 `airfoil` 列的截面文件是自包含模型定义，每个有效截面行仍必须明确填写翼型 basename。
  - 验收：在 `docs/design-principles.md` 记录上述边界，并从 `docs/index.md`、架构说明和中英文使用文档链接或同步相关内容。
  - 实现记录（2026-08-07）：新增 `BladeBuildJob`、Planner 和共享 Executor；`batch` 每个截面定义只生成一个任务，隐式翼型组合已从命令和 Python 批处理入口移除。
- [x] 收紧单模型创建时的 `--airfoil` 语义，同时保留固定截面参数、更换翼型的能力。
  - 验收：非交互 `create` 使用六列截面文件但没有传入 `--airfoil` 时，在启动 CATIA 前明确失败，不再按目录排序自动选择第一个翼型。
  - 验收：交互模式仍可在选定六列截面文件后提示选择一个翼型；含 `airfoil` 列的文件继续拒绝后备 `--airfoil`，不引入逐行覆盖或继承语义。
  - 验收：CLI、输入计划和使用文档覆盖成功、缺参、文件不存在及参数冲突路径。
  - 实现记录（2026-08-07）：非交互 `create` 同时要求明确 `--section`；六列模板缺少 `--airfoil` 在完整输入计划阶段失败，自包含文件仍拒绝后备翼型。
- [x] 统一 CLI 错误传播和进程退出码，使人工日志与脚本判断保持一致。
  - 契约：全部成功返回 0；输入校验、配置、建模、保存、导出或 batch 部分失败返回 1；Typer 参数用法错误返回 2；用户中断返回 130。
  - 验收：命令处理层不再以打印 `[ERROR]` 后正常 `return` 的方式吞掉失败；最外层 CLI 统一呈现错误并转换退出码，同时保留可测试的领域异常或结构化结果。
  - 验收：自动化测试覆盖文件不存在、参数冲突、无效配置、建模失败、batch 部分失败和交互取消，并断言标准输出、标准错误及退出码。
  - 实现记录（2026-08-07）：显式命令异常统一在 CLI 边界写入标准错误并返回 1；用法错误返回 2，中断返回 130，交互安全取消返回 0；批处理部分失败保留全部 `BuildResult` 后返回 1。
- [x] 建立专门的 CLI 参考文档，结束命令说明分散在 README 和多个技术文档中的状态。
  - 验收：新增 `docs/cli.md`，区分当前已实现的 `create`、`batch`、`list`、`config`、独立兼容入口与未来 `sweep`，不把规划功能写成现有能力。
  - 验收：逐项说明参数、默认行为、交互模式、输入文件模式、冲突规则、任务预览、输出覆盖、退出码和常用示例；`docs/index.md` 增加入口，根 README 只保留最短使用路径。
  - 实现记录（2026-08-07）：新增 `docs/cli.md` 作为详细命令来源，根 README 与中文翻译只保留菜单入口、最短显式命令和文档链接。
- [x] 将无参数 `autoblade` 提升为默认人工入口，提供菜单式交互会话而不是嵌套命令 REPL。
  - 契约：在真实 TTY 中直接运行 `autoblade` 时进入顶层菜单，可选择 `create`、`batch`、未来 `sweep`、输入列表、配置管理和退出；一次操作完成后返回菜单。
  - 契约：显式子命令继续作为脚本和可复现调用的稳定接口；`create --interactive` 与 `batch --interactive` 保留为直接进入对应向导的兼容快捷方式。
  - 验收：非 TTY 环境中的无参数调用不得等待输入，应显示帮助并以 CLI 用法错误退出；正常退出返回 0，`Ctrl+C` 返回 130，取消单个选择时安全返回上一级。
  - 验收：交互层只收集选择和执行确认，与显式 CLI 共享同一 Planner 和 Executor；启动 CATIA 前展示模型定义、任务数、输出路径及覆盖冲突，不复制输入校验或建模规则。
  - 验收：自动化测试覆盖无参数 TTY/非 TTY 分支、菜单路由、取消与中断、操作后返回主菜单，以及确认前不会创建 CATIA 会话。
  - 实现记录（2026-08-07）：真实 TTY 进入可循环顶层菜单，非 TTY 无参数调用显示帮助并返回 2；交互向导在已闭合任务预览后才请求建模确认。
- [x] 为版本化输入建立“示例、真实 CATIA 回归、pytest 夹具”三类资产边界。
  - 示例用于最短使用路径；真实回归表示曾经在 CATIA 中成功、后续版本必须继续成功的模型；pytest 夹具只服务自动化测试，预期失败的 CSV 不得进入普通输入扫描目录。
  - 验收：`input/README.md` 逐项记录文件用途、关联功能或历史缺陷、推荐命令、预期结果以及是否需要真实 CATIA。
  - 验收：`section_params-1.csv` 至 `section_params-5.csv` 标记为 batch 回归组；`section_params-multi-airfoil.csv` 标记为 89 截面、不同点数、多翼型回归；`section_params-naca.csv` 以零位移回归身份纳入版本化输入，并决定是保留历史名称还是改为语义名称。
  - 验收：在改变现有 `airfoil_dir`、`section_params_dir` 扫描契约前，先确定是否需要物理拆分为 `input/examples/` 与 `input/regression/`；pytest 专用共享数据统一放在 `tests/fixtures/`，单个测试使用的小型输入继续由 `tmp_path` 构造。
  - 实现记录（2026-08-07）：暂不物理拆分两个配置输入目录；`input/README.md` 逐项登记版本化资产，保留 `section_params-naca.csv` 历史名称并将其纳入零位移回归。
- [x] 补齐分层测试，使每类回归资产都有对应的低成本保护。
  - 单元层继续覆盖单位、旋转、缩放、平移和零位移；Parser/Planner 层覆盖输入引用闭合与任务列表；mock CATIA 层覆盖几何调用顺序和复用；真实 CATIA 层保留人工冒烟与回归，不进入默认 pytest。
  - 验收：仓库输入测试确认零位移样例至少包含一个三轴平移均为 0 的截面，并确认多翼型样例的 89 行引用完整。
  - 验收：`docs/testing.md` 记录每层能发现的问题、不能替代的真实 CATIA 检查及人工回归结果格式。
  - 实现记录（2026-08-07）：新增 Job Planner/Executor、CLI 退出码、菜单和仓库资产测试；默认 pytest 共 93 项，真实 CATIA 仍保持人工层。

## 发布前置：工程一致性与支持范围

- [x] 明确首个可分发版本的受众、渠道和外部依赖边界。
  - 路线：先提供源码或内部 wheel，再验证 GitHub Release 和 TestPyPI，最后决定是否发布公共 PyPI；独立 EXE 只在目标用户明确不使用 Python/uv 时推进。
  - 验收：文档明确支持的 Windows、Python、`pywin32` 和 CATIA V5 组合，并声明 CATIA 本体、许可证和 COM 注册环境不属于分发产物。
  - 验收：`sweep`、多 CAD 后端和插件化不是首个预览版本的发布阻塞项，发布范围只承诺已经完成回归的能力。
  - 实现记录（2026-08-08）：新增 `docs/distribution-scope.md`，将首个制品固定为面向受控工程用户的内部 `v0.x` 预览 wheel；记录唯一已验证环境、源码到公共发布的分阶段路线、CATIA 外部依赖和首版非目标。中英文 README 与技术文档索引同步入口。
- [x] 将跨平台核心与 Windows/CATIA Adapter 的依赖边界提升为稳定架构契约。
  - 契约：领域模型、单位与坐标变换、Parser、Validation、Planner 和 `BladeBuildJob` 不导入 `pythoncom`、`win32com` 或 CATIA COM 对象；CATIA 会话、几何特征和格式导出只存在于 `adapters/cad/catia/` 边界。
  - 契约：跨平台只承诺输入解析、校验、任务规划和后端无关计算，不表示能够在 Linux/macOS 上运行 CATIA 建模；请求不可用后端时必须返回明确的能力或平台错误。
  - 验收：首个 `catia-autoblade` 发行包仍明确标记为 Windows/CATIA 产品，不因内部核心可移植就宣称整个产品跨平台；出现第二个真实后端前不拆分多个发行包。
  - 实现记录（2026-08-08）：CATIA Builder、会话、保存和导出迁移到 `adapters/cad/catia/`；核心新增纯米制坐标模块，旧导入路径仅延迟转发。平台边界测试确认顶层包及 Parser/Planner 导入不加载 COM，不可用后端返回 `CatiaBackendUnavailableError`。
- [x] 统一 `pyproject.toml`、锁文件和实际运行环境的包元数据。
  - 验收：`requires-python` 与 Python classifiers 一致，操作系统改为 Windows，依赖范围与已验证版本相符，并补齐 Documentation、Issues 等项目链接。
  - 验收：当前 `catia-autoblade` 包保留 Windows 和 `pywin32` 依赖；只有未来独立的核心发行包才使用平台无关元数据，CATIA Adapter 不得使用 `OS Independent` classifier 或省略 Windows/CATIA 运行要求；wheel 文件标签本身不作为产品支持范围声明。
  - 验收：确认 PyPI 项目名可用，检查作者信息与 LICENSE 版权声明的关系，并验证 PyPI 长描述中的链接不会依赖仓库内相对路径。
  - 验收：动态版本仍由 `src/catia_autoblade/__init__.py` 提供，`autoblade --version`、wheel 元数据和 Git 标签报告同一版本。
  - 实现记录（2026-08-08）：Python 支持范围收敛为 3.14.x，平台 classifier 改为 Windows，`pywin32` 固定为 311，并补齐 Documentation 与 Issues 链接。PyPI 名称检查当日返回 404；作者元数据与 LICENSE 版权角色分别保留。新增 `autoblade --version` 和产物/标签一致性校验。
- [x] 固化开发与发布检查入口，并维护最小兼容性表。
  - 验收：常规检查至少包含 `pytest`、`ruff`、Hatchling 构建和产物元数据检查，命令在开发文档和自动化环境中一致。
  - 验收：兼容性表记录 Windows、Python、`pywin32`、CATIA 版本/配置和验证日期；未验证组合不得在包元数据或安装文档中宣称支持。
  - 实现记录（2026-08-08）：新增 `scripts/check.ps1` 与 Windows GitHub Actions 工作流，共享 pytest、Ruff、Hatchling 构建和 wheel/sdist 元数据检查；兼容性表由 `docs/distribution-scope.md` 维护。默认 pytest 共 97 项。

## 后续里程碑：建立可安装分发与发布链路

- [ ] 增加 `autoblade init`，让已安装的 wheel 能创建独立、可编辑的建模工作区。
  - 验收：在显式目标目录创建 `config.toml`、`input/airfoils/`、`input/section_params/` 和 `output/`，并可选择复制最小示例；已存在文件默认不覆盖，只有显式 `--force` 或交互确认才允许替换。
  - 验收：确定配置优先级为显式 `--config`、当前工作区配置、用户级配置和内置默认值中的一种稳定顺序，并补充路径解析、无配置和只读目录测试。
  - 验收：包内只保存不可变的模板资源，用户配置、输入和输出始终位于 site-packages 之外；安装、升级和卸载不得删除用户工作区。
- [ ] 固定 Hatchling wheel 与 sdist 的文件清单，保证构建可审计且不受本地临时文件影响。
  - 验收：在 `pyproject.toml` 中明确 wheel/sdist 的 include 与 exclude；输出、失败快照、缓存、私有/客户数据和未授权的未跟踪输入不会进入产物。
  - 验收：只从干净 Git checkout 或版本标签构建；自动列出并检查产物内容，同一源码与版本不会因开发机工作区状态生成不同文件集合。
  - 验收：`uv build` 和产物元数据检查成功，wheel 仅包含运行代码与必要资源，sdist 包含可重建 wheel 所需的源码、测试、许可证和构建配置。
- [ ] 为真实安装产物增加全新环境冒烟测试，而不是只测试 editable 源码工作区。
  - 验收：在干净 Windows/Python 3.14 虚拟环境中从 wheel 安装，验证 `autoblade`、`autoblade-create`、`autoblade-batch` 的 `--help`、`--version` 和退出码。
  - 验收：执行 `autoblade init` 后，`list`、`config show`、输入预检和 mock 建模路径均可运行；测试不得通过仓库源码路径或已有 `.venv` 隐式导入模块。
  - 验收：发布候选产物至少使用一个代表性输入完成真实 CATIA 冒烟，确认 CATPart、STEP 和 COM 清理结果。
- [ ] 建立可重复的版本、发布和回滚流程。
  - 验收：采用明确的版本规则，Git 标签、CHANGELOG/Release Notes 和 `__version__` 保持一致；发布前检查工作区、测试、构建、产物安装和真实 CATIA 验证状态。
  - 验收：Windows CI 构建 wheel/sdist 并执行无 CATIA 自动化测试；公共发布先经过 TestPyPI 安装验证，再使用受保护凭据或可信发布上传正式索引。
  - 验收：GitHub Release 附带 wheel、sdist、版本说明和 SHA-256；失败流程不会留下含糊的部分发布、重复标签或不可重建产物。
- [ ] 定义升级、配置 schema 迁移和用户数据保护策略。
  - 验收：`AppConfig.version` 参与兼容性判断；至少用一个历史配置样例验证读取或迁移，明确未知字段、废弃字段和未来版本配置的警告/失败规则。
  - 验收：升级前后的配置、输入和输出路径保持稳定，迁移操作可预览且不会静默覆盖；只有出现真实迁移需求时才增加独立的 `config migrate` 命令。
- [ ] 增加安装环境诊断与分发文档。
  - 验收：提供 `autoblade doctor`，检查 Windows/Python/pywin32、COM 初始化、CATIA 注册或连接、配置、输入目录、输出写权限和兼容性表状态，并生成可复制的诊断摘要。
  - 验收：新增安装与发布文档，覆盖源码、wheel、升级、卸载、工作区初始化、CATIA 前置条件、常见失败和维护者发布步骤；README 只保留受支持渠道的最短路径。
- [ ] 仅在确认无 Python 用户的真实需求后评估独立 Windows 可执行程序。
  - 验收：比较 PyInstaller 与 Nuitka，首选可诊断的 one-folder 原型，并验证 `pythoncom`、`pywintypes`、`win32com.client`、Questionary 和 Typer 资源完整。
  - 验收：配置和输入继续作为外部工作区管理，在没有开发环境的目标 CATIA 机器上验证安装、启动、建模、升级、卸载、杀毒软件影响和可选代码签名。

## 后续里程碑：统一 Planner、Job 与建模执行边界

- [ ] 引入可在 Windows、Linux 和 macOS 上导入、测试的领域层与应用层。
  - `BladeDefinition` 表达已经解析的叶片几何定义，`BladeBuildJob` 表达一次确定的输入、输出和建模请求；二者不保存 Typer 参数、CSV reader、平台判断或 COM 对象。
  - 验收：Parser 只负责把 CSV 转换为领域对象，Planner 只负责把用户选择转换为任务列表，Builder 只接收已经校验且引用闭合的任务。
  - 验收：缺文件、非法引用、输出命名冲突和任务数量错误均在创建 CATIA 会话前失败。
  - 验收：核心测试在 Windows、Linux 和 macOS CI 上均不安装 `pywin32` 即可运行，包顶层和核心模块不会因导入而加载 CATIA Adapter。
- [ ] 将现有 CATIA 实现迁移到明确的 Adapter 边界，同时保持已验证几何行为。
  - 验收：`CatiaSession`、`HybridShapeFactory` 调用、Spline、`Extremum`、`Near`、Loft、`CloseSurface`、CATPart 和 STEP 导出集中在 `adapters/cad/catia/`，核心层不暴露 CATIA 特征代理。
  - 验收：从当前 `transform_airfoil_section()` 抽出后端无关的旋转、缩放、平移和零位移描述；具体 Direction、Translate 和长度单位换算由 CATIA Adapter 实现。
  - 验收：迁移前后的单翼型、多翼型、密集点云、尖/钝后缘和零位移回归结果一致，旧 Python 调用入口在迁移期通过薄兼容层转发并有弃用计划。
- [ ] 让 `create`、`batch` 和未来 `sweep` 共享同一个任务执行器。
  - 验收：执行器不知道任务来自哪个 CLI 命令，通过最小内部 `build(job) -> BuildResult` 边界调用选定 Adapter，并统一负责结果汇总；当前不把该内部边界承诺为稳定公共 CAD API。
  - 验收：CATIA Adapter 统一负责 CATIA 会话、保存、导出、失败快照和 COM 清理，其他未来 Adapter 不继承无关的 CATIA 生命周期语义。
  - 验收：一个任务失败不影响后续任务，且每个结果都包含模式、输入、输出或错误信息。
- [x] 将 `batch` 收敛为 N 个明确模型任务，不再执行隐式笛卡尔积。
  - 契约：一个自包含截面文件生成一个任务；多个六列截面模板只有在显式绑定同一个翼型后才分别生成一个任务；多个翼型参与组合属于 `sweep`。
  - 验收：`section_params-1.csv` 至 `section_params-5.csv` 绑定一个显式翼型时规划 5 个任务，而不是因为翼型目录中存在其他文件而扩展任务数。
  - 验收：执行前输出稳定排序的任务预览、总数与目标输出；自动化测试直接比较完整任务列表，而不仅检查最终成功计数。
  - 实现记录（2026-08-07）：`plan_batch_jobs()` 接收至多一个外部翼型并完整解析每个模型，五模板回归精确生成五个稳定排序任务；同批次输出冲突在执行前失败。

## 后续里程碑：增加显式参数扫描 `sweep`

- [ ] 增加独立的 `sweep` 命令和 `SweepPlanner`，承接当前 batch 中的笛卡尔积能力。
  - 首版只组合显式选择的六列截面模板与显式选择的翼型；含 `airfoil` 列的自包含文件不参与外部翼型组合。
  - 验收：2 个翼型 × `section_params-1.csv` 至 `section_params-5.csv` 精确生成 10 个稳定排序的 `BladeBuildJob`，并有不启动 CATIA 的 Planner 自动化测试。
  - 验收：不允许仅因输入目录碰巧存在多个文件就静默产生组合；执行前必须显示选择范围、组合数量和任务预览。
- [ ] 为参数扫描保留可扩展但不过度设计的组合契约。
  - 首版仅实现 Cartesian product；只有出现明确需求后才增加 `zip`、全局缩放、桨距、尖部形状等设计变量。
  - 验收：Planner 输出可序列化为稳定清单，用于 dry-run、黄金任务列表回归和未来计算调度，而 CATIA Builder 不包含组合逻辑。

## 长期方向：第二建模后端与独立分包

- [ ] 仅在出现第二个真实后端需求时抽象公共 Builder 接口。
  - 候选方向包括 NX、FreeCAD、OpenCascade 或直接网格输出，但当前阶段不为尚未实现的平台创建空适配器、插件系统或过早稳定的公共 API。
  - 验收：新增后端复用同一 `BladeDefinition` 和 `BladeBuildJob`，并通过后端无关的几何契约测试；平台特有能力和限制保留在各自 Builder 内。
  - 验收：第二个后端落地时再评估拆分为平台无关的核心发行包、`catia-autoblade` 和其他 Adapter 包；核心包可独立安装且不依赖 `pywin32`，各 Adapter 单独声明平台、运行库和外部软件要求。
