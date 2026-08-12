from pathlib import Path

import pytest

from catia_autoblade.core.create_blade import create_single_blade
from catia_autoblade.core.input_validation import (
    InputValidationError,
    read_airfoil_csv,
    read_section_parameters,
)


VALID_AIRFOIL = """x,y,z
0,1,0
0,0.5,0.1
0,0,0
0,0.5,-0.1
0,1,0
"""

VALID_SECTIONS = """idx,scale/m,translate_x/m,translate_y/m,translate_z/m,rotate/deg
1,0.1,0,0,0,10
2,0.08,1,0,0,5
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _assert_location(
    error: InputValidationError,
    path: Path,
    *,
    line: int | None = None,
    field: str | None = None,
) -> None:
    message = str(error)
    assert str(path.resolve()) in message
    if line is not None:
        assert f"line {line}" in message
    if field is not None:
        assert f"field '{field}'" in message


def test_airfoil_missing_column_reports_path_and_header_field(tmp_path: Path) -> None:
    path = _write(tmp_path / "airfoil.csv", "x,y\n0,1\n")

    with pytest.raises(InputValidationError, match="missing required column") as raised:
        read_airfoil_csv(path)

    _assert_location(raised.value, path, line=1, field="z")


@pytest.mark.parametrize("content", ["", "x,y,z\n"])
def test_empty_airfoil_reports_minimum_point_constraint(
    content: str,
    tmp_path: Path,
) -> None:
    path = _write(tmp_path / "empty.csv", content)

    with pytest.raises(InputValidationError) as raised:
        read_airfoil_csv(path)

    _assert_location(raised.value, path)
    assert "expected" in str(raised.value)


def test_airfoil_invalid_number_reports_line_and_field(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "airfoil.csv",
        VALID_AIRFOIL.replace("0,0.5,0.1", "0,not-a-number,0.1"),
    )

    with pytest.raises(InputValidationError, match="finite number") as raised:
        read_airfoil_csv(path)

    _assert_location(raised.value, path, line=3, field="y")


def test_airfoil_non_finite_number_is_rejected(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "airfoil.csv",
        VALID_AIRFOIL.replace("0,0.5,0.1", "0,nan,0.1"),
    )

    with pytest.raises(InputValidationError, match="finite number") as raised:
        read_airfoil_csv(path)

    _assert_location(raised.value, path, line=3, field="y")


def test_airfoil_invalid_point_order_reports_first_violation(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "reordered.csv",
        """x,y,z
0,1,0
0,0.4,0.1
0,0.6,0.08
0,0,0
0,0.5,-0.1
0,1,0
""",
    )

    with pytest.raises(InputValidationError, match="non-increasing") as raised:
        read_airfoil_csv(path)

    _assert_location(raised.value, path, line=4, field="y")


def test_section_missing_column_reports_path_and_field(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "sections.csv",
        VALID_SECTIONS.replace(",rotate/deg", ""),
    )

    with pytest.raises(InputValidationError, match="missing required column") as raised:
        read_section_parameters(path)

    _assert_location(raised.value, path, line=1, field="rotate/deg")


def test_section_invalid_number_reports_line_and_field(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "sections.csv",
        VALID_SECTIONS.replace("2,0.08,1", "2,invalid,1"),
    )

    with pytest.raises(InputValidationError, match="finite number") as raised:
        read_section_parameters(path)

    _assert_location(raised.value, path, line=3, field="scale/m")


def test_section_file_requires_at_least_two_rows(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "sections.csv",
        VALID_SECTIONS.rsplit("2,0.08,1,0,0,5\n", maxsplit=1)[0],
    )

    with pytest.raises(InputValidationError, match="at least 2 section rows") as raised:
        read_section_parameters(path)

    _assert_location(raised.value, path)


def test_section_indices_must_be_strictly_increasing(tmp_path: Path) -> None:
    path = _write(
        tmp_path / "sections.csv",
        VALID_SECTIONS.replace("2,0.08,1", "1,0.08,1"),
    )

    with pytest.raises(InputValidationError, match="strictly greater") as raised:
        read_section_parameters(path)

    _assert_location(raised.value, path, line=3, field="idx")


def test_validation_finishes_before_catia_session_starts(tmp_path: Path) -> None:
    airfoil_dir = tmp_path / "airfoils"
    section_dir = tmp_path / "sections"
    _write(airfoil_dir / "foil.csv", VALID_AIRFOIL)
    _write(
        section_dir / "blade_sections-1.csv",
        VALID_SECTIONS.rsplit("2,0.08,1,0,0,5\n", maxsplit=1)[0],
    )
    session_calls = []

    def forbidden_session():
        session_calls.append(True)
        raise AssertionError("CATIA session must not start for invalid input")

    with pytest.raises(InputValidationError, match="at least 2 section rows"):
        create_single_blade(
            "foil.csv",
            "blade_sections-1.csv",
            tmp_path / "output",
            "blade",
            airfoil_dir=airfoil_dir,
            blade_sections_dir=section_dir,
            keep_failed_part=True,
            session_factory=forbidden_session,
        )

    assert session_calls == []


def test_valid_inputs_are_parsed_into_domain_units(tmp_path: Path) -> None:
    airfoil_path = _write(tmp_path / "airfoil.csv", VALID_AIRFOIL)
    section_path = _write(tmp_path / "sections.csv", VALID_SECTIONS)

    points = read_airfoil_csv(airfoil_path)
    sections = read_section_parameters(section_path)

    assert points[0] == (0.0, -0.75, 0.0)
    assert points[2] == (0.0, 0.25, 0.0)
    assert sections[1] == {
        "idx": 2,
        "chord_m": 0.08,
        "translate_x_m": 1.0,
        "translate_y_m": 0.0,
        "translate_z_m": 0.0,
        "rotation_deg": 5.0,
    }
