"""
Simple test for education dictionary functionality without pytest dependency.
Tests basic functionality and coverage of educational terminology.
"""

import os
import sys

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from src.services.transcript_correction import (
        INDUSTRY_DICTIONARIES,
        TranscriptCorrectionEngine,
        get_industry_dictionary,
    )

    print("✓ Successfully imported transcript correction modules")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_education_dictionary_exists():
    """Test that education dictionary is properly defined."""
    print("\n=== Testing Education Dictionary Existence ===")

    # Check if education dictionary exists
    assert (
        "education" in INDUSTRY_DICTIONARIES
    ), "Education dictionary not found in INDUSTRY_DICTIONARIES"
    print("✓ Education dictionary exists in INDUSTRY_DICTIONARIES")

    # Check if it's a dictionary
    assert isinstance(
        INDUSTRY_DICTIONARIES["education"], dict
    ), "Education dictionary is not a dict"
    print("✓ Education dictionary is properly formatted as dict")

    # Check if it has substantial content
    edu_dict = INDUSTRY_DICTIONARIES["education"]
    print(f"✓ Education dictionary contains {len(edu_dict)} terms")

    assert (
        len(edu_dict) > 100
    ), f"Education dictionary too small: {len(edu_dict)} terms (expected > 100)"
    print("✓ Education dictionary meets minimum size requirement (100+ terms)")


def test_education_dictionary_retrieval():
    """Test that education dictionary can be retrieved via API."""
    print("\n=== Testing Dictionary Retrieval ===")

    edu_dict = get_industry_dictionary("education")
    assert edu_dict is not None, "get_industry_dictionary returned None for education"
    print("✓ Successfully retrieved education dictionary via get_industry_dictionary")

    assert isinstance(edu_dict, dict), "Retrieved dictionary is not a dict"
    assert len(edu_dict) > 0, "Retrieved dictionary is empty"
    print(f"✓ Retrieved dictionary contains {len(edu_dict)} terms")


def test_key_educational_terms():
    """Test that key educational terms are present."""
    print("\n=== Testing Key Educational Terms ===")

    edu_dict = get_industry_dictionary("education")

    # Test academic levels
    academic_levels = ["undergraduate", "graduate", "PhD", "Masters", "Bachelors"]
    for term in academic_levels:
        assert term in edu_dict, f"Missing academic level: {term}"
    print(f"✓ All academic level terms present: {academic_levels}")

    # Test educational roles
    roles = ["professor", "lecturer", "instructor", "dean"]
    for term in roles:
        assert term in edu_dict, f"Missing educational role: {term}"
    print(f"✓ All educational role terms present: {roles}")

    # Test research terms
    research_terms = ["methodology", "hypothesis", "empirical", "qualitative"]
    for term in research_terms:
        assert term in edu_dict, f"Missing research term: {term}"
    print(f"✓ All research terms present: {research_terms}")

    # Test subject areas
    subjects = ["algebra", "biology", "philosophy", "psychology"]
    for term in subjects:
        assert term in edu_dict, f"Missing subject term: {term}"
    print(f"✓ All subject area terms present: {subjects}")

    # Test technology terms
    tech_terms = ["e-learning", "MOOC", "LMS", "online learning"]
    for term in tech_terms:
        assert term in edu_dict, f"Missing technology term: {term}"
    print(f"✓ All educational technology terms present: {tech_terms}")


def test_correction_engine_integration():
    """Test that education dictionary integrates with correction engine."""
    print("\n=== Testing Correction Engine Integration ===")

    try:
        edu_dict = get_industry_dictionary("education")
        engine = TranscriptCorrectionEngine(custom_dictionary=edu_dict)
        print("✓ Successfully created correction engine with education dictionary")

        # Test basic functionality
        test_text = "The professor gave a lecture on methodology"
        suggestions = engine.generate_corrections(test_text)
        print(f"✓ Generated {len(suggestions)} suggestions for test text")

        # Test quality analysis
        quality = engine.analyze_transcript_quality(test_text)
        print(f"✓ Quality analysis completed: {quality.overall_score}% overall score")

    except Exception as e:
        print(f"✗ Correction engine integration failed: {e}")
        raise


def test_term_consistency():
    """Test that dictionary terms are consistently formatted."""
    print("\n=== Testing Term Consistency ===")

    edu_dict = get_industry_dictionary("education")

    inconsistent_terms = []
    empty_terms = []

    for term, replacement in edu_dict.items():
        # Check for self-mapping (term should equal replacement)
        if term != replacement:
            inconsistent_terms.append(f"{term} -> {replacement}")

        # Check for empty terms
        if not term.strip() or not replacement.strip():
            empty_terms.append(term)

    assert (
        len(inconsistent_terms) == 0
    ), f"Inconsistent term mappings: {inconsistent_terms}"
    assert len(empty_terms) == 0, f"Empty terms found: {empty_terms}"

    print("✓ All terms are consistently formatted")
    print(f"✓ All {len(edu_dict)} terms map to themselves correctly")


def test_comprehensive_coverage():
    """Test that education dictionary has comprehensive coverage."""
    print("\n=== Testing Comprehensive Coverage ===")

    edu_dict = get_industry_dictionary("education")

    # Define expected categories and sample terms
    categories = {
        "Academic Levels": ["undergraduate", "graduate", "doctorate", "PhD"],
        "Educational Roles": ["professor", "lecturer", "instructor", "dean"],
        "Academic Processes": ["dissertation", "thesis", "curriculum", "assessment"],
        "Institutions": ["university", "college", "library", "laboratory"],
        "Research": ["methodology", "hypothesis", "empirical", "peer review"],
        "Mathematics": ["algebra", "calculus", "statistics", "theorem"],
        "Science": ["biology", "chemistry", "physics", "experiment"],
        "Liberal Arts": ["humanities", "philosophy", "literature", "psychology"],
        "Publications": ["journal", "conference", "citation", "abstract"],
        "Assessment": ["examination", "assignment", "grading", "rubric"],
        "Technology": ["e-learning", "MOOC", "LMS", "online learning"],
        "Administration": ["enrollment", "transcript", "GPA", "semester"],
    }

    coverage_report = {}

    for category, sample_terms in categories.items():
        found_terms = []
        missing_terms = []

        for term in sample_terms:
            if term in edu_dict:
                found_terms.append(term)
            else:
                missing_terms.append(term)

        coverage_percentage = (len(found_terms) / len(sample_terms)) * 100
        coverage_report[category] = {
            "coverage": coverage_percentage,
            "found": found_terms,
            "missing": missing_terms,
        }

        print(
            f"✓ {category}: {coverage_percentage:.1f}% coverage ({len(found_terms)}/{len(sample_terms)} terms)"
        )

        # Require at least 75% coverage per category
        assert (
            coverage_percentage >= 75
        ), f"Insufficient coverage for {category}: {coverage_percentage:.1f}%"

    # Overall coverage summary
    total_expected = sum(len(terms) for terms in categories.values())
    total_found = sum(len(report["found"]) for report in coverage_report.values())
    overall_coverage = (total_found / total_expected) * 100

    print(
        f"\n✓ Overall coverage: {overall_coverage:.1f}% ({total_found}/{total_expected} terms)"
    )
    assert overall_coverage >= 90, f"Overall coverage too low: {overall_coverage:.1f}%"


def run_all_tests():
    """Run all education dictionary tests."""
    print("🎓 Education Dictionary Test Suite")
    print("=" * 50)

    tests = [
        test_education_dictionary_exists,
        test_education_dictionary_retrieval,
        test_key_educational_terms,
        test_correction_engine_integration,
        test_term_consistency,
        test_comprehensive_coverage,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
            print(f"✅ {test.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Education dictionary is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
