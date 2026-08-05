from pathlib import Path

import pytest

from catia_autoblade.core import batch as batch_module
from catia_autoblade.core import create_blade as create_module
from catia_autoblade.core.catia_session import CatiaCleanupError, CatiaSession


class FakePart:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def Update(self) -> None:
        self.events.append("part.update")


class FakeDocument:
    def __init__(
        self,
        events: list[str],
        *,
        fail_save: bool = False,
        fail_export: bool = False,
        fail_close: bool = False,
    ) -> None:
        self.events = events
        self.Part = FakePart(events)
        self.fail_save = fail_save
        self.fail_export = fail_export
        self.fail_close = fail_close

    def SaveAs(self, path: str) -> None:
        self.events.append("document.save")
        if self.fail_save:
            raise RuntimeError("save failed")

    def ExportData(self, path: str, file_type: str) -> None:
        self.events.append("document.export")
        if self.fail_export:
            raise RuntimeError("export failed")

    def Close(self) -> None:
        self.events.append("document.close")
        if self.fail_close:
            raise RuntimeError("close failed")


class FakeDocuments:
    def __init__(
        self,
        events: list[str],
        document: FakeDocument,
        *,
        fail_add: bool = False,
    ) -> None:
        self.events = events
        self.document = document
        self.fail_add = fail_add

    def Add(self, document_type: str) -> FakeDocument:
        self.events.append(f"documents.add:{document_type}")
        if self.fail_add:
            raise RuntimeError("add document failed")
        return self.document


class FakeApplication:
    def __init__(
        self,
        events: list[str],
        document: FakeDocument,
        *,
        fail_add: bool = False,
        fail_quit: bool = False,
    ) -> None:
        self.events = events
        self.Documents = FakeDocuments(events, document, fail_add=fail_add)
        self.Visible = True
        self.fail_quit = fail_quit

    def Quit(self) -> None:
        self.events.append("application.quit")
        if self.fail_quit:
            raise RuntimeError("quit failed")


class LifecycleHarness:
    """记录假 COM 会话中的初始化、文档和应用释放顺序。"""

    def __init__(
        self,
        *,
        fail_save: bool = False,
        fail_export: bool = False,
        fail_close: bool = False,
        fail_add: bool = False,
        fail_quit: bool = False,
    ) -> None:
        self.events: list[str] = []
        self.document = FakeDocument(
            self.events,
            fail_save=fail_save,
            fail_export=fail_export,
            fail_close=fail_close,
        )
        self.application = FakeApplication(
            self.events,
            self.document,
            fail_add=fail_add,
            fail_quit=fail_quit,
        )

    def session_factory(self) -> CatiaSession:
        return CatiaSession(
            application_factory=self._dispatch,
            com_initialize=self._initialize,
            com_uninitialize=self._uninitialize,
            collect_garbage=self._collect,
        )

    def _initialize(self) -> None:
        self.events.append("com.initialize")

    def _dispatch(self, program_id: str) -> FakeApplication:
        self.events.append(f"application.dispatch:{program_id}")
        return self.application

    def _collect(self) -> int:
        self.events.append("com.collect")
        return 0

    def _uninitialize(self) -> None:
        self.events.append("com.uninitialize")


def _patch_successful_geometry(monkeypatch: pytest.MonkeyPatch) -> None:
    """把几何操作替换为稳定返回值，仅保留生命周期与真实保存流程。"""
    monkeypatch.setattr(create_module, "read_airfoil_csv", lambda path: [object()])
    monkeypatch.setattr(
        create_module,
        "create_airfoil",
        lambda part, points: ("airfoil_body", "airfoil", True, (object(),)),
    )
    monkeypatch.setattr(
        create_module,
        "create_blade_geometry",
        lambda *args: (
            "blade_geometry",
            ["section"],
            "leading_edge",
            "trailing_edge_upper",
            "trailing_edge_lower",
            ["leading_edge_point"],
        ),
    )
    monkeypatch.setattr(
        create_module,
        "create_blade_surface",
        lambda *args: ("blade_surface_body", "blade_surface"),
    )
    monkeypatch.setattr(
        create_module,
        "create_blade_solid",
        lambda *args: "blade_solid",
    )
    monkeypatch.setattr(
        create_module,
        "hide_all_except_blade_solid",
        lambda *args: None,
    )


def _assert_complete_cleanup(events: list[str]) -> None:
    close_index = events.index("document.close")
    quit_index = events.index("application.quit")
    collect_index = events.index("com.collect")
    uninitialize_index = events.index("com.uninitialize")
    assert close_index < quit_index < collect_index < uninitialize_index


def test_session_releases_resources_in_reverse_order() -> None:
    harness = LifecycleHarness()

    with harness.session_factory() as session:
        assert session.part is harness.document.Part
        assert harness.application.Visible is False

    _assert_complete_cleanup(harness.events)


@pytest.mark.parametrize("failure_stage", ["model", "save", "export"])
def test_create_blade_cleans_up_after_each_failure_stage(
    failure_stage: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = LifecycleHarness(
        fail_save=failure_stage == "save",
        fail_export=failure_stage == "export",
    )
    _patch_successful_geometry(monkeypatch)
    if failure_stage == "model":

        def fail_model(part, points):
            raise RuntimeError("model failed")

        monkeypatch.setattr(create_module, "create_airfoil", fail_model)

    with pytest.raises(Exception, match=f"{failure_stage} failed"):
        create_module.create_single_blade(
            "foil.csv",
            "section_params-1.csv",
            tmp_path / "output",
            "blade",
            airfoil_dir=tmp_path / "airfoils",
            section_params_dir=tmp_path / "sections",
            session_factory=harness.session_factory,
        )

    _assert_complete_cleanup(harness.events)


def test_enter_failure_rolls_back_application_and_com() -> None:
    harness = LifecycleHarness(fail_add=True)

    with pytest.raises(RuntimeError, match="add document failed"):
        with harness.session_factory():
            pytest.fail("session should not enter")

    assert "document.close" not in harness.events
    assert harness.events[-3:] == [
        "application.quit",
        "com.collect",
        "com.uninitialize",
    ]


def test_cleanup_failure_does_not_mask_primary_error() -> None:
    harness = LifecycleHarness(fail_close=True)

    with pytest.raises(ValueError, match="primary failure") as raised:
        with harness.session_factory():
            raise ValueError("primary failure")

    assert any("CATIA cleanup failed: close failed" in note for note in raised.value.__notes__)
    assert "application.quit" in harness.events
    assert harness.events[-1] == "com.uninitialize"


def test_cleanup_failure_after_success_is_reported() -> None:
    harness = LifecycleHarness(fail_quit=True)

    with pytest.raises(CatiaCleanupError, match="quit failed"):
        with harness.session_factory():
            pass

    assert harness.events[-1] == "com.uninitialize"


def test_batch_failure_closes_every_owned_application(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harnesses: list[LifecycleHarness] = []

    def fake_create(airfoil_file, section_file, *args, **kwargs):
        harness = LifecycleHarness()
        harnesses.append(harness)
        with harness.session_factory():
            if section_file == "section_params-bad.csv":
                raise RuntimeError("batch item failed")

    monkeypatch.setattr(batch_module, "create_single_blade", fake_create)
    results = batch_module.batch_create_blades(
        ["foil.csv"],
        ["section_params-bad.csv", "section_params-good.csv"],
        tmp_path / "output",
        airfoil_dir=tmp_path / "airfoils",
        section_params_dir=tmp_path / "sections",
        output_name_template="{airfoil}_{idx}",
        author="",
    )

    assert [result["status"] for result in results] == ["failed", "success"]
    assert len(harnesses) == 2
    for harness in harnesses:
        _assert_complete_cleanup(harness.events)
