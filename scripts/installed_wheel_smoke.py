"""在全新非 editable 环境中验证 wheel 的配置、输入和 mock 执行链。"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    args = parser.parse_args()

    import catia_autoblade
    from catia_autoblade.commands.create import run_create_command
    from catia_autoblade.config.manager import ConfigManager
    from catia_autoblade.utils.file_scanner import get_available_files

    package_file = Path(catia_autoblade.__file__).resolve()
    source_tree = (args.repository_root / "src").resolve()
    if package_file == source_tree or source_tree in package_file.parents:
        raise RuntimeError(
            f"Smoke test imported the repository source tree: {package_file}"
        )

    config_file = (args.workspace / "config.toml").resolve()
    manager = ConfigManager(config_file)
    runtime = manager.load_runtime()
    airfoils, sections = get_available_files(config_manager=manager)
    expected_airfoils = [
        "airfoil1_sharp.csv",
        "airfoil2_sharp.csv",
        "airfoil3_sharp.csv",
    ]
    expected_section = "example-section-params.csv"
    if airfoils != expected_airfoils or sections != [expected_section]:
        raise RuntimeError(
            f"Initialized examples were not discovered: {airfoils}, {sections}"
        )

    calls = []
    result = run_create_command(
        None,
        expected_section,
        None,
        False,
        config_manager=manager,
        blade_creator=lambda *call_args, **call_kwargs: calls.append(
            (call_args, call_kwargs)
        ),
    )
    if result.status != "success" or len(calls) != 1:
        raise RuntimeError("Installed wheel mock modeling path did not complete.")
    if runtime.paths.output_dir != (args.workspace / "output").resolve():
        raise RuntimeError("Installed workspace output path resolved incorrectly.")

    print(f"Installed package: {package_file}")
    print(f"Initialized workspace: {args.workspace.resolve()}")
    print("Input preflight and mock modeling path: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
