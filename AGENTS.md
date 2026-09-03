# AutoBlade 项目指南

本文是 AI 和维护者的工作入口，只提供文档路由、执行流程和容易造成严重回归的项目边界。公开能力与使用方法以 `README.md` 为准，技术细节以 `docs/` 为准。

## 项目边界

AutoBlade 当前通过 CATIA V5 COM Automation 生成叶片模型，并已提供显式
`sweep`；主 wheel 也支持在 Linux 上安装、导入和执行无 CAD 规划。当前交付目标
是受控团队使用的内部 `v0.x` preview wheel；公共 PyPI、独立 EXE 和 FreeCAD
建模后端都不是已有能力。

## 文档路由

| 修改主题 | 先读 |
| --- | --- |
| 能力、环境和最短用法 | `README.md` |
| 当前任务、优先级和验收条件 | `TODO.md` |
| 技术文档总览 | `docs/index.md` |
| 模块边界、建模流程和 COM 生命周期 | `docs/architecture.md` |
| 命令职责和任务语义 | `docs/design-principles.md`、`docs/cli.md` |
| CSV schema、坐标系、单位和点序 | `docs/input-formats.md` |
| 配置、路径和输出命名 | `docs/configuration.md` |
| 测试分层与真实 CATIA 回归 | `docs/testing.md` |
| 安装、工作区初始化和升级 | `docs/installation.md` |
| 分发范围、支持矩阵和版本策略 | `docs/distribution-scope.md` |
| 内部发布、验证记录和回滚 | `docs/releasing.md` |

## 工作流

- 开始或继续里程碑工作时，先读取 `TODO.md`，按当前活动任务执行，并在交付前遵循其顶部规则同步任务状态和里程碑。
- 开发中先运行与改动对应的测试；非简单改动交付前在 Windows 运行
  `pwsh -File scripts/check.ps1`，在 Linux 运行 `bash scripts/check-linux.sh`。
- 默认 pytest 使用 fake/mock COM。真实 CATIA 冒烟测试只能显式人工执行，并按 `docs/testing.md` 记录环境、输入、CATPart/STEP、特征树和残留 `CNEXT` 进程。

## 不可破坏的边界

- `autoblade.core` 不得导入 `pythoncom`、`win32com` 或持有 CATIA COM 对象；后端不可用时返回项目定义的后端异常。
- CSV 解析、校验、任务规划和输出冲突检查必须在创建 CATIA 会话之前完成，避免无效输入留下隐藏进程。
- Python 领域长度使用 m、旋转使用 deg；只有 CATIA Builder 的 Automation 调用边界把长度转换为 mm。变换顺序不得偏离 `docs/input-formats.md`。
- 每个 `BladeBuildJob` 使用 `DispatchEx` 创建独占、隐藏的 CATIA 实例；不得连接、复用或退出用户已经打开的会话。清理错误不得遮蔽建模根因。
- `create` 只生成一个任务；`batch` 按选中的截面定义生成任务且不做隐式笛卡尔积；
  参数组合只属于显式的 `sweep`。
- 不得绕过 `tests/conftest.py` 的真实 COM 防护。修改输入拓扑、后缘判定或 CATIA 几何编排时，必须补充对应回归。
- 唯一版本源是 `src/autoblade/__init__.py` 的 `__version__`；不要在其他文件建立独立版本值。

## 文档、依赖与产物

- `README.md` 与 `docs/README.cn.md` 保持结构对齐；根 README 的 Markdown 链接使用绝对 HTTPS URL。
- 活动工作维护在 `TODO.md`，稳定技术说明放在命名明确的 `docs/*.md`，完成的里程碑按 TODO 顶部规则归档到 `docs/archive/`。
- 依赖和 Python 范围以 `pyproject.toml` 为源，`uv.lock` 必须同步且不得手工编辑。
- 不提交 `output/`、`dist/`、`build/`、`.venv/`、`.uv/`、缓存、测试临时文件、日志、私有输入、CATPart 或 STEP 产物。
