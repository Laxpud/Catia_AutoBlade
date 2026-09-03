# AutoBlade unreleased changes

These changes are not an approved artifact set and remain tied to the current
development branch until a new package version and release record are created.

## Added

- audited provenance and direct redistribution permission for the real
  89-section example and its three Hannnk airfoils;
- a manifest-backed built-in airfoil library with stable IDs, point counts,
  modification records, and SHA-256 values;
- `autoblade init --with-airfoil-library` for explicitly copying the complete
  audited catalog without blade section examples;
- clean installed-wheel smoke coverage for both example-only and
  library-only workspaces.

## Breaking changes

- renamed the distribution and Python namespace to `autoblade` with no
  `catia_autoblade` shim; environments containing the legacy distribution now
  fail with an explicit uninstall-first error;
- moved the canonical user configuration directory to `autoblade`, with a
  warning-only legacy fallback, new-directory precedence, and an explicit
  preview/backup/apply migration that preserves resolved input/output roots;
- renamed the user-visible `section_params` collection to `blade_sections`
  across workspace directories, CSV basenames, configuration, Python APIs,
  task models, scripts, and documentation;
- raised the configuration schema to `3.0.0`; explicit migration renames the
  old field and default value after creating a backup, but does not move
  external workspace data;
- raised the sweep manifest schema to version 2 and renamed its selection and
  job fields to `blade_sections`;
- retained CLI `--section`, single-row `section` domain names, and output
  template fields because they describe one section rather than the collection.

## Distribution boundary

- updated wheel/sdist roots, console metadata, internal release artifact names,
  and the release manifest identity to AutoBlade;
- added a Linux check and clean non-editable wheel smoke covering CLI,
  package/core import, Parser, Planner, resources, and the Windows-only
  `pywin32` marker without claiming a Linux modeling backend;
- unaudited `sc1095*`, `sd7032_sharp`, and `naca0012_sharp` repository inputs
  remain outside the wheel library;
- the dense 1,000-point profile remains a maintainer regression asset;
- the catalog ships with the package version and has no independent data
  version.
