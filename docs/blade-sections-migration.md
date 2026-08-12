# `section_params` → `blade_sections` 命名迁移

本记录说明 2026-08-12 完成的用户可见命名迁移。项目维护者确认当前项目尚未大规模
使用，因此不再引入长期别名和弃用警告期，直接把“一份 CSV 定义一片桨叶的展向截面
布置”统一命名为 `blade_sections`。

## 当前契约

| 表面 | 当前名称或行为 |
| --- | --- |
| 工作区目录 | `input/blade_sections/` |
| 配置 | schema `3.0.0`；`paths.blade_sections_dir = "blade_sections"` |
| 仓库输入文件 | `blade_sections-<blade-id>.csv`、`blade_sections-multi-airfoil.csv`、`blade_sections-naca.csv` |
| wheel 示例 | `input/blade_sections/example-blade-sections.csv` |
| Python API 与任务模型 | `blade_sections_dir`、`blade_sections_filename`、`blade_sections_files`、`blade_sections_path` 等 |
| `sweep` JSON | schema version 2；选择范围和任务字段使用 `blade_sections` |
| 输出命名 | `{idx}` 识别 `blade_sections-` 前缀；`{section}`、`{blade}` 继续可用 |

CLI `--section`、CSV 单行领域对象 `section`、输出模板 `{section}`/`{blade}` 和 CATIA
内部截面特征名没有改名。这些名称表达的是单个截面或一次选择，不是文件集合。

## 破坏性边界

- 旧 `input/section_params/` 不再被默认扫描，初始化器也不再创建该目录。
- 旧 Python 关键字和 `BladeBuildJob`/`SweepPlan` 属性没有保留别名；调用方必须同步
  改为 `blade_sections_*`。
- `sweep` schema version 1 的 `section_params` JSON 字段不再由当前序列化器输出；清单
  消费者必须升级到 schema version 2。
- 仓库和 wheel 示例的 CSV basename 已同步改名。输出模板字段保持不变，但显式使用
  完整 CSV stem 的输出名称会随新 basename 改变。
- 历史归档保留旧名，用于复现当时的命令、清单和发布证据。

## 旧工作区迁移

旧配置可以由当前 CLI 显式迁移：

```powershell
autoblade config migrate
autoblade config migrate --apply
```

预览会显示 schema `1.0.0`/`2.0.0` 到 `3.0.0` 的变化；`--apply` 先创建
`config.toml.v<旧版本>.bak[.N]`，再把 `paths.section_params_dir` 改为
`paths.blade_sections_dir`。旧值是默认 `section_params` 时同步改为 `blade_sections`；
自定义或绝对目录值保持不变。

配置迁移不会移动用户数据。使用旧默认工作区时，维护者还需要在执行命令前：

1. 将 `input/section_params/` 改名为 `input/blade_sections/`；
2. 将标准文件前缀 `section_params-` 改为 `blade_sections-`；
3. 更新脚本、Python 调用和 `sweep` 清单消费者；
4. 先运行 `autoblade list` 或 `sweep --dry-run` 确认发现结果和输出名称，再启动 CATIA。

如果旧配置同时包含新旧两个目录键，迁移器会安全失败，要求维护者先人工保留一个，
避免猜测优先级。

## 验收范围

本次盘点和修改覆盖工作区与包资源目录、配置 schema、CLI 文案、Python API、Planner/
Executor 任务模型、`sweep` JSON、输出命名、构建清单、安装冒烟、真实 CATIA 脚本、
自动化测试和中英文文档。数值 CSV 内容及 `--section` 的单项选择语义没有改变。

2026-08-12 最终统一检查通过 140 项 pytest、Ruff、wheel/sdist 构建、两个全新
非 editable 安装工作区冒烟和 49/117 文件分发清单校验。安装冒烟确认示例工作区
只创建 `input/blade_sections/example-blade-sections.csv`，配置使用 schema `3.0.0`。
