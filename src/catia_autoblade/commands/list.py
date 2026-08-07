import typer

from ..config.manager import ConfigManager
from ..core.input_plan import inspect_section_mode
from ..utils.file_scanner import get_available_files


def run_list_command(
    config_show: bool,
    *,
    config_manager: ConfigManager | None = None,
) -> None:
    manager = config_manager or ConfigManager()
    if config_show:
        config = manager.load()
        typer.echo("[INFO] Current configuration:")
        typer.echo(f"  input_dir: {config.paths.input_dir}")
        typer.echo(f"  output_dir: {config.paths.output_dir}")
        typer.echo(f"  airfoil_dir: {config.paths.airfoil_dir}")
        typer.echo(f"  section_params_dir: {config.paths.section_params_dir}")
        typer.echo(f"  author: {config.defaults.author}")
        typer.echo(
            "  output_name_template: "
            f"{config.defaults.output_name_template}"
        )
        return

    config = manager.load_runtime()
    airfoil_files, section_params_files = get_available_files(
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
    )
    typer.echo("[INFO] Available airfoil files:")
    for filename in airfoil_files:
        typer.echo(f"  - {filename}")
    typer.echo("\n[INFO] Available section parameter files:")
    for filename in section_params_files:
        mode = inspect_section_mode(config.paths.section_params_dir / filename)
        label = "self-contained" if mode == "multi" else "six-column template"
        typer.echo(f"  - {filename} ({label})")
