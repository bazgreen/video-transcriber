"""Tests for keyword scenario API endpoints."""

import json
import unittest
from unittest.mock import patch

from src.routes.api import api_bp


class TestKeywordScenariosAPI(unittest.TestCase):
    """Test cases for keyword scenarios API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        from flask import Flask

        self.app = Flask(__name__)
        self.app.register_blueprint(api_bp)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_get_keyword_scenarios_success(self):
        """Test successful retrieval of keyword scenarios."""
        mock_scenarios = [
            {
                "id": "education",
                "name": "🎓 Education & Training",
                "description": "Keywords focused on learning environments",
                "keywords": ["question", "answer", "learn", "study"],
            },
            {
                "id": "business",
                "name": "💼 Business & Meetings",
                "description": "Keywords for corporate environments",
                "keywords": ["meeting", "project", "deadline", "team"],
            },
        ]

        with patch("src.routes.api.load_scenarios", return_value=mock_scenarios):
            response = self.client.get("/api/keywords/scenarios")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)

            self.assertTrue(data["success"])
            self.assertEqual(len(data["scenarios"]), 2)

            # Check first scenario
            first_scenario = data["scenarios"][0]
            self.assertEqual(first_scenario["id"], "education")
            self.assertEqual(first_scenario["name"], "🎓 Education & Training")
            self.assertEqual(first_scenario["keyword_count"], 4)

    def test_get_keyword_scenarios_empty(self):
        """Test retrieval when no scenarios exist."""
        with patch("src.routes.api.load_scenarios", return_value=[]):
            response = self.client.get("/api/keywords/scenarios")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)

            self.assertTrue(data["success"])
            self.assertEqual(len(data["scenarios"]), 0)

    def test_get_keyword_scenario_success(self):
        """Test successful retrieval of a specific scenario."""
        mock_scenario = {
            "id": "education",
            "name": "🎓 Education & Training",
            "description": "Keywords focused on learning environments",
            "keywords": ["question", "answer", "learn", "study"],
        }

        with patch("src.routes.api.get_scenario_by_id", return_value=mock_scenario):
            response = self.client.get("/api/keywords/scenarios/education")

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)

            self.assertTrue(data["success"])
            self.assertEqual(data["scenario"]["id"], "education")
            self.assertEqual(len(data["scenario"]["keywords"]), 4)

    def test_get_keyword_scenario_not_found(self):
        """Test retrieval of non-existent scenario."""
        with patch("src.routes.api.get_scenario_by_id", return_value=None):
            response = self.client.get("/api/keywords/scenarios/nonexistent")

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)

            self.assertFalse(data["success"])
            self.assertIn("not found", data["error"])

    def test_apply_keyword_scenario_replace_mode(self):
        """Test applying a scenario in replace mode."""
        mock_scenario = {
            "id": "education",
            "name": "Education",
            "keywords": ["learn", "study", "test"],
        }

        with patch(
            "src.routes.api.get_scenario_by_id", return_value=mock_scenario
        ), patch("src.routes.api.save_keywords") as mock_save:
            response = self.client.post(
                "/api/keywords/scenarios/apply",
                json={"scenario_id": "education", "merge_mode": "replace"},
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)

            self.assertTrue(data["success"])
            self.assertEqual(len(data["keywords"]), 3)
            self.assertIn("Applied scenario", data["message"])

            # Verify save_keywords was called with scenario keywords
            mock_save.assert_called_once_with(["learn", "study", "test"])

    def test_apply_keyword_scenario_merge_mode(self):
        """Test applying a scenario in merge mode."""
        mock_scenario = {
            "id": "education",
            "name": "Education",
            "keywords": ["learn", "study", "test"],
        }
        existing_keywords = ["existing", "keyword"]

        with patch(
            "src.routes.api.get_scenario_by_id", return_value=mock_scenario
        ), patch("src.routes.api.load_keywords", return_value=existing_keywords), patch(
            "src.routes.api.save_keywords"
        ) as mock_save:
            response = self.client.post(
                "/api/keywords/scenarios/apply",
                json={"scenario_id": "education", "merge_mode": "merge"},
            )

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)

            self.assertTrue(data["success"])
            # Should have merged keywords (5 unique)
            self.assertEqual(len(data["keywords"]), 5)

            # Verify save_keywords was called with merged keywords
            saved_keywords = mock_save.call_args[0][0]
            self.assertIn("learn", saved_keywords)
            self.assertIn("existing", saved_keywords)

    def test_apply_keyword_scenario_invalid_request(self):
        """Test applying scenario with invalid request."""
        response = self.client.post(
            "/api/keywords/scenarios/apply", json={}
        )  # Missing scenario_id

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)

        self.assertFalse(data["success"])
        self.assertIn("scenario_id", data["error"])

    def test_apply_keyword_scenario_not_found(self):
        """Test applying non-existent scenario."""
        with patch("src.routes.api.get_scenario_by_id", return_value=None):
            response = self.client.post(
                "/api/keywords/scenarios/apply", json={"scenario_id": "nonexistent"}
            )

            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)

            self.assertFalse(data["success"])
            self.assertIn("not found", data["error"])


if __name__ == "__main__":
    unittest.main()
