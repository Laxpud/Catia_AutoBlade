from collections.abc import Iterable

from .jobs import BladeBuildJob, BuildResult


def execute_job(job: BladeBuildJob, *, blade_creator=None) -> BuildResult:
    """执行一个已规划任务；输入模式和文件组合不在本层重新推断。"""
    if blade_creator is None:
        from .create_blade import create_single_blade

        blade_creator = create_single_blade

    blade_creator(
        job.airfoil_filename,
        job.section_params_filename,
        job.output_dir,
        job.output_name,
        airfoil_dir=job.airfoil_dir,
        section_params_dir=job.section_params_dir,
        keep_failed_part=job.keep_failed_part,
        input_plan=job.input_plan,
    )
    return BuildResult(job=job, status="success")


def execute_jobs(
    jobs: Iterable[BladeBuildJob],
    *,
    blade_creator=None,
) -> list[BuildResult]:
    """逐个执行任务并保留全部结果；单个失败不会阻断后续任务。"""
    results: list[BuildResult] = []
    for job in jobs:
        try:
            results.append(execute_job(job, blade_creator=blade_creator))
        except Exception as error:
            results.append(
                BuildResult(
                    job=job,
                    status="failed",
                    error=str(error),
                )
            )
    return results
