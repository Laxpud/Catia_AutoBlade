"""旧 CATIA 会话导入路径的延迟兼容层。"""

_EXPORTED_NAMES = {"CatiaCleanupError", "CatiaSession"}


def __getattr__(name: str):
    """仅在旧调用方请求会话类型时装载 Windows COM Adapter。"""
    if name not in _EXPORTED_NAMES:
        raise AttributeError(name)

    from ..adapters.cad.catia import session

    return getattr(session, name)
