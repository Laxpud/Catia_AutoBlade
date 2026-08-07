# 输入数据目录

本目录只保存可公开版本化、用于最短示例或真实 CATIA 回归的输入。生成结果、私有/客户数据和 pytest 专用失败样例不得放在这里。

## 资产边界

- **示例**用于最短使用路径，同时可以被真实回归复用。
- **真实 CATIA 回归**记录曾经成功建模、后续版本必须继续成功的代表性模型；默认 `pytest` 不启动 CATIA。
- **pytest 夹具**只服务自动化测试。共享夹具应放在 `tests/fixtures/`；当前小型输入全部由 `tmp_path` 构造，因此不创建空目录。预期失败 CSV 不得进入普通输入扫描目录。

当前不物理拆分 `input/examples/` 和 `input/regression/`。现有扫描契约只读取 `airfoils/` 与 `section_params/`，资产数量仍适合在本文件维护清单；未来拆分前必须先设计配置和扫描迁移。

## 截面参数资产

| 文件 | 分类与用途 | 推荐命令 | 预期结果 / CATIA |
| --- | --- | --- | --- |
| `section_params-1.csv` 至 `section_params-5.csv` | 单翼型 batch 回归组，每份 26 个截面 | `uv run autoblade batch --interactive`，只选择这五个文件并绑定 `sc1095.csv` | 精确规划 5 个任务并生成实体；真实几何检查需要 CATIA |
| `section_params-multi-airfoil.csv` | 89 截面、300/253/249 点、三翼型切换回归 | `uv run autoblade create --section section_params-multi-airfoil.csv` | Loft、`CloseSurface`、CATPart、STEP AP242 成功；需要 CATIA，2026-08-07 已验证 |
| `section_params-naca.csv` | NACA 0012 零旋转/零位移分支回归 | `uv run autoblade create --airfoil naca0012_sharp.csv --section section_params-naca.csv` | 至少一个截面三轴平移均为 0；真实实体检查需要 CATIA |

`section_params-naca.csv` 保留现有名称：它已清楚表达对应翼型，改变名称只会破坏历史命令和外部记录，额外编码“zero translation”不会增加稳定模型身份。

## 翼型资产

| 文件 | 主要用途 |
| --- | --- |
| `sc1095.csv` | 代表性钝后缘翼型和单翼型示例 |
| `sc1095_sharp.csv`、`sd7032_sharp.csv` | 尖后缘单翼型回归与不同点数输入 |
| `airfoil1_sharp.csv`、`airfoil2_sharp.csv`、`airfoil3_sharp.csv` | 89 截面多翼型回归的三个引用翼型 |
| `airfoil1_sharp_dense_1000.csv` | 密集点云、实际前缘极值和 Loft 稳定性历史缺陷回归 |
| `naca0012_sharp.csv` | `section_params-naca.csv` 的零位移/零旋转回归翼型 |

文件名统一使用 ASCII 小写字母、数字、连字符和下划线；CSV 内的 `airfoil` 值只引用 `airfoils/` 下的精确 basename。私有、客户或大体量数据应通过 `config.toml` 把输入目录指向仓库外位置。

完整字段、单位和点序约束见[输入数据格式](../docs/input-formats.md)，命令选择与任务数量见 [CLI 参考](../docs/cli.md)，真实多翼型结果见[展向多翼型设计](../docs/multi-airfoil-design.md)。
