import psutil
from logger import get_logger

log = get_logger()

def get_system_stats():
    """Returns a dictionary containing current CPU and memory usage."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / (1024 * 1024),
            "memory_total_mb": memory.total / (1024 * 1024)
        }
    except Exception as e:
        log.error(f"Failed to get system stats: {e}")
        return None

def print_stats_comparison(before, after):
    """Logs and prints a comparison of system stats before and after mode switch."""
    if not before or not after:
        return

    log.info("\n--- System Stats Comparison ---")
    log.info(f"CPU Usage:    {before['cpu_percent']}% -> {after['cpu_percent']}%")
    log.info(f"Memory Usage: {before['memory_percent']}% -> {after['memory_percent']}%")
    log.info("-------------------------------\n")
