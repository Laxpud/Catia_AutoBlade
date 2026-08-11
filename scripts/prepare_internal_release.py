"""验证带标签的候选产物并生成内部发布清单、说明和 SHA-256。"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

try:
    from .validate_distribution import ValidationError, _source_version, validate
except ImportError:
    # 直接以 ``python scripts/prepare_internal_release.py`` 执行时，scripts
    # 不是包；测试导入则使用上面的相对路径，两种入口复用同一校验实现。
    from validate_distribution import ValidationError, _source_version, validate


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValidationError(
            f"git {' '.join(arguments)} failed: {result.stderr.strip()}"
        )
    return result.stdout.strip()


def _validate_clean_tagged_source(version: str) -> tuple[str, str]:
    status = _git("status", "--porcelain", "--untracked-files=all")
    if status:
        raise ValidationError(
            "Internal releases must be prepared from a clean tagged checkout."
        )
    commit = _git("rev-parse", "HEAD")
    tags = _git("tag", "--points-at", "HEAD").splitlines()
    expected = {version, f"v{version}"}
    matching = sorted(expected & set(tags))
    if len(matching) != 1:
        raise ValidationError(
            f"Expected exactly one release tag in {sorted(expected)}, found {matching}."
        )
    return commit, matching[0]


def _read_validation_record(path: Path, version: str, commit: str) -> dict:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValidationError(f"Invalid validation record {path}: {error}") from error
    if record.get("version") != version or record.get("commit") != commit:
        raise ValidationError(
            "Validation record version/commit does not match the tagged source."
        )
    required_passes = ("repository_check", "installed_wheel_smoke")
    missing = [name for name in required_passes if record.get(name) != "pass"]
    if record.get("dirty_worktree") is not False:
        missing.append("dirty_worktree must be false")
    catia = record.get("catia_smoke", {})
    required_catia = (
        "date",
        "windows",
        "python",
        "pywin32",
        "catia",
        "input_model",
        "catpart_result",
        "step_result",
        "feature_tree",
        "new_cnext_processes",
    )
    missing.extend(
        f"catia_smoke.{name}"
        for name in required_catia
        if name not in catia
    )
    if catia.get("new_cnext_processes") != 0:
        missing.append("catia_smoke.new_cnext_processes must be 0")
    for name in ("catpart_result", "step_result", "feature_tree"):
        if not str(catia.get(name, "")).lower().startswith("pass"):
            missing.append(f"catia_smoke.{name} must start with 'pass'")
    if missing:
        raise ValidationError(
            f"Validation record is incomplete or failed: {missing}"
        )
    return record


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_release(
    dist_dir: Path,
    validation_record: Path,
    release_notes: Path,
) -> Path:
    version = _source_version()
    commit, tag = _validate_clean_tagged_source(version)
    validate(dist_dir, require_tag=True)
    record = _read_validation_record(validation_record, version, commit)
    if not release_notes.is_file():
        raise ValidationError(f"Release notes not found: {release_notes}")

    wheel_candidates = sorted(dist_dir.glob(f"catia_autoblade-{version}-*.whl"))
    sdist = dist_dir / f"catia_autoblade-{version}.tar.gz"
    if len(wheel_candidates) != 1 or not sdist.is_file():
        raise ValidationError("Expected one wheel and one sdist before packaging.")
    notes_target = dist_dir / f"catia-autoblade-{version}-release-notes.md"
    shutil.copyfile(release_notes, notes_target)

    deliverables = [wheel_candidates[0], sdist, notes_target]
    checksums = {path.name: _sha256(path) for path in deliverables}
    checksum_path = dist_dir / "SHA256SUMS.txt"
    checksum_path.write_text(
        "".join(
            f"{digest}  {name}\n" for name, digest in sorted(checksums.items())
        ),
        encoding="utf-8",
        newline="\n",
    )
    checksums[checksum_path.name] = _sha256(checksum_path)

    manifest = {
        "schema": "catia-autoblade-internal-release/v1",
        "version": version,
        "tag": tag,
        "commit": commit,
        "channel": "internal-preview-wheel",
        "support_baseline": {
            "windows": "Windows 11 x64",
            "python": "CPython 3.14.x x64",
            "pywin32": "311",
            "catia": "CATIA P3 V5-6R2020",
        },
        "validation": record,
        "sha256": checksums,
        "rollback": (
            "Withdraw the affected artifact set, restore the previous versioned "
            "wheel, and restore config.toml from its migration backup if needed."
        ),
    }
    manifest_path = dist_dir / f"catia-autoblade-{version}-internal-release.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Internal release manifest: {manifest_path}")
    print(f"Checksums: {checksum_path}")
    return manifest_path


def main() -> int:
    version = _source_version()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, default=PROJECT_ROOT / "dist")
    parser.add_argument("--validation-record", type=Path, required=True)
    parser.add_argument(
        "--release-notes",
        type=Path,
        default=PROJECT_ROOT / "docs" / "release-notes" / f"v{version}.md",
    )
    args = parser.parse_args()
    try:
        prepare_release(
            args.dist_dir.resolve(),
            args.validation_record.resolve(),
            args.release_notes.resolve(),
        )
    except ValidationError as error:
        print(f"[ERROR] {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
