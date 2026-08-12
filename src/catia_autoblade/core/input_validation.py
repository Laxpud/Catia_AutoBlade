import csv
import math
from dataclasses import dataclass
from pathlib import Path


AIRFOIL_QUARTER_CHORD_RATIO = 0.25
AIRFOIL_FIELDS = ("x", "y", "z")
SECTION_PARAMETER_FIELDS = (
    "idx",
    "scale/m",
    "translate_x/m",
    "translate_y/m",
    "translate_z/m",
    "rotate/deg",
)
COORDINATE_TOLERANCE_M = 1e-9


SectionParameters = dict[str, float | int | str]


@dataclass(frozen=True, slots=True)
class SectionParameterTable:
    """保留截面字段模式和源行号的预检结果。"""

    sections: tuple[SectionParameters, ...]
    source_lines: tuple[int, ...]
    has_airfoil_column: bool


class InputValidationError(ValueError):
    """包含源文件、行号、字段和违反约束的输入错误。"""

    def __init__(
        self,
        path: str | Path,
        constraint: str,
        *,
        line: int | None = None,
        field: str | None = None,
    ) -> None:
        location = str(Path(path).resolve())
        details = []
        if line is not None:
            details.append(f"line {line}")
        if field is not None:
            details.append(f"field '{field}'")
        if details:
            location = f"{location}: {', '.join(details)}"
        super().__init__(f"{location}: {constraint}")


def read_airfoil_csv(csv_path: str | Path) -> list[tuple[float, float, float]]:
    """校验翼型 CSV，并返回转换到模型坐标系的米制点。"""
    path = Path(csv_path)
    rows: list[tuple[int, float, float, float]] = []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            _validate_header(path, reader.fieldnames, AIRFOIL_FIELDS)
            for row in reader:
                line = reader.line_num
                if _is_blank_row(row):
                    continue
                x = _parse_float(path, row, line, "x")
                y = _parse_float(path, row, line, "y")
                z = _parse_float(path, row, line, "z")
                rows.append((line, x, y, z))
    except (OSError, UnicodeError, csv.Error) as error:
        raise InputValidationError(path, f"cannot read airfoil CSV: {error}") from error

    if len(rows) < 3:
        raise InputValidationError(
            path,
            f"expected at least 3 airfoil points, found {len(rows)}",
        )

    _validate_airfoil_geometry(path, rows)
    points = [
        (x, -y + AIRFOIL_QUARTER_CHORD_RATIO, z)
        for _, x, y, z in rows
    ]
    print(f"[INFO] Validated {len(points)} airfoil points from {path}.")
    return points


def read_section_parameters(csv_path: str | Path) -> list[SectionParameters]:
    """校验桨叶截面定义 CSV，并返回建模使用的标准字段。"""
    table = read_section_parameter_table(csv_path)
    return [dict(section) for section in table.sections]


def read_section_parameter_table(csv_path: str | Path) -> SectionParameterTable:
    """解析截面表，并保留多翼型模式和错误定位所需的源行号。"""
    path = Path(csv_path)
    sections: list[SectionParameters] = []
    source_lines: list[int] = []
    previous_idx: int | None = None
    has_airfoil_column = False

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            _validate_header(path, reader.fieldnames, SECTION_PARAMETER_FIELDS)
            has_airfoil_column = (
                reader.fieldnames is not None and "airfoil" in reader.fieldnames
            )
            for row in reader:
                line = reader.line_num
                if _is_blank_row(row):
                    continue

                idx = _parse_int(path, row, line, "idx")
                chord_m = _parse_float(path, row, line, "scale/m")
                if idx <= 0:
                    raise InputValidationError(
                        path,
                        "section index must be a positive integer",
                        line=line,
                        field="idx",
                    )
                if previous_idx is not None and idx <= previous_idx:
                    raise InputValidationError(
                        path,
                        f"section index must be strictly greater than previous idx {previous_idx}",
                        line=line,
                        field="idx",
                    )
                if chord_m <= 0:
                    raise InputValidationError(
                        path,
                        "section chord must be greater than 0 m",
                        line=line,
                        field="scale/m",
                    )

                section: SectionParameters = {
                    "idx": idx,
                    "chord_m": chord_m,
                    "translate_x_m": _parse_float(
                        path, row, line, "translate_x/m"
                    ),
                    "translate_y_m": _parse_float(
                        path, row, line, "translate_y/m"
                    ),
                    "translate_z_m": _parse_float(
                        path, row, line, "translate_z/m"
                    ),
                    "rotation_deg": _parse_float(path, row, line, "rotate/deg"),
                }
                if has_airfoil_column:
                    raw_airfoil = row.get("airfoil")
                    if not isinstance(raw_airfoil, str) or not raw_airfoil:
                        raise InputValidationError(
                            path,
                            "expected a non-empty airfoil filename",
                            line=line,
                            field="airfoil",
                        )
                    section["airfoil_filename"] = raw_airfoil

                sections.append(section)
                source_lines.append(line)
                previous_idx = idx
    except (OSError, UnicodeError, csv.Error) as error:
        raise InputValidationError(
            path,
            f"cannot read blade section definition CSV: {error}",
        ) from error

    if len(sections) < 2:
        raise InputValidationError(
            path,
            f"expected at least 2 section rows for loft, found {len(sections)}",
        )

    print(f"[INFO] Validated {len(sections)} section rows from {path}.")
    return SectionParameterTable(
        sections=tuple(sections),
        source_lines=tuple(source_lines),
        has_airfoil_column=has_airfoil_column,
    )


def _validate_header(
    path: Path,
    fieldnames: list[str] | None,
    required_fields: tuple[str, ...],
) -> None:
    if fieldnames is None:
        expected = ", ".join(required_fields)
        raise InputValidationError(path, f"CSV is empty; expected header: {expected}")

    missing_fields = [field for field in required_fields if field not in fieldnames]
    if missing_fields:
        missing = ", ".join(missing_fields)
        raise InputValidationError(
            path,
            f"missing required column(s): {missing}",
            line=1,
            field=missing,
        )


def _is_blank_row(row: dict[str | None, str | list[str] | None]) -> bool:
    return all(
        value is None
        or value == []
        or (isinstance(value, str) and not value.strip())
        for value in row.values()
    )


def _parse_float(
    path: Path,
    row: dict[str | None, str | list[str] | None],
    line: int,
    field: str,
) -> float:
    raw_value = row.get(field)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise InputValidationError(
            path,
            "expected a finite number, found an empty value",
            line=line,
            field=field,
        )
    try:
        value = float(raw_value)
    except ValueError as error:
        raise InputValidationError(
            path,
            f"expected a finite number, found {raw_value!r}",
            line=line,
            field=field,
        ) from error
    if not math.isfinite(value):
        raise InputValidationError(
            path,
            f"expected a finite number, found {raw_value!r}",
            line=line,
            field=field,
        )
    return value


def _parse_int(
    path: Path,
    row: dict[str | None, str | list[str] | None],
    line: int,
    field: str,
) -> int:
    raw_value = row.get(field)
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise InputValidationError(
            path,
            "expected an integer, found an empty value",
            line=line,
            field=field,
        )
    try:
        return int(raw_value)
    except ValueError as error:
        raise InputValidationError(
            path,
            f"expected an integer, found {raw_value!r}",
            line=line,
            field=field,
        ) from error


def _validate_airfoil_geometry(
    path: Path,
    rows: list[tuple[int, float, float, float]],
) -> None:
    # 1. 当前几何链路要求所有点位于 Y-Z 平面，且弦向坐标归一化到 [0, 1] m。
    for line, x, y, _ in rows:
        if abs(x) > COORDINATE_TOLERANCE_M:
            raise InputValidationError(
                path,
                "airfoil points must lie in the Y-Z plane (x = 0 m)",
                line=line,
                field="x",
            )
        if y < -COORDINATE_TOLERANCE_M or y > 1 + COORDINATE_TOLERANCE_M:
            raise InputValidationError(
                path,
                "chordwise coordinate must be within [0, 1] m",
                line=line,
                field="y",
            )

    # 2. 相邻重复点会导致 CATIA 样条退化；首尾相等仍允许表示尖后缘。
    for index in range(1, len(rows)):
        previous = rows[index - 1][1:]
        current = rows[index][1:]
        if all(
            math.isclose(a, b, abs_tol=COORDINATE_TOLERANCE_M)
            for a, b in zip(previous, current, strict=True)
        ):
            raise InputValidationError(
                path,
                "airfoil point must not repeat the previous point",
                line=rows[index][0],
            )

    # 3. 正式点序是尾缘 -> 前缘 -> 尾缘。前缘允许因离散采样而不精确等于 0，
    # 但必须是内部弦向最小值，两侧分别保持非递增和非递减。
    chordwise = [row[2] for row in rows]
    minimum = min(chordwise)
    maximum = max(chordwise)
    leading_edge_index = chordwise.index(minimum)
    if maximum - minimum <= COORDINATE_TOLERANCE_M:
        raise InputValidationError(
            path,
            "airfoil must span a non-zero chord from trailing edge to leading edge",
            field="y",
        )
    if leading_edge_index in {0, len(rows) - 1}:
        raise InputValidationError(
            path,
            "point order must start at trailing edge, pass an internal leading edge, and return to trailing edge",
            line=rows[leading_edge_index][0],
            field="y",
        )
    if not math.isclose(chordwise[0], maximum, abs_tol=COORDINATE_TOLERANCE_M):
        raise InputValidationError(
            path,
            "first point must be on the trailing edge (maximum chordwise y)",
            line=rows[0][0],
            field="y",
        )
    if not math.isclose(chordwise[-1], maximum, abs_tol=COORDINATE_TOLERANCE_M):
        raise InputValidationError(
            path,
            "last point must return to the trailing edge (maximum chordwise y)",
            line=rows[-1][0],
            field="y",
        )

    for index in range(1, leading_edge_index + 1):
        if chordwise[index] > chordwise[index - 1] + COORDINATE_TOLERANCE_M:
            raise InputValidationError(
                path,
                "upper-surface chordwise y must be non-increasing toward the leading edge",
                line=rows[index][0],
                field="y",
            )
    for index in range(leading_edge_index + 1, len(rows)):
        if chordwise[index] < chordwise[index - 1] - COORDINATE_TOLERANCE_M:
            raise InputValidationError(
                path,
                "lower-surface chordwise y must be non-decreasing toward the trailing edge",
                line=rows[index][0],
                field="y",
            )
