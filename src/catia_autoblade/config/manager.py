from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import shutil
from typing import Any, ClassVar, Mapping
from uuid import uuid4
import warnings

from pydantic import ValidationError
import tomlkit

from .settings import AppConfig, CURRENT_CONFIG_SCHEMA_VERSION


LEGACY_CONFIG_SCHEMA_VERSION = "1.0.0"


class ConfigCompatibilityError(ValueError):
    """配置 schema 无法由当前程序安全解释。"""


class ConfigMigrationRequiredError(ConfigCompatibilityError):
    """写操作被旧 schema 阻止，必须先显式迁移。"""


class ConfigMigrationWarning(UserWarning):
    """配置可读取，但存在应由用户显式应用的迁移。"""


@dataclass(frozen=True)
class ConfigMigrationChange:
    """单项迁移变化；字段值保持可展示，不包含输入或输出文件内容。"""

    field: str
    before: str
    after: str
    reason: str


@dataclass(frozen=True)
class ConfigMigrationPlan:
    """经过验证、可在原文件未变化时安全应用的迁移计划。"""

    config_file: Path
    source_version: str
    target_version: str
    changes: tuple[ConfigMigrationChange, ...]
    original_sha256: str
    migrated_text: str


@dataclass(frozen=True)
class ConfigSource:
    """配置发现结果；内置默认值仍记录其路径解析基准。"""

    kind: str
    path: Path


class ConfigManager:
    """发现、校验和加载配置，并安全处理持久化 schema。"""

    CONFIG_FILE = Path("config.toml")
    USER_CONFIG_DIR = "catia-autoblade"
    CURRENT_SCHEMA_VERSION = CURRENT_CONFIG_SCHEMA_VERSION
    LEGACY_SCHEMA_VERSIONS = frozenset({LEGACY_CONFIG_SCHEMA_VERSION, "unversioned"})
    # 只有真实移除字段时才向此表增加条目。迁移器会在通用 unknown-field
    # 错误之前给出替代字段，避免维护者为了假设场景预建迁移类层次。
    DEPRECATED_FIELDS: ClassVar[Mapping[str, str]] = {}

    def __init__(
        self,
        config_file: str | Path | None = None,
        *,
        source_kind: str | None = None,
    ) -> None:
        if config_file is None:
            discovered = self.discover()
            self.config_file = discovered.config_file
            self.source = discovered.source
            return

        # 相对配置文件名以创建管理器时的工作目录为基准；先固化为绝对路径，
        # 后续即使交互流程改变工作目录，配置解析基准也不会漂移。
        self.config_file = Path(config_file).expanduser().resolve()
        self.source = ConfigSource(source_kind or "explicit", self.config_file)

    @classmethod
    def discover(
        cls,
        explicit_config: str | Path | None = None,
        *,
        working_dir: str | Path | None = None,
        user_config_file: str | Path | None = None,
    ) -> ConfigManager:
        """按显式路径、当前工作区、用户级配置、内置默认值依次发现。"""
        base_dir = Path(working_dir or Path.cwd()).expanduser().resolve()
        if explicit_config is not None:
            candidate = Path(explicit_config).expanduser()
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            return cls(candidate.resolve(), source_kind="explicit")

        workspace_config = (base_dir / cls.CONFIG_FILE).resolve()
        if workspace_config.is_file():
            return cls(workspace_config, source_kind="workspace")

        user_config = Path(
            user_config_file or cls.default_user_config_file()
        ).expanduser().resolve()
        if user_config.is_file():
            return cls(user_config, source_kind="user")

        # 内置默认路径以启动目录为基准，但不会在那里创建 config.toml；只有
        # init、config set/reset/migrate 等显式写命令能够持久化用户文件。
        return cls(workspace_config, source_kind="defaults")

    @classmethod
    def default_user_config_file(cls) -> Path:
        """返回平台惯例下的用户级配置路径，不创建任何目录。"""
        if os.name == "nt":
            base_dir = Path(
                os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            )
        else:
            base_dir = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            )
        return base_dir / cls.USER_CONFIG_DIR / cls.CONFIG_FILE

    @property
    def source_description(self) -> str:
        if self.source.kind == "defaults":
            return f"built-in defaults (base: {self.config_file.parent})"
        return f"{self.source.kind}: {self.config_file}"

    def load(self) -> AppConfig:
        """读取配置；旧 schema 仅在内存迁移并提示，不修改用户文件。"""
        if not self.config_file.exists():
            return AppConfig()

        document, raw_bytes = self._read_document()
        plan = self._plan_document_migration(document, raw_bytes)
        if plan is not None:
            warnings.warn(
                f"Configuration schema {plan.source_version} is readable but "
                f"should be migrated to {plan.target_version}; run "
                "'autoblade config migrate' to preview it.",
                ConfigMigrationWarning,
                stacklevel=2,
            )
            migrated = tomlkit.parse(plan.migrated_text)
            return self._validate_document(migrated)
        return self._validate_document(document)

    def load_runtime(self) -> AppConfig:
        """返回路径均已解析为绝对路径的运行时配置副本。"""
        config = self.load().model_copy(deep=True)
        config_base_dir = self.config_file.parent

        # 1. 输入、输出根目录相对 config.toml 所在目录解析。
        input_dir = self._resolve_path(config.paths.input_dir, config_base_dir)
        output_dir = self._resolve_path(config.paths.output_dir, config_base_dir)

        # 2. 专用输入目录的相对值以 input_dir 为基准；绝对值保持不变。
        airfoil_dir = self._resolve_path(config.paths.airfoil_dir, input_dir)
        section_params_dir = self._resolve_path(
            config.paths.section_params_dir,
            input_dir,
        )

        config.paths.input_dir = input_dir
        config.paths.output_dir = output_dir
        config.paths.airfoil_dir = airfoil_dir
        config.paths.section_params_dir = section_params_dir
        return config

    @staticmethod
    def _resolve_path(path: str | Path, base_dir: Path) -> Path:
        candidate = Path(path).expanduser()
        if candidate.is_absolute():
            return candidate.resolve()
        return (base_dir / candidate).resolve()

    @staticmethod
    def resolve_cli_path(path: str | Path) -> Path:
        """按命令行惯例，以当前工作目录解析用户显式传入的相对路径。"""
        return Path(path).expanduser().resolve()

    def save(self, config: AppConfig) -> None:
        """原子保存当前 schema；旧配置必须先显式迁移并生成备份。"""
        if self.config_file.exists():
            document, raw_bytes = self._read_document()
            if self._plan_document_migration(document, raw_bytes) is not None:
                raise ConfigMigrationRequiredError(
                    "Configuration uses an older schema. Run "
                    "'autoblade config migrate' before changing it."
                )
        data = config.model_dump(mode="json")
        data["version"] = self.CURRENT_SCHEMA_VERSION
        self._atomic_write_text(tomlkit.dumps(data))

    def update_paths(self, **kwargs) -> None:
        config = self.load()
        for key, value in kwargs.items():
            if value is not None:
                setattr(config.paths, key, Path(value))
        self.save(config)

    def plan_migration(self) -> ConfigMigrationPlan | None:
        """返回真实旧 schema 的迁移预览；当前 schema 返回 ``None``。"""
        if not self.config_file.is_file():
            raise FileNotFoundError(
                f"Configuration file does not exist: {self.config_file}"
            )
        document, raw_bytes = self._read_document()
        return self._plan_document_migration(document, raw_bytes)

    def apply_migration(self, plan: ConfigMigrationPlan) -> Path:
        """备份原文件并原子应用仍然有效的迁移计划。"""
        if plan.config_file != self.config_file:
            raise ConfigCompatibilityError(
                "Migration plan belongs to a different configuration file."
            )
        current_bytes = self.config_file.read_bytes()
        current_digest = hashlib.sha256(current_bytes).hexdigest()
        if current_digest != plan.original_sha256:
            raise ConfigCompatibilityError(
                "Configuration changed after the migration preview; preview it again."
            )

        backup = self._next_backup_path(plan.source_version)
        shutil.copy2(self.config_file, backup)
        try:
            self._atomic_write_text(plan.migrated_text)
        except Exception:
            # 原文件仍由原子替换保护；如果写入失败，保留备份用于人工恢复。
            raise
        return backup

    def _read_document(self) -> tuple[tomlkit.TOMLDocument, bytes]:
        raw_bytes = self.config_file.read_bytes()
        try:
            document = tomlkit.parse(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, tomlkit.exceptions.ParseError) as error:
            raise ConfigCompatibilityError(
                f"Invalid TOML configuration {self.config_file}: {error}"
            ) from error
        return document, raw_bytes

    def _plan_document_migration(
        self,
        document: tomlkit.TOMLDocument,
        raw_bytes: bytes,
    ) -> ConfigMigrationPlan | None:
        source_version = str(document.get("version", "unversioned"))
        if source_version == self.CURRENT_SCHEMA_VERSION:
            self._validate_document(document)
            return None

        if source_version not in self.LEGACY_SCHEMA_VERSIONS:
            self._raise_unsupported_version(source_version)

        migrated = tomlkit.parse(tomlkit.dumps(document))
        changes: list[ConfigMigrationChange] = []
        if source_version == "unversioned":
            changes.append(
                ConfigMigrationChange(
                    "version",
                    "<missing>",
                    self.CURRENT_SCHEMA_VERSION,
                    "Record the configuration schema explicitly.",
                )
            )
        else:
            changes.append(
                ConfigMigrationChange(
                    "version",
                    source_version,
                    self.CURRENT_SCHEMA_VERSION,
                    "Upgrade to the current path-resolution schema.",
                )
            )
        migrated["version"] = self.CURRENT_SCHEMA_VERSION

        # schema 1.0.0 曾把专用目录写成 input\\airfoils，同时运行时又以
        # input_dir 为基准拼接。只剥离与 input_dir 完全相同的前缀，绝对路径、
        # 自定义同级路径以及用户的输出命名模板都保持原样。
        paths = migrated.get("paths")
        if isinstance(paths, Mapping):
            input_dir = str(paths.get("input_dir", "input"))
            for field in ("airfoil_dir", "section_params_dir"):
                if field not in paths:
                    continue
                before = str(paths[field])
                after = self._strip_legacy_input_prefix(before, input_dir)
                if after != before:
                    paths[field] = after
                    changes.append(
                        ConfigMigrationChange(
                            f"paths.{field}",
                            before,
                            after,
                            "Keep the resolved directory stable under input_dir.",
                        )
                    )

        self._validate_document(migrated)
        return ConfigMigrationPlan(
            config_file=self.config_file,
            source_version=source_version,
            target_version=self.CURRENT_SCHEMA_VERSION,
            changes=tuple(changes),
            original_sha256=hashlib.sha256(raw_bytes).hexdigest(),
            migrated_text=tomlkit.dumps(migrated),
        )

    def _validate_document(self, document: Mapping[str, Any]) -> AppConfig:
        deprecated = [
            (field, replacement)
            for field, replacement in self.DEPRECATED_FIELDS.items()
            if self._contains_dotted_field(document, field)
        ]
        if deprecated:
            details = ", ".join(
                f"{field} (use {replacement})"
                for field, replacement in deprecated
            )
            raise ConfigCompatibilityError(
                f"Deprecated configuration field(s): {details}."
            )

        try:
            config = AppConfig.model_validate(document)
        except ValidationError as error:
            unknown_fields = [
                ".".join(str(part) for part in item["loc"])
                for item in error.errors()
                if item["type"] == "extra_forbidden"
            ]
            if unknown_fields:
                raise ConfigCompatibilityError(
                    "Unknown configuration field(s): "
                    f"{', '.join(sorted(unknown_fields))}. Refusing to ignore "
                    "them because a later save could lose user settings."
                ) from error
            raise ConfigCompatibilityError(
                f"Invalid configuration {self.config_file}: {error}"
            ) from error

        if config.version != self.CURRENT_SCHEMA_VERSION:
            raise ConfigCompatibilityError(
                f"Configuration validation produced unexpected schema "
                f"{config.version!r}."
            )
        return config

    def _raise_unsupported_version(self, source_version: str) -> None:
        current = self._parse_version(self.CURRENT_SCHEMA_VERSION)
        candidate = self._parse_version(source_version)
        if candidate is not None and current is not None and candidate > current:
            raise ConfigCompatibilityError(
                f"Configuration schema {source_version} is newer than supported "
                f"schema {self.CURRENT_SCHEMA_VERSION}; upgrade CATIA AutoBlade."
            )
        raise ConfigCompatibilityError(
            f"Unsupported configuration schema {source_version!r}; supported "
            f"legacy schemas: {sorted(self.LEGACY_SCHEMA_VERSIONS)}."
        )

    @staticmethod
    def _parse_version(value: str) -> tuple[int, int, int] | None:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
        if match is None:
            return None
        return tuple(int(part) for part in match.groups())

    @staticmethod
    def _strip_legacy_input_prefix(value: str, input_dir: str) -> str:
        candidate = value.replace("\\", "/")
        base = input_dir.replace("\\", "/")
        if Path(value).is_absolute() or Path(input_dir).is_absolute():
            return value
        candidate_parts = [part for part in candidate.split("/") if part not in ("", ".")]
        base_parts = [part for part in base.split("/") if part not in ("", ".")]
        if not base_parts or candidate_parts[: len(base_parts)] != base_parts:
            return value
        remaining = candidate_parts[len(base_parts) :]
        return str(Path(*remaining)) if remaining else value

    @staticmethod
    def _contains_dotted_field(document: Mapping[str, Any], field: str) -> bool:
        current: Any = document
        for part in field.split("."):
            if not isinstance(current, Mapping) or part not in current:
                return False
            current = current[part]
        return True

    def _next_backup_path(self, source_version: str) -> Path:
        safe_version = re.sub(r"[^0-9A-Za-z.-]+", "-", source_version)
        base = self.config_file.with_name(
            f"{self.config_file.name}.v{safe_version}.bak"
        )
        if not base.exists():
            return base
        index = 1
        while True:
            candidate = base.with_name(f"{base.name}.{index}")
            if not candidate.exists():
                return candidate
            index += 1

    def _atomic_write_text(self, content: str) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.config_file.with_name(
            f".{self.config_file.name}.{uuid4().hex}.tmp"
        )
        try:
            temporary.write_text(content, encoding="utf-8", newline="\n")
            os.replace(temporary, self.config_file)
        finally:
            if temporary.exists():
                temporary.unlink()
