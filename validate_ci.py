#!/usr/bin/env python3
"""
Simple validation script for CI/CD pipeline.
This script validates basic configuration and module imports without requiring
heavy dependencies like Whisper and FFmpeg.
"""

import json
import os
import sys
from pathlib import Path


def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        # Basic utility imports
        from src.config import validate_configurations
        from src.utils.memory import get_memory_status_safe
        from src.utils.session import validate_session_access
        from src.utils.validation import validate_request_data

        print("✓ Basic imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False


def test_config_validation():
    """Test configuration validation."""
    try:
        from src.config import validate_configurations

        validate_configurations()
        print("✓ Configuration validation successful")
        return True
    except Exception as e:
        print(f"✗ Configuration validation failed: {e}")
        return False


def test_directory_structure():
    """Test that required directories exist."""
    required_dirs = [
        "src",
        "src/config",
        "src/models",
        "src/routes",
        "src/services",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/config",
    ]

    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)

    if missing_dirs:
        print(f"✗ Missing directories: {missing_dirs}")
        return False
    else:
        print("✓ Directory structure validation successful")
        return True


def test_config_files():
    """Test that configuration files exist and are valid."""
    config_files = ["data/config/keywords_config.json"]

    for config_file in config_files:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"✗ Missing config file: {config_file}")
            return False

        try:
            with open(config_path, "r") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON in {config_file}: {e}")
            return False

    print("✓ Configuration files validation successful")
    return True


def main():
    """Run all validation tests."""
    print("Running CI validation tests...")
    print("=" * 50)

    tests = [
        test_directory_structure,
        test_config_files,
        test_basic_imports,
        test_config_validation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
        print()

    print("=" * 50)
    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"✓ All {total} validation tests passed!")
        return 0
    else:
        print(f"✗ {total - passed}/{total} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
