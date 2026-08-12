from pathlib import Path
from unittest.mock import Mock

import pytest

from catia_autoblade.adapters.cad.catia import builder as create_module
from catia_autoblade.core.input_plan import AirfoilInput, BladeInputPlan


def test_multi_airfoil_geometry_is_created_once_and_selected_by_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """唯一翼型只建一次，截面序列通过文件名引用对应基准曲线。"""
    plan = BladeInputPlan(
        mode="multi",
        blade_sections_path=tmp_path / "sections.csv",
        sections=(
            {"idx": 1, "airfoil_filename": "foil_a.csv"},
            {"idx": 2, "airfoil_filename": "foil_a.csv"},
            {"idx": 3, "airfoil_filename": "foil_b.csv"},
        ),
        airfoils=(
            AirfoilInput(
                "foil_a.csv",
                tmp_path / "foil_a.csv",
                ((0.0, -0.75, 0.0),),
                True,
            ),
            AirfoilInput(
                "foil_b.csv",
                tmp_path / "foil_b.csv",
                ((0.0, -0.75, 0.0),),
                True,
            ),
        ),
        is_sharp=True,
    )
    created_feature_ids: list[str] = []
    geometry_call = {}

    def fake_create_airfoil(part, points, *, feature_id=None):
        created_feature_ids.append(feature_id)
        return (
            f"body:{feature_id}",
            f"profile:{feature_id}",
            True,
            ((0.0, -0.75, 0.0),),
        )

    def fake_create_blade_geometry(part, geometries, is_sharp, sections):
        geometry_call["geometries"] = geometries
        geometry_call["is_sharp"] = is_sharp
        geometry_call["sections"] = sections
        return (
            "blade_geometry",
            ["section"],
            "leading_edge",
            "trailing_edge_upper",
            "trailing_edge_lower",
            ["leading_edge_point"],
        )

    monkeypatch.setattr(create_module, "create_airfoil", fake_create_airfoil)
    monkeypatch.setattr(
        create_module,
        "create_blade_geometry",
        fake_create_blade_geometry,
    )
    monkeypatch.setattr(
        create_module,
        "create_blade_surface",
        lambda *args: ("surface_body", "surface"),
    )
    monkeypatch.setattr(create_module, "create_blade_solid", lambda *args: None)
    monkeypatch.setattr(
        create_module,
        "hide_all_except_blade_solid",
        lambda *args: None,
    )
    monkeypatch.setattr(create_module, "save_part", lambda *args: None)

    create_module._build_and_save_blade(
        Mock(),
        Mock(),
        plan,
        tmp_path / "output",
        "blade-multi",
    )

    assert created_feature_ids == ["foil_a", "foil_b"]
    assert list(geometry_call["geometries"]) == ["foil_a.csv", "foil_b.csv"]
    assert geometry_call["geometries"]["foil_a.csv"].profile == "profile:foil_a"
    assert geometry_call["geometries"]["foil_b.csv"].profile == "profile:foil_b"
    assert geometry_call["is_sharp"] is True
    assert geometry_call["sections"] == plan.sections
