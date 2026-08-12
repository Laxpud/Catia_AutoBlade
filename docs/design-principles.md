# 设计原则

本文记录命令、模型输入和任务执行的稳定语义。参数细节见 [CLI 参考](cli.md)，CSV 字段见[输入数据格式](input-formats.md)。

## 命令职责

| 命令 | 职责 | 任务数量 | 当前状态 |
| --- | --- | --- | --- |
| `create` | 接收一个明确模型定义 | 1 个 `BladeBuildJob` | 已实现 |
| `batch` | 执行多个已经闭合输入引用的模型定义 | N 个 `BladeBuildJob` | 已实现 |
| `sweep` | 显式组合多个设计变量 | N × M 个 `BladeBuildJob` | 已实现首版 Cartesian product |

`batch` 的“多个”来自多个截面定义，不来自目录中碰巧存在的多个翼型。多个六列截面模板可以统一绑定一个显式翼型；多个翼型与多个模板的组合只能由 `sweep` 明确表达。这样新增输入文件不会静默改变已有批处理或扫描的任务数。

首版 `sweep` 只接受用户逐项给出的翼型 basename 和六列模板 basename，按翼型、模板各自字典序去重后生成 airfoil-major Cartesian product。目录中其他文件不参与扫描；含 `airfoil` 列的自包含定义不能再与外部翼型组合。`zip`、全局缩放、桨距和尖部形状均不属于当前契约。

## 模型输入模式

截面参数文件有两种互斥模式：

- 六列表头是几何模板。它尚未闭合翼型引用，非交互调用必须使用 `--airfoil` 绑定一个翼型；交互向导会在选定模板后询问翼型。
- 含 `airfoil` 列的七列表头是自包含模型定义。每个有效截面行都必须填写翼型 basename，不允许空值、继承上一行、目录分量或外部 `--airfoil` 覆盖。

同一六列模板可以在不同的 `create` 调用中绑定不同翼型，这是有意保留的设计能力。逐行混合翼型只通过文件内的 `airfoil` 列表达。

## Planner、Job 与 Executor

显式 CLI 和交互菜单共享同一执行链：

```text
CLI 参数或交互选择
  -> Planner：解析 CSV、闭合引用、校验输出冲突
     （SweepPlanner 只在本层展开显式 Cartesian product）
  -> BladeBuildJob：确定输入计划、输出位置和建模选项
  -> Executor：逐任务调用建模流程并返回 BuildResult
  -> CATIA：建模、保存、导出和资源清理
```

Planner 在 CATIA 会话创建前解析所有输入，包括唯一翼型、逐截面引用、点序、后缘拓扑、输出名称和同批次目标冲突。`SweepPlan` 额外保存选择范围、组合类型和有序任务，并可序列化为带 schema 版本的稳定 JSON 清单。Executor 不根据目录内容推断模型，也不知道任务来自 `create`、`batch` 还是 `sweep`。

批处理保留每个任务的成功或失败结果。某个任务失败后，Executor 继续后续任务；只要存在失败，命令最终退出码就是 1。

## 交互与脚本边界

- 无参数 `autoblade` 只在真实 TTY 中打开顶层菜单；非 TTY 中显示帮助并以 2 退出，避免 CI 或管道等待输入。
- 显式子命令是脚本和可复现调用的稳定接口。`create --interactive`、`batch --interactive` 与 `sweep --interactive` 可直接进入对应向导。
- 交互层只收集选择与确认。模型校验、任务数量和输出冲突仍由 Planner 决定。
- 启动 CATIA 前始终显示任务模式、任务数和输出路径；已有同名文件会标记为 `overwrite`。确认取消不会创建 CATIA 会话。
- `sweep --dry-run` 完整显示选择范围、组合数量、任务预览、磁盘覆盖风险和稳定清单，并在 Executor 边界前返回。

## 兼容性原则

输入目录仍由 `config.toml` 配置，当前不物理拆分 `input/examples/` 与 `input/regression/`。版本化资产数量较小，先在 `input/README.md` 中明确用途；若未来拆分，必须先设计扫描迁移和配置兼容策略。

`autoblade-create` 与 `autoblade-batch` 保留为兼容入口，并与对应子命令共享参数和退出码。Python 层旧的批处理入口仍不接受多个翼型生成隐式组合；调用方应使用 `sweep` 或显式逐次调用。
