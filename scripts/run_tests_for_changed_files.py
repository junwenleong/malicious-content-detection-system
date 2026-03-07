#!/usr/bin/env python3
"""
Smart test runner that maps changed files to related tests.

Runs only relevant tests instead of the full suite, with a safety net of
critical integration tests that always run.

Usage:
  python scripts/run_tests_for_changed_files.py
"""

import subprocess
import sys

# Tests that ALWAYS run — cover cross-cutting concerns and critical paths
ALWAYS_RUN = [
    "tests/test_api.py",  # Full API contract (all endpoints)
    "tests/test_circuit_breaker.py",  # Resilience & fallback behavior
    "tests/test_rate_limiter.py",  # Security & abuse prevention
    "tests/test_hmac.py",  # Authentication & signing
    "tests/test_error_handling.py",  # Error propagation & safety
    "tests/test_mocked_predict.py",  # Inference contract & caching
]

# Map source file prefixes to their related test files
FILE_MAP = {
    "src/inference/": [
        "tests/test_mocked_predict.py",
    ],
    "src/utils/policy.py": [
        "tests/test_api.py",  # Policy affects all endpoints
    ],
    "src/api/auth.py": [
        "tests/test_hmac.py",
        "tests/test_api.py",
    ],
    "src/api/middleware.py": [
        "tests/test_rate_limiter.py",
        "tests/test_api.py",
    ],
    "src/utils/circuit_breaker.py": [
        "tests/test_circuit_breaker.py",
    ],
    "src/utils/rate_limiter.py": [
        "tests/test_rate_limiter.py",
    ],
    "src/utils/": [
        "tests/test_error_handling.py",
    ],
    "src/api/routes/": [
        "tests/test_api.py",
    ],
    "src/config.py": [
        "tests/test_api.py",
    ],
}


def get_changed_files() -> set[str]:
    """Get list of changed files from git."""
    try:
        # Get staged + unstaged changes
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        files = set(result.stdout.strip().split("\n"))
        return {f for f in files if f}  # Remove empty strings
    except subprocess.CalledProcessError:
        return set()


def map_files_to_tests(changed_files: set[str]) -> set[str]:
    """Map changed files to their related test files."""
    tests = set(ALWAYS_RUN)  # Always include critical tests

    for changed_file in changed_files:
        # Skip non-Python files
        if not changed_file.endswith(".py"):
            continue

        # Skip test files themselves
        if changed_file.startswith("tests/"):
            continue

        # Check each mapping
        for source_prefix, test_files in FILE_MAP.items():
            if changed_file.startswith(source_prefix):
                tests.update(test_files)
                break

    return tests


def run_tests(test_files: set[str]) -> int:
    """Run the specified test files."""
    if not test_files:
        print("No tests to run")
        return 0

    test_list = sorted(test_files)
    print(f"Running {len(test_list)} test file(s):")
    for test in test_list:
        print(f"  - {test}")
    print()

    cmd = [
        "python",
        "-m",
        "pytest",
        "-q",
        "--tb=short",
        *test_list,
    ]

    result = subprocess.run(cmd)
    return result.returncode


def main() -> int:
    """Main entry point."""
    changed_files = get_changed_files()

    if not changed_files:
        print("No changed files detected")
        return 0

    print(f"Changed files: {len(changed_files)}")
    for f in sorted(changed_files):
        print(f"  - {f}")
    print()

    tests = map_files_to_tests(changed_files)

    if not tests:
        print("No tests mapped; running full suite as safety net")
        return subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=short"]
        ).returncode

    return run_tests(tests)


if __name__ == "__main__":
    sys.exit(main())
