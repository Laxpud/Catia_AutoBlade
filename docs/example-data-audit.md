# 真实示例数据审计

本文记录 `autoblade init --with-examples` 所复制真实示例的来源、授权、脱敏边界、项目内修改和可复现标识。记录范围只包括一份截面参数和它引用的三个翼型，不自动覆盖 `input/` 中的其他维护者回归资产。

## 来源与再分发授权

- 数据作者：Hannnk
- 作者主页：[https://github.com/Hannnk](https://github.com/Hannnk)
- 联系邮箱：[hannkzhang@gmail.com](mailto:hannkzhang@gmail.com)
- 授权形式：作者本人直接授权，不以某个标准开源数据许可证替代该授权。
- 授权确认：项目维护者于 2026-08-12 确认已经取得作者许可，可以将本记录列出的数据纳入 CATIA AutoBlade 公开仓库、源码归档和 wheel，并通过 `autoblade init --with-examples` 复制到包外用户工作区。

该确认只证明当前四个文件的项目内再分发权。未来加入其他 Hannnk 数据、改变分发项目或无法继续确认授权范围时，必须重新审计，不能沿用本记录推定授权。

## 脱敏与示例边界

公开副本只保留建模所需的数值几何字段、截面序号和通用翼型 ID。检查结果如下：

- CSV 不包含人员、组织、客户、项目、设备型号、本地路径或原始文件位置等识别信息；
- 入口在 wheel 中使用通用名称 `example-blade-sections.csv`，依赖翼型使用可跨示例复用的稳定 ID；
- `--with-examples` 不携带密集点云、零位移分支或其他仅供维护者回归的输入；
- 没有通过扰动弦长、展向位置、扭转角或翼型坐标进行“脱敏”，因为这会把真实几何变为人工样例；几何数据本身的公开分发以作者直接授权为依据。

## 文件清单

SHA-256 对实际进入 wheel 并由 `init` 复制的 LF 字节计算；`.gitattributes` 固定这些包资源的换行符，避免构建平台改变摘要。仓库 `input/` 副本与包资源逐记录内容一致，但 Windows 工作树可能将前者检出为 CRLF，因此不能用其原始字节摘要替代分发摘要。

| 稳定 ID / 入口 | 仓库输入 | wheel / 工作区名称 | 规模 | 项目内修改说明 | SHA-256 |
| --- | --- | --- | ---: | --- | --- |
| `example-multi-airfoil-blade` | `input/blade_sections/blade_sections-multi-airfoil.csv` | `blade_sections/example-blade-sections.csv` | 89 截面 | 数值参数自首次纳入版本控制后未修改；项目将入口改为通用示例名，并把三个翼型引用规范为小写稳定 ID | `f3e1b9d98c796d9d1c8acf8660522fabcbaec59ce7c99ed8b16da362c67999ea` |
| `airfoil1_sharp` | `input/airfoils/airfoil1_sharp.csv` | `airfoils/airfoil1_sharp.csv` | 300 点 | 纳入项目后未修改点坐标；文件 ID 规范为小写 | `fc9dfa453d8547617a0c5f3d36ece38d01e90b0c0582b5c024906fa4c896b077` |
| `airfoil2_sharp` | `input/airfoils/airfoil2_sharp.csv` | `airfoils/airfoil2_sharp.csv` | 253 点 | 纳入项目后未修改点坐标；文件 ID 规范为小写 | `3112030ff5755fd62f064d64f55bd27297e1450bf0b17d7172a18ff06af4fca8` |
| `airfoil3_sharp` | `input/airfoils/airfoil3_sharp.csv` | `airfoils/airfoil3_sharp.csv` | 249 点 | 纳入项目后未修改点坐标；文件 ID 规范为小写 | `2b891ada6dd70414f6b83042dbf7441ddb0133ed81ce3e1a12c233905a6cd8a4` |

“项目内未修改”描述从数据纳入当前 Git 历史后的处理，不推定作者在交付前是否执行过生成、锐化或其他预处理。

## 验证证据

- `tests/test_workspace_init.py` 验证 `--with-examples` 只复制上述四份数据，并构造包含 89 个截面、三个唯一翼型的完整输入计划。
- `tests/test_repository_inputs.py` 验证引用闭合、点数、顺序、尖后缘拓扑和 CATIA 启动前预检。
- 2026-08-07 在 CATIA P3 V5-6R2020 中完成 89 截面 Loft、`CloseSurface` 实体封闭、CATPart 保存和 STEP AP242 导出；详细结果见[展向多翼型设计](multi-airfoil-design.md#真实-catia-验证记录)。
- 2026-08-12 完成 `blade_sections` 直接命名迁移后，140 项 pytest 和 Ruff 检查通过；四组仓库输入与 wheel 资源的 CSV 记录分别一致。

增加、替换或修改这里的任一文件时，必须重新计算摘要、复查授权和脱敏边界，并重新执行输入预检；改变点云或截面拓扑时还必须补做真实 CATIA 回归。
