# TESTS

This document explains how to set up and run the pytest project's tests locally, and provides tips for troubleshooting common issues.

## Prerequisites

- Python >= 3.10 (3.10–3.13 supported; 3.14 pre-release may work)
- pip
- tox (recommended for running the full test matrix)

## Setup

Create and activate a virtual environment, then install dependencies:

```
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate

# Install pytest in editable mode and optional dev deps
pip install -e .
pip install tox
```

## Running tests

You can run tests either via tox (recommended) or directly with pytest.

- Via tox (recommended):
  - List available environments: `tox -l -v`
  - Run default Python envs: `tox -e py`
  - Run a specific version (example): `tox -e py313`

- Direct with pytest:
  - `pytest`

## Coverage (optional)

- Via tox: `tox -e coverage`
- Direct: `pytest --cov --cov-report=xml`

## Troubleshooting

- Some CI jobs use specialized tox environments (doctesting, twisted/asynctest variants). Local runs can use the default envs unless you need to validate those specific jobs.
- When testing plugins with `pytester`, ensure filesystem paths are accessible; path differences on Windows can affect tests.
- If `tox` fails due to missing interpreters, install the required Python versions or run `pytest` directly in your active environment.
- Ensure your virtual environment is active when installing and running.

## Notes

- This file documents local test execution only; it does not modify the test suite or source code.
