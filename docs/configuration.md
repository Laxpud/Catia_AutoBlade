# 运行时配置

根目录的 `config.toml` 是 CLI、文件扫描和核心建模 API 的默认配置来源。程序启动时在当前工作目录查找该文件；如果文件不存在，则使用与仓库默认配置等价的内置值。

## 路径解析

路径按以下规则转换为绝对路径后再进入建模流程：

| 配置或参数 | 相对路径基准 | 说明 |
| --- | --- | --- |
| `paths.input_dir` | `config.toml` 所在目录 | 输入树根目录 |
| `paths.output_dir` | `config.toml` 所在目录 | 未传 `--output` 时的输出根目录 |
| `paths.airfoil_dir` | 解析后的 `input_dir` | 翼型 CSV 目录 |
| `paths.section_params_dir` | 解析后的 `input_dir` | 截面参数 CSV 目录 |
| CLI `--output` | 启动命令时的工作目录 | 显式值优先于 `paths.output_dir` |

任何绝对路径都会保持为绝对路径，不再与上述基准拼接。专用输入目录设计为 `input_dir` 的相对子目录，因此可以只修改 `input_dir` 来整体迁移输入树；如果输入文件分散在不同位置，也可以分别为两个专用目录配置绝对路径。

默认目录配置为：

```toml
[paths]
input_dir = "input"
output_dir = "output"
airfoil_dir = "airfoils"
section_params_dir = "section_params"
```

## CLI 覆盖优先级

`create` 和 `batch` 的 `--output` 显式参数覆盖配置输出目录。未传该参数时，普通模式和交互模式都以 `paths.output_dir` 为默认值。翼型和截面参数文件名仍通过 `--airfoil`、`--section` 选择，但候选文件始终从配置的两个输入目录扫描。

## 输出命名模板

`defaults.output_name_template` 同时用于单模型和批处理，可使用以下字段：

| 字段 | 值 |
| --- | --- |
| `{airfoil}` | 翼型文件名去除 `.csv` 后的 stem |
| `{idx}` | `section_params-` 后的标识；没有该前缀时使用截面参数文件 stem |
| `{section}` | 截面参数文件名去除 `.csv` 后的完整 stem |
| `{author}` | `defaults.author` |

默认模板为 `{airfoil}_blade-{idx}`。模板必须生成单个非空文件名，不能包含目录；未知字段会在启动 CATIA 前报告错误。

## 查看与修改

```powershell
uv run autoblade config show
uv run autoblade config set --key output_dir --value generated
uv run autoblade config set --key output_name_template --value "{airfoil}_{section}"
uv run autoblade config reset
```

`config show` 显示持久化的原始值，而不是解析后的绝对路径，便于确认配置文件是否仍可跨目录移动。
