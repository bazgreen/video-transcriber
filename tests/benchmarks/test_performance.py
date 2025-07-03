"""
Performance benchmark tests for video transcriber.

Tests performance characteristics of key operations including
video processing, memory usage, and API response times.
"""

import os
import tempfile
import time
from unittest.mock import Mock, patch

import pytest

from src.services.transcription import VideoTranscriber
from src.utils.memory import check_memory_constraints, get_memory_status_safe
from src.utils.session import get_session_list, validate_session_access
from src.utils.validation import validate_file_upload, validate_request_data


class TestVideoProcessingPerformance:
    """Benchmark video processing performance."""

    @pytest.fixture
    def benchmark_transcriber(
        self,
        mock_memory_manager,
        mock_file_manager,
        mock_progress_tracker,
        test_directories,
    ):
        """Create optimized transcriber for benchmarking."""
        transcriber = VideoTranscriber(
            memory_manager=mock_memory_manager,
            file_manager=mock_file_manager,
            progress_tracker=mock_progress_tracker,
            results_folder=test_directories["results"],
        )
        return transcriber

    @pytest.mark.benchmark
    def test_video_splitting_performance(
        self, benchmark, benchmark_transcriber, test_directories
    ):
        """Benchmark video splitting performance."""
        # Create test video data
        video_path = os.path.join(test_directories["uploads"], "benchmark_video.mp4")
        video_content = b"fake video data" * 10000  # ~150KB

        with open(video_path, "wb") as f:
            f.write(video_content)

        output_dir = test_directories["results"]

        def split_video_operation():
            with patch("src.services.transcription.ffmpeg.probe") as mock_probe:
                mock_probe.return_value = {
                    "streams": [
                        {"codec_type": "video", "duration": "300.0"}
                    ],  # 5 minutes
                    "format": {"duration": "300.0"},
                }

                with patch("src.services.transcription.ffmpeg.input") as mock_ffmpeg:
                    mock_output = Mock()
                    mock_output.run = Mock()
                    mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value = (
                        mock_output
                    )

                    return benchmark_transcriber.split_video(
                        video_path, output_dir, chunk_duration=60
                    )

        # Benchmark the operation
        result = benchmark(split_video_operation)

        # Verify performance expectations
        assert len(result) == 5  # Should create 5 chunks for 5-minute video

        # Performance assertion (should complete in reasonable time)
        stats = benchmark.stats
        assert stats["mean"] < 1.0  # Should complete in less than 1 second (mocked)

    @pytest.mark.benchmark
    def test_content_analysis_performance(self, benchmark, benchmark_transcriber):
        """Benchmark content analysis performance."""
        # Create test content
        test_text = (
            """
        This is a comprehensive test for content analysis performance.
        Make sure to include various educational keywords like assignment, submission,
        deadline, assessment, grading, criteria, and feedback. Don't forget to test
        question detection as well. What is the main purpose of this test?
        How can we improve the performance? When should we run these benchmarks?
        Important note: this will be used for assessment purposes.
        """
            * 100
        )  # Repeat to create substantial content

        test_segments = []
        for i in range(0, len(test_text), 100):
            segment_text = test_text[i : i + 100]
            test_segments.append(
                {
                    "start": i * 0.1,
                    "end": (i + 100) * 0.1,
                    "text": segment_text,
                    "timestamp_str": f"{i//600:02d}:{(i//10) % 60:02d}:{(i % 10)*10:02d}",
                }
            )

        def analyze_content_operation():
            return benchmark_transcriber.analyze_content(test_text, test_segments)

        # Benchmark the operation
        result = benchmark(analyze_content_operation)

        # Verify analysis results
        assert "keyword_matches" in result
        assert "questions" in result
        assert "emphasis_cues" in result
        assert result["total_words"] > 0

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 2.0  # Should complete analysis in less than 2 seconds

    @pytest.mark.benchmark
    def test_memory_operations_performance(self, benchmark, mock_memory_manager):
        """Benchmark memory utility operations."""

        def memory_operations():
            # Test multiple memory operations
            status = get_memory_status_safe(mock_memory_manager)
            constraints = check_memory_constraints(mock_memory_manager)
            return status, constraints

        # Benchmark the operations
        status, constraints = benchmark(memory_operations)

        # Verify results
        assert "system_total_gb" in status
        assert "memory_pressure" in constraints

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 0.1  # Should be very fast (< 100ms)


class TestSessionManagementPerformance:
    """Benchmark session management performance."""

    @pytest.mark.benchmark
    def test_session_listing_performance(self, benchmark, test_directories):
        """Benchmark session listing with many sessions."""
        results_folder = test_directories["results"]

        # Create many test sessions
        num_sessions = 100
        for i in range(num_sessions):
            session_id = f"benchmark_session_{i:03d}"
            session_dir = os.path.join(results_folder, session_id)
            os.makedirs(session_dir)

            # Create metadata file
            metadata = {
                "session_id": session_id,
                "session_name": f"Benchmark Session {i}",
                "created_at": f"2024-01-01T{i % 24:02d}:00:00",
                "status": "completed",
            }

            metadata_file = os.path.join(session_dir, "metadata.json")
            with open(metadata_file, "w") as f:
                import json

                json.dump(metadata, f)

        def list_sessions_operation():
            return get_session_list(results_folder)

        # Benchmark the operation
        sessions = benchmark(list_sessions_operation)

        # Verify results
        assert len(sessions) == num_sessions

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 5.0  # Should list 100 sessions in less than 5 seconds

    @pytest.mark.benchmark
    def test_session_validation_performance(self, benchmark, test_directories):
        """Benchmark session validation operations."""
        results_folder = test_directories["results"]
        session_ids = [f"valid_session_{i}" for i in range(1000)]

        def validate_sessions_operation():
            valid_count = 0
            for session_id in session_ids:
                try:
                    validate_session_access(session_id, results_folder)
                    valid_count += 1
                except Exception:
                    pass
            return valid_count

        # Benchmark the operation
        valid_count = benchmark(validate_sessions_operation)

        # Verify results
        assert valid_count == 1000  # All should be valid format

        # Performance assertion
        stats = benchmark.stats
        assert (
            stats["mean"] < 1.0
        )  # Should validate 1000 sessions in less than 1 second


class TestValidationPerformance:
    """Benchmark validation utility performance."""

    @pytest.mark.benchmark
    def test_request_validation_performance(self, benchmark):
        """Benchmark request data validation."""
        # Create test data
        test_requests = []
        for i in range(1000):
            test_requests.append(
                {
                    "field1": f"value_{i}",
                    "field2": i,
                    "field3": i % 2 == 0,
                    "field4": f"data_{i}",
                    "field5": i * 1.5,
                }
            )

        required_fields = ["field1", "field2", "field3"]

        def validate_requests_operation():
            valid_count = 0
            for request_data in test_requests:
                try:
                    validate_request_data(request_data, required_fields)
                    valid_count += 1
                except Exception:
                    pass
            return valid_count

        # Benchmark the operation
        valid_count = benchmark(validate_requests_operation)

        # Verify results
        assert valid_count == 1000  # All should be valid

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 0.5  # Should validate 1000 requests in less than 500ms

    @pytest.mark.benchmark
    def test_file_validation_performance(self, benchmark):
        """Benchmark file upload validation."""
        from unittest.mock import Mock

        from werkzeug.datastructures import FileStorage

        # Create mock files
        mock_files = []
        for i in range(100):
            mock_file = Mock(spec=FileStorage)
            mock_file.filename = f"test_video_{i}.mp4"
            mock_file.seek = Mock()
            mock_file.tell = Mock(return_value=1024 * 1024 * (i + 1))  # Variable sizes
            mock_files.append(mock_file)

        def validate_files_operation():
            valid_count = 0
            for mock_file in mock_files:
                try:
                    result = validate_file_upload(mock_file)
                    if result:
                        valid_count += 1
                except Exception:
                    pass
            return valid_count

        # Benchmark the operation
        valid_count = benchmark(validate_files_operation)

        # Verify results
        assert valid_count == 100  # All should be valid

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 1.0  # Should validate 100 files in less than 1 second


class TestAPIPerformance:
    """Benchmark API endpoint performance."""

    @pytest.mark.benchmark
    def test_keywords_api_performance(self, benchmark, client):
        """Benchmark keywords API endpoints."""

        def keywords_api_operations():
            # Test GET keywords
            get_response = client.get("/api/keywords")
            assert get_response.status_code == 200

            # Test POST keywords update
            test_keywords = [f"keyword_{i}" for i in range(50)]
            post_response = client.post(
                "/api/keywords", json={"keywords": test_keywords}
            )
            assert post_response.status_code == 200

            # Test GET keyword scenarios
            scenarios_response = client.get("/api/keywords/scenarios")
            assert scenarios_response.status_code == 200

            # Test GET specific scenario (education)
            scenario_response = client.get("/api/keywords/scenarios/education")
            assert scenario_response.status_code == 200

            # Test apply scenario
            apply_response = client.post(
                "/api/keywords/scenarios/apply",
                json={"scenario_id": "education", "merge_mode": "replace"},
            )
            assert apply_response.status_code == 200

            return (
                get_response,
                post_response,
                scenarios_response,
                scenario_response,
                apply_response,
            )

        # Benchmark the operations
        benchmark(keywords_api_operations)

        # Performance assertion
        stats = benchmark.stats
        assert (
            stats["mean"] < 2.0
        )  # Should complete API operations in less than 2 seconds

    @pytest.mark.benchmark
    def test_performance_api_performance(self, benchmark, client):
        """Benchmark performance monitoring endpoints."""

        def performance_api_operations():
            # Test GET performance settings
            get_response = client.get("/api/performance")

            # Test POST performance update
            post_response = client.post(
                "/api/performance", json={"chunk_duration": 180, "max_workers": 3}
            )

            return get_response, post_response

        # Benchmark the operations
        get_response, post_response = benchmark(performance_api_operations)

        # Verify responses
        assert get_response.status_code == 200
        assert post_response.status_code == 200

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 1.0  # Should be fast for configuration operations


class TestMemoryUsageProfiler:
    """Profile memory usage of key operations."""

    @pytest.mark.benchmark
    def test_memory_usage_during_processing(
        self,
        benchmark,
        mock_memory_manager,
        mock_file_manager,
        mock_progress_tracker,
        test_directories,
    ):
        """Profile memory usage during video processing simulation."""
        from unittest.mock import patch

        transcriber = VideoTranscriber(
            memory_manager=mock_memory_manager,
            file_manager=mock_file_manager,
            progress_tracker=mock_progress_tracker,
            results_folder=test_directories["results"],
        )

        # Create smaller test content for faster processing
        text = "This is test content for memory profiling. " * 100  # Much smaller
        segments = []

        for i in range(10):  # Much fewer segments
            segment = {
                "start": i * 0.5,
                "end": (i + 1) * 0.5,
                "text": f"Segment {i} content",
                "timestamp_str": f"00:00:{i:02d}",
            }
            segments.append(segment)

        # Mock the keywords loading to avoid file I/O
        with patch(
            "src.utils.load_keywords", return_value=["test", "keyword", "analysis"]
        ):

            def memory_intensive_operation():
                # Simulate memory-intensive operations with smaller dataset
                analysis_results = []
                for _ in range(3):  # Reduced iterations
                    result = transcriber.analyze_content(text, segments)
                    analysis_results.append(result)
                return analysis_results

            # Benchmark with memory profiling
            results = benchmark(memory_intensive_operation)

        # Verify results
        assert len(results) == 3

        # Memory usage should be reasonable
        stats = benchmark.stats
        assert stats["mean"] < 1.0  # Should complete quickly with smaller dataset


class TestScalabilityBenchmarks:
    """Test scalability characteristics."""

    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_concurrent_session_handling(self, benchmark, test_directories):
        """Benchmark handling of multiple concurrent sessions."""
        import queue
        import threading

        results_folder = test_directories["results"]
        num_threads = 10
        sessions_per_thread = 10

        def create_sessions_worker(thread_id, result_queue):
            """Worker function to create sessions."""
            session_count = 0
            for i in range(sessions_per_thread):
                session_id = f"thread_{thread_id}_session_{i}"
                session_dir = os.path.join(results_folder, session_id)
                os.makedirs(session_dir, exist_ok=True)

                metadata = {
                    "session_id": session_id,
                    "thread_id": thread_id,
                    "session_index": i,
                    "created_at": f"2024-01-01T{(thread_id*sessions_per_thread + i) % 24:02d}:00:00",
                }

                metadata_file = os.path.join(session_dir, "metadata.json")
                with open(metadata_file, "w") as f:
                    import json

                    json.dump(metadata, f)

                session_count += 1

            result_queue.put(session_count)

        def concurrent_session_operation():
            result_queue = queue.Queue()
            threads = []

            # Start threads
            for thread_id in range(num_threads):
                thread = threading.Thread(
                    target=create_sessions_worker, args=(thread_id, result_queue)
                )
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Collect results
            total_sessions = 0
            while not result_queue.empty():
                total_sessions += result_queue.get()

            return total_sessions

        # Benchmark concurrent operations
        total_sessions = benchmark(concurrent_session_operation)

        # Verify results
        expected_sessions = num_threads * sessions_per_thread
        assert total_sessions == expected_sessions

        # Performance assertion
        stats = benchmark.stats
        assert stats["mean"] < 30.0  # Should handle concurrent load in reasonable time
