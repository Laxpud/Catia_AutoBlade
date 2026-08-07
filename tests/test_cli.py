import typer
from typer.testing import CliRunner

from catia_autoblade import cli
from catia_autoblade.commands import batch as batch_commands
from catia_autoblade.commands import config as config_commands
from catia_autoblade.commands import create as create_commands
from catia_autoblade.commands import list as list_commands


runner = CliRunner()


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

    assert result.exit_code != 0
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
