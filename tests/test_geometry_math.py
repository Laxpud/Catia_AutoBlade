from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from autoblade.adapters.cad.catia.builder import (
    meters_to_catia_mm,
    point_m_to_catia_mm,
    transform_airfoil_section,
)
from autoblade.core.geometry import (
    section_scale_factor,
    transform_point,
)


@pytest.mark.parametrize(
    ("meters", "millimeters"),
    [(0.0, 0.0), (1.0, 1000.0), (-0.025, -25.0)],
)
def test_meters_are_converted_only_at_catia_boundary(
    meters: float,
    millimeters: float,
) -> None:
    assert meters_to_catia_mm(meters) == pytest.approx(millimeters)


def test_point_conversion_preserves_axis_order() -> None:
    assert point_m_to_catia_mm((0.1, -0.2, 0.003)) == pytest.approx(
        (100.0, -200.0, 3.0)
    )


def test_section_scale_factor_uses_one_meter_reference_chord() -> None:
    assert section_scale_factor(0.075) == pytest.approx(0.075)


def test_transform_point_applies_rotation_then_scale_then_translation() -> None:
    # 绕 X 轴旋转 90°后 (1, 2, 3) -> (1, -3, 2)，再整体缩放并平移。
    transformed = transform_point(
        1.0,
        2.0,
        3.0,
        rotation_deg=90.0,
        chord_m=2.0,
        tx=10.0,
        ty=20.0,
        tz=30.0,
    )

    assert transformed == pytest.approx((12.0, 14.0, 34.0))


def test_transform_point_keeps_domain_values_in_meters() -> None:
    transformed = transform_point(
        0.0,
        0.25,
        0.0,
        rotation_deg=0.0,
        chord_m=0.1,
        tx=0.5,
        ty=0.01,
        tz=-0.02,
    )

    assert transformed == pytest.approx((0.5, 0.035, -0.02))


def _make_transform_part():
    """构造只记录截面变换 COM 调用的最小 Part 替身。"""
    rotated = SimpleNamespace(Name=None)
    scaled = SimpleNamespace(Name=None)
    translated = SimpleNamespace(Name=None)
    factory = Mock()
    factory.AddNewRotate.return_value = rotated
    factory.AddNewHybridScaling.return_value = scaled
    factory.AddNewTranslate.return_value = translated
    part = Mock()
    part.HybridShapeFactory = factory
    part.CreateReferenceFromObject.side_effect = lambda feature: feature
    return part, factory, scaled, translated


def test_zero_translation_skips_invalid_catia_direction() -> None:
    part, factory, scaled, _ = _make_transform_part()
    section = {
        "idx": 1,
        "rotation_deg": 0.0,
        "chord_m": 0.1,
        "translate_x_m": 0.0,
        "translate_y_m": 0.0,
        "translate_z_m": 0.0,
    }

    result = transform_airfoil_section(
        part,
        airfoil_ref="airfoil",
        x_axis_ref="x-axis",
        origin_ref="origin",
        section=section,
    )

    assert result is scaled
    factory.AddNewDirectionByCoord.assert_not_called()
    factory.AddNewTranslate.assert_not_called()


def test_nonzero_translation_keeps_direction_and_distance() -> None:
    part, factory, _, translated = _make_transform_part()
    section = {
        "idx": 2,
        "rotation_deg": 0.0,
        "chord_m": 0.1,
        "translate_x_m": 0.3,
        "translate_y_m": 0.4,
        "translate_z_m": 0.0,
    }

    result = transform_airfoil_section(
        part,
        airfoil_ref="airfoil",
        x_axis_ref="x-axis",
        origin_ref="origin",
        section=section,
    )

    assert result is translated
    factory.AddNewDirectionByCoord.assert_called_once_with(0.3, 0.4, 0.0)
    factory.AddNewTranslate.assert_called_once_with(
        factory.AddNewHybridScaling.return_value,
        factory.AddNewDirectionByCoord.return_value,
        pytest.approx(500.0),
    )
