# Running CI Checks Locally

This guide helps you run the same checks that GitHub Actions runs, so you can verify your changes before pushing.

## Prerequisites

Make sure you have all development dependencies installed:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run All CI Checks

### Option 1: Use the provided test runner (Windows)

Run the batch file:
```cmd
run_tests.bat
```

Or run the Python script:
```bash
python run_all_tests.py
```

### Option 2: Run checks individually

#### 1. Run Ruff Linting
```bash
python -m ruff check .
```

To automatically fix issues:
```bash
python -m ruff check . --fix
```

#### 2. Run Test Suite
```bash
python -m pytest tests/ -v
```

Or with coverage:
```bash
python -m pytest tests/ -v --cov=src --cov=backend
```

## CI Pipeline Workflow

The GitHub Actions CI pipeline runs two jobs:

### 1. Python Quality Check (`python-quality`)
- Sets up Python 3.11
- Installs dependencies
- Runs Ruff code quality check
- Runs pytest test suite

### 2. Frontend Build Verification (`frontend-build`)
- Sets up Node.js 20
- Installs npm dependencies
- Builds production bundle

## Common Issues

### Ruff Formatting Issues
If you see whitespace warnings (W293), run:
```bash
python -m ruff check . --fix
```

### Import Errors
Make sure all packages have `__init__.py` files:
- `backend/__init__.py`
- `backend/routes/__init__.py`
- `backend/schemas/__init__.py`
- `tests/__init__.py`
- `tests/api/__init__.py`
- `tests/unit/__init__.py`

### Test Failures
1. Make sure you're in the project root directory
2. Check that all dependencies are installed
3. Verify config files exist in `config/` directory

## Quick Verification

Run this single command to check everything:
```bash
python -m ruff check . && python -m pytest tests/ -v
```

If both commands succeed (exit code 0), your changes should pass CI!

## What the CI Checks For

✅ **Code Quality (Ruff)**
- PEP 8 style compliance
- Unused imports
- Undefined variables
- Line length (100 characters)
- Trailing whitespace

✅ **Tests (Pytest)**
- All 8 unit and integration tests
- API endpoint functionality
- Configuration file structure
- Model prediction logic

## Related Files

- `.github/workflows/ci.yml` - CI pipeline configuration
- `pyproject.toml` - Ruff and pytest configuration
- `requirements-dev.txt` - Development dependencies
- `CI_PIPELINE_FIXES.md` - Summary of all fixes made
