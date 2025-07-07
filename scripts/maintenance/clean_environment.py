#!/usr/bin/env python3
"""
Environment Cleanup Script for Video Transcriber
Resets the environment back to pristine state for fresh installation testing
"""

import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def print_header():
    """Print cleanup header"""
    print("\n" + "=" * 60)
    print("🧹 Video Transcriber - Environment Cleanup")
    print("=" * 60 + "\n")
    print("This script will remove all installation artifacts and reset")
    print("the environment back to a pristine state for fresh testing.")
    print("\n⚠️  WARNING: This will remove:")
    print("   • Virtual environments (.venv, env/, venv*)")
    print("   • Python cache files (__pycache__, *.pyc)")
    print("   • Upload files and results")
    print("   • Log files and temporary data")
    print("   • Development artifacts")
    print("\n📁 Preserved files:")
    print("   • Source code and configuration")
    print("   • README and documentation")
    print("   • Git repository")
    print("\n" + "-" * 60)


def confirm_cleanup():
    """Ask user to confirm the cleanup operation"""
    while True:
        response = (
            input("\n🤔 Are you sure you want to clean the environment? (y/N): ")
            .strip()
            .lower()
        )
        if response in ["", "n", "no"]:
            print("❌ Cleanup cancelled.")
            return False
        elif response in ["y", "yes"]:
            print("✅ Cleanup confirmed.")
            return True
        else:
            print("❌ Please enter 'y' for yes or 'n' for no.")


def kill_running_processes():
    """Kill any running Video Transcriber processes"""
    print("\n🔄 Stopping running processes...")

    try:
        # Kill Python processes running main.py
        if platform.system() == "Windows":
            subprocess.run(
                ["taskkill", "/F", "/IM", "python.exe"],
                capture_output=True,
                check=False,
            )
        else:
            subprocess.run(
                ["pkill", "-f", "python.*main.py"], capture_output=True, check=False
            )
        print("✅ Stopped any running Video Transcriber processes")
    except Exception as e:
        print(f"⚠️  Could not stop processes: {e}")


def remove_virtual_environments():
    """Remove all virtual environment directories"""
    print("\n🗑️  Removing virtual environments...")

    venv_patterns = [
        ".venv",
        "venv",
        "venv311",
        "venv312",
        "venv313",
        "env",
        os.path.join("env", "venv"),
        os.path.join("env", "venv311"),
        os.path.join("env", "venv312"),
        os.path.join("env", "venv313"),
    ]

    removed_count = 0
    for venv_path in venv_patterns:
        if os.path.exists(venv_path):
            try:
                shutil.rmtree(venv_path)
                print(f"  ✅ Removed: {venv_path}")
                removed_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {venv_path}: {e}")

    if removed_count == 0:
        print("  ℹ️  No virtual environments found")
    else:
        print(f"✅ Removed {removed_count} virtual environment(s)")


def remove_python_cache():
    """Remove Python cache files and directories"""
    print("\n🗑️  Removing Python cache files...")

    # Remove __pycache__ directories
    pycache_count = 0
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                pycache_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {pycache_path}: {e}")

    # Remove .pyc files
    pyc_count = 0
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".pyc"):
                pyc_path = os.path.join(root, file)
                try:
                    os.remove(pyc_path)
                    pyc_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to remove {pyc_path}: {e}")

    print(f"  ✅ Removed {pycache_count} __pycache__ directories")
    print(f"  ✅ Removed {pyc_count} .pyc files")


def remove_development_artifacts():
    """Remove development and testing artifacts"""
    print("\n🗑️  Removing development artifacts...")

    artifacts = [
        ".pytest_cache",
        ".mypy_cache",
        ".benchmarks",
        ".coverage",
        "htmlcov",
        ".tox",
        "dist",
        "build",
        "*.egg-info",
        ".eggs",
        "bandit-report.json",
        ".bandit",
    ]

    removed_count = 0
    for artifact in artifacts:
        if artifact.startswith("*"):
            # Handle glob patterns
            import glob

            matches = glob.glob(artifact)
            for match in matches:
                try:
                    if os.path.isdir(match):
                        shutil.rmtree(match)
                    else:
                        os.remove(match)
                    print(f"  ✅ Removed: {match}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to remove {match}: {e}")
        else:
            if os.path.exists(artifact):
                try:
                    if os.path.isdir(artifact):
                        shutil.rmtree(artifact)
                    else:
                        os.remove(artifact)
                    print(f"  ✅ Removed: {artifact}")
                    removed_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to remove {artifact}: {e}")

    if removed_count == 0:
        print("  ℹ️  No development artifacts found")


def clean_data_directories():
    """Clean data directories but preserve structure"""
    print("\n🗑️  Cleaning data directories...")

    data_dirs = [
        "uploads",
        "results",
        "logs",
        "instance",
        "data/uploads",
        "data/results",
    ]

    cleaned_count = 0
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            try:
                # Remove contents but keep the directory
                for item in os.listdir(data_dir):
                    item_path = os.path.join(data_dir, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                print(f"  ✅ Cleaned: {data_dir}/")
                cleaned_count += 1
            except Exception as e:
                print(f"  ❌ Failed to clean {data_dir}: {e}")

    if cleaned_count == 0:
        print("  ℹ️  No data directories found to clean")


def remove_log_files():
    """Remove log files"""
    print("\n🗑️  Removing log files...")

    log_patterns = [
        "*.log",
        "server.log",
        "app.log",
        "error.log",
        "debug.log",
        "logs/*.log",
        "logs/*",
    ]

    removed_count = 0
    import glob

    for pattern in log_patterns:
        matches = glob.glob(pattern)
        for match in matches:
            try:
                if os.path.isfile(match):
                    os.remove(match)
                    print(f"  ✅ Removed: {match}")
                    removed_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {match}: {e}")

    if removed_count == 0:
        print("  ℹ️  No log files found")


def remove_temp_files():
    """Remove temporary files"""
    print("\n🗑️  Removing temporary files...")

    temp_patterns = [
        "tmp*",
        "temp*",
        ".tmp*",
        "*.tmp",
        "*.temp",
        "*~",
        ".DS_Store",
        "Thumbs.db",
        "desktop.ini",
    ]

    removed_count = 0
    import glob

    for pattern in temp_patterns:
        matches = glob.glob(pattern, recursive=True)
        for match in matches:
            try:
                if os.path.isfile(match):
                    os.remove(match)
                    print(f"  ✅ Removed: {match}")
                    removed_count += 1
            except Exception as e:
                print(f"  ❌ Failed to remove {match}: {e}")

    if removed_count == 0:
        print("  ℹ️  No temporary files found")


def reset_configuration():
    """Reset configuration files to defaults if needed"""
    print("\n🔄 Checking configuration files...")

    # Check if config directory has any backup files to clean
    config_dir = "config"
    if os.path.exists(config_dir):
        backup_count = 0
        for item in os.listdir(config_dir):
            if item.endswith((".bak", ".backup", ".old")):
                backup_path = os.path.join(config_dir, item)
                try:
                    os.remove(backup_path)
                    print(f"  ✅ Removed backup: {backup_path}")
                    backup_count += 1
                except Exception as e:
                    print(f"  ❌ Failed to remove {backup_path}: {e}")

        if backup_count == 0:
            print("  ℹ️  No configuration backups found")
    else:
        print("  ℹ️  No config directory found")


def verify_cleanup():
    """Verify that cleanup was successful"""
    print("\n🔍 Verifying cleanup...")

    check_items = [
        (".venv", "Virtual environment"),
        ("venv", "Virtual environment"),
        ("env", "Environment directory"),
        ("__pycache__", "Python cache"),
        (".pytest_cache", "Pytest cache"),
        (".mypy_cache", "MyPy cache"),
        ("bandit-report.json", "Bandit report"),
    ]

    remaining_items = []
    for item, description in check_items:
        if os.path.exists(item):
            remaining_items.append(f"{item} ({description})")

    if remaining_items:
        print("  ⚠️  Some items may still exist:")
        for item in remaining_items:
            print(f"    • {item}")
    else:
        print("  ✅ Environment appears clean")


def show_next_steps():
    """Show next steps after cleanup"""
    print("\n" + "=" * 60)
    print("🎉 Environment Cleanup Complete!")
    print("=" * 60)
    print("\n✅ Your environment has been reset to a pristine state.")
    print("\n🚀 To test fresh installation, run:")
    print("   ./run.sh")
    print("   # or")
    print("   python3 scripts/setup/setup_and_run.py")
    print("\n💡 For development setup:")
    print("   make setup-dev")
    print("\n📝 Note: All source code and documentation remain intact.")
    print("\n🔄 You can now test the installation process as a new user would.")


def main():
    """Main cleanup function"""
    print_header()

    if not confirm_cleanup():
        sys.exit(0)

    print("\n🧹 Starting environment cleanup...")
    time.sleep(1)  # Brief pause for dramatic effect

    try:
        kill_running_processes()
        remove_virtual_environments()
        remove_python_cache()
        remove_development_artifacts()
        clean_data_directories()
        remove_log_files()
        remove_temp_files()
        reset_configuration()
        verify_cleanup()
        show_next_steps()

    except KeyboardInterrupt:
        print("\n\n❌ Cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Cleanup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Fatal error during cleanup: {e}")
        print("\nYou may need to manually remove some files.")
        sys.exit(1)
