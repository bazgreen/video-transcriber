"""Keyword management utilities."""

import json
import logging
import os
from typing import List

logger = logging.getLogger(__name__)


def load_keywords() -> List[str]:
    """Load keywords from config file"""
    keywords_file = os.path.join('data/config', 'keywords_config.json')
    try:
        with open(keywords_file, 'r') as f:
            keywords_config = json.load(f)
            return keywords_config.get('keywords', [])
    except FileNotFoundError:
        # If file doesn't exist, create it with minimal default keywords
        default_keywords = []
        save_keywords(default_keywords)
        return default_keywords
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in keywords file {keywords_file}: {e}")
        # Return empty list and let save_keywords fix the file
        default_keywords = []
        save_keywords(default_keywords)
        return default_keywords
    except (IOError, PermissionError) as e:
        logger.error(f"Unable to read keywords file {keywords_file}: {e}")
        # Return empty list as fallback
        return []


def save_keywords(keywords: List[str]) -> None:
    """Save keywords to config file"""
    keywords_file = os.path.join('data/config', 'keywords_config.json')
    temp_file = keywords_file + '.tmp'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(keywords_file), exist_ok=True)
    
    # Write to temporary file first
    try:
        with open(temp_file, 'w') as f:
            json.dump({'keywords': keywords}, f, indent=4)
        
        # Atomic rename (on POSIX systems)
        os.replace(temp_file, keywords_file)
    except Exception as e:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e