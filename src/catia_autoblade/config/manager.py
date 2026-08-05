from pathlib import Path

import tomlkit

from .settings import AppConfig


class ConfigManager:
    """加载配置，并把持久化路径转换为可直接使用的绝对路径。"""

    CONFIG_FILE = Path("config.toml")

    def __init__(self, config_file: str | Path = CONFIG_FILE) -> None:
        # 相对配置文件名以创建管理器时的工作目录为基准；先固化为绝对路径，
        # 后续即使交互流程改变工作目录，配置解析基准也不会漂移。
        self.config_file = Path(config_file).expanduser().resolve()

    def load(self) -> AppConfig:
        """读取原始配置值；缺少配置文件时返回内置默认配置。"""
        if not self.config_file.exists():
            return AppConfig()

        with self.config_file.open("r", encoding="utf-8") as f:
            data = tomlkit.load(f)
        return AppConfig.model_validate(data)

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
        """保存可移植的原始配置，不在持久化时改写相对路径。"""
        data = config.model_dump(mode="json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with self.config_file.open("w", encoding="utf-8") as f:
            tomlkit.dump(data, f)

    def update_paths(self, **kwargs) -> None:
        config = self.load()
        for key, value in kwargs.items():
            if value is not None:
                setattr(config.paths, key, Path(value))
        self.save(config)
