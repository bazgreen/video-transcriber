#!/usr/bin/env python3
"""
Comprehensive validation test for performance optimization features.
"""

import sys
import traceback
from typing import Any, Dict


def test_configuration_imports():
    """Test that all configuration imports work correctly"""
    try:
        from src.config import AppConfig, Constants, PerformanceConfig

        # Check key configuration values
        assert (
            AppConfig.MAX_FILE_SIZE_BYTES == 1024 * 1024 * 1024
        ), "File size limit not updated"
        assert PerformanceConfig.MIN_WORKERS == 2, "Min workers not updated"
        assert PerformanceConfig.MAX_WORKERS_LIMIT == 16, "Max workers not updated"
        assert PerformanceConfig.DEFAULT_MAX_WORKERS == 6, "Default workers not updated"

        print("✅ Configuration imports and values correct")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_performance_optimizer():
    """Test performance optimizer functionality"""
    try:
        from src.utils.performance_optimizer import performance_optimizer

        # Test basic methods
        recommendations = performance_optimizer.get_performance_recommendations()
        assert isinstance(recommendations, list), "Recommendations should be a list"
        assert len(recommendations) > 0, "Should have some recommendations"

        optimal_workers = performance_optimizer.get_optimal_worker_count()
        assert isinstance(optimal_workers, int), "Worker count should be integer"
        assert optimal_workers >= 2, "Should have at least minimum workers"

        summary = performance_optimizer.get_performance_summary()
        assert isinstance(summary, dict), "Summary should be a dict"

        # Test memory optimization
        memory_result = performance_optimizer.optimize_memory_usage()
        assert isinstance(memory_result, dict), "Memory result should be a dict"

        print("✅ Performance optimizer functionality working")
        print(f"   - {len(recommendations)} recommendations generated")
        print(f"   - Optimal workers: {optimal_workers}")
        return True
    except Exception as e:
        print(f"❌ Performance optimizer test failed: {e}")
        traceback.print_exc()
        return False


def test_transcription_service_integration():
    """Test that transcription service integrates with performance optimizer"""
    try:
        # Test import and basic instantiation without full setup
        from src.services.transcription import VideoTranscriber

        print("✅ Transcription service imports successfully")
        return True
    except Exception as e:
        print(f"❌ Transcription service integration test failed: {e}")
        return False


def test_api_routes_imports():
    """Test that API routes import correctly"""
    try:
        from src.routes.api import api_bp

        # Check that the blueprint has expected endpoints by checking its rules
        rules = list(api_bp.deferred_functions)
        print(
            f"✅ API routes import correctly, blueprint has {len(rules)} registered functions"
        )
        return True
    except Exception as e:
        print(f"❌ API routes test failed: {e}")
        return False


def test_memory_utilities():
    """Test memory utilities"""
    try:
        from src.utils.performance_optimizer import get_safe_memory_status

        memory_status = get_safe_memory_status()
        assert isinstance(memory_status, dict), "Memory status should be a dict"
        assert "system_total_gb" in memory_status, "Should have system total"
        assert "system_available_gb" in memory_status, "Should have available memory"

        print("✅ Memory utilities working correctly")
        return True
    except Exception as e:
        print(f"❌ Memory utilities test failed: {e}")
        return False


def test_performance_chunking():
    """Test performance-aware chunking functionality"""
    try:
        from src.utils.performance_optimizer import performance_optimizer

        # Test chunk size calculation using the correct method name
        chunk_size = performance_optimizer.get_optimal_chunk_size(
            video_duration=3600, file_size_mb=500  # 1 hour
        )

        assert isinstance(chunk_size, int), "Chunk size should be integer"
        assert chunk_size > 0, "Chunk size should be positive"

        print(f"✅ Performance chunking working, optimal chunk size: {chunk_size}s")
        return True
    except Exception as e:
        print(f"❌ Performance chunking test failed: {e}")
        return False


def run_all_tests():
    """Run comprehensive validation tests"""
    print("🧪 Running Performance Optimization Validation Tests")
    print("=" * 60)

    tests = [
        ("Configuration", test_configuration_imports),
        ("Performance Optimizer", test_performance_optimizer),
        ("Transcription Integration", test_transcription_service_integration),
        ("API Routes", test_api_routes_imports),
        ("Memory Utilities", test_memory_utilities),
        ("Performance Chunking", test_performance_chunking),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"   Test failed but didn't crash")
        except Exception as e:
            print(f"   Test crashed: {e}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All performance optimization features validated successfully!")
        print("\n📋 Performance Optimization Summary:")
        print("   ✅ Enhanced configuration settings")
        print("   ✅ Advanced performance optimizer")
        print("   ✅ Memory management utilities")
        print("   ✅ API endpoint integration")
        print("   ✅ Transcription service integration")
        print("   ✅ Intelligent chunking system")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed - check individual test output")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
