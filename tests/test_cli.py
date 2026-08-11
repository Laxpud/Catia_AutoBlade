import typer
import pytest
from click import unstyle
from typer.testing import CliRunner

from catia_autoblade import cli
from catia_autoblade.commands import batch as batch_commands
from catia_autoblade.commands import config as config_commands
from catia_autoblade.commands import create as create_commands
from catia_autoblade.commands import list as list_commands
from catia_autoblade.config.manager import ConfigManager
from catia_autoblade.config.settings import AppConfig
from catia_autoblade.interactive import menu
from catia_autoblade.interactive.prompts import PromptCancelled


runner = CliRunner()


def test_version_reports_package_version_without_opening_menu(monkeypatch) -> None:
    monkeypatch.setattr(cli, "is_interactive_terminal", lambda: True)
    called = []
    monkeypatch.setattr(menu, "run_main_menu", lambda: called.append(True))

    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0, result.output
    assert result.stdout.strip() == "catia-autoblade 0.1.1"
    assert called == []


def test_create_subcommand_parses_short_options(monkeypatch) -> None:
    calls = []

    def fake_run(airfoil, section, output, interactive, keep_failed_part):
        calls.append(
            (airfoil, section, output, interactive, keep_failed_part)
        )

    monkeypatch.setattr(create_commands, "run_create_command", fake_run)
    result = runner.invoke(
        cli.app,
        [
            "create",
            "-a",
            "foil.csv",
            "-s",
            "sections.csv",
            "-o",
            "generated",
            "-i",
            "--keep-failed-part",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        ("foil.csv", "sections.csv", "generated", True, True)
    ]


def test_batch_subcommand_parses_all_options(monkeypatch) -> None:
    calls = []

    def fake_run(airfoil, section, output, list_files, interactive):
        calls.append((airfoil, section, output, list_files, interactive))

    monkeypatch.setattr(batch_commands, "run_batch_command", fake_run)
    result = runner.invoke(
        cli.app,
        [
            "batch",
            "--airfoil",
            "foil.csv",
            "--section",
            "sections.csv",
            "--output",
            "generated",
            "--list",
            "--interactive",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        ("foil.csv", "sections.csv", "generated", True, True)
    ]


def test_list_subcommand_parses_config_flag(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(list_commands, "run_list_command", calls.append)

    result = runner.invoke(cli.app, ["list", "--config"])

    assert result.exit_code == 0, result.output
    assert calls == [True]


def test_config_subcommand_parses_action_key_and_value(monkeypatch) -> None:
    calls = []

    def fake_run(action, key, value):
        calls.append((action, key, value))

    monkeypatch.setattr(config_commands, "run_config_command", fake_run)
    result = runner.invoke(
        cli.app,
        ["config", "set", "--key", "output_dir", "--value", "generated"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [("set", "output_dir", "generated")]


def test_invalid_config_action_is_rejected_before_handler(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(config_commands, "run_config_command", calls.append)

    result = runner.invoke(cli.app, ["config", "invalid"])

    assert result.exit_code == 2
    assert "action must be one of" in result.output
    assert calls == []


def test_standalone_create_signature_matches_main_callback(monkeypatch) -> None:
    callbacks = []
    monkeypatch.setattr(cli.typer, "run", callbacks.append)

    cli.create_entrypoint()

    assert callbacks == [cli.create]


def test_standalone_batch_signature_matches_main_callback(monkeypatch) -> None:
    callbacks = []
    monkeypatch.setattr(cli.typer, "run", callbacks.append)

    cli.batch_entrypoint()

    assert callbacks == [cli.batch]


def test_standalone_callback_parses_same_create_options(monkeypatch) -> None:
    calls = []

    def fake_run(airfoil, section, output, interactive, keep_failed_part):
        calls.append(
            (airfoil, section, output, interactive, keep_failed_part)
        )

    monkeypatch.setattr(create_commands, "run_create_command", fake_run)
    standalone_app = typer.Typer()
    standalone_app.command()(cli.create)

    result = runner.invoke(
        standalone_app,
        ["--airfoil", "foil.csv", "--section", "sections.csv"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [("foil.csv", "sections.csv", None, False, False)]


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (FileNotFoundError("missing input"), "missing input"),
        (ValueError("invalid config"), "invalid config"),
        (RuntimeError("CATIA modeling failed"), "CATIA modeling failed"),
    ],
)
def test_domain_and_execution_errors_exit_one_on_stderr(
    error: Exception,
    message: str,
    monkeypatch,
) -> None:
    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(create_commands, "run_create_command", fail)

    result = runner.invoke(
        cli.app,
        ["create", "--section", "sections.csv"],
    )

    assert result.exit_code == 1
    assert message in result.stderr
    assert "[ERROR]" in result.stderr


def test_typer_usage_error_exits_two() -> None:
    result = runner.invoke(cli.app, ["create", "--unknown-option"])

    assert result.exit_code == 2
    assert "No such option" in result.output


def test_config_set_missing_value_is_usage_error() -> None:
    result = runner.invoke(
        cli.app,
        ["config", "set", "--key", "output_dir"],
    )

    assert result.exit_code == 2
    assert "requires both --key and --value" in unstyle(result.output)


def test_missing_repository_file_exits_one_on_stderr(
    tmp_path,
    monkeypatch,
) -> None:
    config = AppConfig()
    config.paths.input_dir = tmp_path / "input"
    config.paths.output_dir = tmp_path / "output"
    config.paths.airfoil_dir = tmp_path / "input" / "airfoils"
    config.paths.section_params_dir = tmp_path / "input" / "sections"
    config.paths.airfoil_dir.mkdir(parents=True)
    config.paths.section_params_dir.mkdir(parents=True)
    manager = ConfigManager(tmp_path / "config.toml")
    manager.save(config)
    monkeypatch.setattr(create_commands, "ConfigManager", lambda: manager)

    result = runner.invoke(
        cli.app,
        [
            "create",
            "--airfoil",
            "missing.csv",
            "--section",
            "missing.csv",
        ],
    )

    assert result.exit_code == 1
    assert "No section parameter files were found" in result.stderr


def test_invalid_toml_config_exits_one_on_stderr(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("version = [", encoding="utf-8")
    manager = ConfigManager(config_file)
    monkeypatch.setattr(create_commands, "ConfigManager", lambda: manager)

    result = runner.invoke(
        cli.app,
        ["create", "--section", "sections.csv"],
    )

    assert result.exit_code == 1
    assert "[ERROR]" in result.stderr


def test_keyboard_interrupt_exits_130(monkeypatch) -> None:
    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(create_commands, "run_create_command", interrupt)

    result = runner.invoke(
        cli.app,
        ["create", "--section", "sections.csv"],
    )

    assert result.exit_code == 130
    assert "Interrupted by user" in result.stderr


def test_interactive_cancel_is_a_successful_command_cancel(monkeypatch) -> None:
    def cancel(*args, **kwargs):
        raise PromptCancelled("Build was cancelled before CATIA started.")

    monkeypatch.setattr(create_commands, "run_create_command", cancel)

    result = runner.invoke(cli.app, ["create", "--interactive"])

    assert result.exit_code == 0
    assert "cancelled before CATIA started" in result.stdout


def test_no_argument_non_tty_shows_help_and_exits_two(monkeypatch) -> None:
    monkeypatch.setattr(cli, "is_interactive_terminal", lambda: False)
    called = []
    monkeypatch.setattr(menu, "run_main_menu", lambda: called.append(True))

    result = runner.invoke(cli.app, [])

    assert result.exit_code == 2
    assert "Usage:" in result.output
    assert called == []


def test_no_argument_tty_opens_menu_and_exits_zero(monkeypatch) -> None:
    monkeypatch.setattr(cli, "is_interactive_terminal", lambda: True)
    called = []
    monkeypatch.setattr(menu, "run_main_menu", lambda: called.append(True))

    result = runner.invoke(cli.app, [])

    assert result.exit_code == 0, result.output
    assert called == [True]


def test_main_menu_returns_after_action_until_exit(monkeypatch) -> None:
    actions = iter(["create", "exit"])
    calls = []
    monkeypatch.setattr(
        "catia_autoblade.interactive.prompts.select_main_action",
        lambda: next(actions),
    )
    monkeypatch.setattr(menu, "_run_menu_action", calls.append)

    menu.run_main_menu()

    assert calls == ["create"]


def test_main_menu_cancel_returns_to_parent_menu(monkeypatch) -> None:
    actions = iter(["create", "list", "exit"])
    calls = []
    monkeypatch.setattr(
        "catia_autoblade.interactive.prompts.select_main_action",
        lambda: next(actions),
    )

    def run_action(action):
        calls.append(action)
        if action == "create":
            raise PromptCancelled("Current operation cancelled.")

    monkeypatch.setattr(menu, "_run_menu_action", run_action)

    menu.run_main_menu()

    assert calls == ["create", "list"]
