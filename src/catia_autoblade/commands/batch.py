import typer

from ..config.manager import ConfigManager
from ..core.executor import execute_jobs
from ..core.input_plan import inspect_section_mode
from ..core.jobs import BuildResult
from ..core.planner import plan_batch_jobs
from ..utils.file_scanner import get_available_files
from .presentation import show_job_preview


class BatchBuildError(Exception):
    """至少一个批处理任务失败；完整结构化结果仍可由调用方读取。"""

    def __init__(self, results: list[BuildResult]) -> None:
        self.results = results
        failed = sum(result.status == "failed" for result in results)
        super().__init__(
            f"Batch completed with {failed} failed task(s) out of {len(results)}."
        )


def run_batch_command(
    airfoil: str | None,
    section: str | None,
    output: str | None,
    list_files: bool,
    interactive: bool,
    *,
    config_manager: ConfigManager | None = None,
    batch_processor=None,
) -> list[BuildResult]:
    """规划多个闭合模型任务；目录内容不会扩展为翼型笛卡尔积。"""
    manager = config_manager or ConfigManager()
    config = manager.load_runtime()
    airfoil_files, section_params_files = get_available_files(
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
    )

    if list_files:
        _show_available_files(
            airfoil_files,
            section_params_files,
            config.paths.section_params_dir,
        )
        return []
    if not section_params_files:
        raise ValueError("No section parameter files were found.")

    if interactive:
        from ..interactive.prompts import (
            confirm_execution,
            confirm_output_dir,
            select_airfoil,
            select_sections,
        )

        selected_sections = (
            [section]
            if section is not None
            else select_sections(section_params_files, multi=True)
        )
        output_default = (
            manager.resolve_cli_path(output)
            if output
            else config.paths.output_dir
        )
        output_dir = manager.resolve_cli_path(
            confirm_output_dir(str(output_default))
        )
    else:
        selected_sections = [section] if section else section_params_files
        output_dir = (
            manager.resolve_cli_path(output)
            if output
            else config.paths.output_dir
        )

    missing_sections = [
        name for name in selected_sections if name not in section_params_files
    ]
    if missing_sections:
        raise ValueError(
            f"Section parameter file not found: {missing_sections[0]!r}."
        )

    modes = [
        inspect_section_mode(config.paths.section_params_dir / section_name)
        for section_name in selected_sections
    ]
    has_single_sections = "single" in modes
    if airfoil is not None and airfoil not in airfoil_files:
        raise ValueError(f"Airfoil file not found: {airfoil!r}.")
    if not has_single_sections and airfoil is not None:
        raise ValueError(
            "--airfoil cannot be used when all selected section files "
            "contain an airfoil column."
        )

    selected_airfoil = airfoil
    if interactive and has_single_sections and selected_airfoil is None:
        if not airfoil_files:
            raise ValueError("No airfoil files were found for six-column tasks.")
        selected_airfoil = select_airfoil(airfoil_files)

    jobs = plan_batch_jobs(
        selected_airfoil,
        selected_sections,
        output_dir,
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
        output_name_template=config.defaults.output_name_template,
        author=config.defaults.author,
    )
    show_job_preview(jobs)
    if interactive:
        confirm_execution()

    processor = batch_processor or execute_jobs
    results = processor(jobs)
    if len(results) != len(jobs):
        raise ValueError(
            "Batch executor returned "
            f"{len(results)} result(s) for {len(jobs)} job(s)."
        )
    success_count = sum(result.status == "success" for result in results)
    for result in results:
        if result.status == "failed":
            typer.echo(
                "[ERROR] Failed to create blade for "
                f"{result.job.section_params_filename}: {result.error}",
                err=True,
            )
    typer.echo(
        f"[INFO] Batch completed: {success_count}/{len(results)} successful."
    )
    if success_count != len(results):
        raise BatchBuildError(results)
    return results


def _show_available_files(
    airfoil_files: list[str],
    section_params_files: list[str],
    section_params_dir,
) -> None:
    typer.echo("[INFO] Available airfoil files:")
    for filename in airfoil_files:
        typer.echo(f"  - {filename}")
    typer.echo("\n[INFO] Available section parameter files:")
    for filename in section_params_files:
        mode = inspect_section_mode(section_params_dir / filename)
        label = "self-contained" if mode == "multi" else "six-column template"
        typer.echo(f"  - {filename} ({label})")
