"""
File Log Collector
Monitors file system for suspicious activities
"""
import os
from datetime import datetime
from typing import Dict, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
import queue
import hashlib

# Suspicious file extensions
SUSPICIOUS_EXTENSIONS = {
    '.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.hta',
    '.scr', '.pif', '.msi', '.jar', '.wsf', '.wsh', '.lnk',
    '.encrypted', '.locked', '.crypted', '.crypt', '.enc',
    '.ransomware', '.locky', '.cerber', '.zepto'
}

# Ransomware indicators
RANSOMWARE_INDICATORS = [
    'readme.txt', 'decrypt', 'ransom', 'bitcoin', 'payment',
    'your_files', 'encrypted', 'locked', 'restore'
]

# Sensitive directories
SENSITIVE_DIRS = [
    'system32', 'windows', 'program files', 'programdata',
    'appdata', 'temp', 'tmp', 'downloads', '.ssh', '.gnupg'
]


class FileEventHandler(FileSystemEventHandler):
    """Handler for file system events"""
    
    def __init__(self, event_queue: queue.Queue):
        self.event_queue = event_queue
        super().__init__()
    
    def on_created(self, event):
        if not event.is_directory:
            self._add_event("file_created", event.src_path)
    
    def on_modified(self, event):
        if not event.is_directory:
            self._add_event("file_modified", event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self._add_event("file_deleted", event.src_path)
    
    def on_moved(self, event):
        if not event.is_directory:
            self._add_event("file_moved", event.src_path, event.dest_path)
    
    def _add_event(self, event_type: str, src_path: str, dest_path: str = None):
        extension = os.path.splitext(src_path)[1].lower()
        filename = os.path.basename(src_path).lower()
        directory = os.path.dirname(src_path).lower()
        
        # Check for suspicious indicators
        is_suspicious = self._is_suspicious_file(src_path, extension, filename, directory)
        
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "file_path": src_path,
            "destination_path": dest_path,
            "filename": os.path.basename(src_path),
            "extension": extension,
            "directory": os.path.dirname(src_path),
            "is_suspicious": is_suspicious,
            "threat_indicators": self._get_threat_indicators(src_path, extension, filename)
        }
        self.event_queue.put(event)
    
    def _is_suspicious_file(self, path: str, ext: str, filename: str, directory: str) -> bool:
        """Check if file activity is suspicious"""
        # Suspicious extension
        if ext in SUSPICIOUS_EXTENSIONS:
            return True
        
        # Ransomware indicators in filename
        for indicator in RANSOMWARE_INDICATORS:
            if indicator in filename:
                return True
        
        # Sensitive directory access
        for sensitive_dir in SENSITIVE_DIRS:
            if sensitive_dir in directory:
                return True
        
        # Hidden files with executables
        if filename.startswith('.') and ext in ['.exe', '.sh', '.bat']:
            return True
        
        return False
    
    def _get_threat_indicators(self, path: str, ext: str, filename: str) -> List[str]:
        """Get list of threat indicators for this file"""
        indicators = []
        
        if ext in SUSPICIOUS_EXTENSIONS:
            indicators.append(f"suspicious_extension:{ext}")
        
        for ri in RANSOMWARE_INDICATORS:
            if ri in filename:
                indicators.append(f"ransomware_indicator:{ri}")
        
        if filename.startswith('.'):
            indicators.append("hidden_file")
        
        return indicators


class FileLogCollector:
    """Collects file system events"""
    
    def __init__(self):
        self.event_queue = queue.Queue()
        self.observer = None
        self.watched_paths = self._get_watched_paths()
        self._start_observer()
    
    def _get_watched_paths(self) -> List[str]:
        """Get paths to monitor based on OS"""
        paths = []
        
        # Common paths to monitor
        if os.name == 'nt':  # Windows
            paths = [
                os.path.expanduser("~\\Documents"),
                os.path.expanduser("~\\Downloads"),
                "C:\\Windows\\Temp",
                "C:\\ProgramData"
            ]
        else:  # Linux/Mac
            paths = [
                "/var/log",
                "/tmp",
                os.path.expanduser("~/Documents"),
                os.path.expanduser("~/Downloads")
            ]
        
        return [p for p in paths if os.path.exists(p)]
    
    def _start_observer(self):
        """Start the file system observer"""
        self.observer = Observer()
        handler = FileEventHandler(self.event_queue)
        
        for path in self.watched_paths:
            try:
                self.observer.schedule(handler, path, recursive=True)
            except Exception as e:
                print(f"Could not watch {path}: {e}")
        
        self.observer.start()
    
    def collect(self) -> List[Dict]:
        """Collect all pending file events"""
        events = []
        
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                event["source"] = "file_collector"
                event["collector_source"] = "file_collector"
                events.append(event)
            except queue.Empty:
                break
        
        return events
    
    def get_file_hash(self, filepath: str, algorithm: str = "sha256") -> str:
        """Calculate hash of a file"""
        try:
            hasher = hashlib.new(algorithm)
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (IOError, OSError):
            return ""
    
    def analyze_file(self, filepath: str) -> Dict:
        """Perform detailed analysis of a specific file"""
        try:
            stat = os.stat(filepath)
            filename = os.path.basename(filepath).lower()
            extension = os.path.splitext(filepath)[1].lower()
            
            return {
                "filepath": filepath,
                "filename": filename,
                "extension": extension,
                "size_bytes": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed_time": datetime.fromtimestamp(stat.st_atime).isoformat(),
                "sha256_hash": self.get_file_hash(filepath),
                "is_hidden": filename.startswith('.'),
                "is_suspicious_ext": extension in SUSPICIOUS_EXTENSIONS,
                "threat_indicators": self._analyze_file_threats(filepath, filename, extension)
            }
        except (IOError, OSError) as e:
            return {"filepath": filepath, "error": str(e)}
    
    def _analyze_file_threats(self, filepath: str, filename: str, ext: str) -> List[str]:
        """Analyze file for potential threats"""
        threats = []
        
        if ext in SUSPICIOUS_EXTENSIONS:
            threats.append(f"suspicious_extension:{ext}")
        
        for indicator in RANSOMWARE_INDICATORS:
            if indicator in filename:
                threats.append(f"ransomware_indicator:{indicator}")
        
        # Check for double extensions (e.g., .pdf.exe)
        base_name = os.path.splitext(filename)[0]
        if '.' in base_name:
            threats.append("double_extension")
        
        return threats
    
    def stop(self):
        """Stop the observer"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
