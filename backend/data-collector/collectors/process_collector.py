"""
Process Collector
Monitors running processes for suspicious activity
"""
import psutil
from datetime import datetime
from typing import Dict, List
import os

class ProcessCollector:
    """Collects process information and detects anomalies"""
    
    def __init__(self):
        self.known_processes = set()
        self.suspicious_patterns = [
            'mimikatz', 'psexec', 'procdump', 'netcat', 'nc.exe',
            'certutil', 'bitsadmin', 'wmic', 'powershell -enc',
            'base64', 'wget', 'curl', 'nmap', 'masscan'
        ]
        
    def collect(self) -> List[Dict]:
        """Collect current process information"""
        processes = []
        current_processes = set()
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'cmdline', 'create_time']):
            try:
                pinfo = proc.info
                current_processes.add(pinfo['pid'])
                
                process_data = {
                    "event_type": "process_info",
                    "timestamp": datetime.now().isoformat(),
                    "pid": pinfo['pid'],
                    "process_name": pinfo['name'],
                    "user": pinfo['username'],
                    "cpu_usage": pinfo['cpu_percent'],
                    "memory_usage": pinfo['memory_percent'],
                    "cmdline": ' '.join(pinfo['cmdline']) if pinfo['cmdline'] else '',
                    "create_time": datetime.fromtimestamp(pinfo['create_time']).isoformat() if pinfo['create_time'] else None,
                    "is_new": pinfo['pid'] not in self.known_processes,
                    "is_suspicious": self._is_suspicious(pinfo),
                    "source": "process_collector"
                }
                
                # Only collect new or suspicious processes
                if process_data['is_new'] or process_data['is_suspicious']:
                    processes.append(process_data)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        self.known_processes = current_processes
        return processes
    
    def _is_suspicious(self, pinfo: Dict) -> bool:
        """Check if process is suspicious"""
        name = (pinfo.get('name') or '').lower()
        cmdline = ' '.join(pinfo.get('cmdline') or []).lower()
        
        # Check against suspicious patterns
        for pattern in self.suspicious_patterns:
            if pattern in name or pattern in cmdline:
                return True
        
        # Check for unusual characteristics
        cpu = pinfo.get('cpu_percent', 0) or 0
        memory = pinfo.get('memory_percent', 0) or 0
        
        # High resource usage
        if cpu > 80 or memory > 50:
            return True
        
        return False
    
    def get_process_tree(self, pid: int) -> Dict:
        """Get process tree for a specific PID"""
        try:
            proc = psutil.Process(pid)
            parent = proc.parent()
            children = proc.children(recursive=True)
            
            return {
                "pid": pid,
                "name": proc.name(),
                "parent": {
                    "pid": parent.pid,
                    "name": parent.name()
                } if parent else None,
                "children": [
                    {"pid": c.pid, "name": c.name()}
                    for c in children
                ]
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {}
