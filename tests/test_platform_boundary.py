import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from catia_autoblade.adapters.cad.catia import builder as catia_builder
from catia_autoblade.adapters.cad.catia.errors import (
    CatiaBackendUnavailableError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = PROJECT_ROOT / "src" / "catia_autoblade" / "core"


def test_core_modules_do_not_import_windows_com_packages() -> None:
    """静态保护领域层，避免后续改动把 Windows COM 依赖带回 core。"""
    forbidden_roots = {"pythoncom", "win32com"}
    violations: list[str] = []

    for path in sorted(CORE_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = {node.module.split(".", 1)[0]}
            else:
                continue
            blocked = imported & forbidden_roots
            if blocked:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}: "
                    f"{', '.join(sorted(blocked))}"
                )

    assert violations == []


def test_package_and_core_import_without_loading_windows_com() -> None:
    """在全新解释器中确认包入口、Parser 与 Planner 不触发 COM 导入。"""
    script = """
import catia_autoblade
from catia_autoblade.core import geometry, input_plan, input_validation, jobs, planner
import sys
assert "pythoncom" not in sys.modules
assert "win32com" not in sys.modules
assert "win32com.client" not in sys.modules
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_unavailable_platform_reports_catia_capability_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """合法输入到达后端边界时，应返回能力错误而不是裸 ImportError。"""
    airfoil_dir = tmp_path / "airfoils"
    section_dir = tmp_path / "sections"
    airfoil_dir.mkdir()
    section_dir.mkdir()
    (airfoil_dir / "foil.csv").write_text(
        "x,y,z\n0,1,0\n0,0,0\n0,1,0\n",
        encoding="utf-8",
    )
    (section_dir / "sections.csv").write_text(
        "idx,scale/m,translate_x/m,translate_y/m,translate_z/m,rotate/deg\n"
        "1,0.1,0,0,0,0\n2,0.08,1,0,0,0\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(catia_builder, "_is_windows", lambda: False)

    with pytest.raises(CatiaBackendUnavailableError, match="Windows"):
        catia_builder.create_single_blade(
            "foil.csv",
            "sections.csv",
            tmp_path / "output",
            "blade",
            airfoil_dir=airfoil_dir,
            blade_sections_dir=section_dir,
        )
