"""
Event Log Collector
Collects system event logs (Windows Event Log / Linux syslog)
"""
import os
import platform
from datetime import datetime, timedelta
from typing import Dict, List
import re

class EventLogCollector:
    """Collects system event logs"""
    
    def __init__(self):
        self.system = platform.system()
        self.last_collection = datetime.now() - timedelta(minutes=5)
        
        # Security event IDs to monitor (Windows)
        self.security_events = {
            4624: "Successful Login",
            4625: "Failed Login",
            4648: "Explicit Credential Logon",
            4672: "Special Privileges Assigned",
            4720: "User Account Created",
            4722: "User Account Enabled",
            4724: "Password Reset Attempt",
            4728: "User Added to Security Group",
            4732: "User Added to Local Group",
            4756: "User Added to Universal Group",
            1102: "Audit Log Cleared",
            4698: "Scheduled Task Created",
            4702: "Scheduled Task Updated",
            7045: "New Service Installed"
        }
    
    def collect(self) -> List[Dict]:
        """Collect event logs based on OS"""
        if self.system == 'Windows':
            return self._collect_windows_events()
        else:
            return self._collect_linux_events()
    
    def _collect_windows_events(self) -> List[Dict]:
        """Collect Windows Event Logs"""
        events = []
        
        try:
            import win32evtlog
            import win32evtlogutil
            
            logs = ['Security', 'System', 'Application']
            
            for log_type in logs:
                try:
                    hand = win32evtlog.OpenEventLog(None, log_type)
                    flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                    
                    while True:
                        events_batch = win32evtlog.ReadEventLog(hand, flags, 0)
                        if not events_batch:
                            break
                        
                        for event in events_batch:
                            event_time = event.TimeGenerated
                            
                            if event_time < self.last_collection:
                                break
                            
                            event_data = {
                                "event_type": "windows_event",
                                "timestamp": event_time.isoformat(),
                                "event_id": event.EventID & 0xFFFF,
                                "source": event.SourceName,
                                "log_type": log_type,
                                "category": event.EventCategory,
                                "computer": event.ComputerName,
                                "message": win32evtlogutil.SafeFormatMessage(event, log_type),
                                "is_security_event": (event.EventID & 0xFFFF) in self.security_events,
                                "collector_source": "event_collector"
                            }
                            
                            events.append(event_data)
                    
                    win32evtlog.CloseEventLog(hand)
                    
                except Exception as e:
                    print(f"Error reading {log_type} log: {e}")
                    
        except ImportError:
            # pywin32 not available - use alternative method
            events = self._collect_windows_events_fallback()
        
        self.last_collection = datetime.now()
        return events
    
    def _collect_windows_events_fallback(self) -> List[Dict]:
        """Fallback method for Windows event collection using PowerShell"""
        events = []
        
        try:
            import subprocess
            
            # Use PowerShell to get recent security events
            cmd = '''
            Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=(Get-Date).AddMinutes(-5)} -MaxEvents 100 |
            Select-Object TimeCreated, Id, LevelDisplayName, Message |
            ConvertTo-Json
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                import json
                parsed = json.loads(result.stdout)
                
                if isinstance(parsed, list):
                    for event in parsed:
                        events.append({
                            "event_type": "windows_event",
                            "timestamp": event.get('TimeCreated', ''),
                            "event_id": event.get('Id', 0),
                            "level": event.get('LevelDisplayName', ''),
                            "message": event.get('Message', '')[:500],
                            "source": "event_collector"
                        })
                        
        except Exception as e:
            print(f"Fallback event collection error: {e}")
        
        return events
    
    def _collect_linux_events(self) -> List[Dict]:
        """Collect Linux syslog events"""
        events = []
        log_files = [
            '/var/log/syslog',
            '/var/log/auth.log',
            '/var/log/secure',
            '/var/log/messages'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    events.extend(self._parse_syslog(log_file))
                except PermissionError:
                    print(f"Permission denied: {log_file}")
                except Exception as e:
                    print(f"Error reading {log_file}: {e}")
        
        self.last_collection = datetime.now()
        return events
    
    def _parse_syslog(self, log_file: str, max_lines: int = 100) -> List[Dict]:
        """Parse syslog file"""
        events = []
        
        # Read last N lines
        with open(log_file, 'r') as f:
            lines = f.readlines()[-max_lines:]
        
        # Syslog pattern
        pattern = r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[\d+\])?:\s*(.+)$'
        
        for line in lines:
            match = re.match(pattern, line.strip())
            if match:
                timestamp_str, hostname, service, message = match.groups()
                
                # Check for suspicious patterns
                is_suspicious = self._is_suspicious_log(message)
                
                events.append({
                    "event_type": "syslog",
                    "timestamp": timestamp_str,
                    "hostname": hostname,
                    "service": service,
                    "message": message[:500],
                    "log_file": log_file,
                    "is_suspicious": is_suspicious,
                    "source": "event_collector"
                })
        
        return events
    
    def _is_suspicious_log(self, message: str) -> bool:
        """Check if log message contains suspicious patterns"""
        suspicious_patterns = [
            r'failed password',
            r'authentication failure',
            r'invalid user',
            r'connection refused',
            r'permission denied',
            r'segfault',
            r'buffer overflow',
            r'root login',
            r'sudo:.*COMMAND',
            r'POSSIBLE BREAK-IN',
        ]
        
        message_lower = message.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
