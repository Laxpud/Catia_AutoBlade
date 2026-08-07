from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files
from ..utils.output_naming import build_output_name


def run_create_command(
    airfoil: str | None,
    section: str | None,
    output: str | None,
    interactive: bool,
    keep_failed_part: bool = False,
    *,
    config_manager: ConfigManager | None = None,
    blade_creator=None,
):
    manager = config_manager or ConfigManager()
    config = manager.load_runtime()
    airfoil_files, section_params_files = get_available_files(
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
    )
    configured_output_dir = config.paths.output_dir

    if interactive:
        from ..interactive.prompts import (
            confirm_output_dir,
            select_airfoil,
            select_sections,
        )

        if not section_params_files:
            print("[ERROR] No section params files found.")
            return

        selected_section = select_sections(section_params_files, multi=False)[0]
        output_default = (
            manager.resolve_cli_path(output) if output else configured_output_dir
        )
        output_dir = manager.resolve_cli_path(
            confirm_output_dir(str(output_default))
        )
    else:
        if not section_params_files:
            print("[ERROR] No section params files found.")
            return

        selected_section = section if section else section_params_files[0]
        output_dir = (
            manager.resolve_cli_path(output) if output else configured_output_dir
        )

    if selected_section not in section_params_files:
        print(f"[ERROR] Section params file '{selected_section}' not found.")
        return

    try:
        from ..core.input_plan import inspect_section_mode

        section_mode = inspect_section_mode(
            config.paths.section_params_dir / selected_section
        )
    except Exception as error:
        print(f"[ERROR] Invalid section params file: {error}")
        return

    if section_mode == "multi":
        if airfoil is not None:
            print(
                "[ERROR] --airfoil cannot be used when the section file "
                "contains an airfoil column."
            )
            return
        selected_airfoil = None
    else:
        if not airfoil_files:
            print("[ERROR] No airfoil files found.")
            return
        selected_airfoil = (
            select_airfoil(airfoil_files)
            if interactive
            else (airfoil if airfoil else airfoil_files[0])
        )
        if selected_airfoil not in airfoil_files:
            print(f"[ERROR] Airfoil file '{selected_airfoil}' not found.")
            return

    print("\n[INFO] Creating single blade...")
    airfoil_label = selected_airfoil or "per-section references"
    print(f"[INFO] Airfoil: {airfoil_label}, Section: {selected_section}")

    try:
        output_name = build_output_name(
            config.defaults.output_name_template,
            selected_airfoil,
            selected_section,
            author=config.defaults.author,
            is_multi_airfoil=section_mode == "multi",
        )
    except Exception as error:
        print(f"[ERROR] Invalid output naming configuration: {error}")
        return

    try:
        if blade_creator is None:
            from ..core.create_blade import create_single_blade

            blade_creator = create_single_blade
        blade_creator(
            selected_airfoil,
            selected_section,
            output_dir,
            output_name,
            airfoil_dir=config.paths.airfoil_dir,
            section_params_dir=config.paths.section_params_dir,
            keep_failed_part=keep_failed_part,
        )
        print(f"[SUCCESS] Blade created: {output_name}")
    except Exception as e:
        print(f"[ERROR] Failed to create blade: {e}")
