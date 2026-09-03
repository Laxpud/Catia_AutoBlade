"""保护 AutoBlade breaking distribution 迁移的安装边界。"""

from importlib import metadata


LEGACY_DISTRIBUTION = "catia-autoblade"


class LegacyDistributionConflictError(RuntimeError):
    """旧 distribution 与 AutoBlade 同时安装，入口归属不再可信。"""


def ensure_no_legacy_distribution() -> None:
    """检测旧 distribution，并要求用户先卸载再安装新 wheel。

    ``catia-autoblade`` 与 ``autoblade`` 注册同名 console scripts。Python 包管理器
    不提供可靠的互斥依赖声明；运行时检查是避免入口文件被后安装者覆盖后形成混合
    环境的最后一道边界。
    """
    try:
        legacy_version = metadata.version(LEGACY_DISTRIBUTION)
    except metadata.PackageNotFoundError:
        return

    raise LegacyDistributionConflictError(
        "AutoBlade cannot run while the legacy 'catia-autoblade' distribution "
        f"({legacy_version}) is installed. Uninstall it first with "
        "'python -m pip uninstall catia-autoblade', then reinstall the "
        "'autoblade' wheel. No legacy namespace shim is provided."
    )
