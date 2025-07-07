"""
System Monitor for WhisperAppliance Admin
Handles system status and performance monitoring
"""

import logging
import os
import platform
import psutil
from datetime import datetime

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system status and performance"""
    
    def __init__(self, system_stats=None):
        self.system_stats = system_stats or {
            "uptime_start": datetime.now(),
            "total_transcriptions": 0,
            "transcriptions_by_source": {"live": 0, "upload": 0, "api": 0}
        }
        
    def get_system_info(self):
        """Get comprehensive system information"""
        try:
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory info
            memory = psutil.virtual_memory()
            
            # Disk info
            disk = psutil.disk_usage('/')
            
            # Network info
            network = psutil.net_io_counters()
            
            # Process info
            process = psutil.Process(os.getpid())
            
            return {
                "platform": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "python_version": platform.python_version()
                },
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "count_logical": psutil.cpu_count(logical=True)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": disk.percent
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                } if network else {},
                "process": {
                    "pid": process.pid,
                    "memory_percent": process.memory_percent(),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads()
                },
                "uptime": self.get_uptime_seconds(),
                "transcriptions": self.system_stats.get("total_transcriptions", 0),
                "transcriptions_by_source": self.system_stats.get("transcriptions_by_source", {})
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return self._get_fallback_system_info()
    
    def _get_fallback_system_info(self):
        """Fallback system info when psutil fails"""
        return {
            "platform": {
                "system": platform.system(),
                "python_version": platform.python_version()
            },
            "cpu": {"percent": 0, "count": 0},
            "memory": {"percent": 0, "total": 0, "available": 0},
            "disk": {"percent": 0, "total": 0, "free": 0},
            "network": {},
            "process": {"pid": os.getpid()},
            "uptime": self.get_uptime_seconds(),
            "transcriptions": self.system_stats.get("total_transcriptions", 0)
        }
    
    def get_uptime_seconds(self):
        """Get uptime in seconds"""
        if "uptime_start" in self.system_stats:
            uptime = datetime.now() - self.system_stats["uptime_start"]
            return int(uptime.total_seconds())
        return 0
    
    def get_system_status(self):
        """Get simplified system status for API"""
        info = self.get_system_info()
        
        return {
            "uptime": info["uptime"],
            "cpu_percent": info["cpu"]["percent"],
            "memory_percent": info["memory"]["percent"],
            "disk_percent": info["disk"]["percent"],
            "total_transcriptions": info["transcriptions"],
            "transcriptions_by_source": info["transcriptions_by_source"],
            "isConnected": True,  # Can be enhanced with actual connection checks
            "platform": f"{info['platform']['system']} {info['platform'].get('release', '')}"
        }
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
