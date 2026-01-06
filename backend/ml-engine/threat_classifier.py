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
import os

class ThreatClassifier:
    """
    Multi-model threat classification system using ensemble learning
    and deep learning for accurate threat detection.
    """
    
    def __init__(self, model_path: str = None):
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
        self.feature_columns = None
        
        # Try to load pre-trained models on init
        if model_path:
            self.load_trained_models(model_path)
        else:
            # Check default paths
            default_paths = [
                '/app/models/trained',
                './models/trained',
                '../ml-models/threat-classification/trained'
            ]
            for path in default_paths:
                if os.path.exists(path) and os.path.exists(f'{path}/rf_model.joblib'):
                    print(f"Found trained models at {path}")
                    self.load_trained_models(path)
                    break
    
    def load_trained_models(self, path: str):
        """Load pre-trained sklearn models"""
        try:
            self.rf_model = joblib.load(f'{path}/rf_model.joblib')
            self.gb_model = joblib.load(f'{path}/gb_model.joblib')
            self.scaler = joblib.load(f'{path}/scaler.joblib')
            self.label_encoder = joblib.load(f'{path}/label_encoder.joblib')
            
            # Load feature columns
            if os.path.exists(f'{path}/feature_columns.json'):
                with open(f'{path}/feature_columns.json', 'r') as f:
                    self.feature_columns = json.load(f)
            
            self.is_trained = True
            print(f"✓ Loaded trained models from {path}")
            print(f"  Classes: {list(self.label_encoder.classes_)}")
            return True
        except Exception as e:
            print(f"Could not load models from {path}: {e}")
            return False
    
    def extract_features_for_trained_model(self, log_entry):
        """Extract features matching the trained model's feature columns.
        This must match the features used in train_hybrid.py"""
        
        process_name = (log_entry.get('process_name') or '').lower()
        cmdline = (log_entry.get('command_line') or log_entry.get('cmdline') or '').lower()
        username = (log_entry.get('username') or log_entry.get('user') or '').lower()
        
        # Known threat indicators in command line
        encoded_patterns = ['base64', 'encodedcommand', '-enc', '-e ', 'frombase64']
        download_patterns = ['wget', 'curl', 'downloadstring', 'invoke-webrequest', 'bitsadmin', 'certutil -urlcache']
        connect_patterns = ['reverse', 'shell', 'connect', 'bind', 'nc.exe', 'ncat', 'netcat']
        encrypt_patterns = ['encrypt', 'cipher', 'crypt', 'ransom', 'locked', 'vssadmin delete']
        cred_dump_patterns = ['mimikatz', 'procdump', 'lsass', 'sekurlsa', 'sam ', 'hashdump']
        
        # Known malicious tools
        mimikatz_patterns = ['mimikatz', 'sekurlsa', 'logonpasswords', 'lsadump', 'kerberos::']
        psexec_patterns = ['psexec', 'paexec', 'remcom', 'csexec']
        bloodhound_patterns = ['bloodhound', 'sharphound', 'adrecon', 'powerview']
        cobalt_patterns = ['cobaltstrike', 'beacon', 'cobalt']
        lateral_patterns = ['psexec', 'wmiexec', 'smbexec', 'atexec', 'dcomexec', 'winrm']
        priv_esc_patterns = ['juicypotato', 'printspoofer', 'godpotato', 'sweetpotato', 'getsystem']
        
        # Known malware names
        malware_names = [
            'emotet', 'trickbot', 'qbot', 'icedid', 'dridex', 'njrat', 'asyncrat',
            'remcos', 'agenttesla', 'formbook', 'lokibot', 'ryuk', 'conti', 'lockbit',
            'revil', 'darkside', 'xmrig', 'cgminer', 'wannacry', 'cryptolocker'
        ]
        
        # Typosquatting check (misspelled Windows processes)
        typosquat_targets = ['svch0st', 'scvhost', 'svhost', 'crss', 'cssrs', 'lssas', 'isass', 'expl0rer']
        has_typo = any(typo in process_name for typo in typosquat_targets)
        
        # Check for known malware
        known_malware = any(m in process_name or m in cmdline for m in malware_names)
        
        features = {
            'cpu_usage': float(log_entry.get('cpu_usage') or log_entry.get('cpu_percent') or 0),
            'memory_usage': float(log_entry.get('memory_usage') or log_entry.get('memory_percent') or 0),
            'name_length': len(process_name),
            'cmd_length': len(cmdline),
            'has_args': 1 if ' ' in cmdline else 0,
            'has_network': 1 if log_entry.get('network_connections') or log_entry.get('connections') else 0,
            'connections': int(log_entry.get('network_connections') or log_entry.get('connections') or 0),
            'is_system_user': 1 if username in ['system', 'root', 'nt authority\\system'] else 0,
            'encoded_cmd': 1 if any(p in cmdline for p in encoded_patterns) else 0,
            'download_cmd': 1 if any(p in cmdline for p in download_patterns) else 0,
            'connect_cmd': 1 if any(p in cmdline for p in connect_patterns) else 0,
            'encrypt_cmd': 1 if any(p in cmdline for p in encrypt_patterns) else 0,
            'cred_dump': 1 if any(p in cmdline or p in process_name for p in cred_dump_patterns) else 0,
            'is_mimikatz': 1 if any(p in cmdline or p in process_name for p in mimikatz_patterns) else 0,
            'is_psexec': 1 if any(p in cmdline or p in process_name for p in psexec_patterns) else 0,
            'is_bloodhound': 1 if any(p in cmdline or p in process_name for p in bloodhound_patterns) else 0,
            'is_cobalt': 1 if any(p in cmdline or p in process_name for p in cobalt_patterns) else 0,
            'has_typo': 1 if has_typo else 0,
            'known_malware': 1 if known_malware else 0,
            'lateral_movement': 1 if any(p in cmdline for p in lateral_patterns) else 0,
            'priv_esc': 1 if any(p in cmdline or p in process_name for p in priv_esc_patterns) else 0,
        }
        
        return features
        
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
        
        # Use trained model feature extraction if feature_columns are available
        if self.feature_columns:
            features = self.extract_features_for_trained_model(log_entry)
            # Ensure features are in the correct order
            X = pd.DataFrame([features])[self.feature_columns]
        else:
            features = self.extract_advanced_features(log_entry)
            X = pd.DataFrame([features])
        
        X_scaled = self.scaler.transform(X)
        
        # Get predictions from sklearn models (no deep model with pre-trained)
        rf_pred = self.rf_model.predict(X_scaled)[0]
        rf_proba = self.rf_model.predict_proba(X_scaled)[0]
        
        gb_pred = self.gb_model.predict(X_scaled)[0]
        gb_proba = self.gb_model.predict_proba(X_scaled)[0]
        
        # Average probabilities from both models
        ensemble_proba = (0.5 * rf_proba + 0.5 * gb_proba)
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
        IMPROVED: Much lower false positive rate by whitelisting known-good processes.
        """
        threat_indicators = []
        confidence = 0.0
        threat_type = 'normal'
        
        process_name = (log_entry.get('process_name') or '').lower()
        cmdline = (log_entry.get('cmdline') or '').lower()
        user = (log_entry.get('user') or '').lower()
        
        # =====================================================================
        # WHITELIST: These are ALWAYS normal - don't flag them
        # =====================================================================
        safe_processes = [
            # Windows System
            'system', 'system idle process', 'registry', 'memory compression',
            'svchost.exe', 'csrss.exe', 'lsass.exe', 'services.exe', 'wininit.exe',
            'winlogon.exe', 'explorer.exe', 'smss.exe', 'spoolsv.exe', 'dwm.exe',
            'searchindexer.exe', 'runtimebroker.exe', 'taskhostw.exe',
            'shellexperiencehost.exe', 'sihost.exe', 'fontdrvhost.exe',
            'ctfmon.exe', 'audiodg.exe', 'conhost.exe', 'dllhost.exe',
            'wmiprvse.exe', 'searchui.exe', 'searchapp.exe', 'securityhealthservice.exe',
            # Security software - NEVER flag these
            'msmpeng.exe', 'nissrv.exe', 'mssense.exe', 'sense.exe',
            # Browsers - high CPU/memory is NORMAL
            'chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe',
            'iexplore.exe', 'safari.exe', 'vivaldi.exe',
            # Development tools - 100% CPU is NORMAL during builds
            'code.exe', 'devenv.exe', 'rider64.exe', 'pycharm64.exe', 'idea64.exe',
            'python.exe', 'python3.exe', 'pythonw.exe', 'python3.11.exe', 'python3.12.exe',
            'node.exe', 'npm.exe', 'npx.exe', 'yarn.exe', 'pnpm.exe',
            'java.exe', 'javaw.exe', 'gradle.exe', 'mvn.exe',
            'tsc.exe', 'webpack.exe', 'vite.exe', 'esbuild.exe',
            'dotnet.exe', 'msbuild.exe', 'csc.exe', 'cl.exe',
            'go.exe', 'rustc.exe', 'cargo.exe', 'gcc.exe', 'g++.exe', 'make.exe',
            # Shells & Terminals - developers use these legitimately
            'bash.exe', 'sh.exe', 'zsh.exe', 'fish.exe',
            'cmd.exe', 'powershell.exe', 'pwsh.exe', 'windowsterminal.exe',
            # Docker - high usage during builds is NORMAL
            'docker.exe', 'docker desktop.exe', 'com.docker.backend.exe', 'dockerd.exe',
            'wsl.exe', 'wslhost.exe', 'wslservice.exe', 'vmmemwsl',
            # Git
            'git.exe', 'git-remote-https.exe', 'ssh.exe', 'ssh-agent.exe',
            # Office & Communication
            'outlook.exe', 'winword.exe', 'excel.exe', 'powerpnt.exe',
            'teams.exe', 'slack.exe', 'discord.exe', 'zoom.exe', 'skype.exe',
            # Media
            'spotify.exe', 'vlc.exe', 'wmplayer.exe',
            # Database tools
            'postgres.exe', 'mysql.exe', 'mongod.exe', 'redis-server.exe',
        ]
        
        # Quick exit for safe processes
        if any(safe in process_name for safe in safe_processes):
            return {
                'threat_type': 'normal',
                'classification': 'normal',
                'confidence': 0.95,
                'is_threat': False,
                'risk_score': 0.05,
                'severity': 'none',
                'indicators': ['whitelisted_process'],
                'model_predictions': {'rule_based': 'normal'},
                'probabilities': {'normal': 0.95}
            }
        
        # =====================================================================
        # KNOWN MALICIOUS: These are ALWAYS threats
        # =====================================================================
        known_malware = ['mimikatz', 'psexec', 'procdump', 'winpeas', 'linpeas',
                         'juicypotato', 'printspoofer', 'rubeus', 'sharphound',
                         'bloodhound', 'cobaltstrike', 'meterpreter', 'empire']
        for malware in known_malware:
            if malware in process_name or malware in cmdline:
                return {
                    'threat_type': 'malware',
                    'classification': 'malware',
                    'confidence': 0.95,
                    'is_threat': True,
                    'risk_score': 0.95,
                    'severity': 'critical',
                    'indicators': [f'known_malware:{malware}'],
                    'model_predictions': {'rule_based': 'malware'},
                    'probabilities': {'malware': 0.95, 'normal': 0.05}
                }
        
        # =====================================================================
        # PROCESS NAME TYPOSQUATTING (common malware technique)
        # =====================================================================
        typosquat_patterns = {
            'svchost': ['svchosts.exe', 'scvhost.exe', 'svhost.exe', 'svchost32.exe'],
            'csrss': ['csrs.exe', 'csrrs.exe', 'cssrs.exe', 'csrss32.exe'],
            'explorer': ['explore.exe', 'explorar.exe', 'explorer32.exe'],
            'lsass': ['lsas.exe', 'lsass32.exe', 'lsasss.exe'],
        }
        for legit, fakes in typosquat_patterns.items():
            if process_name in [f.lower() for f in fakes]:
                threat_indicators.append(f'typosquatting:{legit}')
                threat_type = 'trojan'
                confidence = 0.9
        
        # =====================================================================
        # SUSPICIOUS COMMAND LINE PATTERNS
        # =====================================================================
        suspicious_cmdline_patterns = [
            ('encodedcommand', 'malware', 0.85),
            ('downloadstring', 'malware', 0.85),
            ('invoke-expression', 'malware', 0.8),
            ('-nop -w hidden', 'malware', 0.9),
            ('net user /add', 'privilege_escalation', 0.85),
            ('reg add.*run', 'malware', 0.8),
            ('sekurlsa', 'malware', 0.95),
            ('lsadump', 'malware', 0.95),
            ('--reverse-shell', 'trojan', 0.95),
            ('--encrypt', 'ransomware', 0.8),
            ('--ransom', 'ransomware', 0.9),
        ]
        for pattern, t_type, conf in suspicious_cmdline_patterns:
            if pattern in cmdline:
                threat_indicators.append(f'suspicious_cmdline:{pattern}')
                threat_type = t_type
                confidence = max(confidence, conf)
        
        # =====================================================================
        # SUSPICIOUS PORTS (only flag if process is unknown)
        # =====================================================================
        remote_port = log_entry.get('remote_port', 0) or 0
        if remote_port in [4444, 5555, 6666, 31337, 12345, 1337]:
            threat_indicators.append(f'suspicious_port:{remote_port}')
            if threat_type == 'normal':
                threat_type = 'trojan'
            confidence = max(confidence, 0.75)
        
        # Default: if no indicators found, it's probably normal
        if not threat_indicators:
            threat_type = 'normal'
            confidence = 0.85
        
        is_threat = threat_type != 'normal'
        risk_score = confidence * (0.9 if is_threat else 0.1)
        
        return {
            'threat_type': threat_type,
            'classification': threat_type,
            'confidence': confidence,
            'is_threat': is_threat,
            'risk_score': risk_score,
            'severity': self._get_severity(threat_type, confidence),
            'indicators': threat_indicators if threat_indicators else ['none'],
            'model_predictions': {'rule_based': threat_type},
            'probabilities': {
                threat_type: confidence,
                'normal': 1 - confidence if is_threat else confidence
            }
        }
