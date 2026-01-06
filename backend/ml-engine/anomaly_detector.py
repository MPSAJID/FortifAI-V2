"""
Anomaly Detection Module
Uses Isolation Forest and statistical methods
"""
import os
import json
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Any
from datetime import datetime

class AnomalyDetector:
    """
    Anomaly detection using Isolation Forest and statistical methods
    """
    
    def __init__(self, model_path: str = None):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.baseline_stats = {}
        self.feature_names = []
        
        # Try to load pre-trained model
        if model_path:
            self.load_trained_model(model_path)
        else:
            # Check default paths
            default_paths = [
                '/app/models/anomaly',
                '/app/models/trained',
                './models/anomaly',
            ]
            for path in default_paths:
                if os.path.exists(path) and os.path.exists(f'{path}/isolation_forest.joblib'):
                    print(f"Found anomaly model at {path}")
                    self.load_trained_model(path)
                    break
    
    def load_trained_model(self, path: str) -> bool:
        """Load pre-trained anomaly detector"""
        try:
            self.model = joblib.load(f'{path}/isolation_forest.joblib')
            self.scaler = joblib.load(f'{path}/anomaly_scaler.joblib')
            
            if os.path.exists(f'{path}/baseline_stats.json'):
                with open(f'{path}/baseline_stats.json', 'r') as f:
                    self.baseline_stats = json.load(f)
            
            if os.path.exists(f'{path}/feature_names.json'):
                with open(f'{path}/feature_names.json', 'r') as f:
                    self.feature_names = json.load(f)
            
            self.is_trained = True
            print(f"✓ Loaded anomaly detector from {path}")
            return True
        except Exception as e:
            print(f"Could not load anomaly model from {path}: {e}")
            return False
    
    def fit(self, data: List[Dict[str, Any]]):
        """Train the anomaly detector"""
        if not data:
            return {"status": "no_data"}
        
        features, self.feature_names = self._extract_features_batch(data)
        
        if len(features) < 10:
            return {"status": "insufficient_data", "required": 10, "current": len(features)}
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Train model
        self.model.fit(features_scaled)
        
        # Calculate baseline statistics
        self._calculate_baseline(features)
        
        self.is_trained = True
        
        return {
            "status": "trained",
            "samples": len(features),
            "features": self.feature_names
        }
    
    def detect(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if data point is anomalous"""
        features, _ = self._extract_features_batch([data])
        
        if not self.is_trained:
            # Use statistical detection if not trained
            return self._statistical_detection(data, features[0])
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict (-1 for anomaly, 1 for normal)
        prediction = self.model.predict(features_scaled)[0]
        score = self.model.decision_function(features_scaled)[0]
        
        # Also check statistical anomalies
        stat_result = self._statistical_detection(data, features[0])
        
        is_anomaly = prediction == -1 or stat_result['is_anomaly']
        
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": float(-score),  # Higher = more anomalous
            "statistical_anomalies": stat_result['anomalies'],
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_features_batch(self, data_list: List[Dict]) -> tuple:
        """Extract numerical features from data"""
        feature_names = [
            'cpu_usage', 'memory_usage', 'connection_count',
            'file_access_count', 'process_count', 'hour',
            'day_of_week', 'is_business_hours'
        ]
        
        features = []
        for data in data_list:
            feature_vector = [
                float(data.get('cpu_usage', 0) or 0),
                float(data.get('memory_usage', 0) or 0),
                int(data.get('connection_count', 0) or 0),
                int(data.get('file_access_count', 0) or 0),
                int(data.get('process_count', 0) or 0),
                self._get_hour(data.get('timestamp')),
                self._get_day_of_week(data.get('timestamp')),
                int(self._is_business_hours(data.get('timestamp')))
            ]
            features.append(feature_vector)
        
        return np.array(features), feature_names
    
    def _calculate_baseline(self, features: np.ndarray):
        """Calculate baseline statistics"""
        self.baseline_stats = {
            'mean': np.mean(features, axis=0),
            'std': np.std(features, axis=0),
            'min': np.min(features, axis=0),
            'max': np.max(features, axis=0)
        }
    
    def _statistical_detection(self, data: Dict, features: np.ndarray) -> Dict:
        """Statistical anomaly detection"""
        anomalies = []
        
        # Check for extreme values
        if data.get('cpu_usage', 0) > 95:
            anomalies.append("Extremely high CPU usage")
        
        if data.get('memory_usage', 0) > 90:
            anomalies.append("Extremely high memory usage")
        
        if data.get('connection_count', 0) > 1000:
            anomalies.append("Unusually high connection count")
        
        # Check for off-hours activity
        if not self._is_business_hours(data.get('timestamp')):
            if data.get('activity_level', 0) > 50:
                anomalies.append("High activity during off-hours")
        
        # Check against baseline if available
        if self.baseline_stats:
            for i, name in enumerate(self.feature_names):
                if self.baseline_stats['std'][i] > 0:
                    z_score = (features[i] - self.baseline_stats['mean'][i]) / self.baseline_stats['std'][i]
                    if abs(z_score) > 3:
                        anomalies.append(f"Statistical anomaly in {name} (z-score: {z_score:.2f})")
        
        return {
            "is_anomaly": len(anomalies) > 0,
            "anomalies": anomalies
        }
    
    def _get_hour(self, timestamp: str) -> int:
        if not timestamp:
            return datetime.now().hour
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.hour
        except:
            return datetime.now().hour
    
    def _get_day_of_week(self, timestamp: str) -> int:
        if not timestamp:
            return datetime.now().weekday()
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.weekday()
        except:
            return datetime.now().weekday()
    
    def _is_business_hours(self, timestamp: str) -> bool:
        hour = self._get_hour(timestamp)
        day = self._get_day_of_week(timestamp)
        return day < 5 and 8 <= hour <= 18
