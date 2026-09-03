"""不依赖 CAD 后端的叶片坐标与尺寸计算。"""

import math


# 输入点云以 1 m 弦长为归一化基准；具体 CAD 后端负责在接口边界换算单位。
AIRFOIL_REFERENCE_CHORD_M = 1.0


def section_scale_factor(chord_m: float) -> float:
    """根据米制弦长计算相对于 1 m 基准翼型的无量纲缩放因子。"""
    return chord_m / AIRFOIL_REFERENCE_CHORD_M


def transform_point(
    px: float,
    py: float,
    pz: float,
    rotation_deg: float,
    chord_m: float,
    tx: float,
    ty: float,
    tz: float,
) -> tuple[float, float, float]:
    """按绕 X 轴旋转、整体缩放、三轴平移的领域顺序返回米制坐标。"""
    angle_rad = math.radians(rotation_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    scale_factor = section_scale_factor(chord_m)

    x_rotated = px
    y_rotated = py * cos_a - pz * sin_a
    z_rotated = py * sin_a + pz * cos_a
    return (
        x_rotated * scale_factor + tx,
        y_rotated * scale_factor + ty,
        z_rotated * scale_factor + tz,
    )
