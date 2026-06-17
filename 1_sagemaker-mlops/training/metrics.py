"""
System metrics logging for training jobs.

Tracks CPU, memory, and GPU utilization during training.
Logs are sent to stdout and automatically picked up by CloudWatch.
"""

import logging
import time
from datetime import datetime
from typing import Optional
import psutil

logger = logging.getLogger(__name__)


class MetricsTracker:
    """Track and log system metrics during training."""

    def __init__(self, interval_seconds: int = 30, track_gpu: bool = True):
        """
        Initialize metrics tracker.

        Args:
            interval_seconds: How often to log metrics (default 30 sec)
            track_gpu: Whether to track GPU metrics (requires nvidia-ml-py)
        """
        self.interval_seconds = interval_seconds
        self.track_gpu = track_gpu
        self.gpu_available = False
        self.process = psutil.Process()

        # Try to import GPU tracking
        if track_gpu:
            try:
                import pynvml
                pynvml.nvmlInit()
                self.gpu_available = True
                self.pynvml = pynvml
            except (ImportError, Exception):
                logger.warning("GPU metrics disabled (nvidia-ml-py not installed or CUDA unavailable)")
                self.gpu_available = False

    def get_metrics(self) -> dict:
        """Get current system metrics."""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": self._get_memory_metrics(),
        }

        if self.gpu_available:
            try:
                metrics["gpu"] = self._get_gpu_metrics()
            except Exception as e:
                logger.debug(f"GPU metrics error: {e}")

        return metrics

    def _get_memory_metrics(self) -> dict:
        """Get memory usage metrics."""
        vm = psutil.virtual_memory()
        return {
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "percent": vm.percent,
            "available_gb": round(vm.available / (1024 ** 3), 2),
        }

    def _get_gpu_metrics(self) -> dict:
        """Get GPU metrics if available."""
        try:
            device_count = self.pynvml.nvmlDeviceGetCount()
            gpus = []

            for i in range(device_count):
                handle = self.pynvml.nvmlDeviceGetHandleByIndex(i)
                mem_info = self.pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = self.pynvml.nvmlDeviceGetUtilizationRates(handle)

                gpus.append({
                    "id": i,
                    "memory_used_gb": round(mem_info.used / (1024 ** 3), 2),
                    "memory_total_gb": round(mem_info.total / (1024 ** 3), 2),
                    "memory_percent": round(100 * mem_info.used / mem_info.total, 1),
                    "utilization_percent": utilization.gpu,
                })

            return {"devices": gpus}
        except Exception as e:
            logger.debug(f"GPU metrics error: {e}")
            return {}

    def log_metrics(self, label: str = ""):
        """Log current metrics to logger."""
        metrics = self.get_metrics()

        # Build log message
        cpu = metrics["cpu_percent"]
        mem = metrics["memory"]

        msg = f"[METRICS] CPU: {cpu:5.1f}% | Memory: {mem['used_gb']:6.1f}GB/{mem['total_gb']:6.1f}GB ({mem['percent']:5.1f}%)"

        if self.gpu_available and "gpu" in metrics and metrics["gpu"]:
            gpus = metrics["gpu"]["devices"]
            for gpu in gpus:
                msg += f" | GPU{gpu['id']}: {gpu['memory_used_gb']:.1f}GB/{gpu['memory_total_gb']:.1f}GB ({gpu['utilization_percent']:.1f}%)"

        if label:
            msg = f"{label} {msg}"

        logger.info(msg)
        return metrics


class MetricsLogger:
    """Context manager for periodic metrics logging."""

    def __init__(self, label: str = "", interval_seconds: int = 30):
        """
        Initialize metrics logger context manager.

        Args:
            label: Label to prepend to log messages
            interval_seconds: How often to log metrics
        """
        self.label = label
        self.interval_seconds = interval_seconds
        self.tracker = MetricsTracker(interval_seconds)
        self.start_time = None
        self.start_metrics = None

    def __enter__(self):
        """Start logging metrics."""
        self.start_time = time.time()
        self.start_metrics = self.tracker.get_metrics()
        logger.info(f"{'='*80}")
        logger.info(f"{self.label} STARTED")
        logger.info(f"{'='*80}")
        self.tracker.log_metrics(self.label)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop logging metrics."""
        elapsed = time.time() - self.start_time
        self.tracker.log_metrics(self.label)

        logger.info(f"{'='*80}")
        logger.info(f"{self.label} COMPLETED in {elapsed/60:.1f} minutes")
        logger.info(f"{'='*80}")

    def log(self, message: str = ""):
        """Manually log metrics with optional message."""
        if message:
            logger.info(f"{self.label} {message}")
        self.tracker.log_metrics(self.label)


def log_system_info():
    """Log system information at startup."""
    logger.info(f"{'='*80}")
    logger.info("SYSTEM INFORMATION")
    logger.info(f"{'='*80}")
    logger.info(f"CPU Cores: {psutil.cpu_count(logical=False)} physical, {psutil.cpu_count(logical=True)} logical")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB total")

    tracker = MetricsTracker()
    if tracker.gpu_available:
        try:
            gpu_count = tracker.pynvml.nvmlDeviceGetCount()
            logger.info(f"GPU: {gpu_count} device(s) available")
            for i in range(gpu_count):
                handle = tracker.pynvml.nvmlDeviceGetHandleByIndex(i)
                gpu_name = tracker.pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                mem_info = tracker.pynvml.nvmlDeviceGetMemoryInfo(handle)
                logger.info(f"  GPU{i}: {gpu_name} ({mem_info.total / (1024**3):.1f}GB)")
        except Exception as e:
            logger.debug(f"Could not get GPU info: {e}")
    else:
        logger.info("GPU: Not available")

    logger.info(f"{'='*80}\n")
