"""
Helper utilities for Labor Market RAG system
"""
import os
import gc
import psutil
import hashlib
from typing import Dict, Any, Optional
import streamlit as st
from datetime import datetime


def get_memory_usage() -> Dict[str, float]:
    """Get current memory usage statistics"""
    try:
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        return {
            'percent': memory_percent,
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024
        }
    except:
        return {'percent': 0, 'rss_mb': 0, 'vms_mb': 0}


def check_memory_and_warn(threshold: int = 80) -> bool:
    """Check memory usage and warn if above threshold"""
    memory = get_memory_usage()
    if memory['percent'] > threshold:
        st.warning(f"⚠️ High memory usage: {memory['percent']:.1f}% ({memory['rss_mb']:.1f} MB)")
        gc.collect()
        return True
    return False


def force_garbage_collection() -> float:
    """Force garbage collection and return memory freed"""
    before = get_memory_usage()
    gc.collect()
    after = get_memory_usage()
    freed_mb = before['rss_mb'] - after['rss_mb']
    return freed_mb


def compute_file_hash(file_content: bytes) -> str:
    """Compute SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()


def format_number(num: float, decimals: int = 2) -> str:
    """Format number with thousands separator"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num/1_000:.{decimals}f}K"
    else:
        return f"{num:.{decimals}f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is 0"""
    return numerator / denominator if denominator != 0 else default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    try:
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_count': cpu_count,
            'cpu_percent': cpu_percent,
            'memory_total_gb': memory.total / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'memory_percent': memory.percent,
            'disk_total_gb': disk.total / (1024**3),
            'disk_used_gb': disk.used / (1024**3),
            'disk_percent': disk.percent
        }
    except:
        return {}


def create_timestamp() -> str:
    """Create formatted timestamp"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def ensure_directory(path: str):
    """Ensure directory exists, create if not"""
    os.makedirs(path, exist_ok=True)


def bytes_to_mb(bytes_size: int) -> float:
    """Convert bytes to megabytes"""
    return bytes_size / (1024 * 1024)


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        st.session_state.setdefault('performance_metrics', {})[self.operation_name] = duration
    
    def get_duration(self) -> Optional[float]:
        """Get duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
