import typer

from ..config.manager import ConfigManager


CONFIG_KEYS = (
    "input_dir",
    "output_dir",
    "airfoil_dir",
    "section_params_dir",
    "author",
    "output_name_template",
)


def run_config_command(
    action: str,
    key: str | None,
    value: str | None,
    *,
    config_manager: ConfigManager | None = None,
) -> None:
    manager = config_manager or ConfigManager()

    if action == "show":
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

    if action == "set":
        if key is None or value is None:
            raise ValueError("Both --key and --value are required for config set.")
        if key not in CONFIG_KEYS:
            raise ValueError(
                f"Invalid configuration key {key!r}. Valid keys: "
                f"{', '.join(CONFIG_KEYS)}"
            )

        config = manager.load()
        owner = config.paths if hasattr(config.paths, key) else config.defaults
        setattr(owner, key, value)
        manager.save(config)
        typer.echo(f"[INFO] {key} set to {value!r}")
        return

    if action == "reset":
        manager.save(manager.load().__class__())
        typer.echo("[INFO] Configuration reset to defaults.")
        return

    raise ValueError("Configuration action must be one of: show, set, reset.")
