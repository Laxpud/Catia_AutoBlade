# 安装、工作区与升级

本文说明受支持的源码开发和内部 preview wheel 安装流程。公共 PyPI、独立
EXE、未经验证的 Python/CATIA 组合都不是当前安装渠道；支持基线见[分发范围
与支持策略](distribution-scope.md)。

## 前置条件

- Windows 11 x64；
- CPython 3.14.x x64；
- 可正常注册 COM Automation 的 CATIA P3 V5-6R2020 和所需许可证；
- `uv`；wheel 安装时会解析并安装 `pywin32==311` 等 Python 依赖。

安装 Python 包不等于 CATIA 已经可用。首次建模前应运行 `autoblade doctor`，
并由工程人员确认 CATIA 版本、许可证和目标模型结果。

## 安装内部 wheel

内部 wheel 只能来自带版本、SHA-256、验证记录和来源标签的受控制品集。不要
安装聊天附件、开发机临时构建或版本号相同但校验和不同的 wheel。

```powershell
uv venv .venv --python 3.14
$wheel = (Resolve-Path .\autoblade-*-py3-none-any.whl).Path
uv pip install --python .venv\Scripts\python.exe $wheel
.\.venv\Scripts\Activate.ps1
autoblade --version
```

从旧产品身份升级时应优先创建全新虚拟环境；复用环境前必须先卸载
`catia-autoblade`。新 wheel 不提供 `catia_autoblade` shim，并会在检测到两个
distribution 共存时要求先卸载旧包，避免同名 console script 指向混合代码。

wheel 安装到虚拟环境，用户工作区必须位于 `site-packages` 之外。初始化器只在
显式目标中创建受管理文件：

```powershell
autoblade init C:\Engineering\blade-workspace --with-examples
cd C:\Engineering\blade-workspace
autoblade doctor
autoblade list
```

`--with-examples` 会安装 `example-blade-sections.csv` 以及
`airfoil1_sharp.csv`、`airfoil2_sharp.csv`、`airfoil3_sharp.csv`。这四个文件
共同构成已验证的 89 截面多翼型真实桨叶示例。

只需要全部已审计翼型和目录清单时使用：

```powershell
autoblade init C:\Engineering\airfoil-workspace --with-airfoil-library
```

该选项不复制截面示例；也可以与 `--with-examples` 同时使用。目录当前只包含三个
已获 Hannnk 直接再分发授权的翼型，未审计的源码回归输入不会被隐式复制。完整
清单和准入规则见[内置翼型目录](airfoil-library.md)。

`init` 会先展示 `config.toml`、三个目录和可选数据资源的完整计划。已存在的受管理
文件默认不会覆盖；脚本可显式使用 `--force`，人工会话可使用 `--interactive`
逐次确认。目标中的其他文件永远不会被删除。

## 源码开发安装

维护者在受控 checkout 中使用冻结锁文件：

```powershell
uv sync --frozen --extra dev
uv run autoblade --version
pwsh -File scripts/check.ps1
```

源码 editable 环境只用于开发，不可替代内部 wheel 的全新环境安装冒烟。

## 配置发现

每次主 CLI 调用只选择一个配置来源，优先级固定为：

1. 顶层 `--config PATH`；
2. 启动目录中的 `config.toml`；
3. 用户级 `%APPDATA%\autoblade\config.toml`；
4. 仅当新路径不存在时读取旧 `%APPDATA%\catia-autoblade\config.toml` 并警告；
5. 以内置默认值运行，路径基准为启动目录但不自动创建配置文件。

Linux 的对应路径为 `$XDG_CONFIG_HOME/autoblade/config.toml` 与旧
`catia-autoblade/config.toml`；未设置 XDG 时以 `~/.config` 为根。两个用户目录
同时存在时只使用新目录。

显式相对配置路径按启动目录解析。选择后，所有子命令和交互菜单复用同一个
`ConfigManager`，不会因后续切换目录重新发现另一个工作区。完整路径语义见
[运行时配置](configuration.md)。

## 升级与配置迁移

升级 wheel 只替换虚拟环境中的包，不移动或删除工作区的配置、输入、输出、
CATPart 或 STEP。升级前先备份组织要求保留的模型数据，再安装新 wheel 并运行：

```powershell
autoblade --config C:\Engineering\blade-workspace\config.toml config migrate
autoblade --config C:\Engineering\blade-workspace\config.toml config migrate --apply
autoblade --config C:\Engineering\blade-workspace\config.toml doctor
```

第一次命令只预览字段变化；`--apply` 会确认原配置自预览后未被修改，创建不
覆盖既有备份的 `config.toml.v<旧版本>.bak[.N]`，再原子替换配置。普通读取只在
内存兼容旧 schema，`config set` 和 `config reset` 不会顺便静默迁移。升级自
schema `1.0.0` 或 `2.0.0` 时，配置会改为 `blade_sections_dir`，但工具不会移动
外部数据；还必须按[命名迁移记录](blade-sections-migration.md)将旧默认目录和标准
CSV basename 显式改名。

如果当前没有工作区配置且程序回退读取旧用户目录，直接运行 `autoblade config
migrate` 可同时预览配置位置；`--apply` 会把活动配置写入新目录、保留旧文件备份，
并保持相对 input/output 根的实际解析位置不变。回滚时先移走新目录中的
`config.toml`，再把旧目录的 `.bak` 复制回 `config.toml`。

## 卸载与回滚

```powershell
uv pip uninstall --python .venv\Scripts\python.exe autoblade
```

卸载包或删除虚拟环境不会删除外部工作区。版本回滚时安装上一份已批准 wheel；
如果新版本已经迁移配置，先退出所有 AutoBlade 进程，再使用对应 `.bak` 恢复
`config.toml`。不要混用不同版本但相同文件名的内部制品。

## 常见失败

| 现象 | 处理 |
| --- | --- |
| 报告旧 `catia-autoblade` distribution 共存 | 先卸载旧包，再重新安装批准的 `autoblade` wheel |
| `doctor` 报 Python 或 pywin32 不匹配 | 重新创建 CPython 3.14 x64 环境并安装批准 wheel |
| CATIA 注册失败 | 修复 CATIA 安装/COM 注册；不要通过连接用户会话绕过检查 |
| 找不到输入目录 | 核对 `--config` 来源及配置文件相对路径基准 |
| 配置来自更新 schema | 升级 AutoBlade；旧程序不会忽略新字段继续写入 |
| `init` 报文件冲突 | 审阅预览，人工用 `--interactive`，脚本确认后用 `--force` |
| 输出不可写 | 修改 `paths.output_dir` 或目录权限，再运行 `doctor` |

诊断摘要适合直接复制到内部问题单，但应先移除组织路径、用户名等敏感信息。
