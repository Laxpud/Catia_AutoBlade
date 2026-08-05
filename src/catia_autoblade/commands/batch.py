from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files


def run_batch_command(
    airfoil: str | None,
    section: str | None,
    output: str | None,
    list_files: bool,
    interactive: bool,
    *,
    config_manager: ConfigManager | None = None,
    batch_processor=None,
):
    manager = config_manager or ConfigManager()
    config = manager.load_runtime()
    airfoil_files, section_params_files = get_available_files(
        airfoil_dir=config.paths.airfoil_dir,
        section_params_dir=config.paths.section_params_dir,
    )

    if list_files:
        print("[INFO] Available airfoil files:")
        for f in airfoil_files:
            print(f"  - {f}")
        print("\n[INFO] Available section params files:")
        for f in section_params_files:
            print(f"  - {f}")
        print(f"\n[INFO] Total combinations: {len(airfoil_files)} x {len(section_params_files)} = {len(airfoil_files) * len(section_params_files)}")
        return

    if interactive:
        from ..interactive.prompts import (
            confirm_output_dir,
            select_airfoil,
            select_sections,
        )

        if not airfoil_files:
            print("[ERROR] No airfoil files found.")
            return

        if not section_params_files:
            print("[ERROR] No section params files found.")
            return

        selected_airfoil = select_airfoil(airfoil_files)
        selected_sections = select_sections(section_params_files, multi=True)
        output_default = (
            manager.resolve_cli_path(output) if output else config.paths.output_dir
        )
        output_dir = manager.resolve_cli_path(
            confirm_output_dir(str(output_default))
        )

        airfoil_list = [selected_airfoil] if selected_airfoil in airfoil_files else []
        section_list = [s for s in selected_sections if s in section_params_files]
    else:
        output_dir = (
            manager.resolve_cli_path(output) if output else config.paths.output_dir
        )

        if airfoil:
            airfoil_list = [airfoil] if airfoil in airfoil_files else []
            if not airfoil_list:
                print(f"[ERROR] Airfoil file '{airfoil}' not found.")
                return
        else:
            airfoil_list = airfoil_files

        if section:
            section_list = [section] if section in section_params_files else []
            if not section_list:
                print(f"[ERROR] Section params file '{section}' not found.")
                return
        else:
            section_list = section_params_files

    print(f"[INFO] Batch processing: {len(airfoil_list)} airfoil(s) x {len(section_list)} section param(s) = {len(airfoil_list) * len(section_list)} blade(s)")

    try:
        if batch_processor is None:
            from ..core.batch import batch_create_blades

            batch_processor = batch_create_blades
        results = batch_processor(
            airfoil_list,
            section_list,
            output_dir,
            airfoil_dir=config.paths.airfoil_dir,
            section_params_dir=config.paths.section_params_dir,
            output_name_template=config.defaults.output_name_template,
            author=config.defaults.author,
        )
        success_count = len([r for r in results if r["status"] == "success"])
        print(f"\n[INFO] Batch completed: {success_count}/{len(results)} successful.")
    except Exception as e:
        print(f"[ERROR] Batch processing failed: {e}")
