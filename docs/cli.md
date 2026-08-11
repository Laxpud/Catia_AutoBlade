# CLI 参考

本文是 CATIA AutoBlade 命令行行为的唯一详细参考。输入字段见[输入数据格式](input-formats.md)，配置路径见[运行时配置](configuration.md)，命令职责的设计理由见[设计原则](design-principles.md)。

## 入口与交互模式

在真实终端中不带参数运行：

```powershell
uv run autoblade
```

程序打开顶层菜单，可进入单模型创建、批处理、输入列表和配置管理。菜单会显示未来 `sweep`，但明确标记为尚未实现；一次操作结束或取消后返回顶层菜单。正常退出返回 0，`Ctrl+C` 返回 130。

标准输入或输出不是 TTY 时，无参数调用不会等待输入，而是显示帮助并返回 2。自动化脚本应始终使用显式子命令。

查看由 `src/catia_autoblade/__init__.py` 提供的安装版本：

```powershell
uv run autoblade --version
```

该命令不读取配置、不进入菜单，也不加载 CATIA COM 后端。

主入口可在子命令之前固定配置来源：

```powershell
autoblade --config C:\Engineering\blade-workspace\config.toml list
```

没有显式参数时依次使用当前工作区配置、用户级配置和内置默认值；完整优先级见
[运行时配置](configuration.md)。

## `init`

```text
autoblade init TARGET [--with-examples] [--force] [--interactive]
```

`TARGET` 必须显式给出。命令先展示所有受影响路径，然后在目标中创建
`config.toml`、`input/airfoils/`、`input/section_params/` 和 `output/`；
`--with-examples` 复制随 wheel 分发的最小只读模板。目标不能位于
`site-packages` 内。

已存在的受管理文件默认导致退出码 1，且执行前不创建任何计划项。`--force` 允许
脚本替换这些明确列出的文件；`--interactive` 允许人工确认。两种方式都不会删除
目标中的其他文件。安装、升级和卸载不会自动调用 `init`。

## `doctor`

```powershell
autoblade doctor
autoblade --config C:\Engineering\blade-workspace\config.toml doctor
```

诊断摘要覆盖 Windows/CPU、Python、`pywin32`、当前线程 COM 初始化、CATIA
ProgID 注册、配置来源/schema、输入目录、输出写权限和支持基线。它只读注册表并
配对 `CoInitialize`/`CoUninitialize`，不会调用 `Dispatch`/`DispatchEx`、连接
用户会话或消耗 CATIA 许可证。明确缺失前置条件返回 1；需要人工确认 CATIA
版本的 `WARN` 不单独导致失败。

## 输入文件模式

| 截面文件 | 是否需要 `--airfoil` | 含义 |
| --- | --- | --- |
| 六列文件 | 非交互调用必需 | 一个需要绑定翼型的几何模板 |
| 含 `airfoil` 列 | 禁止 | 每行引用明确翼型的自包含模型定义 |

文件参数都是配置目录下的精确 CSV basename，不接受任意路径。候选目录、相对路径基准和输出命名模板见[运行时配置](configuration.md)。

## `create`

```text
autoblade create [--airfoil NAME] --section NAME [--output DIR]
                 [--interactive] [--keep-failed-part]
```

`create` 规划并执行一个 `BladeBuildJob`。

| 参数 | 默认行为 |
| --- | --- |
| `--section`, `-s` | 非交互模式必需；交互模式缺省时提示选择 |
| `--airfoil`, `-a` | 六列文件在非交互模式必需；交互模式缺省时提示选择；自包含文件禁止 |
| `--output`, `-o` | 使用 `config.toml` 的 `paths.output_dir`；显式相对路径按当前工作目录解析 |
| `--interactive`, `-i` | 直接进入创建向导，并在任务预览后询问是否启动 CATIA |
| `--keep-failed-part` | 建模失败时在清理前保存不覆盖历史的 `*_failed.CATPart`；不导出失败 STEP |

常用调用：

```powershell
uv run autoblade create --airfoil sc1095.csv --section section_params-1.csv
uv run autoblade create --section section_params-multi-airfoil.csv
uv run autoblade create --interactive
```

以下调用会在启动 CATIA 前失败：六列文件缺少 `--airfoil`、找不到显式文件、自包含文件同时提供 `--airfoil`、CSV 校验失败或输出命名模板不适用于当前模式。

## `batch`

```text
autoblade batch [--airfoil NAME] [--section NAME] [--output DIR]
                [--list] [--interactive]
```

`batch` 为每个选中的截面文件生成一个任务，不执行翼型与模板的笛卡尔积。

| 参数 | 默认行为 |
| --- | --- |
| `--section`, `-s` | 指定一个截面文件；缺省时使用扫描到的全部截面文件 |
| `--airfoil`, `-a` | 统一绑定所有选中的六列模板；只选择自包含文件时禁止 |
| `--output`, `-o` | 使用配置输出目录作为批次根目录 |
| `--list`, `-l` | 只列出候选翼型、截面文件及其模式，不创建任务或启动 CATIA |
| `--interactive`, `-i` | 交互选择多个截面文件、必要时选择一个翼型，并确认任务预览 |

批次可以同时包含六列模板和自包含文件。外部翼型只绑定六列模板，不改变自包含文件中的逐行引用。例如在交互向导中只选仓库的五个单翼型回归模板，再绑定同一个翼型时，精确产生五个任务：

```powershell
uv run autoblade batch --interactive
```

非交互模式不传 `--section` 时会使用扫描到的全部截面文件；因此 `autoblade batch --airfoil sc1095.csv` 的任务数会包含仓库中的其他六列模板和自包含定义。

如果一个任务失败，后续任务仍会执行；最终汇总保留每项结果，并以退出码 1 表示部分失败。单翼型输出按翼型 stem 建子目录，自包含输出按截面文件 stem 建子目录。

## `list`

```powershell
uv run autoblade list
uv run autoblade list --config
```

默认列出配置输入目录中的翼型，以及标记为 `six-column template` 或 `self-contained` 的截面文件。`--config` 显示持久化配置值，不运行 Planner 或 CATIA。

## `config`

```powershell
uv run autoblade config show
uv run autoblade config set --key output_dir --value generated
uv run autoblade config reset
uv run autoblade config migrate
uv run autoblade config migrate --apply
```

`show` 查看配置来源、schema 和持久化值；`set` 需要同时提供 `--key` 与
`--value`；`reset` 恢复内置默认值。可设置键为 `input_dir`、`output_dir`、
`airfoil_dir`、`section_params_dir`、`author` 和 `output_name_template`。

`migrate` 默认只预览已知旧 schema 的字段变化；`--apply` 创建不覆盖已有文件的
备份后原子迁移。未知字段、未来版本和预览后被其他进程修改的配置会安全失败。
路径解析与兼容规则见[运行时配置](configuration.md)。

## 任务预览与覆盖

Planner 完成后、CATIA 启动前，命令输出：

- 任务总数；
- 每个任务的单翼型或多翼型模式；
- 翼型绑定或 `per-section references`；
- 截面文件和输出目标；
- 已存在且将被覆盖的 `.CATPart` 或 `.stp` 文件名。

显式非交互命令按既有契约直接执行并覆盖同名成功输出。交互模式默认不确认执行，用户确认后才会创建 CATIA 会话。

## 独立兼容入口

以下入口分别与 `autoblade create`、`autoblade batch` 使用相同参数和退出码：

```powershell
uv run autoblade-create --airfoil sc1095.csv --section section_params-1.csv
uv run autoblade-batch --airfoil sc1095.csv
uv run autoblade-create --version
uv run autoblade-batch --version
```

新脚本优先使用主命令子命令形式；独立入口用于兼容既有调用。

## 退出码与输出流

| 退出码 | 含义 |
| --- | --- |
| 0 | 帮助、初始化、列表、配置、诊断或全部建模任务成功；交互操作安全取消 |
| 1 | 初始化冲突、环境诊断、输入、配置、Planner、建模、保存、导出或 batch 部分失败 |
| 2 | Typer 参数用法错误，或非 TTY 中无参数调用 |
| 130 | 用户使用 `Ctrl+C` 中断 |

普通信息、任务预览和成功汇总写入标准输出；统一的 `[ERROR]` 错误写入标准错误。领域异常会保留文件路径、CSV 行号和字段信息，命令处理层不会打印错误后正常返回。

## 尚未实现的 `sweep`

`sweep` 将用于显式组合多个翼型与多个六列模板，并生成 N × M × … 个任务。当前没有 `autoblade sweep` 子命令；`batch` 不临时代行参数扫描。规划与验收标准见根目录 [TODO](../TODO.md)。
