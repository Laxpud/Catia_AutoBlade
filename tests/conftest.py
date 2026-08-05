import pytest
import win32com.client


@pytest.fixture(autouse=True)
def forbid_real_catia_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """保证自动化测试不会连接或启动真实 CATIA COM 服务。"""

    def blocked_dispatch(program_id: str):
        raise AssertionError(
            f"Automated tests must not dispatch real COM application: {program_id}"
        )

    # 同时封锁新旧入口，防止未来代码回退到 Dispatch 后测试静默启动 CATIA。
    monkeypatch.setattr(win32com.client, "Dispatch", blocked_dispatch)
    monkeypatch.setattr(win32com.client, "DispatchEx", blocked_dispatch)
