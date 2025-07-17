"""
Test suite for the education dictionary in transcript correction system.
Tests functionality, coverage, and integration of educational terminology.
"""

import os
import sys

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.services.transcript_correction import (
    INDUSTRY_DICTIONARIES,
    TranscriptCorrectionEngine,
    get_industry_dictionary,
)


class TestEducationDictionary:
    """Test suite for education dictionary functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.education_dict = get_industry_dictionary("education")
        self.engine = TranscriptCorrectionEngine(custom_dictionary=self.education_dict)

    def test_education_dictionary_exists(self):
        """Test that education dictionary is properly defined."""
        assert "education" in INDUSTRY_DICTIONARIES
        assert isinstance(INDUSTRY_DICTIONARIES["education"], dict)
        assert len(INDUSTRY_DICTIONARIES["education"]) > 100  # Should have 100+ terms

    def test_education_dictionary_retrieval(self):
        """Test that education dictionary can be retrieved."""
        edu_dict = get_industry_dictionary("education")
        assert edu_dict is not None
        assert isinstance(edu_dict, dict)
        assert len(edu_dict) > 0

    def test_academic_levels_coverage(self):
        """Test coverage of academic level terms."""
        expected_terms = [
            "undergraduate",
            "graduate",
            "postgraduate",
            "doctorate",
            "PhD",
            "Masters",
            "Bachelors",
            "Associate's",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing academic level term: {term}"

    def test_educational_roles_coverage(self):
        """Test coverage of educational role terms."""
        expected_terms = [
            "professor",
            "lecturer",
            "instructor",
            "teaching assistant",
            "dean",
            "provost",
            "chancellor",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing educational role term: {term}"

    def test_research_terms_coverage(self):
        """Test coverage of research methodology terms."""
        expected_terms = [
            "methodology",
            "hypothesis",
            "literature review",
            "peer review",
            "empirical",
            "qualitative",
            "quantitative",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing research term: {term}"

    def test_subject_specific_terms(self):
        """Test coverage of subject-specific academic terms."""
        # Mathematics
        math_terms = ["algebra", "calculus", "geometry", "statistics", "theorem"]
        for term in math_terms:
            assert term in self.education_dict, f"Missing math term: {term}"

        # Science
        science_terms = ["biology", "chemistry", "physics", "experiment", "theory"]
        for term in science_terms:
            assert term in self.education_dict, f"Missing science term: {term}"

        # Liberal Arts
        liberal_arts_terms = ["humanities", "philosophy", "linguistics", "literature"]
        for term in liberal_arts_terms:
            assert term in self.education_dict, f"Missing liberal arts term: {term}"

    def test_academic_publication_terms(self):
        """Test coverage of academic publication terms."""
        expected_terms = [
            "journal",
            "publication",
            "citation",
            "bibliography",
            "reference",
            "abstract",
            "manuscript",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing publication term: {term}"

    def test_assessment_terms_coverage(self):
        """Test coverage of assessment and evaluation terms."""
        expected_terms = [
            "examination",
            "quiz",
            "assignment",
            "rubric",
            "grading",
            "evaluation",
            "midterm",
            "final",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing assessment term: {term}"

    def test_educational_technology_terms(self):
        """Test coverage of educational technology terms."""
        expected_terms = [
            "e-learning",
            "online learning",
            "distance education",
            "blended learning",
            "MOOC",
            "LMS",
        ]

        for term in expected_terms:
            assert term in self.education_dict, f"Missing ed-tech term: {term}"

    def test_correction_engine_with_education_dict(self):
        """Test that correction engine properly uses education dictionary."""
        # Test text with educational terms that might be misspelled
        test_text = "The proffesor gave a lecutre on algebera and calculas"

        suggestions = self.engine.generate_corrections(test_text)

        # Should detect spelling issues and suggest corrections
        assert len(suggestions) > 0

        # Check that suggestions include educational terms
        suggestion_texts = [s.suggested_text for s in suggestions]
        assert any("professor" in text.lower() for text in suggestion_texts)

    def test_case_sensitivity_handling(self):
        """Test that dictionary handles case variations properly."""
        test_cases = [
            "PhD",
            "Ph.D.",
            "phd",
            "PHD",
            "Masters",
            "masters",
            "MASTERS",
            "Bachelor's",
            "bachelor's",
            "BACHELOR'S",
        ]

        for case in test_cases:
            # Test that the engine can find and correct variations
            test_text = f"I have a {case} degree"
            suggestions = self.engine.generate_corrections(test_text)
            # The engine should be able to work with various cases
            assert isinstance(suggestions, list)

    def test_multi_word_terms(self):
        """Test that multi-word educational terms are properly handled."""
        multi_word_terms = [
            "literature review",
            "peer review",
            "teaching assistant",
            "online learning",
            "distance education",
            "grade point average",
        ]

        for term in multi_word_terms:
            assert term in self.education_dict, f"Missing multi-word term: {term}"

            # Test in context
            test_text = f"The student completed a {term} as part of their research."
            suggestions = self.engine.generate_corrections(test_text)
            assert isinstance(suggestions, list)

    def test_abbreviation_handling(self):
        """Test that educational abbreviations are properly handled."""
        abbreviations = ["PhD", "GPA", "LMS", "MOOC"]

        for abbrev in abbreviations:
            assert abbrev in self.education_dict, f"Missing abbreviation: {abbrev}"

    def test_education_dictionary_completeness(self):
        """Test that education dictionary has comprehensive coverage."""
        categories = [
            "professor",
            "lecturer",  # Roles
            "dissertation",
            "thesis",  # Academic processes
            "university",
            "college",  # Institutions
            "methodology",
            "hypothesis",  # Research
            "algebra",
            "biology",  # Subjects
            "journal",
            "conference",  # Academic events/publications
            "examination",
            "assignment",  # Assessment
            "e-learning",
            "MOOC",  # Technology
        ]

        for term in categories:
            assert (
                term in self.education_dict
            ), f"Missing category representative: {term}"

    def test_educational_context_correction(self):
        """Test correction suggestions in educational context."""
        educational_texts = [
            "The proffesor discussed the methodolgy in her reasearch.",
            "Students must complete their disertation before graduaton.",
            "The univercity offers undergaduate and graduat programs.",
            "The conferance included a symosium on pedagoy.",
        ]

        for text in educational_texts:
            suggestions = self.engine.generate_corrections(text)
            assert len(suggestions) > 0, f"No suggestions for: {text}"

            # Verify suggestions include proper educational terms
            corrected_text = self.engine.apply_corrections(text, suggestions)
            assert corrected_text != text, f"No corrections applied to: {text}"

    def test_term_consistency(self):
        """Test that dictionary terms are consistently formatted."""
        for term, replacement in self.education_dict.items():
            # Terms should map to themselves (proper spellings)
            assert term == replacement, f"Inconsistent mapping: {term} -> {replacement}"

            # No empty terms
            assert term.strip() != "", "Empty term found in dictionary"
            assert replacement.strip() != "", "Empty replacement found in dictionary"

    def test_integration_with_other_dictionaries(self):
        """Test that education dictionary works alongside other industry dictionaries."""
        # Create engine with multiple dictionaries
        combined_dict = {}
        combined_dict.update(get_industry_dictionary("education"))
        combined_dict.update(get_industry_dictionary("technical"))

        engine = TranscriptCorrectionEngine(custom_dictionary=combined_dict)

        # Test text with both educational and technical terms
        test_text = "The proffesor used an API to analyze the databse of student grades"
        suggestions = engine.generate_corrections(test_text)

        assert len(suggestions) > 0

        # Should suggest corrections for both domains
        suggestion_texts = " ".join([s.suggested_text for s in suggestions])
        # Should handle both educational and technical terms
        assert "professor" in suggestion_texts.lower() or "API" in suggestion_texts


def test_education_dictionary_api_integration():
    """Test that education dictionary integrates with API endpoints."""
    from src.routes.transcript_correction_routes import get_industry_dictionary

    # Test API dictionary retrieval
    education_dict = get_industry_dictionary("education")
    assert education_dict is not None
    assert len(education_dict) > 100

    # Test that all expected categories are represented
    categories_represented = {
        "academic_levels": any(
            term in education_dict for term in ["undergraduate", "graduate", "PhD"]
        ),
        "roles": any(
            term in education_dict for term in ["professor", "lecturer", "instructor"]
        ),
        "research": any(
            term in education_dict
            for term in ["methodology", "hypothesis", "empirical"]
        ),
        "subjects": any(
            term in education_dict for term in ["algebra", "biology", "philosophy"]
        ),
        "technology": any(
            term in education_dict for term in ["e-learning", "MOOC", "LMS"]
        ),
    }

    for category, represented in categories_represented.items():
        assert (
            represented
        ), f"Category {category} not properly represented in dictionary"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
