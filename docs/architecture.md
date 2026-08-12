# 架构说明

## 系统边界

CATIA AutoBlade 的完整建模产品是运行在 Windows 上的 Python CLI。Python 负责读取输入、计算截面变换和编排流程；实际几何创建、Loft、实体封闭和格式导出由 CATIA V5 COM 对象完成。

Parser、Validation、Planner、任务模型和坐标计算不依赖 Windows COM，可在其他平台导入和测试；这只承诺跨平台预检与规划，不表示能在 Linux 或 macOS 上生成模型。项目不包含独立几何内核，离开受支持的 Windows/CATIA 环境无法生成最终模型。

## 调用链

```text
Typer CLI
  -> init / config / doctor：外部工作区、schema 与无 CATIA 环境诊断
  -> commands / interactive：参数或交互选择、预览和执行确认
  -> Planner：解析 CSV、闭合输入引用并生成 BladeBuildJob
  -> Executor：执行一个或多个任务并汇总 BuildResult
  -> adapters.cad.catia.builder：CATIA 几何调用、建模与导出
  -> adapters.cad.catia.session：Windows COM 与 CATIA 会话生命周期
  -> CATIA V5：CATPart 文档、HybridShape、Loft、CloseSurface
```

主要模块职责：

- `catia_autoblade.cli`：注册子命令、TTY 菜单入口，并统一异常呈现与退出码。
- `catia_autoblade.interactive`：只收集选择和确认；取消当前操作时返回上一级。
- `catia_autoblade.commands`：把 CLI 或交互选择交给 Planner，展示任务并调用 Executor，不包含 CATIA 几何规则。
- `catia_autoblade.core.jobs`：定义已闭合的 `BladeBuildJob` 和结构化 `BuildResult`。
- `catia_autoblade.core.planner`：完整解析输入、固定输出并检查同批次目标冲突。
- `catia_autoblade.core.sweep`：只展开显式选择的 Cartesian product，并生成可序列化的稳定扫描清单。
- `catia_autoblade.core.executor`：执行任务；批量模式记录单项失败并继续后续任务。
- `catia_autoblade.core.geometry`：后端无关的米制坐标变换和截面缩放。
- `catia_autoblade.core.input_validation`：在启动 CATIA 前解析 CSV 并执行数据契约校验。
- `catia_autoblade.core.input_plan`：解析受限跨文件引用，生成有序截面、唯一翼型和后缘拓扑计划。
- `catia_autoblade.adapters.cad.catia.builder`：CATIA 特征创建、单位边界、保存、导出和失败快照。
- `catia_autoblade.adapters.cad.catia.session`：独占 CATIA 实例并管理文档与 COM 生命周期。
- `catia_autoblade.core.create_blade` 与 `core.catia_session`：仅保留旧 Python 导入路径的延迟兼容转发，不包含 COM 实现。
- `catia_autoblade.core.batch`：保留 Python 批处理入口，并转发到统一 Planner 与 Executor。
- `catia_autoblade.config`：配置模型、TOML 持久化及运行时绝对路径解析。
- `catia_autoblade.resources`：wheel 内不可变的工作区配置、真实多翼型示例及其
  依赖翼型；只能由 `autoblade init` 复制到包外目标。
- `catia_autoblade.commands.initialize`：完整预览、冲突授权和原子复制，不删除
  目标中的其他用户文件。
- `catia_autoblade.commands.doctor`：Windows/Python/COM/注册表/配置/目录诊断；
  不创建 CATIA Automation 应用。
- `catia_autoblade.utils.file_scanner`：从配置的输入目录发现 CSV 文件。

## 核心与 CATIA Adapter 边界

`catia_autoblade.core` 不直接导入 `pythoncom`、`win32com` 或 CATIA COM 对象。领域长度统一使用 m，核心坐标函数只返回普通 Python 数值；`CATIA_MM_PER_METER` 和具体 mm 换算只存在于 CATIA Builder 的 Automation 调用边界。

CATIA Builder 在输入计划完成后才延迟加载会话实现。因此仅导入顶层包、Parser、Validation、Planner、`BladeBuildJob` 或坐标函数不会加载 Windows COM；合法建模请求在非 Windows 或缺少 `pywin32` 时抛出 `CatiaBackendUnavailableError`，而不是泄漏裸 `ImportError`。当前发行包仍只声明为 Windows/CATIA 产品，平台无关核心不是独立发行包。

## 单叶片建模流程

1. Planner 解析截面模式和逐截面引用，构造包含有序截面、唯一翼型及后缘拓扑的 `BladeBuildJob`；任何跨文件、领域或输出冲突在初始化 COM 前终止。
2. Executor 把已闭合输入计划交给建模流程；通过 `DispatchEx` 启动当前任务独占的隐藏 `CATIA.Application`，创建空 `Part` 文档。
3. 将每个唯一翼型转换为以 m 表示、弦长为 1 m、X 轴位于 1/4 弦线的模型坐标；重复引用不会重复解析。
4. 为每个唯一翼型创建一套点云和基准样条；钝后缘额外增加封口直线和 Join。
5. 每个截面按 `airfoil_filename` 选择基准曲线，再依次执行绕 X 轴旋转、相对原点缩放和三维平移。
6. 从每条实际截面曲线提取前缘点，按输入端点变换生成后缘点，并用它们建立纵向导引样条。
7. 以变换后的截面为 Loft 截面，以前缘和后缘样条为导引线生成叶片曲面。
8. 使用 `CloseSurface` 将封闭曲面转换为实体。
9. 隐藏辅助几何，保存 `.CATPart`，并导出 `.stp`。
10. 在 `finally` 语义下关闭文档、退出 CATIA、回收动态代理并执行 `CoUninitialize`。

## CATIA 与 COM 生命周期

每个单叶片任务使用一个 `CatiaSession` 上下文，并拥有独立 CATIA 实例。程序不复用或退出用户已经打开的 CATIA 会话。会话进入时先对当前线程执行 `CoInitialize`，随后创建应用和 `Part` 文档；任一初始化步骤失败都会回滚已经创建的资源。

建模、更新、保存和 STEP 导出全部位于上下文范围内。临时几何 COM 代理被限制在内部建模函数的局部作用域中，因此它们会先离开作用域；会话随后按以下顺序清理：

1. 释放 `Part` 代理并关闭文档；
2. 调用当前会话所拥有应用的 `Quit`；
3. 回收残留 Python COM 代理；
4. 调用与本次初始化配对的 `CoUninitialize`。

如果建模过程中已有主异常，清理错误会附加到该异常而不会遮蔽根因；如果建模成功但清理失败，则单独抛出 `CatiaCleanupError`。单模型启用 `--keep-failed-part` 后，会在清理前将当前文档保存为不覆盖历史文件的 `*_failed.CATPart`，但不会对未完成几何导出 STEP。输入校验失败或 CATIA 会话初始化失败时没有可保存的文档。批处理的每个任务都有自己的会话，某一任务失败并完成清理后才会继续下一任务。

## 批处理模型

批处理先检查每个截面文件的模式。所有选中的六列模板统一绑定一个显式翼型，每个模板生成一个任务；包含 `airfoil` 列的自包含文件也各生成一个任务。目录中的其他翼型不会扩大任务数，多个翼型参与组合只属于显式 `sweep`。单翼型结果按翼型名称分目录，多翼型结果按截面参数文件 stem 分目录；两种模式共享 `defaults.output_name_template`。

当前没有共享 CATIA 会话、失败重试、事务式输出或断点续跑。某一任务失败会先释放其独立 CATIA 会话、记录结构化失败结果，然后继续处理其他任务；只要存在失败，批处理进程最终返回 1。

## 参数扫描模型

`SweepPlanner` 接收显式翼型列表和显式六列模板列表，分别去重排序后按 airfoil-major 顺序展开 Cartesian product。每个组合复用单任务 Planner 完成输入闭合和输出命名，随后统一检查计划内部的目标冲突；自包含七列定义在展开前被拒绝。目录扫描只用于验证候选 basename，未选择文件不会扩展任务数。

`SweepPlan` 持有选择范围和有序 `BladeBuildJob`，并以 schema version 1 序列化为 JSON。清单记录组合类型、任务 ID、输入 basename、输出目录、输出名称和两个输出文件，可供 dry-run、黄金任务列表和未来调度使用。`--dry-run` 在 Executor 前返回，因此不会加载或启动 CATIA；实际执行仍使用共享 Executor，CATIA Builder 不包含组合逻辑。

命令和模型输入的稳定职责见[设计原则](design-principles.md)，参数及退出码见 [CLI 参考](cli.md)。

## 安装工作区与配置生命周期

安装包和用户数据采用单向复制边界：wheel 内只保存版本控制的不可变模板，
`autoblade init` 将其复制到显式、位于 `site-packages` 外的工作区。运行时只读
用户工作区；包安装器升级或卸载时不会拥有配置、输入、输出或模型文件。

主 CLI 按显式路径、当前工作区、用户级配置和内置默认值发现一次配置，并把同一
`ConfigManager` 传给子命令。配置相对路径始终由选中配置文件的位置决定，不随
交互流程中的目录变化漂移。

配置 schema 独立于包版本。加载器先检查 `AppConfig.version`，再交给严格的
Pydantic 模型；未知字段和未来版本不能被忽略。历史 schema 可在内存中兼容读取，
但任何持久化前必须显式预览并应用迁移。迁移使用源文件 SHA-256 防止预览后的
并发修改，先复制不覆盖的备份，再以同目录临时文件原子替换；输入和输出树不参与
迁移。

## 几何约束

- 所有输入翼型都位于 Y-Z 平面，因此输入点的 X 坐标应为 0。
- 输入及 Python 领域计算统一使用 m；基准翼型弦长为 1 m，前缘弦向坐标为 0 m，后缘弦向坐标为 1 m。
- CATIA Automation 的长度参数固定使用 mm，因此只有 COM 调用边界负责将 m 换算为 mm；界面显示单位不会改变该接口契约。
- 变换后的 X 轴是展向和旋转轴，正方向指向翼尖。
- `scale/m` 表示最终弦长；传给 CATIA 的无量纲缩放因子为 `scale/m / 1 m`。
- Loft 截面的对应点依靠前缘点定位，前缘及后缘样条用于约束展向走向。
- 前缘闭合点不能使用独立的理论坐标点。程序沿截面扭转后的弦向正方向计算曲线 `Extremum`；若 CATIA 对密集曲线返回多个非连通极值，再以理论前缘为 `Near` 选择器取得唯一曲线点。Loft 和前缘导引样条只引用这个实际曲线点。

## CATIA 特征树命名

程序创建的几何特征使用英文 `snake_case` 语义名称，避免依赖 CATIA 自动生成且会随操作顺序变化的 `Point.N`、`Translate.N` 等名称。单翼型点云继续使用 `airfoil_cloud_point_0001`；多翼型点云增加翼型 stem，例如 `airfoil1_sharp_cloud_point_0001`。截面相关特征使用截面 `idx` 后缀，例如 `section_rotation_1`、`leading_edge_1` 和 `trailing_edge_1`。公共辅助特征按用途命名，例如 `section_rotation_axis`、`leading_edge_guide`、`blade_loft_surface` 和 `blade_closed_solid`。

更完整的字段与点序约束见[输入数据格式](input-formats.md)。

## 当前实现限制

- 同一叶片暂不支持混合尖后缘与钝后缘翼型。
- 尖后缘通过首尾坐标精确相等判断，没有浮点容差。
- CATIA Adapter 内部仍直接使用动态 COM 对象；当前没有第二个 Builder，也没有对外承诺的通用 CAD 插件接口。
