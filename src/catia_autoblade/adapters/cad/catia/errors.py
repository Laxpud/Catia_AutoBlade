"""CATIA Adapter 的能力错误。"""


class CatiaBackendUnavailableError(RuntimeError):
    """当前平台或 Python 环境无法装载 CATIA COM 后端。"""
