import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow import keras
from datetime import datetime
import joblib
import json

class ThreatClassifier:
    """
    Multi-model threat classification system using ensemble learning
    and deep learning for accurate threat detection.
    """
    
    def __init__(self):
        self.rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.gb_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.deep_model = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.threat_categories = [
            'normal', 'malware', 'ransomware', 'trojan', 
            'ddos', 'brute_force', 'data_exfiltration', 'privilege_escalation'
        ]
        self.is_trained = False
        
    def build_deep_model(self, input_dim):
        """Build deep neural network for threat classification"""
        model = keras.Sequential([
            keras.layers.Dense(256, activation='relu', input_dim=input_dim),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.3),
            
            keras.layers.Dense(128, activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.3),
            
            keras.layers.Dense(64, activation='relu'),
            keras.layers.BatchNormalization(),
            keras.layers.Dropout(0.2),
            
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(len(self.threat_categories), activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def extract_advanced_features(self, log_entry):
        """Extract comprehensive features from log entries"""
        features = {
            # Basic process features
            'pid': log_entry.get('pid', 0),
            'ppid': log_entry.get('ppid', 0),
            'cpu_usage': log_entry.get('cpu_usage', 0.0) or 0.0,
            'memory_usage': log_entry.get('memory_usage', 0) or 0,
            
            # Time-based features
            'hour': self._extract_hour(log_entry.get('timestamp')),
            'day_of_week': self._extract_day_of_week(log_entry.get('timestamp')),
            'is_business_hours': self._is_business_hours(log_entry.get('timestamp')),
            
            # Process behavior features
            'process_name_length': len(log_entry.get('process_name', '') or ''),
            'is_system_process': self._is_system_process(log_entry.get('process_name')),
            'has_suspicious_name': self._has_suspicious_name(log_entry.get('process_name')),
            
            # File activity features
            'file_path_depth': self._get_path_depth(log_entry.get('file_path')),
            'is_temp_directory': self._is_temp_directory(log_entry.get('file_path')),
            'is_system_directory': self._is_system_directory(log_entry.get('file_path')),
            
            # Network indicators
            'has_network_activity': log_entry.get('has_network_activity', 0),
            'connection_count': log_entry.get('connection_count', 0),
            
            # Behavioral indicators
            'rapid_file_changes': log_entry.get('rapid_file_changes', 0),
            'privilege_level': self._get_privilege_level(log_entry.get('user')),
        }
        
        return features
    
    def _extract_hour(self, timestamp):
        if not timestamp:
            return 0
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.hour
        except:
            return 0
    
    def _extract_day_of_week(self, timestamp):
        if not timestamp:
            return 0
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.weekday()
        except:
            return 0
    
    def _is_business_hours(self, timestamp):
        hour = self._extract_hour(timestamp)
        day = self._extract_day_of_week(timestamp)
        return 1 if (9 <= hour <= 17 and day < 5) else 0
    
    def _is_system_process(self, process_name):
        if not process_name:
            return 0
        system_processes = ['svchost.exe', 'csrss.exe', 'lsass.exe', 'services.exe', 
                          'winlogon.exe', 'explorer.exe', 'System', 'smss.exe']
        return 1 if process_name in system_processes else 0
    
    def _has_suspicious_name(self, process_name):
        if not process_name:
            return 0
        suspicious_patterns = ['temp', 'tmp', 'random', 'update', 'install', 
                              'setup', 'crack', 'keygen', 'patch']
        name_lower = process_name.lower()
        return 1 if any(p in name_lower for p in suspicious_patterns) else 0
    
    def _get_path_depth(self, file_path):
        if not file_path:
            return 0
        return file_path.count('/') + file_path.count('\\')
    
    def _is_temp_directory(self, file_path):
        if not file_path:
            return 0
        temp_patterns = ['temp', 'tmp', 'cache', 'appdata\\local\\temp']
        path_lower = file_path.lower()
        return 1 if any(p in path_lower for p in temp_patterns) else 0
    
    def _is_system_directory(self, file_path):
        if not file_path:
            return 0
        system_patterns = ['windows\\system32', 'program files', '/usr/bin', '/etc']
        path_lower = file_path.lower()
        return 1 if any(p in path_lower for p in system_patterns) else 0
    
    def _get_privilege_level(self, user):
        if not user:
            return 1
        admin_patterns = ['admin', 'root', 'system', 'administrator']
        return 3 if any(p in user.lower() for p in admin_patterns) else 1
    
    def train(self, training_data, labels):
        """Train all models on the provided data"""
        print("Extracting features...")
        
        features_list = [self.extract_advanced_features(log) for log in training_data]
        X = pd.DataFrame(features_list)
        
        # Encode labels
        y = self.label_encoder.fit_transform(labels)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        print("Training Random Forest...")
        self.rf_model.fit(X_train, y_train)
        rf_score = self.rf_model.score(X_test, y_test)
        print(f"Random Forest Accuracy: {rf_score:.4f}")
        
        # Train Gradient Boosting
        print("Training Gradient Boosting...")
        self.gb_model.fit(X_train, y_train)
        gb_score = self.gb_model.score(X_test, y_test)
        print(f"Gradient Boosting Accuracy: {gb_score:.4f}")
        
        # Train Deep Neural Network
        print("Training Deep Neural Network...")
        self.deep_model = self.build_deep_model(X_train.shape[1])
        
        early_stopping = keras.callbacks.EarlyStopping(
            monitor='val_loss', patience=10, restore_best_weights=True
        )
        
        self.deep_model.fit(
            X_train, y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            callbacks=[early_stopping],
            verbose=1
        )
        
        deep_score = self.deep_model.evaluate(X_test, y_test, verbose=0)[1]
        print(f"Deep Learning Accuracy: {deep_score:.4f}")
        
        self.is_trained = True
        
        return {
            'random_forest': rf_score,
            'gradient_boosting': gb_score,
            'deep_learning': deep_score
        }
    
    def predict(self, log_entry):
        """
        Ensemble prediction using all models with confidence scoring
        """
        if not self.is_trained:
            # Return rule-based analysis when model not trained
            return self._rule_based_prediction(log_entry)
        
        features = self.extract_advanced_features(log_entry)
        X = pd.DataFrame([features])
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from all models
        rf_pred = self.rf_model.predict(X_scaled)[0]
        rf_proba = self.rf_model.predict_proba(X_scaled)[0]
        
        gb_pred = self.gb_model.predict(X_scaled)[0]
        gb_proba = self.gb_model.predict_proba(X_scaled)[0]
        
        deep_proba = self.deep_model.predict(X_scaled, verbose=0)[0]
        deep_pred = np.argmax(deep_proba)
        
        # Ensemble voting (weighted average)
        ensemble_proba = (0.3 * rf_proba + 0.3 * gb_proba + 0.4 * deep_proba)
        final_pred = np.argmax(ensemble_proba)
        confidence = float(np.max(ensemble_proba))
        
        threat_type = self.label_encoder.inverse_transform([final_pred])[0]
        
        return {
            'threat_type': threat_type,
            'classification': threat_type,  # Alias for compatibility
            'confidence': confidence,
            'is_threat': threat_type != 'normal',
            'risk_score': confidence * (0.9 if threat_type != 'normal' else 0.1),
            'severity': self._get_severity(threat_type, confidence),
            'model_predictions': {
                'random_forest': self.label_encoder.inverse_transform([rf_pred])[0],
                'gradient_boosting': self.label_encoder.inverse_transform([gb_pred])[0],
                'deep_learning': self.label_encoder.inverse_transform([deep_pred])[0]
            },
            'probabilities': {
                cat: float(ensemble_proba[i]) 
                for i, cat in enumerate(self.label_encoder.classes_)
            }
        }
    
    def _get_severity(self, threat_type, confidence):
        severity_map = {
            'normal': 'none',
            'malware': 'critical',
            'ransomware': 'critical',
            'trojan': 'high',
            'ddos': 'high',
            'brute_force': 'medium',
            'data_exfiltration': 'critical',
            'privilege_escalation': 'high'
        }
        
        base_severity = severity_map.get(threat_type, 'low')
        
        # Adjust based on confidence
        if confidence < 0.5:
            return 'low' if base_severity in ['critical', 'high'] else 'low'
        
        return base_severity
    
    def save_models(self, path):
        """Save all trained models"""
        joblib.dump(self.rf_model, f'{path}/rf_model.joblib')
        joblib.dump(self.gb_model, f'{path}/gb_model.joblib')
        joblib.dump(self.scaler, f'{path}/scaler.joblib')
        joblib.dump(self.label_encoder, f'{path}/label_encoder.joblib')
        self.deep_model.save(f'{path}/deep_model.h5')
        
    def load_models(self, path):
        """Load pre-trained models"""
        self.rf_model = joblib.load(f'{path}/rf_model.joblib')
        self.gb_model = joblib.load(f'{path}/gb_model.joblib')
        self.scaler = joblib.load(f'{path}/scaler.joblib')
        self.label_encoder = joblib.load(f'{path}/label_encoder.joblib')
        self.deep_model = keras.models.load_model(f'{path}/deep_model.h5')
        self.is_trained = True

    def _rule_based_prediction(self, log_entry):
        """
        Rule-based threat detection when ML models are not trained.
        Provides basic threat detection using heuristics.
        """
        threat_indicators = []
        confidence = 0.0
        threat_type = 'normal'
        
        # Check for suspicious process names
        process_name = (log_entry.get('process_name') or '').lower()
        suspicious_processes = ['mimikatz', 'psexec', 'procdump', 'netcat', 'nc.exe',
                                'certutil', 'bitsadmin', 'powershell -enc', 'nmap', 'masscan']
        for sp in suspicious_processes:
            if sp in process_name:
                threat_indicators.append(f'suspicious_process:{sp}')
                threat_type = 'malware'
                confidence = max(confidence, 0.85)
        
        # Check command line for suspicious patterns
        cmdline = (log_entry.get('cmdline') or '').lower()
        if 'base64' in cmdline or '-enc' in cmdline:
            threat_indicators.append('encoded_command')
            threat_type = 'malware'
            confidence = max(confidence, 0.8)
        
        # Check for high resource usage (potential crypto mining or DoS)
        cpu_usage = log_entry.get('cpu_usage', 0) or 0
        memory_usage = log_entry.get('memory_usage', 0) or 0
        if cpu_usage > 90:
            threat_indicators.append('high_cpu_usage')
            if threat_type == 'normal':
                threat_type = 'ddos'
            confidence = max(confidence, 0.6)
        if memory_usage > 85:
            threat_indicators.append('high_memory_usage')
            confidence = max(confidence, 0.5)
        
        # Check for suspicious network ports
        remote_port = log_entry.get('remote_port', 0) or 0
        suspicious_ports = [4444, 5555, 6666, 31337, 12345, 1337]
        if remote_port in suspicious_ports:
            threat_indicators.append(f'suspicious_port:{remote_port}')
            threat_type = 'malware'
            confidence = max(confidence, 0.9)
        
        # Check for privilege escalation indicators
        if log_entry.get('is_suspicious', False):
            threat_indicators.append('marked_suspicious')
            confidence = max(confidence, 0.7)
            if threat_type == 'normal':
                threat_type = 'privilege_escalation'
        
        # Check for off-hours activity with high privilege
        if not self._is_business_hours(log_entry.get('timestamp')):
            user = (log_entry.get('user') or '').lower()
            if 'admin' in user or 'root' in user:
                threat_indicators.append('off_hours_admin_activity')
                confidence = max(confidence, 0.65)
                if threat_type == 'normal':
                    threat_type = 'privilege_escalation'
        
        # Default confidence for normal activity
        if threat_type == 'normal':
            confidence = 0.95  # High confidence it's normal
        
        is_threat = threat_type != 'normal'
        risk_score = confidence * (0.9 if is_threat else 0.1)
        
        return {
            'threat_type': threat_type,
            'classification': threat_type,
            'confidence': confidence,
            'is_threat': is_threat,
            'risk_score': risk_score,
            'severity': self._get_severity(threat_type, confidence),
            'indicators': threat_indicators,
            'model_predictions': {
                'rule_based': threat_type
            },
            'probabilities': {
                threat_type: confidence,
                'normal': 1 - confidence if is_threat else confidence
            }
        }
