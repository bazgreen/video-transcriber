#!/usr/bin/env python3
"""
Test script for CORS configuration functionality.

This test verifies that the CORS configuration correctly handles different
environments and origin settings.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config.settings import AppConfig  # noqa: E402


class TestCORSConfiguration(unittest.TestCase):
    """Test cases for CORS configuration."""

    def setUp(self):
        """Set up test environment."""
        # Store original environment variables
        self.original_debug = os.environ.get("DEBUG")
        self.original_cors = os.environ.get("CORS_ALLOWED_ORIGINS")

    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment variables
        if self.original_debug is not None:
            os.environ["DEBUG"] = self.original_debug
        elif "DEBUG" in os.environ:
            del os.environ["DEBUG"]

        if self.original_cors is not None:
            os.environ["CORS_ALLOWED_ORIGINS"] = self.original_cors
        elif "CORS_ALLOWED_ORIGINS" in os.environ:
            del os.environ["CORS_ALLOWED_ORIGINS"]

    @patch.dict(os.environ, {"DEBUG": "true"}, clear=False)
    def test_debug_mode_cors_origins(self):
        """Test CORS origins in debug mode."""
        # Force reload of AppConfig to pick up new environment
        expected_origins = [
            "http://localhost:3000",
            "http://localhost:5000",
            "http://localhost:5001",
            "http://127.0.0.1:5001",
        ]

        origins = AppConfig.get_cors_origins()
        self.assertEqual(origins, expected_origins)
        self.assertIn("http://localhost:3000", origins)
        self.assertIn("http://localhost:5001", origins)

    @patch.dict(
        os.environ,
        {
            "DEBUG": "false",
            "CORS_ALLOWED_ORIGINS": "https://example.com,https://app.example.com",
        },
        clear=False,
    )
    def test_production_mode_cors_origins(self):
        """Test CORS origins in production mode with custom origins."""
        expected_origins = ["https://example.com", "https://app.example.com"]

        origins = AppConfig.get_cors_origins()
        self.assertEqual(origins, expected_origins)
        self.assertNotIn("http://localhost:3000", origins)

    @patch.dict(
        os.environ,
        {"DEBUG": "false", "CORS_ALLOWED_ORIGINS": "https://secure-domain.com"},
        clear=False,
    )
    def test_production_mode_single_origin(self):
        """Test CORS origins in production mode with single origin."""
        expected_origins = ["https://secure-domain.com"]

        origins = AppConfig.get_cors_origins()
        self.assertEqual(origins, expected_origins)

    @patch.dict(
        os.environ,
        {
            "DEBUG": "false",
            "CORS_ALLOWED_ORIGINS": "  https://example.com  , https://app.example.com  ",
        },
        clear=False,
    )
    def test_production_mode_whitespace_handling(self):
        """Test CORS origins with whitespace are properly trimmed."""
        expected_origins = ["https://example.com", "https://app.example.com"]

        origins = AppConfig.get_cors_origins()
        self.assertEqual(origins, expected_origins)

    @patch.dict(os.environ, {"DEBUG": "false", "CORS_ALLOWED_ORIGINS": ""}, clear=False)
    def test_production_mode_empty_origins(self):
        """Test CORS origins with empty configuration."""
        origins = AppConfig.get_cors_origins()
        self.assertEqual(origins, [])

    def test_cors_security_no_wildcard(self):
        """Test that wildcard is never returned in any configuration."""
        # Test debug mode
        with patch.dict(os.environ, {"DEBUG": "true"}, clear=False):
            origins = AppConfig.get_cors_origins()
            self.assertNotIn("*", origins)

        # Test production mode
        with patch.dict(
            os.environ,
            {"DEBUG": "false", "CORS_ALLOWED_ORIGINS": "https://example.com"},
            clear=False,
        ):
            origins = AppConfig.get_cors_origins()
            self.assertNotIn("*", origins)

    @patch.dict(os.environ, {"SECRET_KEY": "video-transcriber-secret-key"}, clear=False)
    def test_security_validation_default_secret(self):
        """Test security validation detects default secret key."""
        warnings = AppConfig.validate_security_config()
        self.assertTrue(any("default SECRET_KEY" in warning for warning in warnings))

    @patch.dict(os.environ, {"SECRET_KEY": "custom-secure-key"}, clear=False)
    def test_security_validation_custom_secret(self):
        """Test security validation passes with custom secret key."""
        # Force AppConfig to reload the environment variable
        with patch.object(AppConfig, "SECRET_KEY", "custom-secure-key"):
            warnings = AppConfig.validate_security_config()
            self.assertFalse(
                any("default SECRET_KEY" in warning for warning in warnings)
            )


def run_cors_tests():
    """Run CORS configuration tests."""
    print("🔒 Testing CORS Configuration...")
    print("=" * 50)

    # Run the tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCORSConfiguration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All CORS tests passed!")
        print("🔒 CORS configuration is secure and working correctly.")
        return True
    else:
        print("❌ Some CORS tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return False


if __name__ == "__main__":
    success = run_cors_tests()
    sys.exit(0 if success else 1)
