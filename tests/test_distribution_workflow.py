import importlib.util
import json
from pathlib import Path
import sys

import pytest


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"


def _load_script_module(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load script module: {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validate_distribution = _load_script_module("validate_distribution")
prepare_internal_release = _load_script_module("prepare_internal_release")


def test_pyproject_declares_auditable_hatchling_manifests() -> None:
    validate_distribution._validate_pyproject()


@pytest.mark.parametrize(
    "name",
    [
        "autoblade/__pycache__/module.pyc",
        "C:/private/customer.csv",
        "autoblade/output/model.CATPart",
    ],
)
def test_distribution_content_check_rejects_forbidden_paths(name: str) -> None:
    with pytest.raises(validate_distribution.ValidationError):
        validate_distribution._validate_archive_names([name], artifact="test")


def test_release_validation_record_requires_real_catia_evidence(
    tmp_path: Path,
) -> None:
    record_file = tmp_path / "validation.json"
    record_file.write_text(
        json.dumps(
            {
                "version": "0.2.0",
                "commit": "abc123",
                "dirty_worktree": False,
                "repository_check": "pass",
                "installed_wheel_smoke": "pass",
                "catia_smoke": {
                    "date": "2026-08-11",
                    "windows": "Windows 11 x64",
                    "python": "CPython 3.14.4 x64",
                    "pywin32": "311",
                    "catia": "CATIA P3 V5-6R2020",
                    "input_model": "blade_sections-multi-airfoil.csv",
                    "catpart_result": "pass",
                    "step_result": "pass: closed solid BREP",
                    "feature_tree": "pass",
                    "new_cnext_processes": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    record = prepare_internal_release._read_validation_record(
        record_file,
        "0.2.0",
        "abc123",
    )

    assert record["catia_smoke"]["new_cnext_processes"] == 0


def test_release_validation_record_rejects_residual_catia_process(
    tmp_path: Path,
) -> None:
    record_file = tmp_path / "validation.json"
    record_file.write_text(
        json.dumps(
            {
                "version": "0.2.0",
                "commit": "abc123",
                "dirty_worktree": False,
                "repository_check": "pass",
                "installed_wheel_smoke": "pass",
                "catia_smoke": {
                    "date": "2026-08-11",
                    "windows": "Windows 11 x64",
                    "python": "CPython 3.14.4 x64",
                    "pywin32": "311",
                    "catia": "CATIA P3 V5-6R2020",
                    "input_model": "blade_sections-multi-airfoil.csv",
                    "catpart_result": "pass",
                    "step_result": "pass",
                    "feature_tree": "pass",
                    "new_cnext_processes": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        validate_distribution.ValidationError,
        match="new_cnext_processes",
    ):
        prepare_internal_release._read_validation_record(
            record_file,
            "0.2.0",
            "abc123",
        )


def test_internal_release_artifacts_use_autoblade_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "autoblade-0.2.0-py3-none-any.whl").write_bytes(b"wheel")
    (dist_dir / "autoblade-0.2.0.tar.gz").write_bytes(b"sdist")
    release_notes = tmp_path / "notes.md"
    release_notes.write_text("# Notes\n", encoding="utf-8")
    validation_record = tmp_path / "validation.json"
    validation_record.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(prepare_internal_release, "_source_version", lambda: "0.2.0")
    monkeypatch.setattr(
        prepare_internal_release,
        "_validate_clean_tagged_source",
        lambda version: ("abc123", "v0.2.0"),
    )
    monkeypatch.setattr(prepare_internal_release, "validate", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        prepare_internal_release,
        "_read_validation_record",
        lambda *args: {"repository_check": "pass"},
    )

    manifest_path = prepare_internal_release.prepare_release(
        dist_dir,
        validation_record,
        release_notes,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest_path.name == "autoblade-0.2.0-internal-release.json"
    assert manifest["schema"] == "autoblade-internal-release/v1"
    assert "autoblade-0.2.0-py3-none-any.whl" in manifest["sha256"]
    assert "autoblade-0.2.0.tar.gz" in manifest["sha256"]
    assert "autoblade-0.2.0-release-notes.md" in manifest["sha256"]
