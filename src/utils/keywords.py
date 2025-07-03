"""Keyword management utilities."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def load_keywords() -> List[str]:
    """Load keywords from config file"""
    keywords_file = os.path.join("data/config", "keywords_config.json")
    try:
        with open(keywords_file, "r") as f:
            keywords_config = json.load(f)
            return keywords_config.get("keywords", [])
    except FileNotFoundError:
        # If file doesn't exist, create it with minimal default keywords
        empty_keywords: List[str] = []
        save_keywords(empty_keywords)
        return empty_keywords
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in keywords file {keywords_file}: {e}")
        # Return empty list and let save_keywords fix the file
        fallback_keywords: List[str] = []
        save_keywords(fallback_keywords)
        return fallback_keywords
    except (IOError, PermissionError) as e:
        logger.error(f"Unable to read keywords file {keywords_file}: {e}")
        # Return empty list as fallback
        return []


def load_scenarios() -> List[Dict[str, Any]]:
    """Load pre-built keyword scenarios from config file"""
    scenarios_file = os.path.join("data/config", "keyword_scenarios.json")
    try:
        with open(scenarios_file, "r") as f:
            scenarios_config = json.load(f)
            return scenarios_config.get("scenarios", [])
    except FileNotFoundError:
        # If file doesn't exist, create it with empty scenarios
        save_scenarios([])
        return []
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in scenarios file {scenarios_file}: {e}")
        # Return empty list as fallback
        return []
    except (IOError, PermissionError) as e:
        logger.error(f"Unable to read scenarios file {scenarios_file}: {e}")
        # Return empty list as fallback
        return []


def save_scenarios(scenarios: List[Dict[str, Any]]) -> None:
    """Save pre-built keyword scenarios to config file"""
    scenarios_file = os.path.join("data/config", "keyword_scenarios.json")
    temp_file = scenarios_file + ".tmp"

    # Ensure directory exists
    os.makedirs(os.path.dirname(scenarios_file), exist_ok=True)

    # Write to temporary file first
    try:
        with open(temp_file, "w") as f:
            json.dump({"scenarios": scenarios}, f, indent=4)

        # Atomic rename (on POSIX systems)
        os.replace(temp_file, scenarios_file)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e


def get_scenario_by_id(scenario_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific scenario by ID"""
    scenarios = load_scenarios()
    for scenario in scenarios:
        if scenario.get("id") == scenario_id:
            return scenario
    return None


def save_keywords(keywords: List[str]) -> None:
    """Save keywords to config file"""
    keywords_file = os.path.join("data/config", "keywords_config.json")
    temp_file = keywords_file + ".tmp"

    # Ensure directory exists
    os.makedirs(os.path.dirname(keywords_file), exist_ok=True)

    # Write to temporary file first
    try:
        with open(temp_file, "w") as f:
            json.dump({"keywords": keywords}, f, indent=4)

        # Atomic rename (on POSIX systems)
        os.replace(temp_file, keywords_file)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e
