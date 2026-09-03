from pathlib import Path

import questionary


class PromptCancelled(Exception):
    """用户通过取消选项退出当前向导，而不是中断整个进程。"""


def _ask(question):
    """让 Ctrl+C 保持为 KeyboardInterrupt，以便 CLI 统一映射到 130。"""
    value = question.unsafe_ask()
    if value is None:
        raise PromptCancelled("Interactive selection was cancelled.")
    return value


def select_airfoil(files: list[str]) -> str:
    return _ask(
        questionary.select(
            "Select an airfoil file:",
            choices=files,
        )
    )


def select_airfoils(files: list[str]) -> list[str]:
    """为 sweep 显式选择多个翼型；空选择按取消处理。"""
    selected = _ask(
        questionary.checkbox(
            "Select airfoil files for Cartesian product:",
            choices=files,
        )
    )
    if not selected:
        raise PromptCancelled("No airfoil files were selected.")
    return selected


def select_sections(files: list[str], multi: bool = False) -> list[str]:
    if multi:
        selected = _ask(
            questionary.checkbox(
                "Select section params files (multi-select):",
                choices=files,
            )
        )
        if not selected:
            raise PromptCancelled("No blade section definition files were selected.")
        return selected
    return [
        _ask(
            questionary.select(
                "Select a section params file:",
                choices=files,
            )
        )
    ]


def confirm_output_dir(default: str = "output") -> Path:
    path = _ask(
        questionary.text(
            "Output directory:",
            default=default,
        )
    )
    return Path(path)


def confirm_execution() -> None:
    """在交互预览后取得执行授权；否定只取消当前操作。"""
    confirmed = _ask(
        questionary.confirm(
            "Start CATIA build now?",
            default=False,
        )
    )
    if not confirmed:
        raise PromptCancelled("Build was cancelled before CATIA started.")


def ask_config_value(key: str, current_value: str) -> str:
    return _ask(
        questionary.text(
            f"Set {key}:",
            default=current_value,
        )
    )


def select_main_action() -> str:
    """返回顶层菜单动作；未实现能力会被明确标记为规划项。"""
    return _ask(
        questionary.select(
            "AutoBlade:",
            choices=[
                questionary.Choice("Create one blade", value="create"),
                questionary.Choice("Run a batch", value="batch"),
                questionary.Choice("Sweep explicit combinations", value="sweep"),
                questionary.Choice("List inputs", value="list"),
                questionary.Choice("Manage configuration", value="config"),
                questionary.Choice("Exit", value="exit"),
            ],
        )
    )


def select_config_action() -> str:
    return _ask(
        questionary.select(
            "Configuration:",
            choices=[
                questionary.Choice("Show", value="show"),
                questionary.Choice("Set a value", value="set"),
                questionary.Choice("Reset to defaults", value="reset"),
                questionary.Choice("Back", value="back"),
            ],
        )
    )


def select_config_key(keys: list[str]) -> str:
    return _ask(questionary.select("Configuration key:", choices=keys))


def confirm_config_reset() -> bool:
    return _ask(
        questionary.confirm(
            "Reset configuration to defaults?",
            default=False,
        )
    )


def confirm_workspace_overwrite(paths: list[Path]) -> bool:
    """确认只覆盖初始化器明确列出的受管理模板文件。"""
    joined = ", ".join(str(path) for path in paths)
    return _ask(
        questionary.confirm(
            f"Replace these managed workspace files: {joined}?",
            default=False,
        )
    )
