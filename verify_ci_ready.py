#!/usr/bin/env python
"""
Verify that all CI checks will pass before pushing to GitHub.
This mimics the GitHub Actions CI pipeline checks.
"""
import subprocess
import sys
import os

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70)

def print_section(text):
    """Print a formatted section header."""
    print("\n" + text)
    print("-" * 70)

def check_files_exist():
    """Verify required files exist."""
    print_section("Checking required files...")
    
    required_files = [
        "backend/__init__.py",
        "backend/schemas/__init__.py",
        "backend/routes/__init__.py",
        "tests/__init__.py",
        "tests/api/__init__.py",
        "tests/unit/__init__.py",
        "config/config.yaml",
        "config/label_map.yaml",
        ".github/workflows/ci.yml",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[MISSING] {file_path}")
            all_exist = False
    
    return all_exist

def run_ruff():
    """Run Ruff linting."""
    print_section("Running Ruff linting...")
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[OK] All Ruff checks passed!")
        return True
    else:
        print("[FAIL] Ruff found issues:")
        print(result.stdout)
        print("\nRun 'python -m ruff check . --fix' to auto-fix issues")
        return False

def run_pytest():
    """Run pytest test suite."""
    print_section("Running pytest test suite...")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print("\n[OK] All tests passed!")
        return True
    else:
        print("\n[FAIL] Some tests failed")
        if result.stderr:
            print(result.stderr)
        return False

def main():
    """Run all verification checks."""
    print_header("CI PIPELINE VERIFICATION")
    print("\nThis script verifies your code will pass GitHub Actions CI checks.")
    
    # Track results
    results = {}
    
    # Check files
    results['files'] = check_files_exist()
    
    # Run Ruff
    results['ruff'] = run_ruff()
    
    # Run tests
    results['pytest'] = run_pytest()
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"{status} {check.upper()}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("SUCCESS: All checks passed!".center(70))
        print("Your code is ready to push to GitHub.".center(70))
        print("=" * 70)
        return 0
    else:
        print("FAILURE: Some checks failed.".center(70))
        print("Please fix the issues before pushing.".center(70))
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
