"""Tests for keyword management utilities."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from src.utils.keywords import (
    get_scenario_by_id,
    load_keywords,
    load_scenarios,
    save_keywords,
    save_scenarios,
)


class TestKeywordUtilities(unittest.TestCase):
    """Test cases for keyword management utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: self._cleanup_test_dir())

    def _cleanup_test_dir(self):
        """Clean up test directory."""
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_load_keywords_empty_file(self):
        """Test loading keywords when file doesn't exist."""
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = os.path.join(self.test_dir, 'nonexistent.json')
            
            with patch('src.utils.keywords.save_keywords') as mock_save:
                keywords = load_keywords()
                self.assertEqual(keywords, [])
                mock_save.assert_called_once_with([])

    def test_save_and_load_keywords(self):
        """Test saving and loading keywords."""
        test_keywords = ["test", "example", "keyword"]
        keywords_file = os.path.join(self.test_dir, "keywords.json")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = keywords_file
            
            # Save keywords
            save_keywords(test_keywords)
            
            # Verify file was created
            self.assertTrue(os.path.exists(keywords_file))
            
            # Load keywords
            loaded_keywords = load_keywords()
            self.assertEqual(loaded_keywords, test_keywords)

    def test_load_scenarios_empty_file(self):
        """Test loading scenarios when file doesn't exist."""
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = os.path.join(self.test_dir, 'nonexistent.json')
            
            # The current implementation doesn't call save_scenarios when file doesn't exist
            scenarios = load_scenarios()
            self.assertEqual(scenarios, [])

    def test_save_and_load_scenarios(self):
        """Test saving and loading scenarios."""
        test_scenarios = [
            {
                "id": "test",
                "name": "Test Scenario",
                "description": "A test scenario",
                "keywords": ["test", "example"]
            },
            {
                "id": "example",
                "name": "Example Scenario",
                "description": "An example scenario",
                "keywords": ["example", "demo"]
            }
        ]
        scenarios_file = os.path.join(self.test_dir, "scenarios.json")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = scenarios_file
            
            # Save scenarios
            save_scenarios(test_scenarios)
            
            # Verify file was created
            self.assertTrue(os.path.exists(scenarios_file))
            
            # Load scenarios
            loaded_scenarios = load_scenarios()
            self.assertEqual(loaded_scenarios, test_scenarios)

    def test_get_scenario_by_id_existing(self):
        """Test getting an existing scenario by ID."""
        test_scenarios = [
            {
                "id": "education",
                "name": "Education",
                "keywords": ["learn", "study", "test"]
            },
            {
                "id": "business",
                "name": "Business",
                "keywords": ["meeting", "project", "deadline"]
            }
        ]
        
        with patch('src.utils.keywords.load_scenarios', return_value=test_scenarios):
            scenario = get_scenario_by_id("education")
            
            self.assertIsNotNone(scenario)
            self.assertEqual(scenario["id"], "education")
            self.assertEqual(scenario["name"], "Education")
            self.assertEqual(len(scenario["keywords"]), 3)

    def test_get_scenario_by_id_nonexistent(self):
        """Test getting a non-existent scenario by ID."""
        test_scenarios = [
            {
                "id": "education",
                "name": "Education",
                "keywords": ["learn", "study"]
            }
        ]
        
        with patch('src.utils.keywords.load_scenarios', return_value=test_scenarios):
            scenario = get_scenario_by_id("nonexistent")
            self.assertIsNone(scenario)

    def test_get_scenario_by_id_empty_scenarios(self):
        """Test getting scenario when no scenarios exist."""
        with patch('src.utils.keywords.load_scenarios', return_value=[]):
            scenario = get_scenario_by_id("any_id")
            self.assertIsNone(scenario)

    def test_save_keywords_creates_directory(self):
        """Test that save_keywords creates directory if it doesn't exist."""
        keywords_file = os.path.join(self.test_dir, "subdir", "keywords.json")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = keywords_file
            
            save_keywords(["test"])
            
            # Verify directory was created
            self.assertTrue(os.path.exists(os.path.dirname(keywords_file)))
            self.assertTrue(os.path.exists(keywords_file))

    def test_save_scenarios_creates_directory(self):
        """Test that save_scenarios creates directory if it doesn't exist."""
        scenarios_file = os.path.join(self.test_dir, "subdir", "scenarios.json")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = scenarios_file
            
            save_scenarios([{"id": "test", "name": "Test"}])
            
            # Verify directory was created
            self.assertTrue(os.path.exists(os.path.dirname(scenarios_file)))
            self.assertTrue(os.path.exists(scenarios_file))

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON files."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.test_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = invalid_file
            
            with patch('src.utils.keywords.save_keywords') as mock_save:
                keywords = load_keywords()
                self.assertEqual(keywords, [])
                mock_save.assert_called_once_with([])

    def test_scenarios_invalid_json_handling(self):
        """Test handling of invalid JSON in scenarios file."""
        # Create invalid JSON file
        invalid_file = os.path.join(self.test_dir, "invalid_scenarios.json")
        with open(invalid_file, 'w') as f:
            f.write("invalid json content")
        
        with patch('src.utils.keywords.os.path.join') as mock_join:
            mock_join.return_value = invalid_file
            
            scenarios = load_scenarios()
            self.assertEqual(scenarios, [])


if __name__ == '__main__':
    unittest.main()
