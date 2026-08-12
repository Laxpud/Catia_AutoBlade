from pathlib import Path

import pytest

from catia_autoblade.core.executor import execute_jobs
from catia_autoblade.core.input_validation import InputValidationError
from catia_autoblade.core.planner import plan_batch_jobs, plan_create_job


SHARP_AIRFOIL = """x,y,z
0,1,0
0,0.5,0.1
0,0,0
0,0.5,-0.1
0,1,0
"""

SECTIONS = """idx,scale/m,translate_x/m,translate_y/m,translate_z/m,rotate/deg
1,0.1,0,0,0,10
2,0.08,1,0,0,5
"""


def _inputs(tmp_path: Path, section_count: int = 1):
    airfoil_dir = tmp_path / "airfoils"
    section_dir = tmp_path / "sections"
    airfoil_dir.mkdir()
    section_dir.mkdir()
    for filename in ("foil-a.csv", "foil-b.csv"):
        (airfoil_dir / filename).write_text(SHARP_AIRFOIL, encoding="utf-8")
    section_files = []
    for index in range(1, section_count + 1):
        filename = f"blade_sections-{index}.csv"
        (section_dir / filename).write_text(SECTIONS, encoding="utf-8")
        section_files.append(filename)
    return airfoil_dir, section_dir, section_files


def test_create_planner_returns_one_closed_job(tmp_path: Path) -> None:
    airfoil_dir, section_dir, section_files = _inputs(tmp_path)

    job = plan_create_job(
        "foil-a.csv",
        section_files[0],
        tmp_path / "output",
        airfoil_dir=airfoil_dir,
        blade_sections_dir=section_dir,
        output_name_template="{blade}",
        author="",
    )

    assert job.mode == "single"
    assert job.output_name == "foil-a_blade-1"
    assert job.input_plan.airfoils[0].filename == "foil-a.csv"
    assert len(job.input_plan.sections) == 2


def test_batch_binds_one_airfoil_to_five_templates_without_product(
    tmp_path: Path,
) -> None:
    airfoil_dir, section_dir, section_files = _inputs(tmp_path, section_count=5)

    jobs = plan_batch_jobs(
        "foil-a.csv",
        reversed(section_files),
        tmp_path / "output",
        airfoil_dir=airfoil_dir,
        blade_sections_dir=section_dir,
        output_name_template="{blade}",
        author="",
    )

    assert len(jobs) == 5
    assert [job.blade_sections_filename for job in jobs] == section_files
    assert {job.airfoil_filename for job in jobs} == {"foil-a.csv"}


def test_batch_requires_airfoil_for_six_column_template(tmp_path: Path) -> None:
    airfoil_dir, section_dir, section_files = _inputs(tmp_path)

    with pytest.raises(InputValidationError, match="require --airfoil"):
        plan_batch_jobs(
            None,
            section_files,
            tmp_path / "output",
            airfoil_dir=airfoil_dir,
            blade_sections_dir=section_dir,
            output_name_template="{blade}",
            author="",
        )


def test_executor_continues_after_one_job_failure(tmp_path: Path) -> None:
    airfoil_dir, section_dir, section_files = _inputs(tmp_path, section_count=2)
    jobs = plan_batch_jobs(
        "foil-a.csv",
        section_files,
        tmp_path / "output",
        airfoil_dir=airfoil_dir,
        blade_sections_dir=section_dir,
        output_name_template="{blade}",
        author="",
    )
    calls = []

    def fake_create(airfoil, section, *args, **kwargs):
        calls.append((airfoil, section, kwargs["input_plan"].mode))
        if section == section_files[0]:
            raise RuntimeError("model failed")

    results = execute_jobs(jobs, blade_creator=fake_create)

    assert [result.status for result in results] == ["failed", "success"]
    assert [call[1] for call in calls] == section_files


def test_batch_planner_rejects_duplicate_output_targets(tmp_path: Path) -> None:
    airfoil_dir, section_dir, section_files = _inputs(tmp_path, section_count=2)

    with pytest.raises(ValueError, match="Batch output conflict"):
        plan_batch_jobs(
            "foil-a.csv",
            section_files,
            tmp_path / "output",
            airfoil_dir=airfoil_dir,
            blade_sections_dir=section_dir,
            output_name_template="same-name",
            author="",
        )
