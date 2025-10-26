# TESTS

This document describes how to run pytest's tests locally with a tox-first workflow, and when to use direct pytest runs. It also clarifies coverage collection and PyPy support.

## Prerequisites

- Python >= 3.10 (CPython 3.10–3.14 supported)
- pip
- tox (recommended runner for the full matrix)

## Tox-first workflow (recommended)

Using tox isolates environments and mirrors CI closely:

- List all environments: `tox -l`
- Run tests for the default Python selector: `tox -e py`
- Run a specific Python version (example): `tox -e py313`
- Run linters via pre-commit: `tox -e linting`
- Run on PyPy: `tox -e pypy3`

Specialized environments exist for specific checks (for example: `doctesting`, `xdist`, `twisted24`, `twisted25`, `asynctest`, `plugins`, etc.). Use `tox -l` to discover the full list and pick what you need.

## Coverage

Coverage is configured via `.coveragerc` and collected with `coverage.py`. Tox environments that include the `coverage` factor enable this automatically.

- Typical single-environment run: `tox -e py313-coverage`
  - Runs tests under coverage (`coverage run -m pytest`) and reports using `.coveragerc` (paths, branch, include rules).
- To exercise multiple versions under coverage, run each desired `pyXY-coverage` environment.
- After multi-env runs, `coverage combine` is handled by the tox `coverage` commands; path mapping is defined in `.coveragerc`.

Direct coverage (without tox):

- Preferred (matches project setup):
  - `coverage run -m pytest`
  - `coverage report -m`
- Note: the core test suite does not require `pytest-cov`. Some plugin-integration checks under `testenv:plugins` intentionally use `pytest --cov` for that scenario. For general local runs, prefer `coverage.py`. See https://coverage.readthedocs.io/ for usage.

## Direct pytest workflow (when to use editable installs)

You generally do not need a manual virtual environment when using tox. Use a direct pytest workflow if you want a lighter loop in a single interpreter or to debug in your own environment.

Steps:

```
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install pytest in editable mode with dev extras to match tox deps
python -m pip install -U pip
pip install -e .[dev]
```

Editable installs are useful when:

- Running `pytest` directly (outside tox) so source edits are immediately importable.
- Working on tooling/docs where imports should reflect local changes.

Then run tests:

```
pytest
```

## Troubleshooting

- If `tox` cannot find a requested interpreter, install that Python version or select an available env from `tox -l`.
- Some CI-only jobs use specialized envs; you usually don't need to run them locally unless touching related areas.
- When testing plugins with `pytester`, consider platform/path differences (e.g., Windows paths) that may affect tests.
- Ensure your virtual environment is active when running direct installs or pytest runs.

## Notes

- PyPy is supported; use `tox -e pypy3` to exercise it locally.
- This file documents local test execution only; it does not modify the test suite or source code.
