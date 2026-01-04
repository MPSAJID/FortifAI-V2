"""
Network Analyzer Module for FortifAI
Provides PCAP file analysis capabilities

Originally from SubVeil - Integrated into FortifAI Security Platform
"""

import os
import re
import tempfile
from typing import Optional
from datetime import datetime

try:
    import pyshark
    PYSHARK_AVAILABLE = True
except ImportError:
    pyshark = None
    PYSHARK_AVAILABLE = False


class NetworkAnalyzer:
    """Analyzes network traffic from PCAP files"""
    
    def __init__(self):
        self.results = {}
    
    @staticmethod
    def is_available() -> bool:
        """Check if pyshark is available"""
        return PYSHARK_AVAILABLE
    
    def analyze_pcap(self, file_path: str) -> dict:
        """
        Analyze a PCAP file and return protocol/port/IP statistics
        
        Args:
            file_path: Path to the PCAP file
            
        Returns:
            Dictionary containing analysis results
        """
        if not PYSHARK_AVAILABLE:
            return {
                'success': False,
                'error': 'pyshark is not installed. Install with: pip install pyshark'
            }
        
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        try:
            cap = pyshark.FileCapture(file_path, only_summaries=True)
            
            protocol_counts = {}
            port_counts = {}
            ip_counts = {}
            total_packets = 0
            
            for pkt in cap:
                total_packets += 1
                proto = pkt.protocol if hasattr(pkt, 'protocol') else 'UNKNOWN'
                protocol_counts[proto] = protocol_counts.get(proto, 0) + 1
                
                if hasattr(pkt, 'info'):
                    info = pkt.info
                    # Extract IPs
                    ip_matches = re.findall(r'(\d+\.\d+\.\d+\.\d+)', info)
                    for ip in ip_matches:
                        ip_counts[ip] = ip_counts.get(ip, 0) + 1
                    # Extract ports
                    port_matches = re.findall(r'\b(\d{2,5})\b', info)
                    for port in port_matches:
                        port_counts[port] = port_counts.get(port, 0) + 1
            
            cap.close()
            
            # Sort by count
            protocol_counts = dict(sorted(protocol_counts.items(), key=lambda x: x[1], reverse=True))
            port_counts = dict(sorted(port_counts.items(), key=lambda x: x[1], reverse=True)[:20])
            ip_counts = dict(sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:50])
            
            self.results = {
                'success': True,
                'analysis_time': datetime.now().isoformat(),
                'total_packets': total_packets,
                'protocol_counts': protocol_counts,
                'port_counts': port_counts,
                'ip_counts': ip_counts,
                'unique_protocols': len(protocol_counts),
                'unique_ips': len(ip_counts),
                'top_protocol': max(protocol_counts, key=protocol_counts.get) if protocol_counts else None
            }
            
            return self.results
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to parse PCAP file: {str(e)}'
            }
    
    async def analyze_pcap_async(self, file_content: bytes, filename: str) -> dict:
        """
        Analyze PCAP content from uploaded file
        
        Args:
            file_content: Raw bytes of the PCAP file
            filename: Original filename
            
        Returns:
            Dictionary containing analysis results
        """
        if not PYSHARK_AVAILABLE:
            return {
                'success': False,
                'error': 'pyshark is not installed'
            }
        
        temp_path = None
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pcap') as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
            
            # Analyze the file
            result = self.analyze_pcap(temp_path)
            result['filename'] = filename
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to process file: {str(e)}'
            }
        finally:
            # Clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass


class TrafficAnalyzer:
    """Provides real-time traffic analysis capabilities"""
    
    def __init__(self):
        self.suspicious_patterns = [
            r'(?i)password|passwd|pwd',
            r'(?i)credit.?card|cc.?num',
            r'(?i)ssn|social.?security',
            r'(?i)admin|root|administrator',
            r'(?i)bearer|token|api.?key',
        ]
        self.known_malicious_ports = [
            4444,  # Metasploit default
            5554,  # Sasser worm
            6666, 6667,  # IRC (often used by botnets)
            31337,  # Back Orifice
        ]
    
    def analyze_traffic_patterns(self, ip_counts: dict, port_counts: dict) -> dict:
        """
        Analyze traffic patterns for potential threats
        
        Args:
            ip_counts: Dictionary of IP addresses and their counts
            port_counts: Dictionary of ports and their counts
            
        Returns:
            Dictionary containing threat analysis
        """
        findings = []
        risk_score = 0
        
        # Check for suspicious ports
        for port_str in port_counts:
            try:
                port = int(port_str)
                if port in self.known_malicious_ports:
                    findings.append({
                        'type': 'danger',
                        'category': 'suspicious_port',
                        'message': f'Traffic detected on known malicious port {port}',
                        'port': port,
                        'count': port_counts[port_str]
                    })
                    risk_score += 25
            except ValueError:
                continue
        
        # Check for port scanning patterns (many ports with low counts)
        low_count_ports = [p for p, c in port_counts.items() if c <= 3]
        if len(low_count_ports) > 20:
            findings.append({
                'type': 'warning',
                'category': 'port_scan',
                'message': f'Potential port scanning detected ({len(low_count_ports)} ports with low traffic)',
                'ports_count': len(low_count_ports)
            })
            risk_score += 15
        
        # Check for IP patterns (single IP with high traffic)
        if ip_counts:
            max_ip = max(ip_counts, key=ip_counts.get)
            total_traffic = sum(ip_counts.values())
            if total_traffic > 0:
                max_ip_ratio = ip_counts[max_ip] / total_traffic
                if max_ip_ratio > 0.5:
                    findings.append({
                        'type': 'info',
                        'category': 'traffic_concentration',
                        'message': f'High traffic concentration from {max_ip} ({max_ip_ratio:.1%} of total)',
                        'ip': max_ip,
                        'percentage': max_ip_ratio * 100
                    })
        
        return {
            'findings': findings,
            'risk_score': min(risk_score, 100),
            'risk_level': self._get_risk_level(risk_score)
        }
    
    def _get_risk_level(self, score: int) -> str:
        """Convert risk score to risk level"""
        if score >= 75:
            return 'Critical'
        elif score >= 50:
            return 'High'
        elif score >= 25:
            return 'Medium'
        else:
            return 'Low'
