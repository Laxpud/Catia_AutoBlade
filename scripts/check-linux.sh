#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_temp="$(mktemp -d "$project_root/.test-tmp-check-linux.XXXXXX")"

cleanup() {
    # pytest basetemp 只允许落在这次检查创建的固定前缀目录内。
    case "$test_temp" in
        "$project_root"/.test-tmp-check-linux.*)
            rm -rf -- "$test_temp"
            ;;
        *)
            echo "Refusing to remove unexpected check path: $test_temp" >&2
            ;;
    esac
}
trap cleanup EXIT

cd "$project_root"
uv sync --frozen --extra dev
uv run --frozen --extra dev pytest -q \
    --basetemp="$test_temp/pytest" -p no:cacheprovider
uv run --frozen --extra dev ruff check src tests scripts
uv build --clear

source_version="$(
    uv run --frozen python -c \
        'from autoblade import __version__; print(__version__)'
)"
shopt -s nullglob
wheel_candidates=("$project_root"/dist/autoblade-"$source_version"-*.whl)
if [[ ${#wheel_candidates[@]} -ne 1 ]]; then
    echo "Expected exactly one AutoBlade wheel for installed smoke testing." >&2
    exit 1
fi

bash "$project_root/scripts/smoke_installed_wheel.sh" "${wheel_candidates[0]}"
uv run --frozen python scripts/validate_distribution.py
