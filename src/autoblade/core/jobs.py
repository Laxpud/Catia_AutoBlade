from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .input_plan import BladeInputPlan, BladeMode


BuildStatus = Literal["success", "failed"]


@dataclass(frozen=True, slots=True)
class BladeBuildJob:
    """一次输入引用、输出位置和建模选项均已确定的叶片任务。

    ``input_plan`` 在 Planner 阶段完成 CSV 解析和跨文件引用闭合，因此执行器
    不需要根据目录内容推断翼型，也不会把 Typer 参数带入 CATIA 建模流程。
    """

    mode: BladeMode
    airfoil_filename: str | None
    blade_sections_filename: str
    airfoil_dir: Path
    blade_sections_dir: Path
    output_dir: Path
    output_name: str
    input_plan: BladeInputPlan
    keep_failed_part: bool = False

    @property
    def output_paths(self) -> tuple[Path, Path]:
        """返回任务会覆盖或创建的原生模型与 STEP 路径。"""
        return (
            self.output_dir / f"{self.output_name}.CATPart",
            self.output_dir / f"{self.output_name}.stp",
        )


@dataclass(frozen=True, slots=True)
class BuildResult:
    """记录一个任务的稳定执行结果，供 CLI 汇总而不丢失失败上下文。"""

    job: BladeBuildJob
    status: BuildStatus
    error: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        """提供旧批处理调用方使用的字典视图。"""
        result: dict[str, str | None] = {
            "status": self.status,
            "mode": self.job.mode,
            "airfoil": self.job.airfoil_filename,
            "section": self.job.blade_sections_filename,
        }
        if self.status == "success":
            result["output"] = str(self.job.output_dir)
        else:
            result["error"] = self.error
        return result
