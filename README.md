# CATIA AutoBlade

[English](https://github.com/Laxpud/catia-autoblade/blob/main/README.md) | [简体中文](https://github.com/Laxpud/catia-autoblade/blob/main/docs/README.cn.md)

CATIA AutoBlade is a Windows command-line tool that builds 3D blade models in CATIA V5 from airfoil point clouds and spanwise section parameters. It drives CATIA through its COM automation interface and exports both native `CATPart` files and STEP models.

## Status

The project is an early working prototype. The single-airfoil workflow has been exercised successfully with CATIA P3 V5-6R2020. A six-column section file is a template that requires one explicit airfoil; a section file with an `airfoil` column is one self-contained multi-airfoil model definition. Batch runs create one job per selected section definition and do not perform implicit parameter combinations. The separate `sweep` workflow creates only the Cartesian product of explicitly selected airfoils and six-column templates.

Per-section airfoil parsing, validation, deduplicated base-geometry creation, and section selection are implemented. The 89-section sample using three different point counts has completed Loft, solid closing, CATPart saving, and STEP AP242 export with CATIA P3 V5-6R2020.

The stable single-airfoil and spanwise multi-airfoil milestones are complete. The repository now provides auditable wheel/sdist manifests, external workspace initialization, clean-environment wheel smoke tests, configuration migration safeguards, diagnostics, and a gated internal release workflow. A particular wheel is supported only when it is delivered as a complete tagged artifact set with SHA-256 values and real CATIA validation evidence. No public package-index or standalone executable release is supported. See the [distribution scope and support policy](https://github.com/Laxpud/catia-autoblade/blob/main/docs/distribution-scope.md).

## Scope

CATIA AutoBlade currently provides:

- airfoil spline creation from CSV point clouds;
- per-section airfoil selection with unique-profile reuse;
- section scaling, translation, and twist;
- sharp and blunt trailing-edge handling;
- guided loft creation and surface closing;
- native CATIA and STEP export;
- single-model, non-combinatorial batch, and explicit parameter-sweep CLI workflows;
- stable JSON sweep manifests and CATIA-free dry runs.

It is not a general-purpose airfoil editor, aerodynamic solver, or platform-independent CAD backend.

## Requirements

- Windows 11 x64
- CPython 3.14 x64; the currently verified interpreter is Python 3.14.4
- `pywin32` 311
- CATIA P3 V5-6R2020 with a working COM automation interface and the required licenses
- [`uv`](https://docs.astral.sh/uv/) for the documented environment workflow

This is the only currently verified preview baseline. Other Windows, Python, `pywin32`, processor-architecture, and CATIA combinations are unverified rather than implicitly supported. CATIA itself, its licenses, and COM registration are external prerequisites and are not included in this project. See the [distribution scope and support policy](https://github.com/Laxpud/catia-autoblade/blob/main/docs/distribution-scope.md) for the evidence and channel boundaries.

Install `uv` on Windows with WinGet:

```powershell
winget install --id=astral-sh.uv -e
```

## Installation

Authorized internal preview artifacts are installed directly from their versioned wheel. Verify the supplied SHA-256 before installation:

```powershell
uv venv .venv --python 3.14
uv pip install --python .venv\Scripts\python.exe .\catia_autoblade-0.2.0-py3-none-any.whl
.\.venv\Scripts\Activate.ps1
autoblade init C:\Engineering\blade-workspace --with-examples
```

`--with-examples` installs the validated 89-section multi-airfoil blade example
and its three referenced airfoils into the external workspace.

Public PyPI installation is not supported. Maintainers working from a source checkout use:

```powershell
uv sync
uv pip install -e .
```

Installation, workspace, upgrade, uninstall, and rollback details are in [Installation, workspaces, and upgrades](https://github.com/Laxpud/catia-autoblade/blob/main/docs/installation.md).

## Quick start

Open the menu in an interactive terminal:

```powershell
uv run autoblade
```

For scripts, list available input files:

```powershell
uv run autoblade list
```

Diagnose the installed environment without starting or attaching to CATIA:

```powershell
uv run autoblade doctor
```

Create one blade:

```powershell
uv run autoblade create --airfoil sc1095.csv --section section_params-1.csv
```

Create the repository multi-airfoil sample without a fallback `--airfoil`:

```powershell
uv run autoblade create --section section_params-multi-airfoil.csv
```

Use `--keep-failed-part` to save a `*_failed.CATPart` for debugging modeling
failures.

Build every discovered section definition; the explicit airfoil binds all six-column templates, while self-contained files keep their per-section references:

```powershell
uv run autoblade batch --airfoil sc1095.csv
```

Preview an explicit 2 × 2 Cartesian product without starting CATIA:

```powershell
uv run autoblade sweep --airfoil sc1095.csv --airfoil sd7032_sharp.csv `
  --section section_params-1.csv --section section_params-2.csv --dry-run
```

Detailed options, interactive behavior, standalone compatibility entry points, previews, overwrite rules, and exit codes are documented in the [CLI reference](https://github.com/Laxpud/catia-autoblade/blob/main/docs/cli.md).

## Input overview

By default, airfoil CSV files belong in `input/airfoils/` and section parameter CSV files in `input/section_params/`; both locations are configurable. Coordinates, units, ordering, required columns, and current validation limits are documented in [Input data formats](https://github.com/Laxpud/catia-autoblade/blob/main/docs/input-formats.md).

## Documentation

- [Technical documentation index](https://github.com/Laxpud/catia-autoblade/blob/main/docs/index.md)
- [CLI reference](https://github.com/Laxpud/catia-autoblade/blob/main/docs/cli.md)
- [Design principles](https://github.com/Laxpud/catia-autoblade/blob/main/docs/design-principles.md)
- [Architecture](https://github.com/Laxpud/catia-autoblade/blob/main/docs/architecture.md)
- [Input data formats](https://github.com/Laxpud/catia-autoblade/blob/main/docs/input-formats.md)
- [Runtime configuration](https://github.com/Laxpud/catia-autoblade/blob/main/docs/configuration.md)
- [Installation, workspaces, and upgrades](https://github.com/Laxpud/catia-autoblade/blob/main/docs/installation.md)
- [Distribution scope and support policy](https://github.com/Laxpud/catia-autoblade/blob/main/docs/distribution-scope.md)
- [Internal preview release and rollback](https://github.com/Laxpud/catia-autoblade/blob/main/docs/releasing.md)
- [Automated testing](https://github.com/Laxpud/catia-autoblade/blob/main/docs/testing.md)
- [Active work and acceptance criteria](https://github.com/Laxpud/catia-autoblade/blob/main/TODO.md)

## Development checks

The automated tests use COM fakes and do not require CATIA to be installed or running:

```powershell
pwsh -File scripts/check.ps1
```

This single entry runs pytest, Ruff, wheel/sdist builds, and distribution metadata validation. See [Automated testing](https://github.com/Laxpud/catia-autoblade/blob/main/docs/testing.md) for individual diagnostic commands and release-tag validation.

## License

[MIT](https://github.com/Laxpud/catia-autoblade/blob/main/LICENSE)
