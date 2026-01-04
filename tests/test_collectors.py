"""
FortifAI Data Collector Tests
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'data-collector'))

from collectors.process_collector import ProcessCollector
from collectors.network_collector import NetworkCollector
from collectors.file_collector import FileLogCollector


class TestProcessCollector:
    """Tests for ProcessCollector"""
    
    def setup_method(self):
        self.collector = ProcessCollector()
    
    def test_initialization(self):
        """Test collector initialization"""
        assert self.collector is not None
        assert len(self.collector.suspicious_patterns) > 0
    
    def test_collect(self):
        """Test process collection"""
        processes = self.collector.collect()
        assert isinstance(processes, list)
    
    def test_is_suspicious_normal(self):
        """Test suspicious detection for normal process"""
        pinfo = {
            'name': 'notepad.exe',
            'cmdline': [],
            'cpu_percent': 5,
            'memory_percent': 1
        }
        assert not self.collector._is_suspicious(pinfo)
    
    def test_is_suspicious_pattern(self):
        """Test suspicious detection for known pattern"""
        pinfo = {
            'name': 'mimikatz.exe',
            'cmdline': [],
            'cpu_percent': 5,
            'memory_percent': 1
        }
        assert self.collector._is_suspicious(pinfo)
    
    def test_is_suspicious_high_cpu(self):
        """Test suspicious detection for high CPU"""
        pinfo = {
            'name': 'some_app.exe',
            'cmdline': [],
            'cpu_percent': 95,
            'memory_percent': 10
        }
        assert self.collector._is_suspicious(pinfo)


class TestNetworkCollector:
    """Tests for NetworkCollector"""
    
    def setup_method(self):
        self.collector = NetworkCollector()
    
    def test_initialization(self):
        """Test collector initialization"""
        assert self.collector is not None
        assert len(self.collector.suspicious_ports) > 0
    
    def test_collect(self):
        """Test network collection"""
        connections = self.collector.collect()
        assert isinstance(connections, list)
    
    def test_is_private_ip(self):
        """Test private IP detection"""
        assert self.collector._is_private_ip('192.168.1.1')
        assert self.collector._is_private_ip('10.0.0.1')
        assert self.collector._is_private_ip('172.16.0.1')
        assert self.collector._is_private_ip('127.0.0.1')
        assert not self.collector._is_private_ip('8.8.8.8')
    
    def test_add_suspicious_ip(self):
        """Test adding suspicious IP"""
        self.collector.add_suspicious_ip('1.2.3.4')
        assert '1.2.3.4' in self.collector.suspicious_ips
    
    def test_get_connection_summary(self):
        """Test connection summary"""
        summary = self.collector.get_connection_summary()
        assert 'total' in summary or 'error' in summary


class TestFileLogCollector:
    """Tests for FileLogCollector"""
    
    def test_initialization(self):
        """Test collector initialization"""
        # Use mock to avoid actually starting observer
        with patch.object(FileLogCollector, '_start_observer'):
            collector = FileLogCollector()
            assert collector is not None
            assert collector.watched_paths is not None
    
    def test_get_watched_paths(self):
        """Test watched paths retrieval"""
        with patch.object(FileLogCollector, '_start_observer'):
            collector = FileLogCollector()
            paths = collector._get_watched_paths()
            assert isinstance(paths, list)

