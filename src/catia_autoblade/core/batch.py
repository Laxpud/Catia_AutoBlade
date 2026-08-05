from pathlib import Path

from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files
from ..utils.output_naming import build_output_name
from .create_blade import create_single_blade


def batch_create_blades(
    airfoil_files=None,
    section_params_files=None,
    output_base_dir=None,
    *,
    airfoil_dir=None,
    section_params_dir=None,
    output_name_template=None,
    author=None,
):
    """按配置目录和命名模板批量生成翼型/截面参数组合。"""
    runtime_config = None
    if (
        airfoil_dir is None
        or section_params_dir is None
        or output_base_dir is None
        or output_name_template is None
        or author is None
    ):
        runtime_config = ConfigManager().load_runtime()

    if airfoil_dir is None:
        airfoil_dir = runtime_config.paths.airfoil_dir
    if section_params_dir is None:
        section_params_dir = runtime_config.paths.section_params_dir
    if output_base_dir is None:
        output_base_dir = runtime_config.paths.output_dir
    if output_name_template is None:
        output_name_template = runtime_config.defaults.output_name_template
    if author is None:
        author = runtime_config.defaults.author

    if airfoil_files is None:
        airfoil_files, _ = get_available_files(
            airfoil_dir=airfoil_dir,
            section_params_dir=section_params_dir,
        )
    if section_params_files is None:
        _, section_params_files = get_available_files(
            airfoil_dir=airfoil_dir,
            section_params_dir=section_params_dir,
        )

    airfoil_files = [f for f in airfoil_files if Path(f).suffix.lower() == ".csv"]

    print(f"[INFO] Batch processing: {len(airfoil_files)} airfoil(s) x {len(section_params_files)} section param(s) = {len(airfoil_files) * len(section_params_files)} blade(s)")

    results = []
    for airfoil_file in airfoil_files:
        for section_file in section_params_files:
            try:
                print(f"\n{'='*60}")
                print(f"[INFO] Creating blade: airfoil={airfoil_file}, section={section_file}")
                airfoil_name = Path(airfoil_file).stem
                output_name = build_output_name(
                    output_name_template,
                    airfoil_file,
                    section_file,
                    author=author,
                )
                output_dir = Path(output_base_dir) / airfoil_name
                create_single_blade(
                    airfoil_file,
                    section_file,
                    output_dir,
                    output_name,
                    airfoil_dir=airfoil_dir,
                    section_params_dir=section_params_dir,
                )
                results.append({
                    "status": "success",
                    "airfoil": airfoil_file,
                    "section": section_file,
                    "output": str(output_dir),
                })
                print(f"[SUCCESS] Blade created: {output_name}")
            except Exception as e:
                results.append({"status": "failed", "airfoil": airfoil_file, "section": section_file, "error": str(e)})
                print(f"[ERROR] Failed to create blade: {e}")

    print(f"\n{'='*60}")
    print(f"[INFO] Batch processing completed. {len([r for r in results if r['status'] == 'success'])}/{len(results)} successful.")
    return results
