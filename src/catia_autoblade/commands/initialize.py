from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import resources
import json
import os
from pathlib import Path
import re
import site
import tempfile
from uuid import uuid4

import typer


@dataclass(frozen=True)
class WorkspaceInitItem:
    """一个受管理目录或模板文件及其预期操作。"""

    path: Path
    kind: str
    action: str
    content: bytes | None = None


@dataclass(frozen=True)
class WorkspaceInitPlan:
    """初始化执行前可完整展示和检查的文件系统计划。"""

    target: Path
    items: tuple[WorkspaceInitItem, ...]

    @property
    def conflicting_files(self) -> tuple[Path, ...]:
        return tuple(
            item.path
            for item in self.items
            if item.kind == "file" and item.action == "replace"
        )


_DIRECTORIES = (
    Path("input") / "airfoils",
    Path("input") / "blade_sections",
    Path("output"),
)
_BASE_RESOURCES = {
    Path("config.toml"): Path("workspace") / "config.toml"
}
_EXAMPLE_AIRFOIL_FILENAMES = (
    "airfoil1_sharp.csv",
    "airfoil2_sharp.csv",
    "airfoil3_sharp.csv",
)
_EXAMPLE_RESOURCES = {
    Path("input") / "blade_sections" / "example-blade-sections.csv": (
        Path("workspace")
        / "blade_sections"
        / "example-blade-sections.csv"
    ),
}
_AIRFOIL_LIBRARY_MANIFEST = Path("airfoil_library") / "manifest.json"
_AIRFOIL_LIBRARY_DESTINATION = (
    Path("input") / "airfoils" / "manifest.json"
)
_CANONICAL_LIBRARY_FILENAME = re.compile(
    r"[a-z0-9][a-z0-9_-]*\.csv"
)


def plan_workspace_initialization(
    target: str | Path,
    *,
    with_examples: bool,
    with_airfoil_library: bool = False,
) -> WorkspaceInitPlan:
    """生成不触碰磁盘的初始化计划，并拒绝 site-packages 内目标。"""
    target_path = Path(target).expanduser().resolve()
    _validate_target_location(target_path)
    if target_path.exists() and not target_path.is_dir():
        raise ValueError(f"Workspace target is not a directory: {target_path}")

    items: list[WorkspaceInitItem] = []
    for relative_path in _DIRECTORIES:
        destination = target_path / relative_path
        items.append(
            WorkspaceInitItem(
                destination,
                "directory",
                "keep" if destination.is_dir() else "create",
            )
        )

    resource_root = resources.files("catia_autoblade.resources")
    library_resources: dict[Path, Path] = {}
    if with_examples or with_airfoil_library:
        library_resources = _load_airfoil_library_resources(resource_root)
    selected_resources = dict(_BASE_RESOURCES)
    if with_examples:
        selected_resources.update(_EXAMPLE_RESOURCES)
        for filename in _EXAMPLE_AIRFOIL_FILENAMES:
            destination = Path("input") / "airfoils" / filename
            selected_resources[destination] = library_resources[destination]
    if with_airfoil_library:
        selected_resources.update(library_resources)
    for relative_path, resource_path in selected_resources.items():
        destination = target_path / relative_path
        resource_item = resource_root.joinpath(*resource_path.parts)
        items.append(
            WorkspaceInitItem(
                destination,
                "file",
                "replace" if destination.exists() else "create",
                resource_item.read_bytes(),
            )
        )
    return WorkspaceInitPlan(target_path, tuple(items))


def run_init_command(
    target: str | Path,
    *,
    with_examples: bool,
    force: bool,
    interactive: bool,
    with_airfoil_library: bool = False,
) -> WorkspaceInitPlan:
    """展示计划后创建工作区；冲突必须由 force 或交互确认授权。"""
    plan = plan_workspace_initialization(
        target,
        with_examples=with_examples,
        with_airfoil_library=with_airfoil_library,
    )
    typer.echo(f"[INFO] Workspace initialization plan: {plan.target}")
    for item in plan.items:
        typer.echo(f"  {item.action}: {item.path}")

    conflicts = plan.conflicting_files
    overwrite_allowed = force
    if conflicts and interactive and not overwrite_allowed:
        from ..interactive.prompts import confirm_workspace_overwrite

        overwrite_allowed = confirm_workspace_overwrite(list(conflicts))
    if conflicts and not overwrite_allowed:
        names = ", ".join(str(path) for path in conflicts)
        raise FileExistsError(
            "Workspace contains managed files that would be replaced: "
            f"{names}. Use --force or --interactive to confirm."
        )

    _execute_workspace_plan(plan, allow_replace=overwrite_allowed)
    typer.echo(f"[SUCCESS] Workspace initialized: {plan.target}")
    return plan


def _load_airfoil_library_resources(resource_root) -> dict[Path, Path]:
    """读取并校验内置目录清单，避免复制不可复现或越界的资源。"""
    manifest_item = resource_root.joinpath(
        *_AIRFOIL_LIBRARY_MANIFEST.parts
    )
    try:
        manifest_bytes = manifest_item.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(
            f"Cannot read built-in airfoil library manifest: {error}"
        ) from error

    if manifest.get("schema_version") != 1:
        raise RuntimeError("Unsupported built-in airfoil library schema")
    records = manifest.get("airfoils")
    if not isinstance(records, list) or not records:
        raise RuntimeError("Built-in airfoil library manifest is empty")

    selected = {
        _AIRFOIL_LIBRARY_DESTINATION: _AIRFOIL_LIBRARY_MANIFEST
    }
    seen_filenames: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise RuntimeError("Invalid built-in airfoil library record")
        filename = record.get("filename")
        expected_digest = record.get("sha256")
        if (
            not isinstance(filename, str)
            or _CANONICAL_LIBRARY_FILENAME.fullmatch(filename) is None
        ):
            raise RuntimeError(
                f"Invalid built-in airfoil library filename: {filename!r}"
            )
        if filename in seen_filenames:
            raise RuntimeError(
                f"Duplicate built-in airfoil library filename: {filename}"
            )
        if not isinstance(expected_digest, str) or not re.fullmatch(
            r"[0-9a-f]{64}", expected_digest
        ):
            raise RuntimeError(
                f"Invalid SHA-256 for built-in airfoil: {filename}"
            )

        resource_path = Path("airfoil_library") / filename
        resource_item = resource_root.joinpath(*resource_path.parts)
        try:
            content = resource_item.read_bytes()
        except OSError as error:
            raise RuntimeError(
                f"Cannot read built-in airfoil resource {filename}: {error}"
            ) from error
        actual_digest = hashlib.sha256(content).hexdigest()
        if actual_digest != expected_digest:
            raise RuntimeError(
                "Built-in airfoil resource digest mismatch: "
                f"{filename}"
            )

        seen_filenames.add(filename)
        selected[Path("input") / "airfoils" / filename] = resource_path

    missing_examples = set(_EXAMPLE_AIRFOIL_FILENAMES) - seen_filenames
    if missing_examples:
        raise RuntimeError(
            "Built-in airfoil library is missing example dependencies: "
            f"{sorted(missing_examples)}"
        )
    library_root = resource_root.joinpath("airfoil_library")
    packaged_csv = {
        item.name
        for item in library_root.iterdir()
        if item.name.endswith(".csv")
    }
    unlisted_csv = packaged_csv - seen_filenames
    if unlisted_csv:
        raise RuntimeError(
            "Built-in airfoil resources are missing from the manifest: "
            f"{sorted(unlisted_csv)}"
        )
    return selected


def _execute_workspace_plan(
    plan: WorkspaceInitPlan,
    *,
    allow_replace: bool,
) -> None:
    """只创建计划内目录和文件；不删除目标中的任何其他用户内容。"""
    _probe_target_write_access(plan.target)
    for item in plan.items:
        if item.kind == "directory":
            item.path.mkdir(parents=True, exist_ok=True)

    for item in plan.items:
        if item.kind != "file":
            continue
        if item.path.exists() and not allow_replace:
            raise FileExistsError(f"Refusing to replace managed file: {item.path}")
        if item.content is None:
            raise RuntimeError(f"Workspace template has no content: {item.path}")
        _atomic_write_bytes(item.path, item.content)


def _probe_target_write_access(target: Path) -> None:
    """在最近的已有目录创建并立即删除探针，不创建目标工作区。"""
    ancestor = target
    while not ancestor.exists():
        if ancestor.parent == ancestor:
            raise PermissionError(f"No writable parent found for {target}")
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise ValueError(f"Workspace parent is not a directory: {ancestor}")
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".autoblade-write-probe-",
            dir=ancestor,
            delete=True,
        ):
            pass
    except OSError as error:
        raise PermissionError(
            f"Workspace target is not writable: {target}: {error}"
        ) from error


def _atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_bytes(content)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _validate_target_location(target: Path) -> None:
    """安装资源必须复制到外部工作区，不能把用户文件写回包目录。"""
    candidates = [Path(path).expanduser().resolve() for path in site.getsitepackages()]
    user_site = site.getusersitepackages()
    if user_site:
        candidates.append(Path(user_site).expanduser().resolve())
    for package_root in candidates:
        if target == package_root or package_root in target.parents:
            raise ValueError(
                f"Workspace target must be outside site-packages: {target}"
            )
