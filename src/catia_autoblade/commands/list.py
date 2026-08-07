from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files


def run_list_command(
    config_show: bool,
    *,
    config_manager: ConfigManager | None = None,
):
    manager = config_manager or ConfigManager()
    if config_show:
        config = manager.load()
        print("[INFO] Current configuration:")
        print(f"  input_dir: {config.paths.input_dir}")
        print(f"  output_dir: {config.paths.output_dir}")
        print(f"  airfoil_dir: {config.paths.airfoil_dir}")
        print(f"  section_params_dir: {config.paths.section_params_dir}")
        print(f"  author: {config.defaults.author}")
        print(f"  output_name_template: {config.defaults.output_name_template}")
    else:
        config = manager.load_runtime()
        airfoil_files, section_params_files = get_available_files(
            airfoil_dir=config.paths.airfoil_dir,
            section_params_dir=config.paths.section_params_dir,
        )
        print("[INFO] Available airfoil files:")
        for f in airfoil_files:
            print(f"  - {f}")
        print("\n[INFO] Available section params files:")
        for f in section_params_files:
            print(f"  - {f}")
        try:
            from ..core.batch import plan_batch_jobs

            jobs = plan_batch_jobs(
                airfoil_files,
                section_params_files,
                section_params_dir=config.paths.section_params_dir,
            )
        except Exception as error:
            print(f"\n[ERROR] Cannot plan blade tasks: {error}")
            return
        print(f"\n[INFO] Planned blade tasks: {len(jobs)}")
