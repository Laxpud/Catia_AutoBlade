import csv
import re
from pathlib import Path

from catia_autoblade.core.input_plan import build_blade_input_plan
from catia_autoblade.core.input_validation import (
    read_airfoil_csv,
    read_section_parameters,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AIRFOIL_DIR = PROJECT_ROOT / "input" / "airfoils"
SECTION_PARAMS_DIR = PROJECT_ROOT / "input" / "section_params"
MULTI_AIRFOIL_SAMPLE = SECTION_PARAMS_DIR / "section_params-multi-airfoil.csv"
CANONICAL_INPUT_NAME = re.compile(r"[a-z0-9][a-z0-9_-]*\.csv")
EXPECTED_MULTI_AIRFOILS = (
    "airfoil1_sharp.csv",
    "airfoil2_sharp.csv",
    "airfoil3_sharp.csv",
)


def test_repository_input_filenames_are_portable_and_unambiguous() -> None:
    """版本化输入使用稳定的小写名称，避免 Windows 大小写别名。"""
    for directory in (AIRFOIL_DIR, SECTION_PARAMS_DIR):
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
