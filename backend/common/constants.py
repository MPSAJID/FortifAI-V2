"""
Constants used across FortifAI services
"""

# Alert Severities
SEVERITY_CRITICAL = "CRITICAL"
SEVERITY_HIGH = "HIGH"
SEVERITY_MEDIUM = "MEDIUM"
SEVERITY_LOW = "LOW"
SEVERITY_INFO = "INFO"

SEVERITY_LEVELS = {
    SEVERITY_CRITICAL: 4,
    SEVERITY_HIGH: 3,
    SEVERITY_MEDIUM: 2,
    SEVERITY_LOW: 1,
    SEVERITY_INFO: 0
}

# Threat Classifications
THREAT_CLASSIFICATIONS = [
    "normal",
    "malware",
    "ransomware",
    "trojan",
    "ddos",
    "brute_force",
    "data_exfiltration",
    "privilege_escalation",
    "phishing",
    "cryptomining",
    "backdoor",
    "rootkit"
]

# User Roles
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"
ROLE_API = "api"

ROLE_PERMISSIONS = {
    ROLE_ADMIN: ['read', 'write', 'delete', 'manage_users', 'view_logs', 'manage_alerts', 'configure_system'],
    ROLE_ANALYST: ['read', 'write', 'view_logs', 'manage_alerts'],
    ROLE_VIEWER: ['read', 'view_logs'],
    ROLE_API: ['read', 'write']
}

# Suspicious Process Patterns
SUSPICIOUS_PROCESSES = [
    'mimikatz', 'psexec', 'procdump', 'netcat', 'nc',
    'powershell -enc', 'certutil', 'bitsadmin',
    'wmic', 'reg add', 'schtasks'
]

# System Processes (Windows)
SYSTEM_PROCESSES_WINDOWS = [
    'svchost.exe', 'explorer.exe', 'csrss.exe', 'wininit.exe',
    'services.exe', 'lsass.exe', 'winlogon.exe', 'smss.exe'
]

# System Processes (Linux)
SYSTEM_PROCESSES_LINUX = [
    'systemd', 'init', 'kthreadd', 'kworker', 'migration',
    'rcu_sched', 'watchdog', 'ksoftirqd'
]

# Network Ports of Interest
SUSPICIOUS_PORTS = [
    4444,   # Metasploit default
    5555,   # Android debug
    6666,   # IRC
    31337,  # Back Orifice
    12345,  # NetBus
]

# Event Types
EVENT_LOGIN = "login"
EVENT_LOGOUT = "logout"
EVENT_FILE_ACCESS = "file_access"
EVENT_PROCESS_START = "process_start"
EVENT_NETWORK_CONNECTION = "network_connection"
EVENT_PRIVILEGE_CHANGE = "privilege_change"
