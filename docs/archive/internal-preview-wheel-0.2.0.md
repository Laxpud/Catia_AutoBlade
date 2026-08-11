# `v0.2.0` 内部 preview wheel 里程碑

本记录归档 2026-08-11 完成的“可安装的内部 preview wheel”里程碑。发布标签 `v0.2.0` 指向提交 `1d479ff84a9b8e68abfa830a64cd37f42a4f6ce1`；标签之后的文档提交只负责归档任务状态，不改变已验证源码和发布制品。

## 完成范围

### 工作区初始化与配置发现

- [x] 增加 `autoblade init`，在显式目标目录创建 `config.toml`、输入目录、输出目录和可选最小示例。
- [x] 默认不覆盖已有文件；`--force` 或交互确认前会展示全部受影响路径。
- [x] 固定配置发现优先级：显式 `--config`、当前工作区、用户级配置、内置默认值。
- [x] 包内只保留不可变模板资源，用户配置、输入和输出始终位于 `site-packages` 之外。

### 可审计构建与安装冒烟

- [x] Hatchling wheel 固定包含 `src/catia_autoblade`，sdist 明确包含重建所需源码、测试、许可证、锁文件和构建配置。
- [x] 分发校验器拒绝缓存、虚拟环境、CAD/日志产物、私有输入和本地绝对路径，并为 wheel/sdist 生成排序内容清单。
- [x] 在全新 CPython 3.14 环境中非 editable 安装 wheel，验证三个命令入口、工作区初始化、配置读取、输入预检和 fake Builder 路径。

### 配置 schema 演进与用户数据保护

- [x] 配置 schema 升级到 `2.0.0`，并修复历史 `1.0.0` 配置路径出现双重 `input` 前缀的问题。
- [x] 历史配置默认只在内存中兼容读取；只有显式执行 `config migrate --apply` 才会备份并原子替换用户配置。
- [x] 未来版本、未知字段、已登记废弃字段和预览后并发修改均有明确的警告或安全失败规则。
- [x] 迁移保持配置、输入和输出路径语义稳定，避免安装或升级过程静默覆盖用户文件。

### 环境诊断与内部发布

- [x] 增加 `autoblade doctor`，诊断 Windows、Python、`pywin32`、COM 初始化、CATIA ProgID、配置来源和目录权限；诊断过程不连接或启动 CATIA。
- [x] 增加内部 wheel 安装、升级、卸载、工作区初始化、发布、失败处理和回滚文档。
- [x] 建立版本、Git 标签、Release Notes、wheel、sdist、真实 CATIA 验证记录、SHA-256 和内部发布 manifest 的一致性门槛。

## 最终验证证据

- [x] `pwsh -File scripts/check.ps1 -RequireTag` 在干净的 `v0.2.0` 标签提交上通过。
- [x] pytest 共 128 项通过，Ruff 通过。
- [x] wheel 包含 44 个文件，内容清单 SHA-256 为 `93a8f8d2e6cde415ca34fcbdd1873ef36106ea49125a99bb43523b506584b062`。
- [x] sdist 包含 103 个文件，内容清单 SHA-256 为 `fc4fe33f2885ac3cd9ea81b830d9927dea4757f8e1c431e05004e1c13cf34477`。
- [x] 全新 CPython 3.14.4 环境从候选 wheel 安装 20 个包，并完成非 editable 安装冒烟。
- [x] 真实 CATIA P3 V5-6R2020 使用 89 截面多翼型输入成功生成 7,689,114 字节 CATPart 和 1,022,363 字节 STEP。
- [x] 特征树包含 `blade_loft_surface`、`blade_closed_solid`、`leading_edge_guide` 和 `trailing_edge_upper_guide`，STEP 检查为闭合实体 BREP，新增 `CNEXT` 进程为 0。
- [x] 最终验证记录标记 `dirty_worktree: false`，版本和提交分别为 `0.2.0` 与 `1d479ff84a9b8e68abfa830a64cd37f42a4f6ce1`。

## 内部发布制品

发布制品由 `scripts/prepare_internal_release.py` 从同一标签重新构建，并写入 `dist/`：

- `catia_autoblade-0.2.0-py3-none-any.whl`：`cc339a64be6fabf37340bd8b319327b59ecf0643c62822f96147975d11b9c3c3`
- `catia_autoblade-0.2.0.tar.gz`：`f5de695398cd157e3b037d823508100e67d19800d8b5792b45b618685469d30f`
- `catia-autoblade-0.2.0-release-notes.md`：`9f4af7a2a5994d33f0bdf400f4c9883d4d9f3e613091727d1ca4dab2a5e1467d`
- `SHA256SUMS.txt` 和 `catia-autoblade-0.2.0-internal-release.json`

制品不纳入 Git；内部交付时必须把上述文件作为同一集合分发。若验证或交付失败，撤回整个集合、恢复上一版本 wheel，并在发生配置迁移时使用迁移备份恢复 `config.toml`。
