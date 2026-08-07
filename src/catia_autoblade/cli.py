import typer
from typing import Optional, Annotated

app = typer.Typer(help="CATIA AutoBlade - Blade creation automation tool")


@app.command()
def create(
    airfoil: Annotated[Optional[str], typer.Option("--airfoil", "-a")] = None,
    section: Annotated[Optional[str], typer.Option("--section", "-s")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o")] = None,
    interactive: Annotated[bool, typer.Option("--interactive", "-i")] = False,
    keep_failed_part: Annotated[
        bool,
        typer.Option(
            "--keep-failed-part",
            help="Save a CATPart snapshot when CATIA modeling fails.",
        ),
    ] = False,
):
    """Create a single blade"""
    from .commands.create import run_create_command
    run_create_command(
        airfoil,
        section,
        output,
        interactive,
        keep_failed_part,
    )


@app.command()
def batch(
    airfoil: Annotated[Optional[str], typer.Option("--airfoil", "-a")] = None,
    section: Annotated[Optional[str], typer.Option("--section", "-s")] = None,
    output: Annotated[Optional[str], typer.Option("--output", "-o")] = None,
    list_files: Annotated[bool, typer.Option("--list", "-l")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i")] = False,
):
    """Batch create blades"""
    from .commands.batch import run_batch_command
    run_batch_command(airfoil, section, output, list_files, interactive)


@app.command()
def list(
    config_show: Annotated[bool, typer.Option("--config")] = False,
):
    """List available files or configuration"""
    from .commands.list import run_list_command
    run_list_command(config_show)


@app.command()
def config(
    action: Annotated[str, typer.Argument] = ...,
    key: Annotated[Optional[str], typer.Option("--key", "-k")] = None,
    value: Annotated[Optional[str], typer.Option("--value", "-v")] = None,
):
    """Manage configuration file (show, set, reset)"""
    if action not in ["show", "set", "reset"]:
        raise typer.BadParameter("action must be one of: show, set, reset")
    from .commands.config import run_config_command
    run_config_command(action, key, value)


def create_entrypoint() -> None:
    """运行与 ``autoblade create`` 参数一致的独立 CLI 入口。"""
    # console script 会零参数调用目标函数，因此需要先由 Typer 解析命令行，
    # 再复用主命令的回调，避免独立入口与子命令维护两套参数契约。
    typer.run(create)


def batch_entrypoint() -> None:
    """运行与 ``autoblade batch`` 参数一致的独立 CLI 入口。"""
    # 与 create 入口采用同一模式，保证新增或调整选项时两种调用方式同步变化。
    typer.run(batch)


if __name__ == "__main__":
    app()
