#!/usr/bin/env python3
"""
Test script to verify transcript correction dependencies are properly integrated
into the main installation and setup scripts.
"""

import os
import subprocess
import sys


def test_requirements_integration():
    """Test that transcript correction deps are in main requirements files."""
    print("🔍 Testing Requirements Integration")
    print("=" * 40)

    # Check requirements-full.txt
    with open("requirements-full.txt", "r") as f:
        full_content = f.read()

    required_deps = [
        "language-tool-python",
        "textblob",
        "spacy"
    ]

    missing_deps = []
    for dep in required_deps:
        if dep not in full_content:
            missing_deps.append(dep)

    if missing_deps:
        print(f"❌ Missing from requirements-full.txt: {missing_deps}")
        return False
    else:
        print("✅ All transcript correction dependencies found in requirements-full.txt")

    # Check if model download instructions are present
    if "spacy download en_core_web_sm" in full_content and "textblob.download_corpora" in full_content:
        print("✅ Model download instructions present")
    else:
        print("⚠️  Model download instructions may be incomplete")

    return True


def test_setup_script_integration():
    """Test that setup script includes transcript correction packages."""
    print("\n🔧 Testing Setup Script Integration")
    print("=" * 40)

    script_path = "scripts/install_ai_features.py"

    if not os.path.exists(script_path):
        print(f"❌ Setup script not found: {script_path}")
        return False

    with open(script_path, "r") as f:
        script_content = f.read()

    # Check for transcript correction dependencies
    if "language-tool-python" in script_content:
        print("✅ language-tool-python found in setup script")
    else:
        print("❌ language-tool-python missing from setup script")
        return False

    # Check for model installation
    if "textblob" in script_content and "nltk.download" in script_content:
        print("✅ TextBlob corpora installation found")
    else:
        print("⚠️  TextBlob corpora installation may be missing")

    # Check for feature descriptions
    if "transcript correction" in script_content.lower():
        print("✅ Transcript correction mentioned in feature descriptions")
    else:
        print("⚠️  Transcript correction not mentioned in features")

    return True


def test_readme_integration():
    """Test that README includes transcript correction features."""
    print("\n📚 Testing README Integration")
    print("=" * 40)

    if not os.path.exists("README.md"):
        print("❌ README.md not found")
        return False

    with open("README.md", "r") as f:
        readme_content = f.read()

    # Check for transcript correction in features
    if "transcript correction" in readme_content.lower():
        print("✅ Transcript correction mentioned in README features")
    else:
        print("❌ Transcript correction missing from README features")
        return False

    # Check for feature comparison table
    if "**Transcript Correction**" in readme_content:
        print("✅ Transcript correction in feature comparison table")
    else:
        print("⚠️  Transcript correction may be missing from comparison table")

    return True


def test_dependencies_available():
    """Test that all required dependencies can be imported."""
    print("\n📦 Testing Dependency Availability")
    print("=" * 40)

    dependencies = [
        ("textblob", "TextBlob"),
        ("spacy", "spaCy"),
        ("language_tool_python", "LanguageTool")
    ]

    all_available = True

    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name} available")
        except ImportError:
            print(f"❌ {name} not available")
            all_available = False

    # Test spaCy model
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✅ spaCy English model available")
    except Exception:
        print("❌ spaCy English model not available")
        all_available = False

    return all_available


def main():
    """Run all integration tests."""
    print("🧪 Transcript Correction Integration Tests")
    print("=" * 60)

    tests = [
        ("Requirements Integration", test_requirements_integration),
        ("Setup Script Integration", test_setup_script_integration),
        ("README Integration", test_readme_integration),
        ("Dependencies Available", test_dependencies_available)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:8} | {test_name}")

    print("-" * 60)
    print(f"Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All integration tests passed!")
        print("✅ Transcript correction is properly integrated into setup scripts")
    elif passed >= total * 0.75:
        print("\n✅ Most tests passed - integration looks good with minor issues")
    else:
        print("\n⚠️  Some integration issues found - review the failures above")

    print("\n💡 To install with all features including transcript correction:")
    print("   pip install -r requirements-full.txt")
    print("   # OR")
    print("   python install_ai_features.py")

    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
