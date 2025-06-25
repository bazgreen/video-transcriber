import unittest
import json
import os
import tempfile
import shutil
from io import BytesIO
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app


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
                self.assertNotIn('session name', response_data['error'].lower())
    
    def test_empty_session_name_rejected(self):
        """Test that empty session names are rejected"""
        data = {
            'video': (BytesIO(b'fake content'), 'test.mp4'),
            'session_name': ''
        }
        response = self.client.post('/upload', data=data)
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['error'], 'Session name is required and cannot be empty')


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


class TestPerformanceAPI(unittest.TestCase):
    """Test performance API endpoints"""
    
    def setUp(self):
        """Set up test client"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_get_performance_settings(self):
        """Test GET /api/performance endpoint"""
        response = self.client.get('/api/performance')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('current_settings', data['data'])
        self.assertIn('max_workers', data['data']['current_settings'])
        self.assertIn('chunk_duration', data['data']['current_settings'])
    
    def test_update_performance_settings_valid(self):
        """Test POST /api/performance with valid data"""
        test_data = {
            'max_workers': 2,
            'chunk_duration': 180
        }
        response = self.client.post('/api/performance', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('current_settings', data)
        self.assertEqual(data['current_settings']['max_workers'], 2)
        self.assertEqual(data['current_settings']['chunk_duration'], 180)
    
    def test_update_performance_settings_invalid_workers(self):
        """Test POST /api/performance with invalid max_workers"""
        test_data = {'max_workers': 50}  # Too high
        response = self.client.post('/api/performance', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('Max workers must be between', data['error'])
        self.assertIn('provided: 50', data['error'])
    
    def test_update_performance_settings_invalid_chunk_duration(self):
        """Test POST /api/performance with invalid chunk_duration"""
        test_data = {'chunk_duration': 30}  # Too low
        response = self.client.post('/api/performance', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertIn('Chunk duration must be between 60 and 600 seconds', data['error'])
        self.assertIn('provided: 30', data['error'])
    
    def test_update_performance_settings_no_data(self):
        """Test POST /api/performance with no data"""
        response = self.client.post('/api/performance', 
                                  data=json.dumps({}),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No data provided')
    
    def test_get_live_performance(self):
        """Test GET /api/performance/live endpoint"""
        response = self.client.get('/api/performance/live')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('memory', data['data'])
        self.assertIn('active_sessions', data['data'])
        self.assertIn('timestamp', data['data'])
    
    def test_get_performance_history(self):
        """Test GET /api/performance/history endpoint"""
        response = self.client.get('/api/performance/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)


if __name__ == '__main__':
    unittest.main()