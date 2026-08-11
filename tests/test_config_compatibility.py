from pathlib import Path

import pytest

from catia_autoblade.config.manager import (
    ConfigCompatibilityError,
    ConfigManager,
    ConfigMigrationRequiredError,
    ConfigMigrationWarning,
)


CURRENT_CONFIG = """version = "2.0.0"

[paths]
input_dir = "input"
output_dir = "output"
airfoil_dir = "airfoils"
section_params_dir = "section_params"

[defaults]
author = "Ada"
output_name_template = "{blade}"
"""

LEGACY_CONFIG = r'''version = "1.0.0"

[paths]
input_dir = "input"
output_dir = "output"
airfoil_dir = 'input\airfoils'
section_params_dir = 'input\section_params'

[defaults]
author = "Ada"
output_name_template = "{airfoil}_blade-{idx}"
'''


def _write(path: Path, content: str = CURRENT_CONFIG) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_config_discovery_priority_is_explicit_workspace_user_defaults(
    tmp_path: Path,
) -> None:
    working_dir = tmp_path / "workspace"
    workspace = _write(working_dir / "config.toml")
    user = _write(tmp_path / "user" / "config.toml")
    explicit = _write(tmp_path / "explicit.toml")

    manager = ConfigManager.discover(
        explicit,
        working_dir=working_dir,
        user_config_file=user,
    )
    assert manager.source.kind == "explicit"
    assert manager.config_file == explicit.resolve()

    manager = ConfigManager.discover(
        working_dir=working_dir,
        user_config_file=user,
    )
    assert manager.source.kind == "workspace"
    assert manager.config_file == workspace.resolve()

    workspace.unlink()
    manager = ConfigManager.discover(
        working_dir=working_dir,
        user_config_file=user,
    )
    assert manager.source.kind == "user"
    assert manager.config_file == user.resolve()

    user.unlink()
    manager = ConfigManager.discover(
        working_dir=working_dir,
        user_config_file=user,
    )
    assert manager.source.kind == "defaults"
    assert manager.config_file == (working_dir / "config.toml").resolve()
    assert manager.load().version == "2.0.0"


def test_explicit_relative_config_is_anchored_to_invocation_directory(
    tmp_path: Path,
) -> None:
    working_dir = tmp_path / "caller"
    config_file = _write(working_dir / "configs" / "blade.toml")

    manager = ConfigManager.discover(
        Path("configs") / "blade.toml",
        working_dir=working_dir,
    )

    assert manager.config_file == config_file.resolve()


def test_legacy_config_is_read_without_writing_and_paths_stay_stable(
    tmp_path: Path,
) -> None:
    config_file = _write(tmp_path / "config.toml", LEGACY_CONFIG)
    original = config_file.read_bytes()
    manager = ConfigManager(config_file)

    with pytest.warns(ConfigMigrationWarning):
        runtime = manager.load_runtime()

    assert runtime.paths.airfoil_dir == (tmp_path / "input" / "airfoils").resolve()
    assert runtime.paths.section_params_dir == (
        tmp_path / "input" / "section_params"
    ).resolve()
    assert runtime.defaults.output_name_template == "{airfoil}_blade-{idx}"
    assert config_file.read_bytes() == original


def test_legacy_config_migration_previews_backs_up_and_preserves_values(
    tmp_path: Path,
) -> None:
    config_file = _write(tmp_path / "config.toml", LEGACY_CONFIG)
    manager = ConfigManager(config_file)
    plan = manager.plan_migration()

    assert plan is not None
    assert plan.source_version == "1.0.0"
    assert [change.field for change in plan.changes] == [
        "version",
        "paths.airfoil_dir",
        "paths.section_params_dir",
    ]

    backup = manager.apply_migration(plan)

    assert backup.read_text(encoding="utf-8") == LEGACY_CONFIG
    migrated_text = config_file.read_text(encoding="utf-8")
    assert 'version = "2.0.0"' in migrated_text
    assert 'airfoil_dir = "airfoils"' in migrated_text
    assert 'section_params_dir = "section_params"' in migrated_text
    assert 'output_name_template = "{airfoil}_blade-{idx}"' in migrated_text
    assert manager.plan_migration() is None


def test_legacy_config_cannot_be_silently_saved(tmp_path: Path) -> None:
    config_file = _write(tmp_path / "config.toml", LEGACY_CONFIG)
    manager = ConfigManager(config_file)
    with pytest.warns(ConfigMigrationWarning):
        config = manager.load()

    with pytest.raises(ConfigMigrationRequiredError, match="config migrate"):
        manager.save(config)


def test_migration_rejects_file_changed_after_preview(tmp_path: Path) -> None:
    config_file = _write(tmp_path / "config.toml", LEGACY_CONFIG)
    manager = ConfigManager(config_file)
    plan = manager.plan_migration()
    assert plan is not None
    config_file.write_text(LEGACY_CONFIG + "\n# changed\n", encoding="utf-8")

    with pytest.raises(ConfigCompatibilityError, match="changed after"):
        manager.apply_migration(plan)


def test_future_and_unknown_schema_content_fail_safely(tmp_path: Path) -> None:
    future = _write(
        tmp_path / "future.toml",
        CURRENT_CONFIG.replace('version = "2.0.0"', 'version = "3.0.0"'),
    )
    with pytest.raises(ConfigCompatibilityError, match="newer than supported"):
        ConfigManager(future).load()

    unknown = _write(
        tmp_path / "unknown.toml",
        CURRENT_CONFIG + "\ncustomer_secret = \"keep-me\"\n",
    )
    original = unknown.read_bytes()
    with pytest.raises(ConfigCompatibilityError, match="Unknown configuration"):
        ConfigManager(unknown).load()
    assert unknown.read_bytes() == original


def test_deprecated_field_registry_reports_replacement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_file = _write(
        tmp_path / "deprecated.toml",
        CURRENT_CONFIG.replace(
            'author = "Ada"',
            'author = "Ada"\nlegacy_author = "Ada"',
        ),
    )
    monkeypatch.setattr(
        ConfigManager,
        "DEPRECATED_FIELDS",
        {"defaults.legacy_author": "defaults.author"},
    )

    with pytest.raises(ConfigCompatibilityError, match="use defaults.author"):
        ConfigManager(config_file).load()
