from pathlib import Path

from ..config.manager import ConfigManager
from ..utils.file_scanner import get_available_files
from .create_blade import create_single_blade
from .executor import execute_jobs
from .input_plan import inspect_section_mode
from .planner import plan_batch_jobs


def batch_create_blades(
    airfoil_files=None,
    blade_sections_files=None,
    output_base_dir=None,
    *,
    airfoil_dir=None,
    blade_sections_dir=None,
    output_name_template=None,
    author=None,
):
    """执行多个闭合模型定义，并保留旧 Python 入口的字典结果格式。

    ``batch`` 最多把一个翼型绑定到任意数量的六列截面模板；多个翼型与
    多个模板的参数组合属于未来 ``sweep``，本入口不再根据目录内容生成
    笛卡尔积。
    """
    runtime_config = None
    if (
        airfoil_dir is None
        or blade_sections_dir is None
        or output_base_dir is None
        or output_name_template is None
        or author is None
    ):
        runtime_config = ConfigManager().load_runtime()

    if airfoil_dir is None:
        airfoil_dir = runtime_config.paths.airfoil_dir
    if blade_sections_dir is None:
        blade_sections_dir = runtime_config.paths.blade_sections_dir
    if output_base_dir is None:
        output_base_dir = runtime_config.paths.output_dir
    if output_name_template is None:
        output_name_template = runtime_config.defaults.output_name_template
    if author is None:
        author = runtime_config.defaults.author

    discovered_airfoils, discovered_sections = get_available_files(
        airfoil_dir=airfoil_dir,
        blade_sections_dir=blade_sections_dir,
    )
    if airfoil_files is None:
        airfoil_files = discovered_airfoils
    if blade_sections_files is None:
        blade_sections_files = discovered_sections

    blade_sections_files = list(blade_sections_files)
    modes = [
        inspect_section_mode(Path(blade_sections_dir) / section_filename)
        for section_filename in blade_sections_files
    ]
    has_single_sections = "single" in modes
    selected_airfoils = [
        filename
        for filename in airfoil_files
        if Path(filename).suffix.lower() == ".csv"
    ]
    if has_single_sections and len(selected_airfoils) != 1:
        raise ValueError(
            "batch requires exactly one airfoil for six-column section files; "
            "multiple-airfoil combinations belong to sweep"
        )
    selected_airfoil = selected_airfoils[0] if has_single_sections else None

    jobs = plan_batch_jobs(
        selected_airfoil,
        blade_sections_files,
        output_base_dir,
        airfoil_dir=airfoil_dir,
        blade_sections_dir=blade_sections_dir,
        output_name_template=output_name_template,
        author=author,
    )
    results = execute_jobs(jobs, blade_creator=create_single_blade)
    return [result.as_dict() for result in results]
