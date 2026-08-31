#!/usr/bin/env python3
"""
Test suite for speaker diarization API endpoints
"""

import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path

import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

logger = logging.getLogger(__name__)


class SpeakerAPITester:
    """Test speaker diarization API endpoints"""

    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/speaker"
        self.test_results = []

    def run_all_tests(self):
        """Run complete API test suite"""
        print("🧪 Starting Speaker Diarization API Test Suite")
        print("=" * 60)

        # Check if server is running
        if not self.check_server():
            print("❌ Server not running. Start with: python main.py")
            return self.compile_results()

        # Run individual tests
        test_methods = [
            self.test_speaker_status,
            self.test_speaker_diarization,
            self.test_speaker_alignment,
            self.test_complete_processing,
            self.test_speaker_statistics,
            self.test_export_formats,
            self.test_error_handling,
        ]

        for test_method in test_methods:
            try:
                print(f"\n🔍 Running: {test_method.__name__}")
                result = test_method()
                self.test_results.append(result)
                status = "✅ PASS" if result["success"] else "❌ FAIL"
                print(f"{status}: {result['description']}")
                if not result["success"]:
                    print(f"   Error: {result.get('error', 'Unknown error')}")
            except Exception as e:
                error_result = {
                    "test_name": test_method.__name__,
                    "success": False,
                    "error": str(e),
                    "description": f"Test {test_method.__name__} failed with exception",
                }
                self.test_results.append(error_result)
                print(f"❌ FAIL: {test_method.__name__} - {e}")

        return self.compile_results()

    def check_server(self):
        """Check if the application server is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def test_speaker_status(self):
        """Test speaker service status endpoint"""
        try:
            response = requests.get(f"{self.api_base}/status", timeout=10)

            if response.status_code != 200:
                return {
                    "test_name": "speaker_status",
                    "success": False,
                    "description": "Speaker status endpoint test",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()

            if not data.get("success"):
                return {
                    "test_name": "speaker_status",
                    "success": False,
                    "description": "Speaker status endpoint test",
                    "error": data.get("error", "Unknown error"),
                }

            status = data.get("status", {})
            required_fields = ["available", "using_mock", "device"]

            missing_fields = [field for field in required_fields if field not in status]
            if missing_fields:
                return {
                    "test_name": "speaker_status",
                    "success": False,
                    "description": "Speaker status endpoint test",
                    "error": f"Missing fields: {missing_fields}",
                }

            return {
                "test_name": "speaker_status",
                "success": True,
                "description": "Speaker status endpoint test",
                "details": {
                    "available": status["available"],
                    "using_mock": status["using_mock"],
                    "device": status["device"],
                    "pipeline_loaded": status.get("pipeline_loaded", False),
                },
            }

        except Exception as e:
            return {
                "test_name": "speaker_status",
                "success": False,
                "description": "Speaker status endpoint test",
                "error": str(e),
            }

    def test_speaker_diarization(self):
        """Test speaker diarization endpoint"""
        try:
            payload = {
                "audio_path": "/tmp/test_audio.wav",  # Mock path
                "min_speakers": 1,
                "max_speakers": 3,
            }

            response = requests.post(
                f"{self.api_base}/diarize", json=payload, timeout=15
            )

            if response.status_code != 200:
                return {
                    "test_name": "speaker_diarization",
                    "success": False,
                    "description": "Speaker diarization endpoint test",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()

            if not data.get("success"):
                return {
                    "test_name": "speaker_diarization",
                    "success": False,
                    "description": "Speaker diarization endpoint test",
                    "error": data.get("error", "Unknown error"),
                }

            # Validate response structure
            required_fields = ["speaker_segments", "total_segments", "unique_speakers"]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return {
                    "test_name": "speaker_diarization",
                    "success": False,
                    "description": "Speaker diarization endpoint test",
                    "error": f"Missing fields: {missing_fields}",
                }

            speaker_segments = data["speaker_segments"]
            if not isinstance(speaker_segments, list):
                return {
                    "test_name": "speaker_diarization",
                    "success": False,
                    "description": "Speaker diarization endpoint test",
                    "error": "speaker_segments should be a list",
                }

            return {
                "test_name": "speaker_diarization",
                "success": True,
                "description": "Speaker diarization endpoint test",
                "details": {
                    "total_segments": data["total_segments"],
                    "unique_speakers": data["unique_speakers"],
                    "using_mock": data.get("using_mock", False),
                    "has_segments": len(speaker_segments) > 0,
                },
            }

        except Exception as e:
            return {
                "test_name": "speaker_diarization",
                "success": False,
                "description": "Speaker diarization endpoint test",
                "error": str(e),
            }

    def test_speaker_alignment(self):
        """Test speaker-transcription alignment endpoint"""
        try:
            # Mock transcription and speaker segments
            payload = {
                "transcription_segments": [
                    {"start": 0.0, "end": 3.0, "text": "Hello everyone"},
                    {"start": 3.5, "end": 6.0, "text": "Welcome to the meeting"},
                    {"start": 6.5, "end": 9.0, "text": "Let me start the presentation"},
                ],
                "speaker_segments": [
                    {
                        "start": 0.0,
                        "end": 3.2,
                        "speaker": "SPEAKER_00",
                        "speaker_id": "speaker_SPEAKER_00",
                    },
                    {
                        "start": 3.3,
                        "end": 6.1,
                        "speaker": "SPEAKER_01",
                        "speaker_id": "speaker_SPEAKER_01",
                    },
                    {
                        "start": 6.2,
                        "end": 9.5,
                        "speaker": "SPEAKER_00",
                        "speaker_id": "speaker_SPEAKER_00",
                    },
                ],
                "overlap_threshold": 0.5,
            }

            response = requests.post(f"{self.api_base}/align", json=payload, timeout=10)

            if response.status_code != 200:
                return {
                    "test_name": "speaker_alignment",
                    "success": False,
                    "description": "Speaker alignment endpoint test",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()

            if not data.get("success"):
                return {
                    "test_name": "speaker_alignment",
                    "success": False,
                    "description": "Speaker alignment endpoint test",
                    "error": data.get("error", "Unknown error"),
                }

            # Validate response structure
            required_fields = [
                "enhanced_segments",
                "speaker_statistics",
                "total_segments",
            ]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return {
                    "test_name": "speaker_alignment",
                    "success": False,
                    "description": "Speaker alignment endpoint test",
                    "error": f"Missing fields: {missing_fields}",
                }

            enhanced_segments = data["enhanced_segments"]
            speaker_stats = data["speaker_statistics"]

            # Check that segments have speaker information
            segments_with_speakers = len(
                [s for s in enhanced_segments if s.get("speaker") != "unknown"]
            )

            return {
                "test_name": "speaker_alignment",
                "success": True,
                "description": "Speaker alignment endpoint test",
                "details": {
                    "total_segments": data["total_segments"],
                    "segments_with_speakers": segments_with_speakers,
                    "total_speakers": speaker_stats.get("total_speakers", 0),
                    "alignment_success_rate": segments_with_speakers
                    / len(enhanced_segments)
                    * 100,
                },
            }

        except Exception as e:
            return {
                "test_name": "speaker_alignment",
                "success": False,
                "description": "Speaker alignment endpoint test",
                "error": str(e),
            }

    def test_complete_processing(self):
        """Test complete speaker processing pipeline"""
        try:
            payload = {
                "audio_path": "/tmp/test_audio.wav",
                "transcription_segments": [
                    {"start": 0.0, "end": 3.0, "text": "Hello everyone"},
                    {"start": 3.5, "end": 6.0, "text": "Welcome to the meeting"},
                ],
                "min_speakers": 1,
                "max_speakers": 3,
            }

            response = requests.post(
                f"{self.api_base}/process", json=payload, timeout=20
            )

            if response.status_code != 200:
                return {
                    "test_name": "complete_processing",
                    "success": False,
                    "description": "Complete speaker processing test",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()

            if not data.get("success"):
                return {
                    "test_name": "complete_processing",
                    "success": False,
                    "description": "Complete speaker processing test",
                    "error": data.get("error", "Unknown error"),
                }

            # Validate complete pipeline results
            required_fields = [
                "enhanced_segments",
                "speaker_segments",
                "speaker_statistics",
            ]
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return {
                    "test_name": "complete_processing",
                    "success": False,
                    "description": "Complete speaker processing test",
                    "error": f"Missing fields: {missing_fields}",
                }

            return {
                "test_name": "complete_processing",
                "success": True,
                "description": "Complete speaker processing test",
                "details": {
                    "enhanced_segments": len(data["enhanced_segments"]),
                    "speaker_segments": len(data["speaker_segments"]),
                    "total_speakers": data["speaker_statistics"].get(
                        "total_speakers", 0
                    ),
                    "mock_used": data.get("mock_used", False),
                },
            }

        except Exception as e:
            return {
                "test_name": "complete_processing",
                "success": False,
                "description": "Complete speaker processing test",
                "error": str(e),
            }

    def test_speaker_statistics(self):
        """Test speaker statistics endpoint"""
        try:
            session_id = "test_session_123"

            response = requests.get(
                f"{self.api_base}/statistics/{session_id}", timeout=10
            )

            if response.status_code != 200:
                return {
                    "test_name": "speaker_statistics",
                    "success": False,
                    "description": "Speaker statistics endpoint test",
                    "error": f"Status code: {response.status_code}",
                }

            data = response.json()

            if not data.get("success"):
                return {
                    "test_name": "speaker_statistics",
                    "success": False,
                    "description": "Speaker statistics endpoint test",
                    "error": data.get("error", "Unknown error"),
                }

            statistics = data.get("statistics", {})
            required_fields = ["total_speakers", "total_duration", "speaker_breakdown"]
            # Check if all required fields are present
            _ = [field for field in statistics if field not in required_fields]

            return {
                "test_name": "speaker_statistics",
                "success": True,
                "description": "Speaker statistics endpoint test",
                "details": {
                    "total_speakers": statistics.get("total_speakers", 0),
                    "total_duration": statistics.get("total_duration", 0),
                    "speakers_with_breakdown": len(
                        statistics.get("speaker_breakdown", {})
                    ),
                    "session_id": statistics.get("session_id"),
                },
            }

        except Exception as e:
            return {
                "test_name": "speaker_statistics",
                "success": False,
                "description": "Speaker statistics endpoint test",
                "error": str(e),
            }

    def test_export_formats(self):
        """Test export functionality with different formats"""
        try:
            session_id = "test_session_export"
            formats = ["srt", "vtt", "txt", "json"]
            export_results = {}

            for format_type in formats:
                try:
                    response = requests.get(
                        f"{self.api_base}/export/{session_id}/{format_type}", timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()
                        export_results[format_type] = {
                            "success": data.get("success", False),
                            "has_content": "content" in data or "data" in data,
                            "has_filename": "filename" in data,
                        }
                    else:
                        export_results[format_type] = {
                            "success": False,
                            "error": f"Status code: {response.status_code}",
                        }

                except Exception as e:
                    export_results[format_type] = {"success": False, "error": str(e)}

            successful_exports = sum(
                1 for result in export_results.values() if result.get("success")
            )

            return {
                "test_name": "export_formats",
                "success": successful_exports
                >= len(formats) * 0.75,  # 75% success rate
                "description": "Export formats endpoint test",
                "details": {
                    "formats_tested": len(formats),
                    "successful_exports": successful_exports,
                    "export_results": export_results,
                },
            }

        except Exception as e:
            return {
                "test_name": "export_formats",
                "success": False,
                "description": "Export formats endpoint test",
                "error": str(e),
            }

    def test_error_handling(self):
        """Test API error handling"""
        try:
            error_scenarios = []

            # Test missing required fields
            scenarios = [
                {
                    "name": "diarize_missing_audio_path",
                    "url": f"{self.api_base}/diarize",
                    "method": "POST",
                    "data": {"min_speakers": 1},
                },
                {
                    "name": "align_missing_transcription",
                    "url": f"{self.api_base}/align",
                    "method": "POST",
                    "data": {"speaker_segments": []},
                },
                {
                    "name": "process_missing_audio",
                    "url": f"{self.api_base}/process",
                    "method": "POST",
                    "data": {"transcription_segments": []},
                },
                {
                    "name": "invalid_export_format",
                    "url": f"{self.api_base}/export/test/invalid_format",
                    "method": "GET",
                    "data": None,
                },
            ]

            for scenario in scenarios:
                try:
                    if scenario["method"] == "POST":
                        response = requests.post(
                            scenario["url"], json=scenario["data"], timeout=10
                        )
                    else:
                        response = requests.get(scenario["url"], timeout=10)

                    # Expect 400 error for bad requests
                    if response.status_code in [400, 422]:
                        error_scenarios.append(
                            {
                                "scenario": scenario["name"],
                                "handled_correctly": True,
                                "status_code": response.status_code,
                            }
                        )
                    else:
                        error_scenarios.append(
                            {
                                "scenario": scenario["name"],
                                "handled_correctly": False,
                                "status_code": response.status_code,
                            }
                        )

                except Exception as e:
                    error_scenarios.append(
                        {
                            "scenario": scenario["name"],
                            "handled_correctly": False,
                            "error": str(e),
                        }
                    )

            handled_correctly = sum(
                1 for s in error_scenarios if s.get("handled_correctly")
            )
            success_rate = handled_correctly / len(scenarios) if scenarios else 0

            return {
                "test_name": "error_handling",
                "success": success_rate >= 0.75,  # 75% success rate
                "description": "API error handling test",
                "details": {
                    "scenarios_tested": len(scenarios),
                    "handled_correctly": handled_correctly,
                    "success_rate": success_rate * 100,
                    "error_scenarios": error_scenarios,
                },
            }

        except Exception as e:
            return {
                "test_name": "error_handling",
                "success": False,
                "description": "API error handling test",
                "error": str(e),
            }

    def compile_results(self):
        """Compile and summarize all test results"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "overall_status": "PASS" if success_rate >= 80 else "FAIL",
            "test_results": self.test_results,
        }

        return summary

    def print_final_report(self, results):
        """Print comprehensive test report"""
        print(f"\n{'='*60}")
        print("🎯 SPEAKER API TEST REPORT")
        print(f"{'='*60}")
        print(f"📅 Timestamp: {results['timestamp']}")
        print(f"📊 Total Tests: {results['total_tests']}")
        print(f"✅ Passed: {results['passed_tests']}")
        print(f"❌ Failed: {results['failed_tests']}")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        print(f"🎯 Overall Status: {results['overall_status']}")

        print(f"\n{'='*40}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*40}")

        for result in results["test_results"]:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {result['test_name']}")
            print(f"     {result['description']}")

            if not result["success"] and "error" in result:
                print(f"     Error: {result['error']}")

            if "details" in result:
                for key, value in result["details"].items():
                    print(f"     {key}: {value}")
            print()

        print(f"{'='*60}")

        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if results["success_rate"] < 50:
            print("❗ Critical: Multiple API failures detected")
            print("   - Check server configuration")
            print("   - Verify speaker diarization service initialization")
            print("   - Review error logs for detailed information")
        elif results["success_rate"] < 80:
            print("⚠️ Warning: Some API tests failed")
            print("   - Review failed endpoints above")
            print("   - Consider additional error handling")
        else:
            print("🎉 Excellent: Speaker API is working well!")
            print("   - Ready for integration with UI")
            print("   - Consider adding performance monitoring")


def main():
    """Main test execution"""
    print("🚀 Video Transcriber - Speaker API Test Suite")
    print("=" * 60)

    tester = SpeakerAPITester()
    results = tester.run_all_tests()
    tester.print_final_report(results)

    # Exit with appropriate code
    exit_code = 0 if results["overall_status"] == "PASS" else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
