"""旧建模入口的兼容转发层。

CATIA 几何实现位于 :mod:`autoblade.adapters.cad.catia`。此模块只保留
历史导入路径，不在导入核心包时装载 ``pythoncom`` 或 ``win32com``。
"""


def create_single_blade(*args, **kwargs):
    """转发到 CATIA Adapter；参数与历史 Python 入口保持兼容。"""
    from ..adapters.cad.catia import create_single_blade as build_with_catia

    return build_with_catia(*args, **kwargs)


__all__ = ["create_single_blade"]
