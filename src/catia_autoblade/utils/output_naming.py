from pathlib import Path
from string import Formatter


OUTPUT_NAME_FIELDS = frozenset(
    {"airfoil", "idx", "section", "author", "blade"}
)


def build_output_name(
    template: str,
    airfoil_filename: str | None,
    section_filename: str,
    *,
    author: str = "",
    is_multi_airfoil: bool = False,
) -> str:
    """根据配置模板生成不含目录和扩展名的输出名称。

    ``idx`` 延续历史命名规则：对 ``section_params-1.csv`` 取 ``1``；
    不符合该前缀的文件则使用完整 stem，避免静默生成空名称。
    """
    airfoil = Path(airfoil_filename).stem if airfoil_filename else None
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
    if is_multi_airfoil and "airfoil" in fields:
        raise ValueError(
            "Output name field '{airfoil}' is unavailable for a multi-airfoil blade"
        )
    if not is_multi_airfoil and airfoil is None:
        raise ValueError("Single-airfoil output naming requires an airfoil filename")

    # ``blade`` 是模式无关的稳定输出标识；默认模板迁移后仍保持旧单翼型名称。
    blade = (
        f"blade-{idx}"
        if is_multi_airfoil
        else f"{airfoil}_blade-{idx}"
    )

    output_name = template.format(
        airfoil=airfoil,
        idx=idx,
        section=section,
        author=author,
        blade=blade,
    )
    if not output_name or Path(output_name).name != output_name:
        raise ValueError("Output name template must produce a non-empty file name")
    return output_name
