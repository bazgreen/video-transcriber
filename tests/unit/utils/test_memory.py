"""
Unit tests for memory utility functions.

Tests the memory management utilities including status checking,
constraint validation, and logging functions.
"""

from unittest.mock import Mock, patch

import pytest

from src.models.exceptions import UserFriendlyError
from src.utils.memory import (
    check_memory_constraints,
    get_memory_status_safe,
    log_memory_status,
    validate_memory_for_operation,
)


class TestGetMemoryStatusSafe:
    """Test safe memory status retrieval."""

    @pytest.mark.unit
    def test_with_valid_memory_manager(self, mock_memory_manager):
        """Test with functioning memory manager."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 8.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 100.0,
            "process_vms_mb": 200.0,
        }

        result = get_memory_status_safe(mock_memory_manager)

        assert result["system_total_gb"] == 16.0
        assert result["system_available_gb"] == 8.0
        assert result["system_used_percent"] == 50.0
        assert result["available"] is True
        mock_memory_manager.get_memory_info.assert_called_once()

    @pytest.mark.unit
    def test_with_none_memory_manager(self):
        """Test with None memory manager."""
        result = get_memory_status_safe(None)

        # Should return conservative fallback values
        assert result["system_total_gb"] == 8.0  # Conservative default
        assert result["system_available_gb"] == 4.0
        assert result["system_used_percent"] == 50.0
        assert result["available"] is False

    @pytest.mark.unit
    def test_with_failing_memory_manager(self, mock_memory_manager):
        """Test with memory manager that raises exceptions."""
        mock_memory_manager.get_memory_info.side_effect = Exception("Memory error")

        with patch("src.utils.memory.logger") as mock_logger:
            result = get_memory_status_safe(mock_memory_manager)

            # Should fall back to conservative values
            assert result["available"] is False
            mock_logger.warning.assert_called_once()


class TestCheckMemoryConstraints:
    """Test memory constraint checking."""

    @pytest.mark.unit
    def test_healthy_memory_status(self, mock_memory_manager):
        """Test with healthy memory conditions."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 8.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 100.0,
            "process_vms_mb": 200.0,
        }
        mock_memory_manager.get_optimal_workers.return_value = 4

        result = check_memory_constraints(mock_memory_manager)

        assert result["memory_pressure"] is False
        assert result["low_memory"] is False
        assert result["status"] == "ok"
        assert len(result["recommendations"]) == 0

    @pytest.mark.unit
    def test_memory_pressure_detection(self, mock_memory_manager):
        """Test detection of memory pressure conditions."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 1.0,
            "system_used_percent": 95.0,
            "process_rss_mb": 1000.0,
            "process_vms_mb": 2000.0,
        }
        mock_memory_manager.get_optimal_workers.return_value = 2

        result = check_memory_constraints(
            mock_memory_manager, pressure_threshold=90, min_available_gb=2.0
        )

        assert result["memory_pressure"] is True
        assert result["low_memory"] is True
        assert result["status"] == "warning"
        assert len(result["recommendations"]) >= 2

    @pytest.mark.unit
    def test_custom_thresholds(self, mock_memory_manager):
        """Test with custom memory thresholds."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 8.0,
            "system_available_gb": 3.0,
            "system_used_percent": 85.0,
            "process_rss_mb": 500.0,
            "process_vms_mb": 1000.0,
        }
        mock_memory_manager.get_optimal_workers.return_value = 3

        # Test with lenient thresholds
        result = check_memory_constraints(
            mock_memory_manager, pressure_threshold=95, min_available_gb=1.0
        )

        assert result["memory_pressure"] is False
        assert result["low_memory"] is False
        assert result["status"] == "ok"

    @pytest.mark.unit
    def test_low_worker_count_recommendation(self, mock_memory_manager):
        """Test recommendation when worker count is limited by memory."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 4.0,
            "system_available_gb": 2.0,
            "system_used_percent": 70.0,
            "process_rss_mb": 200.0,
            "process_vms_mb": 400.0,
        }
        mock_memory_manager.get_optimal_workers.return_value = 1  # Low worker count

        result = check_memory_constraints(mock_memory_manager)

        assert any("workers to 1" in rec for rec in result["recommendations"])

    @pytest.mark.unit
    def test_none_memory_manager_constraints(self):
        """Test constraint checking with None memory manager."""
        result = check_memory_constraints(None)

        # Should use safe fallback values
        assert result["memory_pressure"] is False
        assert result["low_memory"] is False
        assert result["status"] == "ok"


class TestLogMemoryStatus:
    """Test memory status logging."""

    @pytest.mark.unit
    def test_log_with_context(self, mock_memory_manager):
        """Test logging with context string."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 8.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 100.0,
            "process_vms_mb": 200.0,
        }

        with patch("src.utils.memory.logger") as mock_logger:
            log_memory_status(mock_memory_manager, "test operation")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "test operation" in call_args
            assert "50.0% used" in call_args
            assert "8.0GB available" in call_args

    @pytest.mark.unit
    def test_log_without_context(self, mock_memory_manager):
        """Test logging without context string."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 8.0,
            "system_available_gb": 4.0,
            "system_used_percent": 60.0,
            "process_rss_mb": 150.0,
            "process_vms_mb": 300.0,
        }

        with patch("src.utils.memory.logger") as mock_logger:
            log_memory_status(mock_memory_manager)

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "Memory status:" in call_args
            assert "60.0% used" in call_args

    @pytest.mark.unit
    def test_log_with_none_memory_manager(self):
        """Test logging with None memory manager."""
        with patch("src.utils.memory.logger") as mock_logger:
            log_memory_status(None, "fallback test")

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "fallback test" in call_args


class TestValidateMemoryForOperation:
    """Test memory validation for operations."""

    @pytest.mark.unit
    def test_sufficient_memory_for_operation(self, mock_memory_manager):
        """Test with sufficient memory for operation."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 8.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 100.0,
            "process_vms_mb": 200.0,
        }

        # Should not raise any exception
        validate_memory_for_operation(
            mock_memory_manager,
            "test operation",
            required_memory_gb=2.0,
            max_pressure_threshold=80,
        )

    @pytest.mark.unit
    def test_insufficient_memory_pressure(self, mock_memory_manager):
        """Test with insufficient memory due to high pressure."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 8.0,
            "system_available_gb": 2.0,
            "system_used_percent": 90.0,
            "process_rss_mb": 500.0,
            "process_vms_mb": 1000.0,
        }

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_memory_for_operation(
                mock_memory_manager,
                "video processing",
                required_memory_gb=1.0,
                max_pressure_threshold=85,
            )

        error_msg = str(exc_info.value)
        assert "Insufficient memory for video processing" in error_msg
        assert "90.0% used" in error_msg

    @pytest.mark.unit
    def test_insufficient_available_memory(self, mock_memory_manager):
        """Test with insufficient available memory."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 8.0,
            "system_available_gb": 0.5,  # Very low available memory
            "system_used_percent": 70.0,
            "process_rss_mb": 300.0,
            "process_vms_mb": 600.0,
        }

        with pytest.raises(UserFriendlyError) as exc_info:
            validate_memory_for_operation(
                mock_memory_manager,
                "large file processing",
                required_memory_gb=2.0,
                max_pressure_threshold=90,
            )

        error_msg = str(exc_info.value)
        assert "Low memory for large file processing" in error_msg
        assert "0.5GB available" in error_msg
        assert "need at least 2.0GB" in error_msg

    @pytest.mark.unit
    def test_default_parameters(self, mock_memory_manager):
        """Test with default parameters."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 16.0,
            "system_available_gb": 8.0,
            "system_used_percent": 50.0,
            "process_rss_mb": 100.0,
            "process_vms_mb": 200.0,
        }

        # Should use default values (1.0GB required, 85% threshold)
        validate_memory_for_operation(mock_memory_manager, "default test")

    @pytest.mark.unit
    def test_edge_case_exact_threshold(self, mock_memory_manager):
        """Test edge case where memory usage equals threshold."""
        mock_memory_manager.get_memory_info.return_value = {
            "system_total_gb": 8.0,
            "system_available_gb": 2.0,
            "system_used_percent": 85.0,  # Exactly at threshold
            "process_rss_mb": 300.0,
            "process_vms_mb": 600.0,
        }

        # Should not raise exception when at threshold
        validate_memory_for_operation(
            mock_memory_manager, "edge case test", max_pressure_threshold=85
        )

        # Should raise exception when over threshold
        with pytest.raises(UserFriendlyError):
            validate_memory_for_operation(
                mock_memory_manager, "edge case test", max_pressure_threshold=84
            )
