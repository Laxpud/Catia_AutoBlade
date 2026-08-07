from collections.abc import Iterable

import typer

from ..core.jobs import BladeBuildJob


def show_job_preview(jobs: Iterable[BladeBuildJob]) -> list[BladeBuildJob]:
    """展示输入模式、任务总数、输出位置和已有文件覆盖风险。"""
    planned = list(jobs)
    typer.echo(f"[INFO] Planned build jobs: {len(planned)}")
    for index, job in enumerate(planned, start=1):
        airfoil = job.airfoil_filename or "per-section references"
        typer.echo(
            f"  {index}. mode={job.mode}, airfoil={airfoil}, "
            f"section={job.section_params_filename}"
        )
        typer.echo(f"     output={job.output_dir / job.output_name}")
        existing = [path for path in job.output_paths if path.exists()]
        if existing:
            names = ", ".join(path.name for path in existing)
            typer.echo(f"     overwrite={names}")
    return planned
