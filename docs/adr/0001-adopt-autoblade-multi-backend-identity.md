# 采用 AutoBlade 多后端产品身份

Status: accepted

项目已有 CATIA 后端并出现了真实 FreeCAD 建模需求，继续让产品身份等同于单一 CAD 会让平台边界和后续能力难以准确表达。`0.3.0` 将品牌、distribution 和 Python namespace 分别迁移为 `AutoBlade`、`autoblade` 和 `autoblade`，保留现有中性 CLI 名称，并把 CATIA 与 FreeCAD 定义为显式选择的后端；CATIA 继续作为内置默认值。

## Considered Options

- 只改品牌而保留 `catia-autoblade` 和 `catia_autoblade`，兼容成本最低，但继续把单一后端写进规范身份。
- 为旧 namespace 维护弃用 shim，能延缓迁移，却容易让深层 import 以两个模块身份加载并产生类型身份问题。
- 一次完成干净的 v0.x breaking migration，使规范名称重新一致。

## Consequences

- `0.3.0` 不保留 `catia_autoblade` import shim；受控团队必须先卸载旧 distribution，再安装新 wheel。
- 配置目录通过显式迁移保留数据安全，当前 CLI 命令 `autoblade`、`autoblade-create` 和 `autoblade-batch` 不变。
- 当前版本仍是内部 preview wheel；公共 PyPI、独立 EXE 和公共第三方 CAD 插件 API 不随改名自动进入范围。
- GitHub 仓库和本地 checkout 的改名是独立外部操作，不能由源码迁移隐式执行。
