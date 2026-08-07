from pathlib import Path

from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files
from ..utils.output_naming import build_output_name
from .create_blade import create_single_blade
from .input_plan import inspect_section_mode


def plan_batch_jobs(
    airfoil_files,
    section_params_files,
    *,
    section_params_dir,
):
    """按截面文件模式展开实际任务，避免多翼型文件参与笛卡尔积。"""
    jobs = []
    for section_file in section_params_files:
        mode = inspect_section_mode(Path(section_params_dir) / section_file)
        if mode == "multi":
            jobs.append((None, section_file, mode))
        else:
            jobs.extend(
                (airfoil_file, section_file, mode)
                for airfoil_file in airfoil_files
            )
    return jobs


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

    jobs = plan_batch_jobs(
        airfoil_files,
        section_params_files,
        section_params_dir=section_params_dir,
    )
    print(
        f"[INFO] Batch processing: {len(jobs)} planned blade task(s) "
        f"from {len(section_params_files)} section parameter file(s)"
    )

    results = []
    for airfoil_file, section_file, mode in jobs:
        try:
            print(f"\n{'='*60}")
            airfoil_label = airfoil_file or "per-section references"
            print(
                f"[INFO] Creating blade: airfoil={airfoil_label}, "
                f"section={section_file}"
            )
            if mode == "multi":
                output_subdir = Path(section_file).stem
            else:
                airfoil_name = Path(airfoil_file).stem
                output_subdir = airfoil_name
            output_name = build_output_name(
                output_name_template,
                airfoil_file,
                section_file,
                author=author,
                is_multi_airfoil=mode == "multi",
            )
            output_dir = Path(output_base_dir) / output_subdir
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
                "mode": mode,
                "airfoil": airfoil_file,
                "section": section_file,
                "output": str(output_dir),
            })
            print(f"[SUCCESS] Blade created: {output_name}")
        except Exception as e:
            results.append({
                "status": "failed",
                "mode": mode,
                "airfoil": airfoil_file,
                "section": section_file,
                "error": str(e),
            })
            print(f"[ERROR] Failed to create blade: {e}")

    print(f"\n{'='*60}")
    print(f"[INFO] Batch processing completed. {len([r for r in results if r['status'] == 'success'])}/{len(results)} successful.")
    return results
