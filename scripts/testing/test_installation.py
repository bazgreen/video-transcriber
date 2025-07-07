#!/usr/bin/env python3
"""
Video Transcriber Installation Test Suite
Automates testing of both minimal and full installations
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def print_header():
    """Print test header"""
    print("\n" + "=" * 60)
    print("🧪 Video Transcriber - Installation Test Suite")
    print("=" * 60 + "\n")


def run_cleanup():
    """Run the cleanup script"""
    print("🧹 Running cleanup script...")
    result = subprocess.run(
        ["python3", "clean_environment.py"], input="y\n", text=True, capture_output=True
    )
    if result.returncode == 0:
        print("✅ Cleanup completed successfully")
        return True
    else:
        print("❌ Cleanup failed")
        print(result.stderr)
        return False


def test_installation(installation_type):
    """Test an installation type"""
    print(f"\n🧪 Testing {installation_type.upper()} installation...")

    choice = "1" if installation_type == "minimal" else "2"

    # Run the installation
    result = subprocess.run(
        ["python3", "scripts/setup/setup_and_run.py"],
        input=f"{choice}\ny\n",  # Choose installation type and continue without FFmpeg if needed
        text=True,
        capture_output=True,
        timeout=600,  # 10 minute timeout
    )

    # Check if installation was successful
    if "Installation Complete!" in result.stdout:
        print(f"✅ {installation_type.capitalize()} installation completed")

        # Test if the application can start
        print("🔍 Testing application startup...")
        app_test = subprocess.run(
            [".venv/bin/python", "-c", "import main; print('Import successful')"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if app_test.returncode == 0:
            print("✅ Application imports successfully")
            return True
        else:
            print("❌ Application import failed")
            print(app_test.stderr)
            return False
    else:
        print(f"❌ {installation_type.capitalize()} installation failed")
        print(result.stderr)
        return False


def test_package_availability(installation_type):
    """Test if required packages are available"""
    print(f"\n🔍 Testing package availability for {installation_type} installation...")

    # Basic packages (both minimal and full should have these)
    basic_packages = [
        "whisper",
        "flask",
        "flask_socketio",
        "flask_login",
        "torch",
        "numpy",
    ]

    # AI packages (only full installation should have these)
    ai_packages = ["textblob", "sklearn", "spacy"]

    # Export packages (only full installation should have these)
    export_packages = ["reportlab", "docx"]

    failed_imports = []

    # Test basic packages
    for package in basic_packages:
        test_result = subprocess.run(
            [".venv/bin/python", "-c", f"import {package}; print('{package} OK')"],
            capture_output=True,
            text=True,
        )
        if test_result.returncode != 0:
            failed_imports.append(package)

    # Test AI packages (should only work for full installation)
    if installation_type == "full":
        for package in ai_packages:
            test_result = subprocess.run(
                [".venv/bin/python", "-c", f"import {package}; print('{package} OK')"],
                capture_output=True,
                text=True,
            )
            if test_result.returncode != 0:
                failed_imports.append(package)

        # Test export packages
        for package in export_packages:
            test_result = subprocess.run(
                [".venv/bin/python", "-c", f"import {package}; print('{package} OK')"],
                capture_output=True,
                text=True,
            )
            if test_result.returncode != 0:
                failed_imports.append(package)

    if failed_imports:
        print(f"❌ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print("✅ All expected packages available")
        return True


def test_upgrade_path():
    """Test upgrading from minimal to full"""
    print("\n🔄 Testing upgrade path (minimal → full)...")

    # First install minimal
    if not run_cleanup():
        return False

    if not test_installation("minimal"):
        return False

    # Test upgrade script
    print("🔄 Running upgrade script...")
    upgrade_result = subprocess.run(
        [".venv/bin/python", "install_ai_features.py"],
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
    )

    if upgrade_result.returncode == 0:
        print("✅ Upgrade completed successfully")

        # Test if AI packages are now available
        ai_test = subprocess.run(
            [
                ".venv/bin/python",
                "-c",
                "import textblob, sklearn, spacy; print('AI packages OK')",
            ],
            capture_output=True,
            text=True,
        )

        if ai_test.returncode == 0:
            print("✅ AI packages available after upgrade")
            return True
        else:
            print("❌ AI packages not available after upgrade")
            return False
    else:
        print("❌ Upgrade failed")
        print(upgrade_result.stderr)
        return False


def main():
    """Main test function"""
    print_header()

    test_results = {}

    # Test minimal installation
    if run_cleanup():
        test_results["minimal_install"] = test_installation("minimal")
        if test_results["minimal_install"]:
            test_results["minimal_packages"] = test_package_availability("minimal")
        else:
            test_results["minimal_packages"] = False
    else:
        test_results["minimal_install"] = False
        test_results["minimal_packages"] = False

    # Test full installation
    if run_cleanup():
        test_results["full_install"] = test_installation("full")
        if test_results["full_install"]:
            test_results["full_packages"] = test_package_availability("full")
        else:
            test_results["full_packages"] = False
    else:
        test_results["full_install"] = False
        test_results["full_packages"] = False

    # Test upgrade path
    test_results["upgrade_path"] = test_upgrade_path()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title():<25} {status}")

    all_passed = all(test_results.values())

    if all_passed:
        print("\n🎉 All tests passed! Installation system is working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the installation system.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        sys.exit(1)
