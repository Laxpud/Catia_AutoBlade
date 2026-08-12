import hashlib
from importlib import resources
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_AIRFOIL_DIR = PROJECT_ROOT / "input" / "airfoils"


def test_builtin_airfoil_library_manifest_is_complete_and_reproducible() -> None:
    """清单必须完整描述每个可复制资源，并固定来源授权与字节摘要。"""
    library_root = resources.files("catia_autoblade.resources").joinpath(
        "airfoil_library"
    )
    manifest = json.loads(
        library_root.joinpath("manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["schema_version"] == 1
    assert manifest["authorization"]["basis"] == (
        "direct_permission_from_author"
    )
    assert manifest["authorization"]["author"] == "Hannnk"
    assert len(manifest["airfoils"]) == 3
    manifest_filenames = {
        record["filename"] for record in manifest["airfoils"]
    }
    packaged_filenames = {
        item.name for item in library_root.iterdir() if item.name.endswith(".csv")
    }
    assert packaged_filenames == manifest_filenames

    for record in manifest["airfoils"]:
        filename = record["filename"]
        packaged_content = library_root.joinpath(filename).read_bytes()
        repository_content = (REPOSITORY_AIRFOIL_DIR / filename).read_text(
            encoding="utf-8"
        )

        assert packaged_content.decode("utf-8").splitlines() == (
            repository_content.splitlines()
        )
        assert hashlib.sha256(packaged_content).hexdigest() == record["sha256"]
        assert len(packaged_content.splitlines()) - 1 == record["point_count"]
        assert record["source_author"] == "Hannnk"
        assert record["license_or_permission"] == (
            "direct_permission_from_author"
        )
