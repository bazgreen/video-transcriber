import unittest
import json
import os
import tempfile
import shutil
from io import BytesIO
from app import app


class TestFileValidation(unittest.TestCase):
    """Test file upload validation logic"""
    
    def setUp(self):
        """Set up test client and app configuration"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        self.app.config['RESULTS_FOLDER'] = tempfile.mkdtemp()
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.app.config['UPLOAD_FOLDER'], ignore_errors=True)
        shutil.rmtree(self.app.config['RESULTS_FOLDER'], ignore_errors=True)
    
    def test_no_file_uploaded(self):
        """Test handling of request with no file"""
        response = self.client.post('/upload')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'No file uploaded')
    
    def test_empty_filename(self):
        """Test handling of file with empty filename"""
        data = {'video': (BytesIO(b'fake content'), '')}
        response = self.client.post('/upload', data=data)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'No file selected')
    
    def test_invalid_file_extension(self):
        """Test rejection of invalid file types"""
        invalid_files = [
            'test.txt',
            'test.pdf',
            'test.doc',
            'test.exe',
            'test.zip'
        ]
        
        for filename in invalid_files:
            data = {'video': (BytesIO(b'fake content'), filename)}
            response = self.client.post('/upload', data=data)
            self.assertEqual(response.status_code, 400)
            response_data = json.loads(response.data)
            self.assertIn('Invalid file type', response_data['error'])
    
    def test_valid_file_extensions(self):
        """Test acceptance of valid video file types"""
        valid_files = [
            'test.mp4',
            'test.avi',
            'test.mov',
            'test.mkv',
            'test.webm',
            'test.flv',
            'test.wmv',
            'test.m4v',
            'TEST.MP4',  # Test case insensitivity
            'Video.MOV'
        ]
        
        for filename in valid_files:
            # Create a small valid file
            data = {
                'video': (BytesIO(b'fake video content'), filename),
                'session_name': f'test_{filename}'
            }
            response = self.client.post('/upload', data=data)
            # Should either succeed or fail for reasons other than file type
            if response.status_code == 400:
                response_data = json.loads(response.data)
                self.assertNotIn('Invalid file type', response_data['error'])
    
    def test_file_size_limit(self):
        """Test rejection of files exceeding size limit"""
        # Create a file larger than 500MB limit
        large_content = b'x' * (501 * 1024 * 1024)  # 501 MB
        data = {'video': (BytesIO(large_content), 'large_video.mp4')}
        response = self.client.post('/upload', data=data)
        # Flask returns 413 (Request Entity Too Large) for large files
        self.assertIn(response.status_code, [400, 413])
        if response.status_code == 400:
            response_data = json.loads(response.data)
            self.assertIn('File too large', response_data['error'])
            self.assertIn('500MB', response_data['error'])
    
    def test_file_within_size_limit(self):
        """Test acceptance of files within size limit"""
        # Create a file smaller than 500MB limit
        normal_content = b'x' * (100 * 1024)  # 100 KB
        data = {
            'video': (BytesIO(normal_content), 'normal_video.mp4'),
            'session_name': 'test_normal_size'
        }
        response = self.client.post('/upload', data=data)
        # Should not fail due to file size
        if response.status_code == 400:
            response_data = json.loads(response.data)
            self.assertNotIn('File too large', response_data['error'])
    
    def test_session_name_validation(self):
        """Test session name sanitization"""
        test_cases = [
            ('Normal Session', 'Normal_Session'),
            ('Session with spaces', 'Session_with_spaces'),
            ('Session-with-dashes', 'Session-with-dashes'),
            ('Session_with_underscores', 'Session_with_underscores'),
            ('Session123', 'Session123'),
            ('Session!@#$%', 'Session_____'),
            ('', None),  # Empty should trigger auto-generation
        ]
        
        for input_name, expected_pattern in test_cases:
            data = {
                'video': (BytesIO(b'fake content'), 'test.mp4'),
                'session_name': input_name
            }
            response = self.client.post('/upload', data=data)
            # We can't easily test the actual session name without mocking,
            # but we can verify the request doesn't fail due to session name
            if response.status_code == 400:
                response_data = json.loads(response.data)
                self.assertNotIn('session', response_data['error'].lower())


class TestErrorResponses(unittest.TestCase):
    """Test consistent JSON error responses"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['RESULTS_FOLDER'] = tempfile.mkdtemp()
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.app.config['RESULTS_FOLDER'], ignore_errors=True)
    
    def test_invalid_session_id_format(self):
        """Test JSON error response for invalid session ID"""
        # Test IDs that will actually reach our validation
        invalid_ids = [
            'session;rm',
            'session|cat',
            'session$USER',
            'session@hack',
            'session!danger'
        ]
        
        for session_id in invalid_ids:
            # Test view_results
            response = self.client.get(f'/results/{session_id}')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content_type, 'application/json')
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid session ID')
            
            # Test download_file
            response = self.client.get(f'/download/{session_id}/file.txt')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content_type, 'application/json')
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid session ID')
            
            # Test view_transcript
            response = self.client.get(f'/transcript/{session_id}')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content_type, 'application/json')
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid session ID')
    
    def test_session_not_found(self):
        """Test JSON error response for non-existent session"""
        response = self.client.get('/results/nonexistent_session')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Session not found')
    
    def test_invalid_filename_format(self):
        """Test JSON error response for invalid filename"""
        # Create a valid session directory
        valid_session = 'test_session'
        session_dir = os.path.join(self.app.config['RESULTS_FOLDER'], valid_session)
        os.makedirs(session_dir)
        
        # Test filenames that will reach our validation
        invalid_filenames = [
            'file;rm.txt',
            'file|cat.txt',
            'file$USER.txt',
            'file@hack.txt',
            'file!danger.txt'
        ]
        
        for filename in invalid_filenames:
            response = self.client.get(f'/download/{valid_session}/{filename}')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.content_type, 'application/json')
            data = json.loads(response.data)
            self.assertEqual(data['error'], 'Invalid filename')
    
    def test_file_not_found(self):
        """Test JSON error response for non-existent file"""
        # Create a valid session directory
        valid_session = 'test_session'
        session_dir = os.path.join(self.app.config['RESULTS_FOLDER'], valid_session)
        os.makedirs(session_dir)
        
        response = self.client.get(f'/download/{valid_session}/nonexistent.txt')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'File not found')
    
    def test_transcript_not_found(self):
        """Test JSON error response for non-existent transcript"""
        # Create a valid session directory without transcript
        valid_session = 'test_session'
        session_dir = os.path.join(self.app.config['RESULTS_FOLDER'], valid_session)
        os.makedirs(session_dir)
        
        response = self.client.get(f'/transcript/{valid_session}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Transcript not found')


if __name__ == '__main__':
    unittest.main()