from collections.abc import Iterable
from pathlib import Path

from ..utils.output_naming import build_output_name
from .input_plan import build_blade_input_plan, inspect_section_mode
from .input_validation import InputValidationError
from .jobs import BladeBuildJob


def plan_create_job(
    airfoil_filename: str | None,
    section_params_filename: str,
    output_dir: str | Path,
    *,
    airfoil_dir: str | Path,
    section_params_dir: str | Path,
    output_name_template: str,
    author: str,
    keep_failed_part: bool = False,
) -> BladeBuildJob:
    """把一个明确模型定义规划为可直接执行的闭合任务。"""
    airfoil_path = Path(airfoil_dir).resolve()
    section_dir_path = Path(section_params_dir).resolve()
    section_path = _resolve_section_file(
        section_dir_path,
        section_params_filename,
    )

    # 完整解析必须发生在 Planner 内；Executor 后续启动 CATIA 时不再发现输入
    # 文件缺失、逐行翼型引用错误或后缘拓扑冲突。
    input_plan = build_blade_input_plan(
        section_path,
        airfoil_path,
        airfoil_filename,
    )
    output_name = build_output_name(
        output_name_template,
        airfoil_filename,
        section_params_filename,
        author=author,
        is_multi_airfoil=input_plan.mode == "multi",
    )
    return BladeBuildJob(
        mode=input_plan.mode,
        airfoil_filename=airfoil_filename,
        section_params_filename=section_params_filename,
        airfoil_dir=airfoil_path,
        section_params_dir=section_dir_path,
        output_dir=Path(output_dir).resolve(),
        output_name=output_name,
        input_plan=input_plan,
        keep_failed_part=keep_failed_part,
    )


def plan_batch_jobs(
    airfoil_filename: str | None,
    section_params_filenames: Iterable[str],
    output_base_dir: str | Path,
    *,
    airfoil_dir: str | Path,
    section_params_dir: str | Path,
    output_name_template: str,
    author: str,
) -> list[BladeBuildJob]:
    """为多个模型定义生成稳定排序的任务，不执行隐式笛卡尔积。

    六列截面模板统一绑定同一个显式翼型；含 ``airfoil`` 列的文件已经
    自包含，始终以 ``None`` 作为后备翼型。多翼型文件与六列模板可以在
    同一批次中出现，但外部翼型只作用于后者。
    """
    section_files = sorted(dict.fromkeys(section_params_filenames))
    if not section_files:
        raise ValueError("No section parameter files were selected.")

    section_dir_path = Path(section_params_dir).resolve()
    jobs: list[BladeBuildJob] = []
    for section_filename in section_files:
        section_path = _resolve_section_file(
            section_dir_path,
            section_filename,
        )
        mode = inspect_section_mode(section_path)
        if mode == "single" and airfoil_filename is None:
            raise InputValidationError(
                section_path,
                "six-column section parameters in batch require --airfoil",
                field="airfoil",
            )

        job_airfoil = airfoil_filename if mode == "single" else None
        output_subdir = (
            Path(job_airfoil).stem
            if job_airfoil is not None
            else Path(section_filename).stem
        )
        jobs.append(
            plan_create_job(
                job_airfoil,
                section_filename,
                Path(output_base_dir) / output_subdir,
                airfoil_dir=airfoil_dir,
                section_params_dir=section_dir_path,
                output_name_template=output_name_template,
                author=author,
            )
        )

    # 同一批次的两个任务不得指向相同文件。磁盘上已有同名文件仍按既有
    # 覆盖契约处理，并由交互预览显式标记。
    targets: dict[Path, BladeBuildJob] = {}
    for job in jobs:
        for target in job.output_paths:
            normalized = target.resolve()
            if normalized in targets:
                other = targets[normalized]
                raise ValueError(
                    "Batch output conflict between "
                    f"{other.section_params_filename!r} and "
                    f"{job.section_params_filename!r}: {normalized}"
                )
            targets[normalized] = job
    return jobs


def _resolve_section_file(
    section_params_dir: Path,
    section_params_filename: str,
) -> Path:
    """将 CLI 中的截面 basename 限制在配置目录内并检查精确文件名。"""
    if Path(section_params_filename).name != section_params_filename:
        raise InputValidationError(
            section_params_dir / section_params_filename,
            "section parameters must be a CSV basename",
        )
    section_path = section_params_dir / section_params_filename
    if section_path.suffix.lower() != ".csv" or not section_path.is_file():
        raise InputValidationError(
            section_path,
            f"section parameter file not found: {section_params_filename}",
        )
    return section_path
