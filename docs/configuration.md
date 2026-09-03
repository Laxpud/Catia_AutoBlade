# 运行时配置

`config.toml` 是 CLI、文件扫描和核心建模 API 的配置来源。主 CLI 每次调用按
以下稳定优先级发现一次配置，所有子命令和交互菜单复用同一结果：

1. 顶层显式 `autoblade --config PATH ...`；
2. 启动目录中的 `config.toml`；
3. 规范用户级 `%APPDATA%\autoblade\config.toml`（Linux 为
   `$XDG_CONFIG_HOME/autoblade/config.toml`，未设置 XDG 时使用
   `~/.config/autoblade/config.toml`）；
4. 仅当规范路径不存在时，读取旧 `catia-autoblade/config.toml` 并发出迁移警告；
5. 内置默认值。

新旧用户目录同时存在时，新目录是唯一来源，旧目录不会合并或覆盖它。工作区配置
仍高于两种用户级路径。

显式相对配置路径按启动目录解析。内置默认值不会自动写入磁盘，其输入和输出
相对路径仍以启动目录为基准。需要长期可编辑的工作区时，应使用 `autoblade init
<显式目标>`，不要依赖当前目录偶然存在的文件。

## 路径解析

路径按以下规则转换为绝对路径后再进入建模流程：

| 配置或参数 | 相对路径基准 | 说明 |
| --- | --- | --- |
| `paths.input_dir` | `config.toml` 所在目录 | 输入树根目录 |
| `paths.output_dir` | `config.toml` 所在目录 | 未传 `--output` 时的输出根目录 |
| `paths.airfoil_dir` | 解析后的 `input_dir` | 翼型 CSV 目录 |
| `paths.blade_sections_dir` | 解析后的 `input_dir` | 桨叶截面定义 CSV 目录 |
| CLI `--output` | 启动命令时的工作目录 | 显式值优先于 `paths.output_dir` |

任何绝对路径都会保持为绝对路径，不再与上述基准拼接。专用输入目录设计为 `input_dir` 的相对子目录，因此可以只修改 `input_dir` 来整体迁移输入树；如果输入文件分散在不同位置，也可以分别为两个专用目录配置绝对路径。

默认目录配置为：

```toml
[paths]
input_dir = "input"
output_dir = "output"
airfoil_dir = "airfoils"
blade_sections_dir = "blade_sections"
```

## CLI 覆盖优先级

顶层 `--config` 先固定配置来源；`create` 和 `batch` 的 `--output` 再覆盖该配置
的输出目录。未传输出参数时，普通模式和交互模式都以 `paths.output_dir` 为默认
值。六列截面文件通过 `--airfoil` 绑定一个翼型；包含 `airfoil` 列的文件自行
定义全部截面引用，不能再与 `create --airfoil` 组合。`batch --airfoil` 只绑定
同批次的六列模板，不改变自包含文件。候选文件始终从选中配置的两个输入目录
扫描。

## 配置 schema 与兼容性

`AppConfig.version` 是持久化配置格式版本，不是包的 `__version__`。当前 schema
为 `3.0.0`：它把用户可见集合从 `section_params` 统一命名为 `blade_sections`，
并延续专用输入目录相对 `paths.input_dir` 解析的语义。

历史 `1.0.0` 配置曾把专用目录写成包含 `input` 的路径；`2.0.0` 修复了路径
解析，但仍使用 `paths.section_params_dir`。当前程序会：

- 在内存中把已知 `1.0.0`、`2.0.0` 或无版本配置转换为当前模型，但不改写原文件；
- 对旧 schema 发出迁移提示，并阻止 `config set`、`config reset` 顺便升级；
- 拒绝未知字段，避免旧程序忽略新版数据后在保存时将其删除；
- 当前 schema 若仍写入 `paths.section_params_dir`，会明确提示改用
  `paths.blade_sections_dir`；
- 对高于 `3.0.0` 的配置安全失败并要求升级程序；对未支持的旧版本同样失败。

迁移器只实现真实存在的 `1.0.0/2.0.0 → 3.0.0` schema 路径和旧产品用户目录到
`autoblade` 目录的位置迁移，没有通用插件式迁移框架。

## 输出命名模板

`defaults.output_name_template` 同时用于单模型和批处理，可使用以下字段：

| 字段 | 值 |
| --- | --- |
| `{airfoil}` | 翼型文件名去除 `.csv` 后的 stem |
| `{idx}` | `blade_sections-` 后的标识；没有该前缀时使用桨叶截面定义文件 stem |
| `{section}` | 桨叶截面定义文件名去除 `.csv` 后的完整 stem |
| `{author}` | `defaults.author` |
| `{blade}` | 模式无关的完整叶片名；单翼型为 `<airfoil>_blade-<idx>`，多翼型为 `blade-<idx>` |

默认模板为 `{blade}`，因此现有单翼型输出名称保持不变，多翼型样例输出为 `blade-multi-airfoil`。`{airfoil}` 只在单翼型模式可用；多翼型若使用该字段会在启动 CATIA 前报告错误。模板必须生成单个非空文件名，不能包含目录；未知字段同样会提前报错。

## 查看与修改

```powershell
uv run autoblade config show
uv run autoblade config set --key output_dir --value generated
uv run autoblade config set --key output_name_template --value "{blade}"
uv run autoblade config reset
uv run autoblade config migrate
uv run autoblade config migrate --apply
```

`config show` 显示来源、schema 和持久化值，而不是解析后的绝对路径。`config
migrate` 会预览 schema 字段与用户目录目标；`--apply` 先验证文件自预览后没有
变化，再创建 `config.toml.v<旧版本>.bak[.N]`。schema 迁移在原路径原子替换；
旧用户目录迁移原子写入规范路径，成功后移除旧活动 `config.toml` 并保留备份。
迁移会把相对 `input_dir`/`output_dir` 改写为从新目录指向同一实际位置的值，避免
静默切换数据根。旧默认值 `section_params` 会改为 `blade_sections`，但迁移不会
读取、移动或覆盖翼型、桨叶截面定义、CATPart 或 STEP；旧工作区还需按
[命名迁移记录](blade-sections-migration.md)显式改名目录和标准 CSV basename。

完整的安装、升级、卸载和回滚流程见[安装、工作区与升级](installation.md)。
