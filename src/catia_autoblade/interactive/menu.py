import typer

from .prompts import PromptCancelled


def run_main_menu() -> None:
    """运行一次操作后返回顶层菜单，直到用户明确退出。"""
    from .prompts import select_main_action

    while True:
        action = select_main_action()
        if action == "exit":
            return
        if action == "sweep":
            typer.echo("[INFO] sweep is planned but not implemented yet.")
            continue

        try:
            _run_menu_action(action)
        except PromptCancelled as error:
            typer.echo(f"[INFO] {error}")
        except KeyboardInterrupt:
            raise
        except Exception as error:
            # 菜单会话中的单次操作失败不应结束整个人工会话；显式子命令仍由
            # CLI 边界把同一异常转换为退出码 1。
            typer.echo(f"[ERROR] {error}", err=True)


def _run_menu_action(action: str) -> None:
    if action == "create":
        from ..commands.create import run_create_command

        run_create_command(None, None, None, True)
    elif action == "batch":
        from ..commands.batch import run_batch_command

        run_batch_command(None, None, None, False, True)
    elif action == "list":
        from ..commands.list import run_list_command

        run_list_command(False)
    elif action == "config":
        _run_config_menu()
    else:
        raise ValueError(f"Unknown menu action: {action}")


def _run_config_menu() -> None:
    from ..commands.config import CONFIG_KEYS, run_config_command
    from ..config.manager import ConfigManager
    from .prompts import (
        ask_config_value,
        confirm_config_reset,
        select_config_action,
        select_config_key,
    )

    action = select_config_action()
    if action == "back":
        return
    if action == "show":
        run_config_command("show", None, None)
        return
    if action == "reset":
        if confirm_config_reset():
            run_config_command("reset", None, None)
        return

    manager = ConfigManager()
    config = manager.load()
    key = select_config_key(list(CONFIG_KEYS))
    owner = config.paths if hasattr(config.paths, key) else config.defaults
    current_value = str(getattr(owner, key))
    value = ask_config_value(key, current_value)
    run_config_command("set", key, value, config_manager=manager)
