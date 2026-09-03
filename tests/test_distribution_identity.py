from importlib import metadata
import os
from pathlib import Path
import subprocess
import sys

import pytest

from autoblade._distribution import (
    LegacyDistributionConflictError,
    ensure_no_legacy_distribution,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_legacy_distribution_conflict_has_actionable_uninstall_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(metadata, "version", lambda name: "0.2.0")

    with pytest.raises(
        LegacyDistributionConflictError,
        match="pip uninstall catia-autoblade",
    ):
        ensure_no_legacy_distribution()


def test_package_import_fails_fast_when_legacy_distribution_metadata_exists(
    tmp_path: Path,
) -> None:
    legacy_metadata = tmp_path / "catia_autoblade-0.2.0.dist-info"
    legacy_metadata.mkdir()
    (legacy_metadata / "METADATA").write_text(
        "Metadata-Version: 2.4\nName: catia-autoblade\nVersion: 0.2.0\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        (str(tmp_path), str(PROJECT_ROOT / "src"))
    )

    result = subprocess.run(
        [sys.executable, "-c", "import autoblade"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "pip uninstall catia-autoblade" in result.stderr
    assert "No legacy namespace shim is provided" in result.stderr


def test_legacy_python_namespace_is_not_present() -> None:
    assert not (PROJECT_ROOT / "src" / "catia_autoblade").exists()
