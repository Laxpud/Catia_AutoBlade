from pathlib import Path


def get_available_files(
    input_dir: str | Path | None = None,
    *,
    airfoil_dir: str | Path | None = None,
    blade_sections_dir: str | Path | None = None,
    config_manager=None,
) -> tuple[list[str], list[str]]:
    """扫描配置指定的两个输入目录并返回稳定排序的 CSV 文件名。

    ``input_dir`` 保留旧版父目录调用方式；新调用方应传入两个专用目录，
    或省略路径让 ``ConfigManager`` 提供运行时目录。
    """
    if input_dir is not None:
        input_path = Path(input_dir)
        airfoil_dir = airfoil_dir or input_path / "airfoils"
        blade_sections_dir = blade_sections_dir or input_path / "blade_sections"

    if airfoil_dir is None or blade_sections_dir is None:
        if config_manager is None:
            from ..config.manager import ConfigManager

            config_manager = ConfigManager()
        runtime_config = config_manager.load_runtime()
        airfoil_dir = airfoil_dir or runtime_config.paths.airfoil_dir
        blade_sections_dir = (
            blade_sections_dir or runtime_config.paths.blade_sections_dir
        )

    return _csv_filenames(Path(airfoil_dir)), _csv_filenames(
        Path(blade_sections_dir)
    )


def _csv_filenames(directory: Path) -> list[str]:
    if not directory.is_dir():
        return []
    return sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() == ".csv"
    )
