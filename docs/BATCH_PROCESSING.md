# Batch Processing System

## Overview

The batch processing system enables users to efficiently process multiple video files concurrently with automatic resource management, progress tracking, and result aggregation.

## Features

### 🔄 Core Capabilities
- **Concurrent Processing**: Process 1-5 videos simultaneously with configurable limits
- **Memory-Aware Scheduling**: Automatic resource optimization based on system memory
- **Real-time Progress Tracking**: Live updates on batch and individual job progress
- **Persistent Metadata**: Batch information survives application restarts
- **Background Processing**: Non-blocking operation with threading

### 📊 User Interface
- **Modern Web Interface**: Responsive batch processing page at `/batch`
- **Drag-and-Drop Upload**: Intuitive file selection and queue management
- **Progress Visualization**: Real-time progress bars and status indicators
- **Batch Management**: Start, cancel, delete, and monitor batches
- **Statistics Dashboard**: Overview of processing metrics

### 🚀 Export & Results
- **Individual Results**: Each video processed with unique session
- **Batch Aggregation**: Combined results view and management
- **ZIP Export**: Download all batch results in a single archive
- **Session Grouping**: Organized results with meaningful names

## Architecture

### Service Layer

#### BatchProcessor
The main service class that orchestrates batch processing:

```python
from src.services.batch_processing import batch_processor

# Create a new batch
batch_id = batch_processor.create_batch(
    name="Marketing Videos Batch",
    max_concurrent=3
)

# Add videos to the batch
job_id = batch_processor.add_video_to_batch(
    batch_id=batch_id,
    file_path="/uploads/video1.mp4",
    original_filename="marketing_video_1.mp4",
    session_name="Marketing Video 1"
)

# Start processing
batch_processor.start_batch(batch_id)
```

#### Core Classes

**BatchSession**: Represents a collection of video jobs
- Manages multiple `BatchJob` instances
- Tracks overall progress and status
- Handles concurrent execution limits
- Persists metadata to disk

**BatchJob**: Represents a single video processing task
- Tracks individual video processing state
- Stores file paths and session information
- Monitors progress and handles errors
- Links to transcription results

### API Endpoints

#### Batch Management
- `POST /api/batch/create` - Create new batch
- `GET /api/batch/list` - List all batches
- `GET /api/batch/<id>` - Get batch details
- `DELETE /api/batch/<id>` - Delete batch

#### Video Management
- `POST /api/batch/add-video` - Add video to batch
- `POST /api/batch/<id>/start` - Start batch processing
- `POST /api/batch/<id>/cancel` - Cancel batch

#### Results & Export
- `GET /api/batch/<id>/results` - Get batch results
- `GET /api/batch/<id>/download` - Download ZIP archive

### Data Models

#### Batch Status States
```python
class BatchStatus(Enum):
    PENDING = "pending"      # Created, videos can be added
    PROCESSING = "processing" # Currently running
    COMPLETED = "completed"   # All jobs finished
    FAILED = "failed"        # All jobs failed
    CANCELLED = "cancelled"  # User cancelled
```

#### Video Job States
```python
class VideoStatus(Enum):
    QUEUED = "queued"        # Waiting to process
    PROCESSING = "processing" # Currently being processed
    COMPLETED = "completed"   # Successfully finished
    FAILED = "failed"        # Processing failed
    SKIPPED = "skipped"      # Cancelled before processing
```

## Usage Examples

### Basic Batch Processing

```javascript
// Create a new batch
const response = await fetch('/api/batch/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        name: 'Conference Recordings',
        max_concurrent: 2
    })
});

const { batch_id } = await response.json();

// Add videos
const formData = new FormData();
formData.append('file', videoFile);
formData.append('batch_id', batch_id);
formData.append('session_name', 'Day 1 Keynote');

await fetch('/api/batch/add-video', {
    method: 'POST',
    body: formData
});

// Start processing
await fetch(`/api/batch/${batch_id}/start`, {
    method: 'POST'
});
```

### Progress Monitoring

```javascript
// Poll for batch progress
async function monitorBatch(batchId) {
    const response = await fetch(`/api/batch/${batchId}`);
    const { batch } = await response.json();
    
    console.log(`Progress: ${batch.progress.progress_percentage}%`);
    console.log(`Completed: ${batch.progress.completed_jobs}/${batch.progress.total_jobs}`);
    
    if (batch.status === 'processing') {
        setTimeout(() => monitorBatch(batchId), 3000);
    }
}
```

### Result Download

```javascript
// Download all results as ZIP
function downloadBatchResults(batchId) {
    window.location.href = `/api/batch/${batchId}/download`;
}
```

## Configuration

### Memory Management
The system automatically determines optimal concurrency based on available memory:

```python
# Low memory systems (< 8GB available)
max_concurrent = min(optimal_workers, 2)

# Higher memory systems (>= 8GB available)  
max_concurrent = min(optimal_workers, 3)

# Manual override (1-5 videos)
batch_processor.create_batch(max_concurrent=4)
```

### File Storage
- **Uploads**: Stored in `uploads/` directory with unique names
- **Results**: Individual sessions in `results/<session_id>/`
- **Metadata**: Batch information in `results/batches/<batch_id>.json`

## Error Handling

### Batch Level Errors
- **Empty Batch**: Cannot start batch with no videos
- **Invalid State**: Cannot modify processing/completed batches
- **Resource Limits**: Automatic fallback for memory constraints

### Job Level Errors
- **File Upload Failures**: Individual videos can fail without affecting others
- **Processing Errors**: Jobs marked as failed with error messages
- **Timeout Handling**: Long-running jobs have appropriate timeouts

### Recovery Mechanisms
- **Graceful Degradation**: Failed jobs don't stop entire batch
- **State Persistence**: Batch state survives application restarts
- **Partial Results**: Access completed jobs even if others fail

## Performance Optimization

### Resource Management
- **Memory Monitoring**: Real-time memory usage tracking
- **Worker Scaling**: Dynamic adjustment based on system load
- **Concurrent Limits**: Configurable per-batch concurrency
- **Background Processing**: Non-blocking UI operations

### Efficiency Features
- **Progress Callbacks**: Minimal overhead progress updates
- **Lazy Loading**: Results loaded only when requested
- **Batch Aggregation**: Efficient bulk operations
- **ZIP Streaming**: Memory-efficient archive creation

## Security Considerations

### Input Validation
- **File Type Checking**: Only video files accepted
- **Size Limits**: Configurable maximum file sizes
- **Path Sanitization**: Secure filename handling
- **Session Validation**: Proper session ID validation

### CSRF Protection
- **API Exemptions**: Batch endpoints exempt from CSRF
- **Token Validation**: Proper authentication where required
- **Cross-Origin**: Configured CORS for legitimate requests

## Testing

### Unit Tests
Comprehensive test suite covering:

```bash
# Run batch processing tests
python -m pytest tests/unit/services/test_batch_processing.py -v
```

Test coverage includes:
- Batch creation and management
- Video addition and processing
- Progress calculation and tracking
- Metadata persistence and loading
- Error handling and recovery
- Serialization and deserialization

### Integration Tests
- API endpoint testing
- File upload validation
- Real video processing workflows
- Multi-user scenarios

## Troubleshooting

### Common Issues

#### Batch Not Starting
```python
# Check if batch has videos
batch = batch_processor.get_batch(batch_id)
if not batch.jobs:
    print("Batch is empty - add videos first")

# Check transcriber initialization
if not batch_processor.transcriber:
    print("Transcriber not initialized")
```

#### Memory Issues
```python
# Check available memory
memory_info = batch_processor.memory_manager.get_memory_info()
print(f"Available: {memory_info['system_available_gb']:.1f}GB")

# Reduce concurrency
batch_processor.create_batch(max_concurrent=1)
```

#### File Upload Errors
- Verify file formats (MP4, AVI, MOV, etc.)
- Check file size limits (500MB default)
- Ensure sufficient disk space
- Validate upload directory permissions

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('src.services.batch_processing').setLevel(logging.DEBUG)
```

Monitor batch metadata:
```bash
# View batch metadata files
ls -la results/batches/
cat results/batches/<batch_id>.json
```

## Future Enhancements

### Planned Features
- **Email Notifications**: Completion alerts
- **Scheduling**: Delayed batch processing
- **Priority Queues**: High-priority batch handling
- **Cloud Storage**: S3/GCS integration
- **Webhooks**: External system notifications

### API Extensions
- **Bulk Operations**: Multiple batch management
- **Template Batches**: Reusable batch configurations
- **Advanced Filtering**: Complex result queries
- **Export Formats**: Additional result formats

### Performance Improvements
- **Distributed Processing**: Multi-node execution
- **Caching Layer**: Redis/Memcached integration
- **Database Backend**: PostgreSQL/MySQL support
- **Queue Systems**: RabbitMQ/Celery integration

## Migration Guide

### From Single Processing
Users familiar with single video processing can easily adopt batch processing:

1. **Create Batch**: Replace single upload with batch creation
2. **Add Videos**: Upload multiple files to the batch
3. **Monitor Progress**: Use batch progress instead of single job
4. **Download Results**: Get all results in one archive

### Backward Compatibility
- Existing single video processing remains unchanged
- Batch results use same session format
- All export features work with batch sessions
- API versioning maintains compatibility
