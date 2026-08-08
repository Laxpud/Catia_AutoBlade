import sys
from collections.abc import Callable
from typing import Annotated

import typer


app = typer.Typer(
    help="CATIA AutoBlade - Blade creation automation tool",
    invoke_without_command=True,
    no_args_is_help=False,
)


def is_interactive_terminal() -> bool:
    """无参数菜单只在输入和输出都连接真实终端时启用。"""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _run_cli(action: Callable[[], object]) -> object | None:
    """统一人类可读错误、取消和进程退出码的最外层命令边界。"""
    from .interactive.prompts import PromptCancelled

    try:
        return action()
    except PromptCancelled as error:
        typer.echo(f"[INFO] {error}")
        return None
    except KeyboardInterrupt:
        typer.echo("\n[ERROR] Interrupted by user.", err=True)
        raise typer.Exit(130) from None
    except typer.Exit:
        raise
    except Exception as error:
        typer.echo(f"[ERROR] {error}", err=True)
        raise typer.Exit(1) from None


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            help="Show the installed CATIA AutoBlade version and exit.",
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Open the interactive menu when no explicit subcommand is provided."""
    if version:
        from . import __version__

        typer.echo(f"catia-autoblade {__version__}")
        raise typer.Exit()
    if ctx.invoked_subcommand is not None:
        return
    if not is_interactive_terminal():
        typer.echo(ctx.get_help(), err=True)
        raise typer.Exit(2)

    from .interactive.menu import run_main_menu

    _run_cli(run_main_menu)


@app.command()
def create(
    airfoil: Annotated[str | None, typer.Option("--airfoil", "-a")] = None,
    section: Annotated[str | None, typer.Option("--section", "-s")] = None,
    output: Annotated[str | None, typer.Option("--output", "-o")] = None,
    interactive: Annotated[bool, typer.Option("--interactive", "-i")] = False,
    keep_failed_part: Annotated[
        bool,
        typer.Option(
            "--keep-failed-part",
            help="Save a CATPart snapshot when CATIA modeling fails.",
        ),
    ] = False,
) -> None:
    """Create one blade from one explicit model definition."""
    from .commands.create import run_create_command

    _run_cli(
        lambda: run_create_command(
            airfoil,
            section,
            output,
            interactive,
            keep_failed_part,
        )
    )


@app.command()
def batch(
    airfoil: Annotated[str | None, typer.Option("--airfoil", "-a")] = None,
    section: Annotated[str | None, typer.Option("--section", "-s")] = None,
    output: Annotated[str | None, typer.Option("--output", "-o")] = None,
    list_files: Annotated[bool, typer.Option("--list", "-l")] = False,
    interactive: Annotated[bool, typer.Option("--interactive", "-i")] = False,
) -> None:
    """Build multiple closed model definitions without parameter combinations."""
    from .commands.batch import run_batch_command

    _run_cli(
        lambda: run_batch_command(
            airfoil,
            section,
            output,
            list_files,
            interactive,
        )
    )


@app.command("list")
def list_inputs(
    config_show: Annotated[bool, typer.Option("--config")] = False,
) -> None:
    """List available files or configuration."""
    from .commands.list import run_list_command

    _run_cli(lambda: run_list_command(config_show))


@app.command()
def config(
    action: Annotated[str, typer.Argument()] = ...,
    key: Annotated[str | None, typer.Option("--key", "-k")] = None,
    value: Annotated[str | None, typer.Option("--value", "-v")] = None,
) -> None:
    """Manage configuration file (show, set, reset)."""
    if action not in {"show", "set", "reset"}:
        raise typer.BadParameter("action must be one of: show, set, reset")
    if action == "set" and (key is None or value is None):
        raise typer.BadParameter(
            "config set requires both --key and --value"
        )

    from .commands.config import run_config_command

    _run_cli(lambda: run_config_command(action, key, value))


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
