"""
File management module.

This module provides progressive file cleanup and management capabilities
for temporary files created during video processing.
"""

import os
import time
import threading
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ProgressiveFileManager:
    """
    Progressive cleanup manager for temporary files during processing.
    
    This class manages temporary files created during video processing,
    providing progressive cleanup to prevent disk space issues and
    automatic cleanup of old files.
    """
    
    def __init__(self, max_temp_files: int = 20) -> None:
        """
        Initialize the file manager.
        
        Args:
            max_temp_files: Maximum number of temporary files to keep before cleanup
        """
        self.max_temp_files = max_temp_files
        self.temp_files: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        
    def add_temp_file(self, file_path: str, file_type: str = 'audio') -> None:
        """
        Add temporary file to cleanup queue with progressive management.
        
        Args:
            file_path: Path to the temporary file
            file_type: Type of file (e.g., 'audio', 'video', 'chunk')
        """
        with self.lock:
            timestamp = time.time()
            self.temp_files.append({
                'path': file_path,
                'type': file_type,
                'timestamp': timestamp,
                'size': self._get_file_size(file_path)
            })
            
            # Progressive cleanup: remove oldest files if we exceed limit
            if len(self.temp_files) > self.max_temp_files:
                self._cleanup_oldest_files(keep_recent_count=self.max_temp_files)
    
    def _get_file_size(self, file_path: str) -> int:
        """
        Get file size safely.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or 0 if file doesn't exist or error occurs
        """
        try:
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0
        except OSError as e:
            logger.warning(f"Could not get size for file {file_path}: {e}")
            return 0
    
    def _cleanup_oldest_files(self, keep_recent_count: int = 10) -> None:
        """
        Clean up oldest temporary files.
        
        Args:
            keep_recent_count: Number of recent files to keep
        """
        if len(self.temp_files) <= keep_recent_count:
            return
            
        # Sort by timestamp (oldest first)
        self.temp_files.sort(key=lambda x: x['timestamp'])
        
        files_to_remove = self.temp_files[:-keep_recent_count]
        self.temp_files = self.temp_files[-keep_recent_count:]
        
        # Remove old files
        total_removed_size = 0
        for file_info in files_to_remove:
            total_removed_size += file_info['size']
            self._safe_remove_file(file_info['path'])
        
        if files_to_remove:
            logger.info(
                f"Progressive cleanup: removed {len(files_to_remove)} files "
                f"({total_removed_size / (1024*1024):.1f}MB)"
            )
    
    def _safe_remove_file(self, file_path: str) -> None:
        """
        Safely remove a file with logging.
        
        Args:
            file_path: Path to the file to remove
        """
        try:
            if os.path.exists(file_path):
                file_size = self._get_file_size(file_path)
                os.remove(file_path)
                logger.debug(
                    f"Cleaned up temp file: {os.path.basename(file_path)} "
                    f"({file_size / (1024*1024):.1f}MB)"
                )
        except OSError as e:
            logger.warning(f"Failed to remove temp file {file_path}: {e}")
    
    def cleanup_all(self) -> None:
        """Clean up all tracked temporary files."""
        with self.lock:
            total_size = 0
            files_removed = 0
            
            for file_info in self.temp_files:
                total_size += file_info['size']
                if os.path.exists(file_info['path']):
                    self._safe_remove_file(file_info['path'])
                    files_removed += 1
            
            if self.temp_files:
                logger.info(
                    f"Final cleanup: removed {files_removed}/{len(self.temp_files)} temp files "
                    f"({total_size / (1024*1024):.1f}MB total)"
                )
            
            self.temp_files.clear()
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """
        Get statistics about temporary files.
        
        Returns:
            Dict containing file statistics:
            - count: Number of tracked files
            - total_size_mb: Total size in MB
            - types: Breakdown by file type
        """
        with self.lock:
            total_size = sum(f['size'] for f in self.temp_files)
            
            # Count by file type
            type_counts = {}
            for file_info in self.temp_files:
                file_type = file_info['type']
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            return {
                'count': len(self.temp_files),
                'total_size_mb': total_size / (1024*1024),
                'types': type_counts
            }
    
    def cleanup_by_type(self, file_type: str) -> None:
        """
        Clean up all files of a specific type.
        
        Args:
            file_type: Type of files to clean up
        """
        with self.lock:
            files_to_remove = [f for f in self.temp_files if f['type'] == file_type]
            self.temp_files = [f for f in self.temp_files if f['type'] != file_type]
            
            total_size = 0
            for file_info in files_to_remove:
                total_size += file_info['size']
                self._safe_remove_file(file_info['path'])
            
            if files_to_remove:
                logger.info(
                    f"Cleaned up {len(files_to_remove)} {file_type} files "
                    f"({total_size / (1024*1024):.1f}MB)"
                )