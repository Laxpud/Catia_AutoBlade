"""校验源码版本、CLI、Git 标签和构建产物中的发布元数据。"""

from __future__ import annotations

import argparse
import ast
from email.message import Message
from email.parser import Parser
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tomllib
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
VERSION_PATH = PROJECT_ROOT / "src" / "catia_autoblade" / "__init__.py"
README_PATH = PROJECT_ROOT / "README.md"
EXPECTED_PROJECT_NAME = "catia-autoblade"
EXPECTED_REQUIRES_PYTHON = ">=3.14,<3.15"


class ValidationError(RuntimeError):
    """构建元数据违反已发布契约。"""


def _source_version() -> str:
    """从 Hatchling 使用的源文件读取字面量版本，避免导入运行时模块。"""
    tree = ast.parse(VERSION_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(
            node.value.value, str
        ):
            return node.value.value
    raise ValidationError(f"Literal __version__ not found in {VERSION_PATH}")


def _read_wheel_metadata(dist_dir: Path, version: str) -> Message:
    wheel_pattern = f"catia_autoblade-{version}-*.whl"
    wheels = sorted(dist_dir.glob(wheel_pattern))
    if len(wheels) != 1:
        raise ValidationError(
            f"Expected exactly one {wheel_pattern} in {dist_dir}, found {len(wheels)}"
        )

    with ZipFile(wheels[0]) as archive:
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_names) != 1:
            raise ValidationError(
                f"Expected one wheel METADATA file, found {len(metadata_names)}"
            )
        content = archive.read(metadata_names[0]).decode("utf-8")
    return Parser().parsestr(content)


def _read_sdist_metadata(dist_dir: Path, version: str) -> Message:
    sdist = dist_dir / f"catia_autoblade-{version}.tar.gz"
    if not sdist.is_file():
        raise ValidationError(f"Expected sdist not found: {sdist}")

    with tarfile.open(sdist, "r:gz") as archive:
        metadata_members = [
            member
            for member in archive.getmembers()
            if member.name.endswith("/PKG-INFO")
        ]
        if len(metadata_members) != 1:
            raise ValidationError(
                f"Expected one sdist PKG-INFO file, found {len(metadata_members)}"
            )
        extracted = archive.extractfile(metadata_members[0])
        if extracted is None:
            raise ValidationError("Unable to read sdist PKG-INFO")
        content = extracted.read().decode("utf-8")
    return Parser().parsestr(content)


def _validate_metadata(metadata: Message, version: str, artifact: str) -> None:
    """验证 wheel 与 sdist 必须一致的核心元数据和 Windows 支持声明。"""
    expected_headers = {
        "Name": EXPECTED_PROJECT_NAME,
        "Version": version,
        "License-File": "LICENSE",
    }
    for header, expected in expected_headers.items():
        if metadata.get(header) != expected:
            raise ValidationError(
                f"{artifact} {header} mismatch: {metadata.get(header)!r} != {expected!r}"
            )

    requires_python = metadata.get("Requires-Python", "")
    if set(requires_python.split(",")) != set(EXPECTED_REQUIRES_PYTHON.split(",")):
        raise ValidationError(
            f"{artifact} Requires-Python mismatch: {requires_python!r} != "
            f"{EXPECTED_REQUIRES_PYTHON!r}"
        )

    classifiers = set(metadata.get_all("Classifier", []))
    required_classifiers = {
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.14",
    }
    missing_classifiers = required_classifiers - classifiers
    if missing_classifiers:
        raise ValidationError(
            f"{artifact} missing classifiers: {sorted(missing_classifiers)}"
        )
    if "Operating System :: OS Independent" in classifiers:
        raise ValidationError(f"{artifact} must not claim OS Independent")

    requirements = metadata.get_all("Requires-Dist", [])
    if not any(
        requirement.startswith("pywin32==311;")
        and "sys_platform == 'win32'" in requirement
        for requirement in requirements
    ):
        raise ValidationError(
            f"{artifact} does not declare the supported pywin32 requirement: "
            f"{requirements}"
        )

    project_urls = metadata.get_all("Project-URL", [])
    for label in ("Documentation", "Issues", "Repository"):
        if not any(url.startswith(f"{label}, https://") for url in project_urls):
            raise ValidationError(f"{artifact} missing HTTPS Project-URL: {label}")

    relative_targets = _relative_markdown_targets(metadata.get_payload())
    if relative_targets:
        raise ValidationError(
            f"{artifact} long description contains relative links: {relative_targets}"
        )


def _validate_pyproject() -> None:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    project = data["project"]
    if project["name"] != EXPECTED_PROJECT_NAME:
        raise ValidationError("pyproject project name changed unexpectedly")
    if project["requires-python"] != EXPECTED_REQUIRES_PYTHON:
        raise ValidationError("pyproject requires-python differs from support policy")
    if project.get("dynamic") != ["version"]:
        raise ValidationError("pyproject must keep dynamic versioning")
    version_path = data["tool"]["hatch"]["version"]["path"]
    if version_path != "src/catia_autoblade/__init__.py":
        raise ValidationError("Hatchling version path differs from source contract")


def _validate_readme_links() -> None:
    """PyPI 长描述不能依赖 GitHub 仓库上下文解析相对 Markdown 链接。"""
    content = README_PATH.read_text(encoding="utf-8")
    relative_targets = _relative_markdown_targets(content)
    if relative_targets:
        raise ValidationError(
            f"README contains relative long-description links: {relative_targets}"
        )


def _relative_markdown_targets(content: str) -> list[str]:
    """返回需要仓库上下文才能解析的 Markdown 链接目标。"""
    relative_targets: list[str] = []
    for target in re.findall(r"\]\(([^)]+)\)", content):
        normalized = target.strip().lower()
        if not normalized.startswith(("https://", "http://", "mailto:", "#")):
            relative_targets.append(target)
    return relative_targets


def _validate_cli_version(version: str) -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "catia_autoblade.cli", "--version"],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    expected = f"catia-autoblade {version}"
    if result.returncode != 0 or result.stdout.strip() != expected:
        raise ValidationError(
            "CLI version mismatch: "
            f"code={result.returncode}, stdout={result.stdout!r}, stderr={result.stderr!r}"
        )


def _validate_git_tag(version: str, *, require_tag: bool) -> None:
    result = subprocess.run(
        ["git", "tag", "--points-at", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(f"Unable to inspect Git tags: {result.stderr.strip()}")

    version_tags = {
        tag
        for tag in result.stdout.splitlines()
        if re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", tag)
    }
    expected_tags = {version, f"v{version}"}
    mismatched = version_tags - expected_tags
    if mismatched:
        raise ValidationError(
            f"HEAD version tags do not match {version}: {sorted(mismatched)}"
        )
    if require_tag and not version_tags:
        raise ValidationError(
            f"Release validation requires HEAD tag {version!r} or {f'v{version}'!r}"
        )


def validate(dist_dir: Path, *, require_tag: bool) -> None:
    version = _source_version()
    _validate_pyproject()
    _validate_readme_links()
    _validate_cli_version(version)
    _validate_git_tag(version, require_tag=require_tag)
    _validate_metadata(_read_wheel_metadata(dist_dir, version), version, "wheel")
    _validate_metadata(_read_sdist_metadata(dist_dir, version), version, "sdist")
    print(
        f"Distribution metadata valid: {EXPECTED_PROJECT_NAME} {version} "
        f"(tag required: {require_tag})"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=PROJECT_ROOT / "dist",
        help="Directory containing one wheel and one sdist for the source version.",
    )
    parser.add_argument(
        "--require-tag",
        action="store_true",
        help="Require HEAD to carry a version tag matching the source version.",
    )
    args = parser.parse_args()
    try:
        validate(args.dist_dir.resolve(), require_tag=args.require_tag)
    except ValidationError as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
