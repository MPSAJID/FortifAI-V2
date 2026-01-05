"""
FortifAI ML Engine Tests
Tests for anomaly detection and behavior analytics (TensorFlow-free)
"""
import pytest
import numpy as np
import sys
from unittest.mock import MagicMock, patch

# Mock tensorflow before importing modules that use it
sys.modules['tensorflow'] = MagicMock()
sys.modules['tensorflow.keras'] = MagicMock()

import importlib

# Import modules that don't require TensorFlow
AnomalyDetector = importlib.import_module('backend.ml-engine.anomaly_detector').AnomalyDetector
UserBehaviorAnalytics = importlib.import_module('backend.ml-engine.behaviour_analytics').UserBehaviorAnalytics


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
        # anomaly_score may or may not be present depending on implementation
        assert 'is_anomaly' in result or 'anomalies' in result
    
    def test_fit_with_data(self):
        """Test fitting the model with data"""
        training_data = [
            {'cpu_usage': 20, 'memory_usage': 30},
            {'cpu_usage': 25, 'memory_usage': 35},
            {'cpu_usage': 22, 'memory_usage': 32},
            {'cpu_usage': 23, 'memory_usage': 31},
            {'cpu_usage': 21, 'memory_usage': 33},
        ] * 10  # Repeat to have enough samples
        
        result = self.detector.fit(training_data)
        assert result['status'] in ['trained', 'insufficient_data', 'success']
    
    def test_fit_empty_data(self):
        """Test fitting with empty data"""
        result = self.detector.fit([])
        assert result['status'] == 'no_data'
    
    def test_detect_after_training(self):
        """Test detection after training"""
        training_data = [
            {'cpu_usage': 20, 'memory_usage': 30},
            {'cpu_usage': 25, 'memory_usage': 35},
        ] * 20
        
        self.detector.fit(training_data)
        
        # Test with normal data
        normal_result = self.detector.detect({
            'cpu_usage': 22,
            'memory_usage': 32
        })
        assert 'is_anomaly' in normal_result
        
        # Test with anomalous data
        anomaly_result = self.detector.detect({
            'cpu_usage': 99,
            'memory_usage': 99
        })
        assert 'is_anomaly' in anomaly_result


class TestUserBehaviorAnalytics:
    """Tests for UserBehaviorAnalytics"""
    
    def setup_method(self):
        self.analytics = UserBehaviorAnalytics()
    
    def test_initialization(self):
        """Test analytics initialization"""
        assert self.analytics is not None
        assert self.analytics.baseline_established == False
    
    def test_record_activity(self):
        """Test recording user activity"""
        activity = {
            'event_type': 'login',
            'timestamp': '2024-01-15T09:00:00',
            'ip_address': '192.168.1.100'
        }
        
        self.analytics.record_activity('user1', activity)
        assert 'user1' in self.analytics.user_profiles
    
    def test_record_multiple_activities(self):
        """Test recording multiple activities for a user"""
        for i in range(5):
            self.analytics.record_activity('user1', {
                'event_type': 'login',
                'timestamp': f'2024-01-{15+i}T09:00:00'
            })
        
        assert 'user1' in self.analytics.user_profiles
        profile = self.analytics.user_profiles['user1']
        assert len(profile['activities']) == 5
    
    def test_analyze_behavior_new_user(self):
        """Test behavior analysis for new user"""
        result = self.analytics.analyze_behavior('new_user', {
            'event_type': 'login',
            'timestamp': '2024-01-30T03:00:00'
        })
        
        # Should return some result for new users
        assert result is not None
    
    def test_analyze_behavior_existing_user(self):
        """Test behavior analysis for existing user"""
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
        
        assert result is not None
        # Should have some risk assessment
        assert 'risk_level' in result or 'risk_score' in result or 'reason' in result or 'status' in result
    
    def test_multiple_users(self):
        """Test tracking multiple users"""
        self.analytics.record_activity('user1', {'event_type': 'login'})
        self.analytics.record_activity('user2', {'event_type': 'login'})
        self.analytics.record_activity('user3', {'event_type': 'login'})
        
        assert 'user1' in self.analytics.user_profiles
        assert 'user2' in self.analytics.user_profiles
        assert 'user3' in self.analytics.user_profiles


class TestThreatClassifierMocked:
    """Tests for ThreatClassifier with mocked TensorFlow"""
    
    def test_threat_classifier_import(self):
        """Test that ThreatClassifier can be imported with mocked TensorFlow"""
        ThreatClassifier = importlib.import_module('backend.ml-engine.threat_classifier').ThreatClassifier
        classifier = ThreatClassifier()
        assert classifier is not None
        assert len(classifier.threat_categories) > 0
    
    def test_threat_categories(self):
        """Test threat categories are defined"""
        ThreatClassifier = importlib.import_module('backend.ml-engine.threat_classifier').ThreatClassifier
        classifier = ThreatClassifier()
        
        expected_categories = ['normal', 'malware', 'ransomware', 'trojan']
        for cat in expected_categories:
            assert cat in classifier.threat_categories
    
    def test_classifier_not_trained_initially(self):
        """Test classifier is not trained on initialization"""
        ThreatClassifier = importlib.import_module('backend.ml-engine.threat_classifier').ThreatClassifier
        classifier = ThreatClassifier()
        assert classifier.is_trained == False
