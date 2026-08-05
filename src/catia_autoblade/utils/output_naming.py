from pathlib import Path
from string import Formatter


OUTPUT_NAME_FIELDS = frozenset({"airfoil", "idx", "section", "author"})


def build_output_name(
    template: str,
    airfoil_filename: str,
    section_filename: str,
    *,
    author: str = "",
) -> str:
    """根据配置模板生成不含目录和扩展名的输出名称。

    ``idx`` 延续历史命名规则：对 ``section_params-1.csv`` 取 ``1``；
    不符合该前缀的文件则使用完整 stem，避免静默生成空名称。
    """
    airfoil = Path(airfoil_filename).stem
    section = Path(section_filename).stem
    prefix = "section_params-"
    idx = section[len(prefix):] if section.startswith(prefix) else section

    fields = {
        field_name
        for _, field_name, _, _ in Formatter().parse(template)
        if field_name is not None
    }
    unsupported_fields = fields - OUTPUT_NAME_FIELDS
    if unsupported_fields:
        unsupported = ", ".join(sorted(unsupported_fields))
        supported = ", ".join(sorted(OUTPUT_NAME_FIELDS))
        raise ValueError(
            f"Unsupported output name field(s): {unsupported}. Supported: {supported}"
        )

    output_name = template.format(
        airfoil=airfoil,
        idx=idx,
        section=section,
        author=author,
    )
    if not output_name or Path(output_name).name != output_name:
        raise ValueError("Output name template must produce a non-empty file name")
    return output_name
