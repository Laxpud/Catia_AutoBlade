import os
import math
from dataclasses import dataclass
from pathlib import Path

from ....config.manager import ConfigManager
from ....core.geometry import (
    AIRFOIL_REFERENCE_CHORD_M,
    section_scale_factor,
    transform_point,
)
from ....core.input_validation import (
    AIRFOIL_QUARTER_CHORD_RATIO,
    COORDINATE_TOLERANCE_M,
    read_airfoil_csv,
)
from ....core.input_plan import BladeInputPlan, build_blade_input_plan
from ....utils.output_naming import build_output_name
from .errors import CatiaBackendUnavailableError

CATHybridShapePointCoord = 0
CATConstraintMode = 1
CAT_GSM_MAX = 1

# 输入文件和领域计算统一使用 m；CATIA Automation 的长度参数固定使用 mm，
# 因此只允许在调用 COM 接口的边界执行单位换算。
CATIA_MM_PER_METER = 1000.0


@dataclass(frozen=True, slots=True)
class AirfoilGeometry:
    """一个唯一翼型在当前 CATPart 中创建的可复用基准几何。"""

    body: object
    profile: object
    is_sharp: bool
    trailing_edge_coords: tuple


def meters_to_catia_mm(value_m):
    """在 CATIA COM 边界将领域长度从 m 换算为接口要求的 mm。"""
    return value_m * CATIA_MM_PER_METER


def point_m_to_catia_mm(point_m):
    """将领域坐标点从 m 换算为 CATIA Automation 使用的 mm 三元组。"""
    return tuple(meters_to_catia_mm(coordinate) for coordinate in point_m)


def create_airfoil(part, points: list, *, feature_id: str | None = None):
    try:
        feature_prefix = feature_id or "airfoil"
        hybrid_bodies = part.HybridBodies
        gs_airfoil = hybrid_bodies.Add()
        gs_airfoil.Name = feature_prefix
        hybrid_shape_factory = part.HybridShapeFactory

        hybrid_shapes = []
        point_index_width = max(4, len(str(len(points))))
        for point_index, point_m in enumerate(points, start=1):
            point = hybrid_shape_factory.AddNewPointCoord(
                *point_m_to_catia_mm(point_m)
            )
            point.Name = (
                f"{feature_prefix}_cloud_point_"
                f"{point_index:0{point_index_width}d}"
            )
            gs_airfoil.AppendHybridShape(point)
            part.Update()
            hybrid_shapes.append(point)

        spline = hybrid_shape_factory.AddNewSpline()
        for point in hybrid_shapes:
            reference = part.CreateReferenceFromObject(point)
            spline.AddPoint(reference)
        spline.Name = f"{feature_prefix}_surface_spline"
        gs_airfoil.AppendHybridShape(spline)
        part.Update()
        print(f"[INFO] Airfoil spline created with {len(hybrid_shapes)} points.")

        first_point = points[0]
        last_point = points[-1]
        if first_point != last_point:
            is_sharp = False
            start_point = hybrid_shape_factory.AddNewPointCoord(
                *point_m_to_catia_mm(first_point)
            )
            end_point = hybrid_shape_factory.AddNewPointCoord(
                *point_m_to_catia_mm(last_point)
            )
            start_point.Name = f"{feature_prefix}_trailing_edge_upper"
            end_point.Name = f"{feature_prefix}_trailing_edge_lower"
            gs_airfoil.AppendHybridShape(start_point)
            gs_airfoil.AppendHybridShape(end_point)
            part.Update()

            start_point_ref = part.CreateReferenceFromObject(start_point)
            end_point_ref = part.CreateReferenceFromObject(end_point)
            line = hybrid_shape_factory.AddNewLinePtPt(start_point_ref, end_point_ref)
            line.Name = f"{feature_prefix}_trailing_edge_closure"
            gs_airfoil.AppendHybridShape(line)
            part.Update()
            print("[INFO] Line created to connect first and last points of airfoil cloud.")

            spline_ref = part.CreateReferenceFromObject(spline)
            line_ref = part.CreateReferenceFromObject(line)
            join_feature = hybrid_shape_factory.AddNewJoin(spline_ref, line_ref)
            join_feature.Name = f"{feature_prefix}_closed_profile"
            gs_airfoil.AppendHybridShape(join_feature)
            part.Update()
            print("[INFO] Spline and line joined successfully.")
            te_coord = (first_point, last_point)
            return gs_airfoil, join_feature, is_sharp, te_coord
        else:
            is_sharp = True
            te_coord = (first_point,)
            return gs_airfoil, spline, is_sharp, te_coord
    except Exception as e:
        raise Exception(f"Error creating airfoil cloud: {e}") from e


def transform_airfoil_section(part, airfoil_ref, x_axis_ref, origin_ref, section):
    try:
        hsf = part.HybridShapeFactory
        rotated = hsf.AddNewRotate(
            airfoil_ref, x_axis_ref, section['rotation_deg']
        )
        rotated.Name = f"section_rotation_{section['idx']}"
        part.Update()

        rotated_ref = part.CreateReferenceFromObject(rotated)
        scale_factor = section_scale_factor(section['chord_m'])
        scaled = hsf.AddNewHybridScaling(rotated_ref, origin_ref, scale_factor)
        scaled.Name = f"section_scaling_{section['idx']}"
        part.Update()

        translate_distance_m = math.sqrt(
            section['translate_x_m']**2 +
            section['translate_y_m']**2 +
            section['translate_z_m']**2
        )

        # 零位移是合法的恒等变换，但零向量不能定义 CATIA Direction。
        # 此时直接复用缩放后的截面，避免创建缺少有效方向的 Translate 特征。
        if math.isclose(
            translate_distance_m,
            0.0,
            abs_tol=COORDINATE_TOLERANCE_M,
        ):
            return scaled

        scaled_ref = part.CreateReferenceFromObject(scaled)
        translate_dir = hsf.AddNewDirectionByCoord(
            section['translate_x_m'],
            section['translate_y_m'],
            section['translate_z_m']
        )
        translated = hsf.AddNewTranslate(
            scaled_ref,
            translate_dir,
            meters_to_catia_mm(translate_distance_m),
        )
        translated.Name = f"section_translated_profile_{section['idx']}"
        part.Update()

        return translated
    except Exception as e:
        raise Exception(f"Error transforming section {section['idx']}: {e}") from e


def create_section_le_te_points(
    part,
    gs_blade,
    section_curve,
    te_coords,
    section,
    le_points,
    te_upper_points,
    te_lower_points,
):
    try:
        hsf = part.HybridShapeFactory
        angle_rad = math.radians(section['rotation_deg'])

        # 前缘闭合点必须由当前截面曲线本身派生。理论前缘坐标不一定落在
        # CATIA 根据离散点拟合出的样条上，点云越密时这种偏差反而可能更明显。
        #
        # 1. 基准翼型的前缘位于 +Y 极值；绕 X 轴扭转后，对应方向为
        #    (0, cos(theta), sin(theta))。
        # 2. 密集点云的 Extremum 可能包含多个非连通点，不能直接作为样条点。
        # 3. 理论前缘仅用作 Near 的候选选择器；最终结果仍来自曲线极值，
        #    因而严格位于当前截面上并随上游几何自动更新。
        selector_x, selector_y, selector_z = transform_point(
            0.0,
            AIRFOIL_QUARTER_CHORD_RATIO * AIRFOIL_REFERENCE_CHORD_M,
            0.0,
            section['rotation_deg'],
            section['chord_m'],
            section['translate_x_m'],
            section['translate_y_m'],
            section['translate_z_m'],
        )
        le_selector = hsf.AddNewPointCoord(
            *point_m_to_catia_mm((selector_x, selector_y, selector_z))
        )
        le_selector.Name = f"leading_edge_selector_{section['idx']}"
        gs_blade.AppendHybridShape(le_selector)
        part.Update()

        section_curve_ref = part.CreateReferenceFromObject(section_curve)
        leading_edge_direction = hsf.AddNewDirectionByCoord(
            0.0,
            math.cos(angle_rad),
            math.sin(angle_rad),
        )
        le_candidates = hsf.AddNewExtremum(
            section_curve_ref,
            leading_edge_direction,
            CAT_GSM_MAX,
        )
        le_candidates.Name = f"leading_edge_candidates_{section['idx']}"
        gs_blade.AppendHybridShape(le_candidates)
        part.Update()

        candidates_ref = part.CreateReferenceFromObject(le_candidates)
        selector_ref = part.CreateReferenceFromObject(le_selector)
        le_final = hsf.AddNewNear(candidates_ref, selector_ref)
        le_final.Name = f"leading_edge_{section['idx']}"
        gs_blade.AppendHybridShape(le_final)
        part.Update()
        le_points.append(le_final)

        if len(te_coords) == 2:
            te_upper_coord, te_lower_coord = te_coords
            te_u_x, te_u_y, te_u_z = transform_point(
                te_upper_coord[0], te_upper_coord[1], te_upper_coord[2],
                section['rotation_deg'], section['chord_m'],
                section['translate_x_m'], section['translate_y_m'], section['translate_z_m']
            )
            te_upper_final = hsf.AddNewPointCoord(
                *point_m_to_catia_mm((te_u_x, te_u_y, te_u_z))
            )
            te_upper_final.Name = f"trailing_edge_upper_{section['idx']}"
            gs_blade.AppendHybridShape(te_upper_final)
            part.Update()
            te_upper_points.append(te_upper_final)

            te_l_x, te_l_y, te_l_z = transform_point(
                te_lower_coord[0], te_lower_coord[1], te_lower_coord[2],
                section['rotation_deg'], section['chord_m'],
                section['translate_x_m'], section['translate_y_m'], section['translate_z_m']
            )
            te_lower_final = hsf.AddNewPointCoord(
                *point_m_to_catia_mm((te_l_x, te_l_y, te_l_z))
            )
            te_lower_final.Name = f"trailing_edge_lower_{section['idx']}"
            gs_blade.AppendHybridShape(te_lower_final)
            part.Update()
            te_lower_points.append(te_lower_final)
        else:
            te_single_coord = te_coords[0]
            te_x, te_y, te_z = transform_point(
                te_single_coord[0], te_single_coord[1], te_single_coord[2],
                section['rotation_deg'], section['chord_m'],
                section['translate_x_m'], section['translate_y_m'], section['translate_z_m']
            )
            te_final = hsf.AddNewPointCoord(
                *point_m_to_catia_mm((te_x, te_y, te_z))
            )
            te_final.Name = f"trailing_edge_{section['idx']}"
            gs_blade.AppendHybridShape(te_final)
            part.Update()
            te_upper_points.append(te_final)
            te_lower_points.append(te_final)
    except Exception as e:
        raise Exception(
            f"Error creating LE/TE points for section {section['idx']}: {e}"
        ) from e


def create_blade_geometry(
    part,
    airfoil_geometries: dict[str, AirfoilGeometry],
    is_sharp,
    blade_sections,
):
    try:
        hybrid_bodies = part.HybridBodies
        gs_blade = hybrid_bodies.Add()
        gs_blade.Name = "blade_geometry"

        hsf = part.HybridShapeFactory
        origin_point = hsf.AddNewPointCoord(0, 0, 0)
        origin_point.Name = "section_transform_origin"
        gs_blade.AppendHybridShape(origin_point)
        part.Update()
        origin_ref = part.CreateReferenceFromObject(origin_point)

        x_dir = hsf.AddNewDirectionByCoord(1, 0, 0)
        x_axis = hsf.AddNewLinePtDir(
            origin_ref, x_dir, 0, meters_to_catia_mm(1.0), True
        )
        x_axis.Name = "section_rotation_axis"
        gs_blade.AppendHybridShape(x_axis)
        part.Update()
        x_axis_ref = part.CreateReferenceFromObject(x_axis)

        le_points = []
        te_upper_points = []
        te_lower_points = []
        section_splines = []

        for section in blade_sections:
            airfoil_filename = str(section["airfoil_filename"])
            airfoil_geometry = airfoil_geometries[airfoil_filename]
            airfoil_ref = part.CreateReferenceFromObject(
                airfoil_geometry.profile
            )
            translated = transform_airfoil_section(
                part, airfoil_ref, x_axis_ref, origin_ref, section
            )
            gs_blade.AppendHybridShape(translated)
            part.Update()
            section_splines.append(translated)

            create_section_le_te_points(
                part,
                gs_blade,
                translated,
                airfoil_geometry.trailing_edge_coords,
                section,
                le_points,
                te_upper_points,
                te_lower_points,
            )

            print(f"[INFO] Section {section['idx']}: "
                  f"airfoil={airfoil_filename}, "
                  f"rotate={section['rotation_deg']}deg, "
                  f"chord={section['chord_m']}m, scale_factor="
                  f"{section_scale_factor(section['chord_m'])}, "
                  f"translate=({section['translate_x_m']}, "
                  f"{section['translate_y_m']}, {section['translate_z_m']})m")

        le_spline = hsf.AddNewSpline()
        for pt in le_points:
            ref = part.CreateReferenceFromObject(pt)
            le_spline.AddPoint(ref)
        le_spline.Name = "leading_edge_guide"
        gs_blade.AppendHybridShape(le_spline)
        part.Update()

        te_upper_spline = hsf.AddNewSpline()
        for pt in te_upper_points:
            ref = part.CreateReferenceFromObject(pt)
            te_upper_spline.AddPoint(ref)
        te_upper_spline.Name = "trailing_edge_upper_guide"
        gs_blade.AppendHybridShape(te_upper_spline)
        part.Update()

        if is_sharp:
            te_lower_spline = te_upper_spline
        else:
            te_lower_spline = hsf.AddNewSpline()
            for pt in te_lower_points:
                ref = part.CreateReferenceFromObject(pt)
                te_lower_spline.AddPoint(ref)
            te_lower_spline.Name = "trailing_edge_lower_guide"
            gs_blade.AppendHybridShape(te_lower_spline)
            part.Update()

        print("[INFO] Blade geometry created successfully.")
        return gs_blade, section_splines, le_spline, te_upper_spline, te_lower_spline, le_points

    except Exception as e:
        raise Exception(f"Error creating blade geometry: {e}") from e


def create_blade_surface(part, section_splines: list, le_spline, te_upper_spline, te_lower_spline, le_points, is_sharp):
    try:
        hybrid_bodies = part.HybridBodies
        gs_blade_surface = hybrid_bodies.Add()
        gs_blade_surface.Name = "blade_surface"

        hsf = part.HybridShapeFactory

        section_refs = []
        for spline in section_splines:
            ref = part.CreateReferenceFromObject(spline)
            section_refs.append(ref)

        le_point_refs = []
        for le_pt in le_points:
            le_pt_ref = part.CreateReferenceFromObject(le_pt)
            le_point_refs.append(le_pt_ref)

        le_ref = part.CreateReferenceFromObject(le_spline)
        te_upper_ref = part.CreateReferenceFromObject(te_upper_spline)
        blade_surface = hsf.AddNewLoft()
        blade_surface.Name = "blade_loft_surface"

        for i, ref in enumerate(section_refs):
            le_pt_ref = le_point_refs[i]
            blade_surface.AddSectionToLoft(ref, 1, le_pt_ref)

        blade_surface.AddGuide(le_ref)
        blade_surface.AddGuide(te_upper_ref)
        if not is_sharp:
            te_lower_ref = part.CreateReferenceFromObject(te_lower_spline)
            blade_surface.AddGuide(te_lower_ref)

        gs_blade_surface.AppendHybridShape(blade_surface)
        part.Update()
        print("[INFO] Blade surface created successfully.")
        return gs_blade_surface, blade_surface

    except Exception as e:
        raise Exception(f"Error creating blade surface: {e}") from e


def create_blade_solid(part, surface):
    try:
        shape_factory = part.ShapeFactory
        bodies = part.Bodies
        new_body = bodies.Add()
        new_body.Name = "blade_solid_body"
        part.InWorkObject = new_body

        surface_ref = part.CreateReferenceFromObject(surface)
        blade_solid = shape_factory.AddNewCloseSurface(surface_ref)
        blade_solid.Name = "blade_closed_solid"
        part.Update()
        print("[INFO] Blade solid created successfully.")
        return blade_solid

    except Exception as e:
        raise Exception(f"Error creating blade solid: {e}") from e


def save_part(part_document, output_dir, output_name="blade_part"):
    try:
        os.makedirs(output_dir, exist_ok=True)
        output_absdir = os.path.abspath(output_dir)
        catpart_path = os.path.join(output_absdir, f"{output_name}.CATPart")
        if os.path.exists(catpart_path):
            os.remove(catpart_path)
        part_document.SaveAs(catpart_path)
        print(f"[INFO] Part saved to: {catpart_path}")
        stp_path = os.path.join(output_absdir, f"{output_name}.stp")
        if os.path.exists(stp_path):
            os.remove(stp_path)
        part_document.ExportData(stp_path, "stp")
        print(f"[INFO] Part exported to: {stp_path}")
    except Exception as e:
        raise Exception(f"Error saving part: {e}") from e


def save_failed_part(part_document, output_dir, output_name="blade_part"):
    """将 CATIA 失败现场保存为不覆盖历史快照的原生文档。"""
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    # 失败快照用于逐次对比特征树和 CATIA 更新状态，因此必须保留旧文件。
    # 首次使用 ``_failed``，后续冲突时追加递增编号；失败现场不导出 STEP，
    # 因为未完成几何通常无法稳定通过中性格式导出。
    failed_path = output_path / f"{output_name}_failed.CATPart"
    suffix = 2
    while failed_path.exists():
        failed_path = output_path / f"{output_name}_failed-{suffix}.CATPart"
        suffix += 1

    try:
        part_document.SaveAs(str(failed_path))
    except Exception as error:
        raise Exception(
            f"Error saving failed CATIA part to {failed_path}: {error}"
        ) from error

    print(f"[INFO] Failed CATIA part saved to: {failed_path}")
    return failed_path


def hide_object(selection, obj):
    try:
        selection.Add(obj)
        selection.VisProperties.SetShow(1)
        selection.Clear()
    except Exception:
        pass


def hide_all_except_blade_solid(
    part_document,
    gs_airfoils,
    gs_blade_geometry,
    gs_blade_surface,
):
    try:
        selection = part_document.Selection
        for gs_airfoil in gs_airfoils:
            hide_object(selection, gs_airfoil)
        hide_object(selection, gs_blade_geometry)
        hide_object(selection, gs_blade_surface)
        print("[INFO] Hidden airfoil, blade geometry and blade surface sets.")
    except Exception as e:
        print(f"[WARNING] Error hiding objects: {e}")


def create_single_blade(
    airfoil_filename,
    blade_sections_filename,
    output_dir=None,
    output_name=None,
    *,
    airfoil_dir=None,
    blade_sections_dir=None,
    output_name_template=None,
    keep_failed_part=False,
    session_factory=None,
    input_plan: BladeInputPlan | None = None,
):
    """创建单个叶片，并按需保留建模失败时的 CATIA 原生快照。"""
    runtime_config = None
    needs_runtime_config = (
        airfoil_dir is None
        or blade_sections_dir is None
        or output_dir is None
        or (output_name is None and output_name_template is None)
    )
    if needs_runtime_config:
        runtime_config = ConfigManager().load_runtime()

    if airfoil_dir is None:
        airfoil_dir = runtime_config.paths.airfoil_dir
    if blade_sections_dir is None:
        blade_sections_dir = runtime_config.paths.blade_sections_dir
    if output_dir is None:
        output_dir = runtime_config.paths.output_dir
    # 输入必须在 COM 初始化前完成解析和领域校验。这样缺列、非法数字、
    # 点序、截面数量或跨文件引用错误不会启动昂贵且需要清理的 CATIA 进程。
    if input_plan is None:
        blade_sections_path = Path(blade_sections_dir) / blade_sections_filename
        input_plan = build_blade_input_plan(
            blade_sections_path,
            airfoil_dir,
            airfoil_filename,
            airfoil_reader=read_airfoil_csv,
        )

    if output_name is None:
        template = output_name_template
        if template is None:
            template = runtime_config.defaults.output_name_template
        author = runtime_config.defaults.author if runtime_config else ""
        output_name = build_output_name(
            template,
            airfoil_filename,
            blade_sections_filename,
            author=author,
            is_multi_airfoil=input_plan.mode == "multi",
        )

    session_factory = _resolve_session_factory(session_factory)

    # 会话上下文只覆盖 CATIA 建模、更新、保存和导出。启用失败快照时，必须
    # 在 __exit__ 关闭文档前执行 SaveAs；快照保存自身的错误只能作为附加诊断，
    # 不能遮蔽最初发生的几何、更新或导出异常。
    with session_factory() as session:
        try:
            _build_and_save_blade(
                session.part_document,
                session.part,
                input_plan,
                output_dir,
                output_name,
            )
        except Exception as primary_error:
            if keep_failed_part:
                try:
                    save_failed_part(
                        session.part_document,
                        output_dir,
                        output_name,
                    )
                except Exception as snapshot_error:
                    warning = (
                        "Failed CATIA snapshot could not be saved: "
                        f"{snapshot_error}"
                    )
                    primary_error.add_note(warning)
                    print(f"[WARNING] {warning}")
            raise

    return output_name, output_dir


def _resolve_session_factory(session_factory):
    """延迟装载 Windows COM 会话，并为不可用平台提供稳定能力错误。"""
    if session_factory is not None:
        return session_factory
    if not _is_windows():
        raise CatiaBackendUnavailableError(
            "CATIA backend is unavailable: Windows, pywin32, and a registered "
            "CATIA V5 COM server are required."
        )

    try:
        from .session import CatiaSession
    except ImportError as error:
        if error.name == "pythoncom" or (
            error.name is not None and error.name.startswith("win32com")
        ):
            raise CatiaBackendUnavailableError(
                "CATIA backend is unavailable: pywin32 is not installed for "
                "this Python environment."
            ) from error
        raise
    return CatiaSession


def _is_windows() -> bool:
    """集中平台判断，便于在不改变 pathlib 行为的情况下测试失败分支。"""
    return os.name == "nt"


def _build_and_save_blade(
    part_document,
    part,
    input_plan: BladeInputPlan,
    output_dir,
    output_name,
):
    """在独立作用域内持有临时 CATIA 几何代理并完成建模与导出。"""
    # 该函数返回或因异常退栈后，几何特征代理会先于 CatiaSession.__exit__
    # 离开局部作用域，避免残留 COM 引用延迟隐藏 CATIA 进程退出。
    # 每个唯一翼型只创建一套点云和基准曲线；截面循环只复用对应曲线引用。
    airfoil_geometries: dict[str, AirfoilGeometry] = {}
    gs_airfoils = []
    for airfoil_input in input_plan.airfoils:
        if input_plan.mode == "multi":
            created = create_airfoil(
                part,
                list(airfoil_input.points),
                feature_id=Path(airfoil_input.filename).stem,
            )
        else:
            # 保留单翼型特征树名称，也兼容现有 COM fake 的两参数接口。
            created = create_airfoil(part, list(airfoil_input.points))
        gs_airfoil, profile, is_sharp, te_coords = created
        gs_airfoils.append(gs_airfoil)
        airfoil_geometries[airfoil_input.filename] = AirfoilGeometry(
            body=gs_airfoil,
            profile=profile,
            is_sharp=is_sharp,
            trailing_edge_coords=te_coords,
        )

    (
        gs_blade_geometry,
        section_splines,
        le_spline,
        te_upper_spline,
        te_lower_spline,
        le_points,
    ) = create_blade_geometry(
        part,
        airfoil_geometries,
        input_plan.is_sharp,
        input_plan.sections,
    )

    gs_blade_surface, blade_surface = create_blade_surface(
        part,
        section_splines,
        le_spline,
        te_upper_spline,
        te_lower_spline,
        le_points,
        input_plan.is_sharp,
    )

    create_blade_solid(part, blade_surface)
    hide_all_except_blade_solid(
        part_document,
        gs_airfoils,
        gs_blade_geometry,
        gs_blade_surface,
    )

    try:
        part.Update()
    except Exception as e:
        print(f"[WARNING] Part update failed: {e}")

    save_part(part_document, output_dir, output_name)


def main():
    create_single_blade("sc1095.csv", "blade_sections-1.csv")


if __name__ == "__main__":
    main()
