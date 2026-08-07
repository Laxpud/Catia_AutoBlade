import typer

from ..config.manager import ConfigManager
from ..core.executor import execute_job
from ..core.input_plan import inspect_section_mode
from ..core.jobs import BuildResult
from ..core.planner import plan_create_job
from ..utils.file_scanner import get_available_files
from .presentation import show_job_preview


def run_create_command(
    airfoil: str | None,
    section: str | None,
    output: str | None,
    interactive: bool,
    keep_failed_part: bool = False,
    *,
    config_manager: ConfigManager | None = None,
    blade_creator=None,
) -> BuildResult:
    """规划并执行一个模型；失败保持为异常交给最外层 CLI 呈现。"""
    manager = config_manager or ConfigManager()
    config = manager.load_runtime()
    airfoil_files, section_params_files = get_available_files(
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
    )
    if not section_params_files:
        raise ValueError("No section parameter files were found.")

    if interactive:
        from ..interactive.prompts import (
            confirm_execution,
            confirm_output_dir,
            select_airfoil,
            select_sections,
        )

        selected_section = section or select_sections(
            section_params_files,
            multi=False,
        )[0]
        output_default = (
            manager.resolve_cli_path(output)
            if output
            else config.paths.output_dir
        )
        output_dir = manager.resolve_cli_path(
            confirm_output_dir(str(output_default))
        )
    else:
        if section is None:
            raise ValueError(
                "Non-interactive create requires --section with one model definition."
            )
        selected_section = section
        output_dir = (
            manager.resolve_cli_path(output)
            if output
            else config.paths.output_dir
        )

    if selected_section not in section_params_files:
        raise ValueError(
            f"Section parameter file not found: {selected_section!r}."
        )

    section_mode = inspect_section_mode(
        config.paths.section_params_dir / selected_section
    )
    if section_mode == "multi":
        if airfoil is not None:
            raise ValueError(
                "--airfoil cannot be used when the section file contains "
                "an airfoil column."
            )
        selected_airfoil = None
    else:
        if airfoil is not None and airfoil not in airfoil_files:
            raise ValueError(f"Airfoil file not found: {airfoil!r}.")
        if interactive and airfoil is None:
            if not airfoil_files:
                raise ValueError("No airfoil files were found.")
            selected_airfoil = select_airfoil(airfoil_files)
        else:
            # Planner 对非交互缺参给出带截面路径和字段的领域错误。
            selected_airfoil = airfoil

    job = plan_create_job(
        selected_airfoil,
        selected_section,
        output_dir,
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
        output_name_template=config.defaults.output_name_template,
        author=config.defaults.author,
        keep_failed_part=keep_failed_part,
    )
    show_job_preview([job])
    if interactive:
        confirm_execution()

    typer.echo("[INFO] Creating single blade...")
    result = execute_job(job, blade_creator=blade_creator)
    typer.echo(f"[SUCCESS] Blade created: {job.output_name}")
    return result
