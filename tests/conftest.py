import pytest


@pytest.fixture(autouse=True)
def forbid_real_catia_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """保证自动化测试不会连接或启动真实 CATIA COM 服务。"""
    try:
        import win32com.client
    except ImportError:
        # 纯核心测试允许在未安装 pywin32 的平台执行；Adapter 测试通过注入
        # session_factory 隔离 COM，真实会话测试则在模块级明确跳过。
        return

    def blocked_dispatch(program_id: str):
        raise AssertionError(
            f"Automated tests must not dispatch real COM application: {program_id}"
        )

    # 同时封锁新旧入口，防止未来代码回退到 Dispatch 后测试静默启动 CATIA。
    monkeypatch.setattr(win32com.client, "Dispatch", blocked_dispatch)
    monkeypatch.setattr(win32com.client, "DispatchEx", blocked_dispatch)
