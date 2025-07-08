// Batch Processing JavaScript
let currentBatchId = null;
let refreshInterval = null;
let socket = null;
let connectedBatches = new Set();

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket(); // Start real-time updates
    loadBatches();
    setupEventListeners();
    startAutoRefresh();
});

function setupEventListeners() {
    // Create batch form
    document.getElementById('createBatchForm').addEventListener('submit', createBatch);

    // File upload
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);

    // Batch actions
    document.getElementById('startBatchBtn').addEventListener('click', startCurrentBatch);
    document.getElementById('clearQueueBtn').addEventListener('click', clearQueue);
}

async function createBatch(e) {
    e.preventDefault();

    const name = document.getElementById('batchName').value.trim();
    const maxConcurrent = document.getElementById('maxConcurrent').value;

    try {
        const response = await fetch('/api/batch/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name || undefined,
                max_concurrent: maxConcurrent ? parseInt(maxConcurrent) : undefined
            })
        });

        const data = await response.json();

        if (data.success) {
            currentBatchId = data.batch_id;
            document.getElementById('fileUploadSection').style.display = 'block';
            document.getElementById('createBatchForm').style.display = 'none';
            showToast('Batch created successfully!', 'success');
            loadBatches();
        } else {
            showToast('Error creating batch: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error creating batch: ' + error.message, 'error');
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = Array.from(e.dataTransfer.files);
    addFilesToQueue(files);
}

function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    addFilesToQueue(files);
}

function addFilesToQueue(files) {
    const fileQueue = document.getElementById('fileQueue');
    const fileList = document.getElementById('fileList');

    files.forEach(file => {
        if (file.type.startsWith('video/')) {
            const fileItem = createFileItem(file);
            fileList.appendChild(fileItem);
        }
    });

    if (fileList.children.length > 0) {
        fileQueue.style.display = 'block';
        document.getElementById('batchActions').style.display = 'block';
    }
}

function createFileItem(file) {
    const div = document.createElement('div');
    div.className = 'job-item';

    // Generate clean session name from filename
    const baseName = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
    const cleanName = baseName
        .replace(/[_\-\.]+/g, ' ')  // Replace separators with spaces
        .replace(/\s+/g, ' ')       // Normalize multiple spaces
        .trim()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
        .join(' ');

    div.innerHTML = `
        <div class="job-details">
            <div class="job-filename">
                <i class="bi bi-camera-video text-primary"></i>
                ${file.name}
            </div>
            <div class="job-info">
                <small class="text-muted">${formatFileSize(file.size)}</small>
            </div>
            <div class="session-name-input">
                <label class="form-label small mb-1">Session Name:</label>
                <input type="text" class="form-control form-control-sm session-name-field"
                       placeholder="Enter custom session name (optional)"
                       value="${cleanName}"
                       maxlength="60">
                <small class="text-muted">
                    Preview: <span class="preview-name">${cleanName}_${new Date().toLocaleDateString('en-US', {month:'2-digit', day:'2-digit'})}_${new Date().toLocaleTimeString('en-US', {hour12: false, hour:'2-digit', minute:'2-digit'})}</span>
                </small>
            </div>
        </div>
        <div class="batch-actions">
            <span class="badge bg-secondary">Queued</span>
            <button type="button" class="btn btn-sm btn-outline-danger ms-2" onclick="removeFileItem(this)">
                <i class="bi bi-x"></i>
            </button>
        </div>
    `;

    // Add real-time preview update
    const sessionInput = div.querySelector('.session-name-field');
    const previewSpan = div.querySelector('.preview-name');

    sessionInput.addEventListener('input', function() {
        const value = this.value.trim();
        const now = new Date();
        const timestamp = `${(now.getMonth() + 1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}`;

        if (value) {
            previewSpan.textContent = `${value}_${timestamp}`;
        } else {
            previewSpan.textContent = `${cleanName}_${timestamp}`;
        }
    });

    div.dataset.file = JSON.stringify({
        name: file.name,
        size: file.size
    });
    div._file = file;
    return div;
}

function removeFileItem(button) {
    button.closest('.job-item').remove();

    const fileList = document.getElementById('fileList');
    if (fileList.children.length === 0) {
        document.getElementById('fileQueue').style.display = 'none';
        document.getElementById('batchActions').style.display = 'none';
    }
}

function clearQueue() {
    document.getElementById('fileList').innerHTML = '';
    document.getElementById('fileQueue').style.display = 'none';
    document.getElementById('batchActions').style.display = 'none';
}

async function startCurrentBatch() {
    if (!currentBatchId) return;

    const fileItems = document.querySelectorAll('#fileList .job-item');

    // Upload all files first
    for (const item of fileItems) {
        const file = item._file;
        if (file) {
            await uploadFileToCurrentBatch(file, item);
        }
    }

    // Start the batch
    try {
        const response = await fetch(`/api/batch/${currentBatchId}/start`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Batch processing started!', 'success');
            resetForm();
            loadBatches();
        } else {
            showToast('Error starting batch: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error starting batch: ' + error.message, 'error');
    }
}

async function uploadFileToCurrentBatch(file, itemElement) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('batch_id', currentBatchId);

    // Get the custom session name from the input field
    const sessionNameInput = itemElement.querySelector('.session-name-field');
    if (sessionNameInput && sessionNameInput.value.trim()) {
        formData.append('session_name', sessionNameInput.value.trim());
    }

    try {
        const response = await fetch('/api/batch/add-video', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            const badge = itemElement.querySelector('.badge');
            badge.textContent = 'Added';
            badge.className = 'badge bg-success';
        } else {
            const badge = itemElement.querySelector('.badge');
            badge.textContent = 'Failed';
            badge.className = 'badge bg-danger';
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

function resetForm() {
    currentBatchId = null;
    document.getElementById('createBatchForm').style.display = 'block';
    document.getElementById('fileUploadSection').style.display = 'none';
    document.getElementById('createBatchForm').reset();
    clearQueue();
}

async function loadBatches() {
    try {
        const response = await fetch('/api/batch/list');
        const data = await response.json();

        if (data.success) {
            renderBatches(data.batches);
            updateStats(data.batches);
        }
    } catch (error) {
        console.error('Error loading batches:', error);
    }
}

function renderBatches(batches) {
    const container = document.getElementById('batchesList');

    if (batches.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-inbox" style="font-size: 3rem;"></i>
                <p>No batches created yet. Create your first batch above!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = batches.map(batch => `
        <div class="batch-card p-3" data-batch-id="${batch.batch_id}">
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                    <h5 class="mb-1">${batch.name || 'Unnamed Batch'}</h5>
                    <small class="text-muted">Created: ${formatDate(batch.created_at)}</small>
                    <div class="batch-timestamp">
                        <small class="text-muted">Last updated: ${new Date().toLocaleTimeString()}</small>
                    </div>
                </div>
                <div class="batch-actions">
                    ${getStatusBadge(batch.status)}
                    <div class="btn-group" role="group">
                        ${batch.status === 'pending' ? `
                            <button class="btn btn-sm btn-outline-success" onclick="startBatchRealTime('${batch.batch_id}')">
                                <i class="bi bi-play"></i> Start
                            </button>
                        ` : ''}
                        ${batch.status === 'processing' ? `
                            <button class="btn btn-sm btn-outline-warning" onclick="cancelBatchRealTime('${batch.batch_id}')">
                                <i class="bi bi-stop"></i> Cancel
                            </button>
                        ` : ''}
                        ${batch.status === 'completed' ? `
                            <button class="btn btn-sm btn-outline-primary" onclick="viewBatchResults('${batch.batch_id}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="downloadBatchResults('${batch.batch_id}')">
                                <i class="bi bi-download"></i> Download
                            </button>
                        ` : ''}
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteBatchRealTime('${batch.batch_id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>

            <div class="progress-container">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <div class="job-info">
                        <span>${batch.progress.completed_jobs}/${batch.progress.total_jobs} jobs completed</span>
                        ${batch.progress.failed_jobs > 0 ? `<span class="text-danger ms-2">• ${batch.progress.failed_jobs} failed</span>` : ''}
                        ${batch.progress.estimated_remaining ? `<span class="text-muted ms-2">• ETA: ${batch.progress.estimated_remaining}</span>` : ''}
                    </div>
                    <span class="fw-bold progress-text">${batch.progress.progress_percentage}%</span>
                </div>
                <div class="progress">
                    <div class="progress-bar ${getProgressBarClass(batch.status)}"
                         style="width: ${batch.progress.progress_percentage}%"
                         role="progressbar"
                         aria-valuenow="${batch.progress.progress_percentage}"
                         aria-valuemin="0"
                         aria-valuemax="100"></div>
                </div>
                ${batch.progress.estimated_remaining ? `
                    <small class="text-muted">Estimated remaining: ${batch.progress.estimated_remaining}</small>
                ` : ''}
            </div>
        </div>
    `).join('');

    // Join WebSocket rooms for all batches to receive real-time updates
    if (socket && socket.connected) {
        batches.forEach(batch => {
            joinBatchRoom(batch.batch_id);
        });
    }
}

function updateStats(batches) {
    document.getElementById('totalBatches').textContent = batches.length;
    const totalJobs = batches.reduce((sum, batch) => sum + batch.progress.total_jobs, 0);
    document.getElementById('totalJobs').textContent = totalJobs;
}

function getStatusBadge(status) {
    const badges = {
        pending: 'badge bg-secondary',
        processing: 'badge bg-primary',
        completed: 'badge bg-success',
        failed: 'badge bg-danger',
        cancelled: 'badge bg-warning'
    };

    const icons = {
        pending: 'clock',
        processing: 'arrow-clockwise',
        completed: 'check-circle',
        failed: 'x-circle',
        cancelled: 'stop-circle'
    };

    return `<span class="${badges[status]} status-badge">
        <i class="bi bi-${icons[status]}"></i> ${status.charAt(0).toUpperCase() + status.slice(1)}
    </span>`;
}

function getProgressBarClass(status) {
    return {
        pending: '',
        processing: 'progress-bar-striped progress-bar-animated',
        completed: 'bg-success',
        failed: 'bg-danger',
        cancelled: 'bg-warning'
    }[status] || '';
}

async function cancelBatch(batchId) {
    if (!confirm('Are you sure you want to cancel this batch?')) return;

    try {
        const response = await fetch(`/api/batch/${batchId}/cancel`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Batch cancelled successfully', 'success');
            loadBatches();
        } else {
            showToast('Error cancelling batch: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error cancelling batch: ' + error.message, 'error');
    }
}

async function deleteBatch(batchId) {
    if (!confirm('Are you sure you want to delete this batch? This cannot be undone.')) return;

    try {
        const response = await fetch(`/api/batch/${batchId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Batch deleted successfully', 'success');
            loadBatches();
        } else {
            showToast('Error deleting batch: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error deleting batch: ' + error.message, 'error');
    }
}

function viewBatchResults(batchId) {
    window.open(`/api/batch/${batchId}/results`, '_blank');
}

function downloadBatchResults(batchId) {
    window.location.href = `/api/batch/${batchId}/download`;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// ========================================
// REAL-TIME WEBSOCKET FUNCTIONALITY
// ========================================

function initializeWebSocket() {
    if (socket && socket.connected) {
        return; // Already connected
    }

    socket = io();

    socket.on('connect', function() {
        console.log('🔌 Connected to WebSocket server');
        updateConnectionStatus(true);

        // Join rooms for currently visible batches
        document.querySelectorAll('.batch-card').forEach(card => {
            const batchId = card.getAttribute('data-batch-id');
            if (batchId) {
                joinBatchRoom(batchId);
            }
        });
    });

    socket.on('disconnect', function() {
        console.log('🔌 Disconnected from WebSocket server');
        updateConnectionStatus(false);
        connectedBatches.clear();
    });

    // Real-time batch progress updates
    socket.on('batch_progress_update', function(data) {
        console.log('📊 Batch progress update:', data);
        updateBatchCardRealTime(data);
    });

    // Individual job status updates
    socket.on('job_status_update', function(data) {
        console.log('🔄 Job status update:', data);
        updateJobStatusRealTime(data);
    });

    // Batch status changes
    socket.on('batch_status_update', function(data) {
        console.log('📋 Batch status update:', data);
        updateBatchStatusRealTime(data);
    });

    // Handle batch control results
    socket.on('batch_control_result', function(data) {
        console.log('🎮 Batch control result:', data);
        if (data.success) {
            showToast(data.message, 'success');
            loadBatches(); // Refresh the list
        } else {
            showToast(data.message, 'error');
        }
    });

    socket.on('error', function(data) {
        console.error('❌ WebSocket error:', data);
        showToast('WebSocket error: ' + data.message, 'error');
    });
}

function joinBatchRoom(batchId) {
    if (socket && socket.connected && !connectedBatches.has(batchId)) {
        socket.emit('join_batch', { batch_id: batchId });
        connectedBatches.add(batchId);
        console.log(`🏠 Joined room for batch ${batchId}`);
    }
}

function leaveBatchRoom(batchId) {
    if (socket && socket.connected && connectedBatches.has(batchId)) {
        socket.emit('leave_batch', { batch_id: batchId });
        connectedBatches.delete(batchId);
        console.log(`🚪 Left room for batch ${batchId}`);
    }
}

function updateBatchCardRealTime(data) {
    const batchCard = document.querySelector(`[data-batch-id="${data.batch_id}"]`);
    if (!batchCard) return;

    // Update overall progress
    if (data.progress && typeof data.progress.progress_percentage === 'number') {
        const progressBar = batchCard.querySelector('.progress-bar');
        const progressText = batchCard.querySelector('.progress-text');

        if (progressBar && progressText) {
            const percentage = Math.round(data.progress.progress_percentage);
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            progressText.textContent = `${percentage}%`;

            // Update progress bar color based on status
            progressBar.className = 'progress-bar';
            if (data.status === 'completed') {
                progressBar.classList.add('bg-success');
            } else if (data.status === 'failed') {
                progressBar.classList.add('bg-danger');
            } else if (data.status === 'processing') {
                progressBar.classList.add('bg-primary', 'progress-bar-animated', 'progress-bar-striped');
            }
        }

        // Update job counts
        if (data.progress.total_jobs) {
            const jobInfo = batchCard.querySelector('.job-info');
            if (jobInfo) {
                jobInfo.innerHTML = `
                    <small class="text-muted">
                        ${data.progress.completed_jobs}/${data.progress.total_jobs} jobs completed
                        ${data.progress.failed_jobs > 0 ? `• ${data.progress.failed_jobs} failed` : ''}
                        ${data.progress.estimated_remaining ? `• ETA: ${data.progress.estimated_remaining}` : ''}
                    </small>
                `;
            }
        }
    }

    // Update status badge
    const statusBadge = batchCard.querySelector('.status-badge');
    if (statusBadge && data.status) {
        statusBadge.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
        statusBadge.className = 'badge status-badge ms-2';

        switch (data.status) {
            case 'pending':
                statusBadge.classList.add('bg-secondary');
                break;
            case 'processing':
                statusBadge.classList.add('bg-primary');
                break;
            case 'completed':
                statusBadge.classList.add('bg-success');
                break;
            case 'failed':
                statusBadge.classList.add('bg-danger');
                break;
            case 'cancelled':
                statusBadge.classList.add('bg-warning');
                break;
        }
    }

    // Update timestamp
    const timestamp = batchCard.querySelector('.batch-timestamp');
    if (timestamp && data.timestamp) {
        const date = new Date(data.timestamp);
        timestamp.textContent = `Updated: ${date.toLocaleTimeString()}`;
    }
}

function updateJobStatusRealTime(data) {
    // This could be used for detailed job view if implemented
    console.log(`Job ${data.job_id} in batch ${data.batch_id}: ${data.status} (${Math.round(data.progress * 100)}%)`);

    // You could implement a detailed job list view here
    // For now, we'll just trigger a batch card update
    const batchCard = document.querySelector(`[data-batch-id="${data.batch_id}"]`);
    if (batchCard) {
        // Add a subtle animation to show activity
        batchCard.style.transform = 'scale(1.02)';
        setTimeout(() => {
            batchCard.style.transform = 'scale(1)';
        }, 200);
    }
}

function updateBatchStatusRealTime(data) {
    updateBatchCardRealTime(data);
}

// Enhanced batch operations with real-time feedback
async function startBatchRealTime(batchId) {
    try {
        // Join the batch room before starting to get real-time updates
        joinBatchRoom(batchId);

        const response = await fetch(`/api/batch/${batchId}/start`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Batch started! Watch for real-time progress updates.', 'success');
        } else {
            showToast('Error starting batch: ' + data.error, 'error');
        }
    } catch (error) {
        showToast('Error starting batch: ' + error.message, 'error');
    }
}

async function cancelBatchRealTime(batchId) {
    if (!confirm('Are you sure you want to cancel this batch?')) return;

    // Use WebSocket for immediate feedback
    if (socket && socket.connected) {
        socket.emit('batch_control', {
            batch_id: batchId,
            action: 'cancel'
        });
    } else {
        // Fallback to HTTP request
        await cancelBatch(batchId);
    }
}

async function deleteBatchRealTime(batchId) {
    if (!confirm('Are you sure you want to delete this batch? This cannot be undone.')) return;

    // Leave the room first
    leaveBatchRoom(batchId);

    // Use WebSocket for immediate feedback
    if (socket && socket.connected) {
        socket.emit('batch_control', {
            batch_id: batchId,
            action: 'delete'
        });
    } else {
        // Fallback to HTTP request
        await deleteBatch(batchId);
    }
}

// Auto-refresh is now handled by WebSocket, but keep as fallback
function startAutoRefresh() {
    // Reduce polling frequency since we have real-time updates
    refreshInterval = setInterval(() => {
        // Only refresh if WebSocket is not connected
        if (!socket || !socket.connected) {
            const hasProcessingBatches = document.querySelector('.badge.bg-primary');
            if (hasProcessingBatches) {
                loadBatches();
            }
        }
    }, 10000); // Reduced from 3s to 10s since WebSocket provides real-time updates
}

function updateConnectionStatus(connected) {
    const statusElement = document.getElementById('connectionStatus');

    if (connected) {
        statusElement.className = 'connection-indicator connection-connected';
        statusElement.style.display = 'block';
        statusElement.innerHTML = '<i class="bi bi-wifi"></i> Connected';

        // Hide after 3 seconds when connected
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 3000);
    } else {
        statusElement.className = 'connection-indicator connection-disconnected';
        statusElement.style.display = 'block';
        statusElement.innerHTML = '<i class="bi bi-wifi-off"></i> Disconnected';

        // Keep showing when disconnected
    }
}

function showToast(message, type = 'info') {
    // Simple toast implementation
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 5000);
}
