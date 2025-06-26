# Performance Optimization Features

This document describes the comprehensive performance optimization features implemented in the video transcriber project.

## Overview

The performance optimization system provides intelligent resource management, dynamic scaling, and memory-aware processing to ensure optimal performance across different system configurations.

## Key Features

### 1. Enhanced Configuration Settings

#### File Upload Limits

- **Increased maximum file size**: From 500MB to 1GB
- **Chunked upload support**: 50MB chunks for better handling of large files
- **Progressive processing**: Files are processed in optimally-sized chunks

#### Worker Optimization

- **Minimum workers**: Increased from 1 to 2 for better responsiveness
- **Maximum workers**: Increased from 14 to 16 for high-performance systems
- **Default workers**: Increased from 4 to 6 for better throughput
- **Dynamic scaling**: Workers are adjusted based on system resources and file size

#### Performance Features

- **Parallel upload processing**: Enabled by default for large files
- **Automatic memory cleanup**: Enabled to prevent memory leaks
- **Dynamic chunk size optimization**: Adapts to video characteristics
- **Extended timeouts**: Better handling of large file processing

### 2. Advanced Performance Optimizer

#### Intelligent Resource Management

```python
from src.utils.performance_optimizer import performance_optimizer

# Get optimal worker count for current system
optimal_workers = performance_optimizer.get_optimal_worker_count()

# Get performance recommendations
recommendations = performance_optimizer.get_performance_recommendations()

# Optimize memory usage
memory_result = performance_optimizer.optimize_memory_usage()
```

#### Dynamic Worker Scaling

- **CPU-based scaling**: Considers available CPU cores
- **Memory-aware adjustment**: Reduces workers on memory-constrained systems
- **File size consideration**: Scales workers based on input file size
- **Safety limits**: Respects configured minimum and maximum worker limits

#### Memory Optimization

- **Automatic garbage collection**: Periodic cleanup of unused objects
- **Memory pressure detection**: Monitors system memory usage
- **Conservative fallbacks**: Safe defaults when system monitoring unavailable
- **Process memory tracking**: Monitors application memory usage

### 3. API Endpoints

#### Performance Status

```http
GET /api/performance
```

Returns current performance settings and system status.

#### Performance Optimization

```http
GET /api/performance/optimization
```

Provides detailed performance recommendations and system analysis.

#### Apply Optimizations

```http
POST /api/performance/optimize
```

Applies performance optimizations based on current system state.

## Configuration Options

### AppConfig Enhancements

```python
# File handling
MAX_FILE_SIZE_BYTES = 1024 * 1024 * 1024  # 1GB
CHUNK_UPLOAD_SIZE = 50 * 1024 * 1024      # 50MB

# Performance features
ENABLE_PARALLEL_UPLOAD = True
ENABLE_MEMORY_CLEANUP = True
CHUNK_SIZE_OPTIMIZATION = True
```

### PerformanceConfig Updates

```python
# Worker configuration
MIN_WORKERS = 2
MAX_WORKERS_LIMIT = 16
DEFAULT_MAX_WORKERS = 6

# Memory thresholds
LOW_MEMORY_THRESHOLD_GB = 4.0
HIGH_MEMORY_THRESHOLD_GB = 16.0
MEMORY_SAFETY_FACTOR = 0.8

# Processing timeouts
PROCESSING_TIMEOUT_SECONDS = 1800  # 30 minutes
LARGE_FILE_TIMEOUT_SECONDS = 3600  # 60 minutes
```

## Performance Recommendations

The system automatically generates intelligent recommendations based on:

1. **System Resources**
   - Available CPU cores
   - Available memory
   - Current memory usage

2. **Configuration State**
   - Current worker settings
   - Feature enablement status
   - Processing timeouts

3. **Runtime Conditions**
   - Memory pressure
   - Processing queue status
   - Recent performance metrics

### Example Recommendations

- "High-performance system detected (14 cores) - consider increasing max workers to 14"
- "Low available memory - enable memory cleanup and use smaller chunk sizes"
- "Parallel upload enabled - large files will be processed more efficiently"
- "Dynamic chunk sizing enabled - processing will adapt to video characteristics"

## Usage Examples

### Basic Usage

```python
# Get current optimal settings
optimizer = performance_optimizer
recommendations = optimizer.get_performance_recommendations()
optimal_workers = optimizer.get_optimal_worker_count()

# Apply memory optimizations
memory_result = optimizer.optimize_memory_usage()
```

### Integration with Transcription Service

```python
# The transcription service automatically uses performance optimizer
from src.services.transcription import VideoTranscriptionService

# Performance optimizer is integrated into video splitting
service = VideoTranscriptionService(...)
chunks = service.split_video_with_optimization(video_path, duration)
```

### API Integration

```javascript
// Get performance recommendations
const response = await fetch('/api/performance/optimization');
const data = await response.json();
console.log('Recommendations:', data.recommendations);

// Apply optimizations
await fetch('/api/performance/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_memory_cleanup: true })
});
```

## Memory Management

### Safe Memory Status

The system provides robust memory monitoring with fallbacks:

- **Primary**: Uses psutil for detailed system information
- **Secondary**: Attempts to use application memory manager
- **Fallback**: Conservative estimates when monitoring unavailable

### Memory Optimization Features

- **Garbage collection**: Automatic cleanup of unused objects
- **Memory pressure detection**: Monitors system memory usage
- **Worker adjustment**: Reduces workers when memory is constrained
- **Chunk size adaptation**: Smaller chunks for memory-limited systems

## Testing

### Performance Validation

```bash
# Test performance optimizer functionality
python -c "
from src.utils.performance_optimizer import performance_optimizer
print('Recommendations:', performance_optimizer.get_performance_recommendations())
print('Optimal workers:', performance_optimizer.get_optimal_worker_count())
"

# Test API endpoints (requires server running)
python test_performance_endpoints.py
```

### Benchmarking

The system includes performance benchmarks in `tests/benchmarks/test_performance.py`:

- Memory usage tracking
- Processing time measurement
- Worker efficiency analysis
- System resource utilization

## Monitoring

### Performance Metrics

- **Memory usage**: System and process memory consumption
- **Worker utilization**: Number of active workers and efficiency
- **Processing times**: Time taken for various operations
- **Resource availability**: CPU and memory availability

### Logging

Performance operations are logged with detailed information:

```
INFO: Performance optimization completed - memory cleaned: 150MB
INFO: Optimal workers calculated: 8 (based on 14 cores, 12GB available)
WARNING: Memory pressure detected: 92% usage
```

## Best Practices

1. **System Monitoring**
   - Regularly check performance recommendations
   - Monitor memory usage during large file processing
   - Adjust worker counts based on system capabilities

2. **Configuration Tuning**
   - Increase workers on high-performance systems
   - Enable memory cleanup for long-running processes
   - Use chunk size optimization for varied video content

3. **Resource Management**
   - Monitor system resources during processing
   - Apply memory optimizations periodically
   - Use appropriate timeouts for large files

## Future Enhancements

Planned improvements include:

- **Historical performance tracking**: Database storage of performance metrics
- **Predictive scaling**: ML-based worker count prediction
- **Advanced memory management**: More sophisticated memory optimization strategies
- **Real-time monitoring**: Live performance dashboards
- **Automated tuning**: Self-adjusting configuration based on usage patterns

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that psutil is available for detailed system monitoring

2. **Memory Issues**
   - Enable memory cleanup in configuration
   - Reduce worker count on memory-constrained systems
   - Use smaller chunk sizes for large files

3. **Performance Degradation**
   - Check system resources and memory usage
   - Apply performance optimizations: `/api/performance/optimize`
   - Review performance recommendations

### Debug Commands

```bash
# Check performance optimizer status
python -c "from src.utils.performance_optimizer import performance_optimizer; print(performance_optimizer.get_performance_summary())"

# Validate configuration
python -c "from src.config import PerformanceConfig; print(vars(PerformanceConfig))"
```

---

This performance optimization system provides a robust foundation for handling video transcription workloads efficiently across different system configurations while maintaining optimal resource utilization.
