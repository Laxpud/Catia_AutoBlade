# 展向多翼型设计

本文固化“支持展向多翼型”里程碑的数据、路径和运行语义。输入计划、唯一翼型复用、逐截面选择以及 CLI/批处理编排已经实现，并已通过真实 CATIA 几何验收。

## 目标与边界

一份截面参数文件描述一片叶片。每个截面可以引用不同翼型，同一翼型在一片叶片内只解析一次、只创建一次 CATIA 基准几何。所有输入必须在启动 CATIA 前完成解析、引用解析和领域校验。

本里程碑不引入翼型目录递归搜索、远程资源、跨目录引用或通用翼型插值器。首版也不支持在同一叶片中混合尖后缘与钝后缘翼型。

## 路径和文件命名

运行时只从 `ConfigManager` 解析后的 `paths.airfoil_dir` 和 `paths.section_params_dir` 读取输入，不以进程工作目录或源码目录作为隐式后备位置。

版本化样例遵循以下约定：

```text
input/
  airfoils/
    <airfoil-id>[_<variant>].csv
  section_params/
    section_params-<blade-id>.csv
```

- 文件名使用 ASCII 小写字母、数字、连字符和下划线，扩展名统一为 `.csv`。
- 文件名不包含空格，不通过大小写区分两个数据集。
- `airfoil-id` 表示稳定的翼型标识；`variant` 可表达 `sharp`、点数或其他会改变几何的数据版本。
- `blade-id` 表示一份可独立生成的叶片定义，不在名称中编码可能频繁变化的截面数量。
- 自动化测试继续在 `tmp_path` 中构造最小夹具，不把测试专用临时文件混入运行时输入目录。
- 私有、客户或大体量输入应通过 `config.toml` 指向仓库外目录，不应复制到版本化样例目录。

当前里程碑的规范样例是：

```text
input/airfoils/airfoil1_sharp.csv
input/airfoils/airfoil2_sharp.csv
input/airfoils/airfoil3_sharp.csv
input/section_params/section_params-multi-airfoil.csv
```

## `airfoil` 字段契约

截面参数支持两种互斥模式：

1. 表头没有 `airfoil`：兼容现有单翼型流程，所有截面使用 CLI 或调用方提供的后备翼型。
2. 表头包含 `airfoil`：进入多翼型流程，每个非空截面行都必须填写该字段，不允许空值、沿用上一行或与后备翼型混用。

`airfoil` 的值是 `paths.airfoil_dir` 下 CSV 文件的精确 basename，例如 `airfoil1_sharp.csv`。解析器必须执行以下检查：

- 值符合输入文件命名约定并以 `.csv` 结尾；
- 不包含 `/`、`\`、盘符、`.`、`..` 或任何目录分量；
- 解析后的目标仍位于配置的翼型目录内，并且是可读取的普通文件；
- 翼型目录内不存在仅大小写不同的同名候选；
- 所有被引用翼型都通过现有点云 schema、单位、点序和几何校验；
- 一片叶片引用的翼型具有相同后缘拓扑。

重复引用按规范化的精确文件名去重，并保留首次出现顺序。每个唯一文件只读取一次；进入 CATIA 后，每个唯一翼型也只创建一次基准几何。

## 运行计划模型

输入层应先构造一个与 COM 无关的叶片运行计划，再交给几何层。计划至少包含：

- 按 `idx` 严格递增的截面序列；
- 每个截面的翼型标识和变换参数；
- 按首次使用顺序排列的唯一翼型定义；
- 单翼型或多翼型模式；
- 整片叶片的后缘拓扑。

这样缺文件、非法引用、空 `airfoil`、混合后缘拓扑和 CSV 数据错误都能在 `CatiaSession` 创建前失败。路径解析只存在于输入层，CATIA 几何函数只接收已经验证的领域对象。

## CLI、批处理与输出命名

- `create` 应先确定截面文件模式。单翼型模式才需要选择或验证 `--airfoil`；多翼型模式不要求该参数，若显式提供则报告参数冲突，避免产生“覆盖某些行”的隐含语义。
- 交互模式应先选择截面参数文件，仅在单翼型模式下继续询问翼型。
- `batch` 对每个多翼型截面文件只创建一个任务；只有单翼型截面文件继续与所选翼型做笛卡尔积。
- `batch --airfoil` 只筛选单翼型任务，不改变多翼型文件内的引用。
- 批处理的任务数和日志必须基于展开后的实际运行计划，不能继续简单显示 `翼型数 × 参数文件数`。

输出命名应新增计算字段 `{blade}`，并最终把默认模板迁移为 `{blade}`：

- 单翼型：`<airfoil-stem>_blade-<section-id>`，保持现有默认输出不变；
- 多翼型：`blade-<section-id>`，例如 `blade-multi-airfoil`。

旧模板字段继续服务单翼型模式。多翼型模式若使用依赖单个 `{airfoil}` 的自定义模板，应在启动 CATIA 前报错，而不是注入含义模糊的虚拟翼型名。

## Loft 对齐与稳定性

不同翼型不要求具有相同点数。首版直接使用各自经过校验的原始点云，并依靠以下拓扑约束建立对应关系：

1. 所有翼型采用上侧后缘 → 前缘 → 下侧后缘的相同点序和曲线方向；
2. 所有基准翼型使用相同的 1 m 弦长和 1/4 弦坐标系；
3. 每个截面的 Loft 闭合点都从该截面的实际曲线极值提取；
4. 前缘及后缘导引样条使用各截面所属翼型的实际锚点；
5. 首版拒绝混合尖、钝后缘，避免导引线数量和截面拓扑在展向变化。

只有真实 CATIA 回归证明原始样条参数化导致扭曲或更新失败时，才引入共同弦向站位重采样。重采样必须分别处理上下表面，精确保留前缘和后缘锚点，并以独立回归证明没有改变既有单翼型几何。

## 迁移与验收

本轮命名迁移如下：

| 旧名称 | 规范名称 |
| --- | --- |
| `AIRFOIL1_sharp.csv` | `airfoil1_sharp.csv` |
| `AIRFOIL2_sharp.csv` | `airfoil2_sharp.csv` |
| `AIRFOIL3_sharp.csv` | `airfoil3_sharp.csv` |
| `AIRFOIL1_sharp_1000.csv` | `airfoil1_sharp_dense_1000.csv` |
| `section_params.csv` | `section_params-multi-airfoil.csv` |

完成实现时至少验证：

- 89 个截面按 `idx` 顺序选择 3 个翼型，三个基准几何各创建一次；
- `idx 33→34` 和 `46→47` 两个翼型切换位置没有截面反向或 Loft 扭曲；
- 完整曲面能封闭为实体，并导出 `.CATPart` 和 `.stp`；
- 缺失或越界引用、空 `airfoil`、大小写冲突和混合后缘拓扑均在 CATIA 启动前失败；
- 现有六列截面文件和单翼型命令保持兼容。

## 真实 CATIA 验证记录

2026-08-07 使用 CATIA P3 V5-6R2020 执行：

```powershell
uv run autoblade create --section section_params-multi-airfoil.csv --keep-failed-part
```

验证结果：

- 300、253、249 点的三个基准样条各创建一次；
- 89 个截面按 `idx` 顺序完成变换，`idx 33→34` 和 `46→47` 的翼型切换未触发 CATIA 更新错误；
- Loft 和 `CloseSurface` 均成功，输出 `output/blade-multi-airfoil.CATPart` 和 `output/blade-multi-airfoil.stp`；
- STEP AP242 包含一个 `MANIFOLD_SOLID_BREP`、一个 `CLOSED_SHELL` 和 7 个 `ADVANCED_FACE`；
- 未生成失败快照，命令结束后的新增 `CNEXT` 进程数为 0。

本次原始点云方案直接通过，因此没有启用或实现共同弦向站位重采样。
