# 隔离 CAD 后端与 FreeCAD 进程

Status: accepted

核心解析、验证、任务规划和坐标计算必须保持 CAD 厂商无关；CATIA 继续通过受控 COM Adapter 运行，FreeCAD 则通过每任务一个独立 `FreeCADCmd` 子进程运行。CLI 只依赖内部类型化 backend factory，FreeCAD 使用固定 runner 和严格版本化 JSON 协议，不在项目 Python 中导入 FreeCAD，也不接受自由 shell command。

## Considered Options

- 在项目解释器内 `import FreeCAD`，会把 wheel 的 Python 版本和 ABI 绑定到 FreeCAD 自带解释器。
- 建立公共动态插件系统，会在只有两个已知后端时过早稳定第三方接口。
- 复用一个长期 FreeCAD 进程，启动更少，但会扩大文档状态、崩溃和内存污染的影响范围。

## Consequences

- 首个认证启动器是 Flatpak `org.freecad.FreeCAD` 1.1.3；未来 NativeLauncher 只能接受经过类型校验的 executable path。
- 所有输入和输出冲突必须在外部 CAD 启动前验证；dry-run 不探测或启动 CAD。
- timeout、Ctrl-C 和清理只能作用于 AutoBlade 自己创建的进程，不得连接、复用或全局终止用户的 CAD 会话。
- 后端不可用或构建失败时明确失败，不自动回退到另一个后端。
