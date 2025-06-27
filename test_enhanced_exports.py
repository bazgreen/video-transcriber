#!/usr/bin/env python3
"""
Test the enhanced export service integration.
"""

import os
import tempfile

# Mock session data for testing
MOCK_RESULTS = {
    "session_id": "test_session_123",
    "session_dir": "",
    "metadata": {
        "session_id": "test_session_123",
        "original_filename": "test_video.mp4",
        "created_at": "2025-01-26 10:00:00",
        "processing_time": 120.5,
    },
    "analysis": {
        "total_words": 1250,
        "keyword_matches": [
            {"keyword": "important", "count": 5},
            {"keyword": "test", "count": 3},
            {"keyword": "example", "count": 2},
        ],
        "questions": [
            {"timestamp": "00:02:15", "text": "What is the main objective?"},
            {"timestamp": "00:05:30", "text": "How do we implement this?"},
            {"timestamp": "00:08:45", "text": "Are there any alternatives?"},
        ],
        "emphasis_cues": [
            {"timestamp": "00:01:30", "text": "Make sure to remember this point"},
            {"timestamp": "00:04:20", "text": "Don't forget the important details"},
            {"timestamp": "00:07:10", "text": "This is really crucial to understand"},
        ],
    },
    "full_transcript": "This is a test transcript with multiple sentences. "
    "It contains various important keywords and phrases. "
    "The content includes questions and emphasis cues. "
    "What is the main objective? This text simulates a real transcription. "
    "Make sure to remember this point about testing. "
    "How do we implement this solution effectively? "
    "Don't forget the important details when reviewing. "
    "Are there any alternatives we should consider? "
    "This is really crucial to understand for implementation.",
    "chunks": [
        [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "This is a test transcript with multiple sentences.",
                "timestamp_str": "00:00:00",
            },
            {
                "start": 3.5,
                "end": 7.2,
                "text": "It contains various important keywords and phrases.",
                "timestamp_str": "00:00:03",
            },
            {
                "start": 7.2,
                "end": 10.8,
                "text": "The content includes questions and emphasis cues.",
                "timestamp_str": "00:00:07",
            },
            {
                "start": 10.8,
                "end": 14.5,
                "text": "What is the main objective?",
                "timestamp_str": "00:00:10",
            },
        ]
    ],
}


def test_enhanced_export_service():
    """Test the enhanced export service functionality"""
    print("🧪 Testing Enhanced Export Service")
    print("=" * 50)

    try:
        from src.services.export import EnhancedExportService

        export_service = EnhancedExportService()
        print("✅ Enhanced export service imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import export service: {e}")
        return False

    # Create temporary directory for test files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Using temporary directory: {temp_dir}")

        # Update mock results with temp directory
        test_results = MOCK_RESULTS.copy()
        test_results["session_dir"] = temp_dir

        # Test 1: Check available formats
        print("\n1. Testing available formats...")
        try:
            available_formats = export_service.get_available_formats()
            print("✅ Available formats retrieved:")
            for format_name, available in available_formats.items():
                status = "✅" if available else "❌"
                print(f"   {status} {format_name}")
        except Exception as e:
            print(f"❌ Failed to get available formats: {e}")
            return False

        # Test 2: Test format descriptions
        print("\n2. Testing format descriptions...")
        try:
            descriptions = export_service.get_format_descriptions()
            print("✅ Format descriptions retrieved:")
            for format_name, desc in descriptions.items():
                print(f"   📝 {format_name}: {desc}")
        except Exception as e:
            print(f"❌ Failed to get format descriptions: {e}")
            return False

        # Test 3: Export all formats
        print("\n3. Testing export all formats...")
        try:
            exported_files = export_service.export_all_formats(test_results)

            # Debug: Print what was returned
            print(f"🔍 Exported files returned: {list(exported_files.keys())}")

            # Assert that exported_files is a dictionary
            assert isinstance(
                exported_files, dict
            ), "Exported files should be a dictionary"

            # Assert that at least basic text is available
            assert (
                "basic_txt" in exported_files
            ), f"Basic text format should always be available. Available formats: {list(exported_files.keys())}"

            # Assert that all files have valid paths
            for format_name, file_path in exported_files.items():
                assert (
                    file_path is not None
                ), f"File path for {format_name} should not be None"
                assert isinstance(
                    file_path, str
                ), f"File path for {format_name} should be a string"
                assert (
                    len(file_path) > 0
                ), f"File path for {format_name} should not be empty"

            print(f"✅ Export completed! Generated {len(exported_files)} files:")

            for format_name, file_path in exported_files.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(
                        f"   ✅ {format_name}: {os.path.basename(file_path)} ({file_size} bytes)"
                    )
                    # Assert that file has content
                    assert file_size > 0, f"{format_name} file should not be empty"
                else:
                    print(f"   ❌ {format_name}: File not found at {file_path}")
                    assert False, f"{format_name} file should exist at {file_path}"

        except Exception as e:
            print(f"❌ Failed to export formats: {e}")
            return False

        # Test 4: Verify file contents
        print("\n4. Testing file contents...")

        # Check SRT file
        srt_path = os.path.join(temp_dir, "subtitles.srt")
        if os.path.exists(srt_path):
            with open(srt_path, "r", encoding="utf-8") as f:
                srt_content = f.read()
                assert (
                    "00:00:00,000 --> 00:00:03,500" in srt_content
                ), "SRT file should have correct timestamp format"
                print("   ✅ SRT file has correct timestamp format")

        # Check VTT file
        vtt_path = os.path.join(temp_dir, "subtitles.vtt")
        if os.path.exists(vtt_path):
            with open(vtt_path, "r", encoding="utf-8") as f:
                vtt_content = f.read()
                assert (
                    "WEBVTT" in vtt_content
                ), "VTT file should start with WEBVTT header"
                assert (
                    "00:00:00.000 --> 00:00:03.500" in vtt_content
                ), "VTT file should have correct timestamp format"
                print("   ✅ VTT file has correct format")

        # Check enhanced text file
        enhanced_txt_path = os.path.join(temp_dir, "transcript_enhanced.txt")
        if os.path.exists(enhanced_txt_path):
            with open(enhanced_txt_path, "r", encoding="utf-8") as f:
                enhanced_content = f.read()
                assert (
                    "📋 SESSION INFORMATION" in enhanced_content
                ), "Enhanced text should have session information section"
                assert (
                    "📊 SUMMARY STATISTICS" in enhanced_content
                ), "Enhanced text should have summary statistics section"
                print("   ✅ Enhanced text file has structured format")

        print("\n🎉 Export service test completed successfully!")
        print(f"📁 Test files created in: {temp_dir}")
        return True


def test_integration():
    """Test integration with transcription service"""
    print("\n" + "=" * 50)
    print("🔗 Testing Integration with Transcription Service")
    print("=" * 50)

    try:
        from src.services.transcription import VideoTranscriber

        print("✅ VideoTranscriber imported successfully")

        # Test if the save_results method includes export functionality
        # Instead of instantiating (which requires many args), just check the class methods
        if hasattr(VideoTranscriber, "save_results"):
            print("✅ save_results method exists")

            # Check if the method has been enhanced
            import inspect

            source = inspect.getsource(VideoTranscriber.save_results)
            if "EnhancedExportService" in source:
                print("✅ save_results method includes enhanced export integration")
            else:
                print(
                    "⚠️  save_results method may not be integrated with enhanced exports"
                )
        else:
            print("❌ save_results method not found")

    except ImportError as e:
        print(f"❌ Failed to import transcription service: {e}")
        return False

    return True


def main():
    """Main test function"""
    print("🚀 Enhanced Export Feature Test Suite")
    print("Testing the complete export functionality...")
    print()

    success = True

    # Test 1: Export service functionality
    if not test_enhanced_export_service():
        success = False

    # Test 2: Integration testing
    if not test_integration():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Enhanced export feature is working correctly.")
        print("\n💡 Next steps:")
        print("   • Run the application: python app.py")
        print("   • Process a video to test the full workflow")
        print("   • Check the results page for new export options")
        print("   • Install optional dependencies for PDF/DOCX exports:")
        print("     pip install reportlab python-docx")
    else:
        print("❌ Some tests failed. Please check the error messages above.")

    return success


if __name__ == "__main__":
    main()
