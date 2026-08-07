from pathlib import Path

import pytest

from catia_autoblade.commands.batch import run_batch_command
from catia_autoblade.commands.create import run_create_command
from catia_autoblade.config.manager import ConfigManager
from catia_autoblade.utils.file_scanner import get_available_files
from catia_autoblade.utils.output_naming import build_output_name


def _write_config(config_dir: Path) -> ConfigManager:
    """创建一份路径与命名均偏离默认值的最小测试配置。"""
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"
    config_file.write_text(
        """version = "1.0.0"

[paths]
input_dir = "data"
output_dir = "artifacts"
airfoil_dir = "profiles"
section_params_dir = "sections"

[defaults]
author = "Ada"
output_name_template = "{author}_{airfoil}_{idx}"
""",
        encoding="utf-8",
    )
    return ConfigManager(config_file)


def _create_input_files(config_dir: Path) -> None:
    profiles = config_dir / "data" / "profiles"
    sections = config_dir / "data" / "sections"
    profiles.mkdir(parents=True)
    sections.mkdir(parents=True)
    (profiles / "foil.csv").touch()
    (profiles / "ignored.txt").touch()
    (sections / "section_params-7.csv").touch()


def test_runtime_paths_are_resolved_from_config_location(tmp_path: Path) -> None:
    config_dir = tmp_path / "project"
    manager = _write_config(config_dir)

    runtime = manager.load_runtime()

    assert runtime.paths.input_dir == (config_dir / "data").resolve()
    assert runtime.paths.output_dir == (config_dir / "artifacts").resolve()
    assert runtime.paths.airfoil_dir == (config_dir / "data" / "profiles").resolve()
    assert runtime.paths.section_params_dir == (
        config_dir / "data" / "sections"
    ).resolve()


def test_cli_path_is_resolved_from_process_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    working_dir = tmp_path / "caller"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)

    assert ConfigManager.resolve_cli_path("custom-output") == (
        working_dir / "custom-output"
    ).resolve()


def test_scanner_uses_configured_input_directories(tmp_path: Path) -> None:
    config_dir = tmp_path / "project"
    manager = _write_config(config_dir)
    _create_input_files(config_dir)

    airfoils, sections = get_available_files(config_manager=manager)

    assert airfoils == ["foil.csv"]
    assert sections == ["section_params-7.csv"]


def test_output_name_uses_configured_template_fields() -> None:
    assert build_output_name(
        "{author}_{airfoil}_{idx}_{section}",
        "foil.csv",
        "section_params-7.csv",
        author="Ada",
    ) == "Ada_foil_7_section_params-7"


def test_output_name_rejects_unknown_template_field() -> None:
    with pytest.raises(ValueError, match="Unsupported output name field"):
        build_output_name("{unknown}", "foil.csv", "section_params-7.csv")


def test_create_command_cli_output_overrides_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_dir = tmp_path / "project"
    manager = _write_config(config_dir)
    _create_input_files(config_dir)
    working_dir = tmp_path / "caller"
    working_dir.mkdir()
    monkeypatch.chdir(working_dir)
    calls = []

    def fake_create(*args, **kwargs):
        calls.append((args, kwargs))

    run_create_command(
        "foil.csv",
        "section_params-7.csv",
        "cli-output",
        False,
        True,
        config_manager=manager,
        blade_creator=fake_create,
    )

    args, kwargs = calls[0]
    assert args == (
        "foil.csv",
        "section_params-7.csv",
        (working_dir / "cli-output").resolve(),
        "Ada_foil_7",
    )
    assert kwargs["airfoil_dir"] == (config_dir / "data" / "profiles").resolve()
    assert kwargs["section_params_dir"] == (
        config_dir / "data" / "sections"
    ).resolve()
    assert kwargs["keep_failed_part"] is True


def test_batch_command_uses_configured_output_and_template(tmp_path: Path) -> None:
    config_dir = tmp_path / "project"
    manager = _write_config(config_dir)
    _create_input_files(config_dir)
    calls = []

    def fake_batch(*args, **kwargs):
        calls.append((args, kwargs))
        return [{"status": "success"}]

    run_batch_command(
        "foil.csv",
        "section_params-7.csv",
        None,
        False,
        False,
        config_manager=manager,
        batch_processor=fake_batch,
    )

    args, kwargs = calls[0]
    assert args == (
        ["foil.csv"],
        ["section_params-7.csv"],
        (config_dir / "artifacts").resolve(),
    )
    assert kwargs["output_name_template"] == "{author}_{airfoil}_{idx}"
    assert kwargs["author"] == "Ada"


def test_batch_core_applies_template_to_each_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from catia_autoblade.core import batch as batch_module

    calls = []

    def fake_create(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(batch_module, "create_single_blade", fake_create)
    batch_module.batch_create_blades(
        ["foil.csv"],
        ["section_params-7.csv"],
        tmp_path / "artifacts",
        airfoil_dir=tmp_path / "profiles",
        section_params_dir=tmp_path / "sections",
        output_name_template="{author}_{airfoil}_{idx}",
        author="Ada",
    )

    args, kwargs = calls[0]
    assert args[3] == "Ada_foil_7"
    assert kwargs == {
        "airfoil_dir": tmp_path / "profiles",
        "section_params_dir": tmp_path / "sections",
    }
