# CATIA AutoBlade

[English](README.md) | [简体中文](docs/README.cn.md)

CATIA AutoBlade is a Windows command-line tool that builds 3D blade models in CATIA V5 from airfoil point clouds and spanwise section parameters. It drives CATIA through its COM automation interface and exports both native `CATPart` files and STEP models.

## Status

The project is an early working prototype. The single-airfoil workflow has been exercised successfully with CATIA P3 V5-6R2020, and batch generation is available as a Cartesian product of airfoil files and section-parameter files.

The current implementation uses one airfoil for every section of a blade. Per-section airfoil selection, including the optional `airfoil` column found in newer input data, is not supported yet.

The stable single-airfoil milestone is complete. The current milestone extends the geometry model to select different airfoils across blade sections. See [TODO.md](TODO.md) for the active acceptance checklist.

## Scope

CATIA AutoBlade currently provides:

- airfoil spline creation from CSV point clouds;
- section scaling, translation, and twist;
- sharp and blunt trailing-edge handling;
- guided loft creation and surface closing;
- native CATIA and STEP export;
- single-model and batch CLI workflows.

It is not a general-purpose airfoil editor, aerodynamic solver, or platform-independent CAD backend.

## Requirements

- Windows
- Python 3.14 or later
- CATIA V5 with a working COM automation interface
- [`uv`](https://docs.astral.sh/uv/) for the documented environment workflow

The project has been used with CATIA P3 V5-6R2020. Other CATIA V5 releases have not been documented as verified environments.

## Installation

```powershell
uv sync
uv pip install -e .
```

## Quick start

List available input files:

```powershell
uv run autoblade list
```

Create one blade:

```powershell
uv run autoblade create --airfoil sc1095.csv --section section_params-1.csv
```

Create all selected combinations:

```powershell
uv run autoblade batch --airfoil sc1095.csv
```

Use `--interactive` with `create` or `batch` to select inputs at the prompt. Generated files use the directory and naming template from `config.toml`; an explicit `--output` overrides the configured output directory.

The standalone entry points accept the same options as their corresponding subcommands:

```powershell
uv run autoblade-create --airfoil sc1095.csv --section section_params-1.csv
uv run autoblade-batch --airfoil sc1095.csv
```

## Input overview

By default, airfoil CSV files belong in `input/airfoils/` and section parameter CSV files in `input/section_params/`; both locations are configurable. Coordinates, units, ordering, required columns, and current validation limits are documented in [Input data formats](docs/input-formats.md).

## Documentation

- [Technical documentation index](docs/index.md)
- [Architecture](docs/architecture.md)
- [Input data formats](docs/input-formats.md)
- [Runtime configuration](docs/configuration.md)
- [Automated testing](docs/testing.md)
- [Active work and acceptance criteria](TODO.md)

## Development checks

The automated tests use COM fakes and do not require CATIA to be installed or running:

```powershell
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
```

## License

[MIT](LICENSE)
