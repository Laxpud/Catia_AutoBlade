"""CATIA V5 Adapter 的稳定入口。"""

from .errors import CatiaBackendUnavailableError


def create_single_blade(*args, **kwargs):
    """延迟加载 CATIA Builder，避免仅导入包时装载 Windows COM。"""
    from .builder import create_single_blade as build_with_catia

    return build_with_catia(*args, **kwargs)


__all__ = ["CatiaBackendUnavailableError", "create_single_blade"]
