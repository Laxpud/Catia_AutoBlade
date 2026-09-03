from pathlib import Path

import pytest

from autoblade.core.create_blade import create_single_blade
from autoblade.core.input_plan import build_blade_input_plan
from autoblade.core.input_validation import (
    InputValidationError,
    read_airfoil_csv,
)


SHARP_AIRFOIL = """x,y,z
0,1,0
0,0.5,0.1
0,0,0
0,0.5,-0.1
0,1,0
"""

BLUNT_AIRFOIL = """x,y,z
0,1,0.01
0,0.5,0.1
0,0,0
0,0.5,-0.1
0,1,-0.01
"""

LEGACY_SECTIONS = """idx,scale/m,translate_x/m,translate_y/m,translate_z/m,rotate/deg
1,0.1,0,0,0,10
2,0.08,1,0,0,5
"""

MULTI_SECTIONS = """idx,scale/m,translate_x/m,translate_y/m,translate_z/m,rotate/deg,airfoil
1,0.1,0,0,0,10,foil_a.csv
2,0.09,0.5,0,0,7,foil_a.csv
3,0.08,1,0,0,5,foil_b.csv
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_legacy_plan_assigns_one_fallback_airfoil_to_every_section(
    tmp_path: Path,
) -> None:
    airfoil_dir = tmp_path / "airfoils"
    section_path = _write(tmp_path / "sections.csv", LEGACY_SECTIONS)
    _write(airfoil_dir / "foil.csv", SHARP_AIRFOIL)

    plan = build_blade_input_plan(section_path, airfoil_dir, "foil.csv")

    assert plan.mode == "single"
    assert [section["airfoil_filename"] for section in plan.sections] == [
        "foil.csv",
        "foil.csv",
    ]
    assert [airfoil.filename for airfoil in plan.airfoils] == ["foil.csv"]
    assert plan.is_sharp is True


def test_multi_plan_reads_unique_airfoils_once_in_first_use_order(
    tmp_path: Path,
) -> None:
    airfoil_dir = tmp_path / "airfoils"
    section_path = _write(tmp_path / "sections.csv", MULTI_SECTIONS)
    _write(airfoil_dir / "foil_a.csv", SHARP_AIRFOIL)
    _write(airfoil_dir / "foil_b.csv", SHARP_AIRFOIL)
    reads: list[str] = []

    def recording_reader(path: str | Path):
        reads.append(Path(path).name)
        return read_airfoil_csv(path)

    plan = build_blade_input_plan(
        section_path,
        airfoil_dir,
        None,
        airfoil_reader=recording_reader,
    )

    assert plan.mode == "multi"
    assert reads == ["foil_a.csv", "foil_b.csv"]
    assert [airfoil.filename for airfoil in plan.airfoils] == reads
    assert [section["airfoil_filename"] for section in plan.sections] == [
        "foil_a.csv",
        "foil_a.csv",
        "foil_b.csv",
    ]


@pytest.mark.parametrize(
    "invalid_reference",
    ["", "../foil.csv", "nested/foil.csv", "Foil.csv", " foil.csv"],
)
def test_multi_plan_rejects_noncanonical_or_cross_directory_references(
    invalid_reference: str,
    tmp_path: Path,
) -> None:
    airfoil_dir = tmp_path / "airfoils"
    airfoil_dir.mkdir()
    section_path = _write(
        tmp_path / "sections.csv",
        MULTI_SECTIONS.replace("foil_a.csv", invalid_reference),
    )

    with pytest.raises(InputValidationError) as raised:
        build_blade_input_plan(section_path, airfoil_dir, None)

    assert "line 2" in str(raised.value)
    assert "field 'airfoil'" in str(raised.value)


def test_multi_plan_reports_missing_reference_at_first_section_line(
    tmp_path: Path,
) -> None:
    airfoil_dir = tmp_path / "airfoils"
    airfoil_dir.mkdir()
    section_path = _write(tmp_path / "sections.csv", MULTI_SECTIONS)

    with pytest.raises(InputValidationError, match="not found") as raised:
        build_blade_input_plan(section_path, airfoil_dir, None)

    assert "line 2" in str(raised.value)
    assert "field 'airfoil'" in str(raised.value)


def test_multi_plan_rejects_cli_fallback_instead_of_silently_overriding(
    tmp_path: Path,
) -> None:
    section_path = _write(tmp_path / "sections.csv", MULTI_SECTIONS)

    with pytest.raises(InputValidationError, match="cannot be combined"):
        build_blade_input_plan(section_path, tmp_path / "airfoils", "foil.csv")


def test_multi_plan_rejects_mixed_trailing_edge_topology(
    tmp_path: Path,
) -> None:
    airfoil_dir = tmp_path / "airfoils"
    section_path = _write(tmp_path / "sections.csv", MULTI_SECTIONS)
    _write(airfoil_dir / "foil_a.csv", SHARP_AIRFOIL)
    _write(airfoil_dir / "foil_b.csv", BLUNT_AIRFOIL)

    with pytest.raises(InputValidationError, match="trailing-edge topology"):
        build_blade_input_plan(section_path, airfoil_dir, None)


def test_missing_multi_airfoil_reference_fails_before_catia_session(
    tmp_path: Path,
) -> None:
    section_dir = tmp_path / "sections"
    airfoil_dir = tmp_path / "airfoils"
    _write(section_dir / "sections.csv", MULTI_SECTIONS)
    airfoil_dir.mkdir()
    session_calls = []

    def forbidden_session():
        session_calls.append(True)
        raise AssertionError("CATIA session must not start for invalid input")

    with pytest.raises(InputValidationError, match="not found"):
        create_single_blade(
            None,
            "sections.csv",
            tmp_path / "output",
            "blade",
            airfoil_dir=airfoil_dir,
            blade_sections_dir=section_dir,
            session_factory=forbidden_session,
        )

    assert session_calls == []
