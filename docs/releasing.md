# 内部 preview 发布与回滚

本文是维护者发布内部 wheel 的唯一流程。GitHub Release、TestPyPI 和公共 PyPI
属于后续渠道，不能用来绕过内部验证门槛。

## 版本规则

- 预览阶段使用 SemVer 风格的 `0.x.y`；不兼容的配置 schema 单独使用
  `AppConfig.version`，不能拿包版本代替 schema 版本。
- 唯一包版本源是 `src/catia_autoblade/__init__.py`。
- Git 标签使用 `v<版本>`；同一个版本号不得重新构建不同内容并继续分发。
- Release Notes、源码版本、标签、wheel、sdist 和发布 manifest 必须一致。
- 内置翼型目录不建立第二版本源；其内容随包版本发布，清单中的
  `schema_version` 只表示清单结构。

## 翼型目录变更

增加、修改或删除 `resources/airfoil_library` 中的翼型时，必须在同一改动中：

1. 更新清单的稳定 ID、来源、许可证或直接授权、修改说明、点数和 SHA-256；
2. 完成 CSV 数据校验，并保证包中没有未列入清单的 CSV；
3. 更新 `docs/release-notes/unreleased.md`，发布时再并入下一个版本的正式说明；
4. 更新 wheel 内容校验和安装冒烟；涉及坐标、点序或拓扑时补做真实 CATIA 回归。

来源或授权不清楚的数据必须留在 wheel 外。不能只更新 CSV 而沿用旧摘要，也不能
把 `schema_version` 递增当作数据内容版本或包版本。

## 发布前证据

1. 在最终提交上确认工作区干净，把未发布说明整理进
   `docs/release-notes/v<版本>.md`，并清空已发布条目。
2. 创建唯一匹配标签后运行完整检查：

   ```powershell
   pwsh -File scripts/check.ps1 -RequireTag
   ```

3. 在支持基线上显式执行候选 wheel 的真实 CATIA 回归：

   ```powershell
   pwsh -File scripts/smoke_real_catia.ps1
   ```

   该脚本会先重跑自动化与非 editable 安装冒烟，再从 wheel 创建独立环境和
   工作区，使用 89 截面多翼型输入建模，检查 CATPart 关键特征、STEP 固体
   BREP 和新增 `CNEXT` 进程。输出和 `validation.json` 保存在忽略的
   `output/real-catia-smoke-<时间>/`；脚本只使用 `DispatchEx` 独占实例。

4. 工程人员复核 CATPart/STEP 几何和记录内容。验证记录必须包含日期、完整提交、
   Windows/Python/pywin32/CATIA、输入、特征树、两个产物和零新增进程。

## 生成内部制品集

只有最终标签提交上的工作区干净、验证记录的 `dirty_worktree` 为 `false` 时执行：

```powershell
uv run python scripts/prepare_internal_release.py `
  --validation-record output\real-catia-smoke-<时间>\validation.json
```

发布器会再次校验标签、版本、长描述链接、wheel/sdist 内容清单和真实验证记录，
然后在 `dist/` 生成：

- `catia_autoblade-<版本>-py3-none-any.whl`；
- `catia_autoblade-<版本>.tar.gz`；
- `catia-autoblade-<版本>-release-notes.md`；
- `SHA256SUMS.txt`；
- `catia-autoblade-<版本>-internal-release.json`。

每个内部交付必须整体传递上述文件。接收方应先核对 SHA-256，再按[安装、工作区
与升级](installation.md)创建独立环境。`dist/` 是本地生成目录，不提交 Git。

## 失败与回滚

- 自动化、安装冒烟、真实 CATIA 或证据校验任一失败时，不创建或分发 manifest。
- 标签前失败：修复后创建新提交并重新运行全部检查。
- 标签后但未分发失败：不要在原标签上重写内容；修复后递增 patch 版本并创建新标签。
- 已分发版本失败：停止分发受影响的完整制品集，通知使用者安装上一批准 wheel；
  配置已迁移时使用对应备份恢复，并保留失败产物供排查。
- 不允许用相同版本号替换 wheel、只补传部分文件、删除验证记录或把开发机 dirty
  build 标为 preview。

公共发布渠道只有在内部流程稳定、名称与凭据策略重新评估后才能单独晋级。
