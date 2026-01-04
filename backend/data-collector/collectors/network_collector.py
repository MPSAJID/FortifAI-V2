"""
Network Collector
Monitors network connections for suspicious activity
"""
import psutil
from datetime import datetime
from typing import Dict, List
import socket
import logging

logger = logging.getLogger(__name__)


class NetworkCollector:
    """Collects network connection information"""
    
    def __init__(self):
        self.known_connections = set()
        self.suspicious_ports = [
            4444,   # Metasploit default
            5555,   # Android debug
            6666,   # IRC
            31337,  # Back Orifice
            12345,  # NetBus
            1337,   # Common hacker port
            8080,   # Alt HTTP (when unexpected)
            3389,   # RDP (when unexpected)
            22,     # SSH (when unexpected outbound)
            23,     # Telnet
        ]
        
        self.suspicious_ips = set()  # Can be populated from threat intel
    
    def collect(self) -> List[Dict]:
        """Collect network connection information"""
        connections = []
        current_connections = set()
        
        try:
            net_connections = psutil.net_connections(kind='inet')
            
            for conn in net_connections:
                try:
                    conn_key = (
                        conn.laddr.ip if conn.laddr else '',
                        conn.laddr.port if conn.laddr else 0,
                        conn.raddr.ip if conn.raddr else '',
                        conn.raddr.port if conn.raddr else 0
                    )
                    current_connections.add(conn_key)
                    
                    # Get process info
                    process_name = ""
                    if conn.pid:
                        try:
                            process_name = psutil.Process(conn.pid).name()
                        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                            logger.debug(f"Could not get process name for PID {conn.pid}: {e}")
                    
                    connection_data = {
                        "event_type": "network_connection",
                        "timestamp": datetime.now().isoformat(),
                        "local_address": conn.laddr.ip if conn.laddr else None,
                        "local_port": conn.laddr.port if conn.laddr else None,
                        "remote_address": conn.raddr.ip if conn.raddr else None,
                        "remote_port": conn.raddr.port if conn.raddr else None,
                        "status": conn.status,
                        "pid": conn.pid,
                        "process_name": process_name,
                        "is_new": conn_key not in self.known_connections,
                        "is_suspicious": self._is_suspicious(conn),
                        "source": "network_collector"
                    }
                    
                    # Only collect new or suspicious connections
                    if connection_data['is_new'] or connection_data['is_suspicious']:
                        connections.append(connection_data)
                        
                except Exception as e:
                    logger.warning(f"Error processing connection: {e}")
                    continue
                    
        except (psutil.AccessDenied, PermissionError) as e:
            logger.error(f"Permission denied accessing network connections: {e}")
        
        self.known_connections = current_connections
        return connections
    
    def _is_suspicious(self, conn) -> bool:
        """Check if connection is suspicious"""
        # Check remote port
        if conn.raddr and conn.raddr.port in self.suspicious_ports:
            return True
        
        # Check local port
        if conn.laddr and conn.laddr.port in self.suspicious_ports:
            return True
        
        # Check against suspicious IPs
        if conn.raddr and conn.raddr.ip in self.suspicious_ips:
            return True
        
        # Check for unusual established connections
        if conn.status == 'ESTABLISHED':
            # External connection on non-standard ports
            if conn.raddr and conn.raddr.port not in [80, 443, 53, 25, 587]:
                if not self._is_private_ip(conn.raddr.ip):
                    return True
        
        return False
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private"""
        try:
            parts = [int(p) for p in ip.split('.')]
            
            # 10.0.0.0/8
            if parts[0] == 10:
                return True
            # 172.16.0.0/12
            if parts[0] == 172 and 16 <= parts[1] <= 31:
                return True
            # 192.168.0.0/16
            if parts[0] == 192 and parts[1] == 168:
                return True
            # 127.0.0.0/8 (localhost)
            if parts[0] == 127:
                return True
                
        except (ValueError, IndexError) as e:
            logger.debug(f"Error parsing IP address {ip}: {e}")
        
        return False
    
    def add_suspicious_ip(self, ip: str):
        """Add IP to suspicious list"""
        self.suspicious_ips.add(ip)
    
    def get_connection_summary(self) -> Dict:
        """Get summary of current connections"""
        try:
            connections = psutil.net_connections(kind='inet')
            
            summary = {
                "total": len(connections),
                "established": 0,
                "listening": 0,
                "time_wait": 0,
                "unique_remote_ips": set(),
                "unique_local_ports": set()
            }
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    summary["established"] += 1
                elif conn.status == 'LISTEN':
                    summary["listening"] += 1
                elif conn.status == 'TIME_WAIT':
                    summary["time_wait"] += 1
                
                if conn.raddr:
                    summary["unique_remote_ips"].add(conn.raddr.ip)
                if conn.laddr:
                    summary["unique_local_ports"].add(conn.laddr.port)
            
            summary["unique_remote_ips"] = len(summary["unique_remote_ips"])
            summary["unique_local_ports"] = len(summary["unique_local_ports"])
            
            return summary
            
        except (psutil.AccessDenied, PermissionError) as e:
            logger.error(f"Permission denied getting connection summary: {e}")
            return {"error": "Access denied"}
