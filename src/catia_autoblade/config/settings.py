from pathlib import Path

from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """配置文件中保存的路径契约。"""

    input_dir: Path = Path("input")
    output_dir: Path = Path("output")
    # 这两个目录的相对值以 input_dir 为基准，便于整体迁移输入树。
    airfoil_dir: Path = Path("airfoils")
    section_params_dir: Path = Path("section_params")


class DefaultsConfig(BaseModel):
    """不由 CLI 显式指定时采用的运行默认值。"""

    author: str = ""
    output_name_template: str = "{blade}"


class AppConfig(BaseModel):
    """持久化配置及其运行时解析结果共用的模型。"""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    version: str = "1.0.0"
