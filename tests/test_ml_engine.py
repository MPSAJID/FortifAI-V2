"""
FortifAI ML Engine Tests
"""
import pytest
import numpy as np
from backend.ml_engine.threat_classifier import ThreatClassifier
from backend.ml_engine.anomaly_detector import AnomalyDetector
from backend.ml_engine.behaviour_analytics import UserBehaviorAnalytics

class TestThreatClassifier:
    """Tests for ThreatClassifier"""
    
    def setup_method(self):
        self.classifier = ThreatClassifier()
    
    def test_initialization(self):
        """Test classifier initialization"""
        assert self.classifier is not None
        assert len(self.classifier.threat_categories) > 0
    
    def test_extract_features(self):
        """Test feature extraction"""
        log_entry = {
            'pid': 1234,
            'process_name': 'test.exe',
            'cpu_usage': 50.0,
            'memory_usage': 1024,
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        features = self.classifier.extract_advanced_features(log_entry)
        assert 'cpu_usage' in features
        assert 'memory_usage' in features
        assert 'hour' in features
    
    def test_predict_without_training(self):
        """Test prediction returns default when not trained"""
        log_entry = {
            'process_name': 'test.exe',
            'cpu_usage': 10.0
        }
        
        result = self.classifier.predict(log_entry)
        assert 'classification' in result


class TestAnomalyDetector:
    """Tests for AnomalyDetector"""
    
    def setup_method(self):
        self.detector = AnomalyDetector()
    
    def test_initialization(self):
        """Test detector initialization"""
        assert self.detector is not None
        assert self.detector.is_trained == False
    
    def test_detect_without_training(self):
        """Test detection without training uses statistical methods"""
        data = {
            'cpu_usage': 95,
            'memory_usage': 90,
            'connection_count': 100
        }
        
        result = self.detector.detect(data)
        assert 'is_anomaly' in result
        assert 'anomaly_score' in result
    
    def test_fit(self):
        """Test fitting the model"""
        training_data = [
            {'cpu_usage': 20, 'memory_usage': 30},
            {'cpu_usage': 25, 'memory_usage': 35},
            {'cpu_usage': 22, 'memory_usage': 32},
        ] * 10  # Repeat to have enough samples
        
        result = self.detector.fit(training_data)
        assert result['status'] in ['trained', 'insufficient_data']


class TestUserBehaviorAnalytics:
    """Tests for UserBehaviorAnalytics"""
    
    def setup_method(self):
        self.analytics = UserBehaviorAnalytics()
    
    def test_initialization(self):
        """Test analytics initialization"""
        assert self.analytics is not None
    
    def test_record_activity(self):
        """Test recording user activity"""
        activity = {
            'event_type': 'login',
            'timestamp': '2024-01-15T09:00:00',
            'ip_address': '192.168.1.100'
        }
        
        self.analytics.record_activity('user1', activity)
        assert 'user1' in self.analytics.user_profiles
    
    def test_analyze_behavior(self):
        """Test behavior analysis"""
        # Record some activities first
        for i in range(10):
            self.analytics.record_activity('user1', {
                'event_type': 'login',
                'timestamp': f'2024-01-{15+i}T09:00:00'
            })
        
        result = self.analytics.analyze_behavior('user1', {
            'event_type': 'login',
            'timestamp': '2024-01-30T03:00:00'  # Unusual hour
        })
        
        assert 'risk_level' in result or 'reason' in result
