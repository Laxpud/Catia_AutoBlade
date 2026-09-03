import csv
import re
from pathlib import Path

from autoblade.core.input_plan import build_blade_input_plan
from autoblade.core.input_validation import (
    read_airfoil_csv,
    read_section_parameters,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AIRFOIL_DIR = PROJECT_ROOT / "input" / "airfoils"
BLADE_SECTIONS_DIR = PROJECT_ROOT / "input" / "blade_sections"
MULTI_AIRFOIL_SAMPLE = BLADE_SECTIONS_DIR / "blade_sections-multi-airfoil.csv"
ZERO_TRANSLATION_SAMPLE = BLADE_SECTIONS_DIR / "blade_sections-naca.csv"
CANONICAL_INPUT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*\.csv")
EXPECTED_MULTI_AIRFOILS = (
    "airfoil1_sharp.csv",
    "airfoil2_sharp.csv",
    "airfoil3_sharp.csv",
)
BATCH_REGRESSION_FILES = tuple(
    BLADE_SECTIONS_DIR / f"blade_sections-{index}.csv"
    for index in range(1, 6)
)


def test_repository_input_filenames_are_portable_and_unambiguous() -> None:
    """版本化输入使用稳定的小写名称，避免 Windows 大小写别名。"""
    for directory in (AIRFOIL_DIR, BLADE_SECTIONS_DIR):
        csv_names = sorted(path.name for path in directory.glob("*.csv"))

        assert csv_names
        assert all(CANONICAL_INPUT_NAME.fullmatch(name) for name in csv_names)
        assert len(csv_names) == len({name.casefold() for name in csv_names})


def test_multi_airfoil_sample_has_complete_resolvable_references() -> None:
    """里程碑样例必须自包含，不能引用仅存在于某台开发机的文件。"""
    with MULTI_AIRFOIL_SAMPLE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 89
    assert [int(row["idx"]) for row in rows] == list(range(1, 90))
    assert len(read_section_parameters(MULTI_AIRFOIL_SAMPLE)) == 89

    # dict 保留首次出现顺序，这里同时固化三个展向区域的切换顺序。
    referenced_airfoils = tuple(dict.fromkeys(row["airfoil"] for row in rows))
    assert referenced_airfoils == EXPECTED_MULTI_AIRFOILS

    for airfoil_name in referenced_airfoils:
        assert Path(airfoil_name).name == airfoil_name
        assert CANONICAL_INPUT_NAME.fullmatch(airfoil_name)
        airfoil_path = AIRFOIL_DIR / airfoil_name
        assert airfoil_path.is_file()
        assert len(read_airfoil_csv(airfoil_path)) >= 3


def test_multi_airfoil_sample_builds_complete_pre_catia_plan() -> None:
    """真实 89 行样例必须能在不启动 CATIA 的情况下闭合所有输入。"""
    plan = build_blade_input_plan(
        MULTI_AIRFOIL_SAMPLE,
        AIRFOIL_DIR,
        None,
    )

    assert plan.mode == "multi"
    assert len(plan.sections) == 89
    assert [airfoil.filename for airfoil in plan.airfoils] == list(
        EXPECTED_MULTI_AIRFOILS
    )
    assert [len(airfoil.points) for airfoil in plan.airfoils] == [300, 253, 249]
    assert plan.is_sharp is True


def test_naca_regression_contains_a_zero_translation_section() -> None:
    """零位移资产必须实际覆盖三轴平移同时为 0 的分支。"""
    sections = read_section_parameters(ZERO_TRANSLATION_SAMPLE)

    assert any(
        section["translate_x_m"] == 0
        and section["translate_y_m"] == 0
        and section["translate_z_m"] == 0
        for section in sections
    )
    naca_airfoil = AIRFOIL_DIR / "naca0012_sharp.csv"
    assert naca_airfoil.is_file()
    assert len(read_airfoil_csv(naca_airfoil)) >= 3


def test_five_single_airfoil_batch_regressions_remain_parseable() -> None:
    """固定 batch 回归组必须保持五份、每份 26 个有效截面。"""
    assert all(path.is_file() for path in BATCH_REGRESSION_FILES)
    assert [
        len(read_section_parameters(path))
        for path in BATCH_REGRESSION_FILES
    ] == [26, 26, 26, 26, 26]
