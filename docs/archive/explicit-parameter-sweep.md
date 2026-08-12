# 显式参数扫描 `sweep` 里程碑

本记录归档 2026-08-12 完成的“显式参数扫描 `sweep`”里程碑。功能提交为
`ba7e647`；提交后的干净工作区已完成统一检查。本里程碑只固定首版显式
Cartesian product，不把 `zip`、全局缩放、桨距或尖部形状纳入既有契约。

## 完成范围

### 独立命令与规划边界

- [x] 增加独立的 `autoblade sweep` 命令、交互入口和 `SweepPlanner`。
- [x] 非交互调用通过重复 `--airfoil` 和 `--section` 显式选择两个维度；目录中的额外文件不会增加任务。
- [x] 只接受六列截面模板；含 `airfoil` 列的自包含文件不能与外部翼型组合。
- [x] 两个维度分别去重排序，并按 airfoil-major 顺序展开稳定 Cartesian product。
- [x] 每个组合复用单任务 Planner 和共享 Executor；CATIA Builder 不包含组合逻辑。

### 清单、预览与 dry-run

- [x] `SweepPlan` 可序列化为 schema version 1 的稳定 JSON 清单。
- [x] 清单记录选择范围、组合类型、有序任务 ID、输入 basename、输出目录、输出名称以及 CATPart/STEP 路径。
- [x] 执行前完整展示选择范围、组合数量、有序任务和已有输出冲突。
- [x] `--dry-run` 在 Executor 边界前返回，不加载或启动 CATIA。
- [x] 同一计划内部的重复输出目标在启动 CATIA 前整体拒绝。

### 兼容性与回归

- [x] 2 个翼型与 `section_params-1.csv` 至 `section_params-5.csv` 精确生成 10 个稳定排序任务。
- [x] 自动化测试封锁真实 COM，并验证 dry-run 不调用 Executor。
- [x] `create` 仍只生成一个明确任务；`batch` 仍不执行隐式参数组合。
- [x] 中英文项目入口、架构、设计原则、CLI 和测试文档已同步。

## 最终验证证据

- [x] 功能提交：`ba7e647 feat(sweep): 实现显式参数扫描与真实示例`。
- [x] 提交后 `git status --porcelain=v1` 为空。
- [x] `scripts/check.ps1` 在该干净提交上通过；当前机器没有可调用的 PowerShell 7 `pwsh.exe`，因此使用脚本明确兼容的 Windows PowerShell 5.1 执行同一完整流程。
- [x] pytest 共 136 项通过，Ruff 通过。
- [x] wheel 与 sdist 构建通过，分别包含 48 和 109 个文件。
- [x] 全新 CPython 3.14.4 环境完成非 editable wheel 安装、命令帮助、版本、工作区初始化、输入预检和 fake Builder 冒烟。
- [x] 分发元数据验证通过；wheel/sdist 内容清单 SHA-256 分别为 `1ac34b35e2330b4841f6bf04712b9054b14ef66d6fc84f614416f01bec432f88` 和 `9240fec82ab491928ef3f95a45884b95ead745780839b6134594a5614c46a208`。

真实 CATIA 几何回归不属于本里程碑新增组合逻辑的验收项；Planner、清单和 dry-run
自动化均在 COM 会话创建前完成。实际建模仍沿用已经验证的共享 Executor 与
CATIA Adapter 边界。
