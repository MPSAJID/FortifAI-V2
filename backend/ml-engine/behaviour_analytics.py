import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import json

class UserBehaviorAnalytics:
    """
    User and Entity Behavior Analytics (UEBA) for detecting
    insider threats and compromised accounts.
    """
    
    def __init__(self):
        self.user_profiles = defaultdict(lambda: {
            'login_times': [],
            'locations': [],
            'devices': [],
            'activities': [],
            'file_access_patterns': [],
            'process_patterns': [],
            'risk_score': 0.0
        })
        self.baseline_established = False
        self.scaler = StandardScaler()
        
    def record_activity(self, user, activity):
        """Record user activity for behavior analysis"""
        profile = self.user_profiles[user]
        
        timestamp = datetime.fromisoformat(activity.get('timestamp', datetime.now().isoformat()))
        
        profile['activities'].append({
            'timestamp': timestamp,
            'type': activity.get('event_type'),
            'process': activity.get('process_name'),
            'file_path': activity.get('file_path'),
            'ip_address': activity.get('ip_address'),
            'device_id': activity.get('device_id')
        })
        
        # Track login times
        if activity.get('event_type') == 'login':
            profile['login_times'].append(timestamp.hour)
        
        # Track file access
        if activity.get('file_path'):
            profile['file_access_patterns'].append({
                'path': activity.get('file_path'),
                'time': timestamp,
                'action': activity.get('event_type')
            })
        
        # Track processes
        if activity.get('process_name'):
            profile['process_patterns'].append({
                'name': activity.get('process_name'),
                'time': timestamp,
                'cpu': activity.get('cpu_usage', 0),
                'memory': activity.get('memory_usage', 0)
            })
    
    def establish_baseline(self, user, days=30):
        """Establish baseline behavior for a user"""
        profile = self.user_profiles[user]
        
        if len(profile['activities']) < 50:
            return {'status': 'insufficient_data', 'required': 50, 'current': len(profile['activities'])}
        
        # Calculate baseline metrics
        baseline = {
            'avg_login_hour': np.mean(profile['login_times']) if profile['login_times'] else 9,
            'std_login_hour': np.std(profile['login_times']) if len(profile['login_times']) > 1 else 2,
            'avg_daily_activities': len(profile['activities']) / max(days, 1),
            'common_processes': self._get_common_items([p['name'] for p in profile['process_patterns']]),
            'common_files': self._get_common_items([f['path'] for f in profile['file_access_patterns']]),
            'typical_devices': list(set(profile['devices']))
        }
        
        profile['baseline'] = baseline
        self.baseline_established = True
        
        return {'status': 'success', 'baseline': baseline}
    
    def _get_common_items(self, items, top_n=10):
        """Get most common items from a list"""
        from collections import Counter
        return [item for item, count in Counter(items).most_common(top_n)]
    
    def analyze_behavior(self, user, current_activity):
        """Analyze current activity against baseline behavior"""
        profile = self.user_profiles[user]
        
        if 'baseline' not in profile:
            self.establish_baseline(user)
            if 'baseline' not in profile:
                return {'risk_level': 'unknown', 'reason': 'Insufficient baseline data'}
        
        baseline = profile['baseline']
        anomalies = []
        risk_score = 0.0
        
        # Check login time anomaly
        current_hour = datetime.fromisoformat(
            current_activity.get('timestamp', datetime.now().isoformat())
        ).hour
        
        if baseline['std_login_hour'] > 0:
            z_score = abs(current_hour - baseline['avg_login_hour']) / baseline['std_login_hour']
            if z_score > 2:
                anomalies.append({
                    'type': 'unusual_login_time',
                    'details': f'Login at hour {current_hour} (typical: {baseline["avg_login_hour"]:.0f})',
                    'severity': 'medium' if z_score < 3 else 'high'
                })
                risk_score += 0.3 if z_score < 3 else 0.5
        
        # Check for unusual process
        current_process = current_activity.get('process_name')
        if current_process and current_process not in baseline['common_processes']:
            anomalies.append({
                'type': 'unusual_process',
                'details': f'Uncommon process: {current_process}',
                'severity': 'low'
            })
            risk_score += 0.1
        
        # Check for unusual file access
        current_file = current_activity.get('file_path')
        if current_file:
            is_sensitive = self._is_sensitive_file(current_file)
            is_unusual = not any(f in current_file for f in baseline['common_files'][:5])
            
            if is_sensitive and is_unusual:
                anomalies.append({
                    'type': 'sensitive_file_access',
                    'details': f'Access to sensitive file: {current_file}',
                    'severity': 'high'
                })
                risk_score += 0.5
        
        # Check for data exfiltration patterns
        if self._check_exfiltration_pattern(profile, current_activity):
            anomalies.append({
                'type': 'potential_exfiltration',
                'details': 'Unusual data transfer pattern detected',
                'severity': 'critical'
            })
            risk_score += 0.8
        
        # Update user risk score
        profile['risk_score'] = min(1.0, profile['risk_score'] * 0.9 + risk_score * 0.1)
        
        risk_level = self._get_risk_level(profile['risk_score'])
        
        return {
            'user': user,
            'risk_level': risk_level,
            'risk_score': profile['risk_score'],
            'anomalies': anomalies,
            'timestamp': datetime.now().isoformat()
        }
    
    def _is_sensitive_file(self, file_path):
        """Check if file path indicates sensitive data"""
        if not file_path:
            return False
        
        sensitive_patterns = [
            'password', 'credential', 'secret', 'private', 'key',
            'confidential', 'financial', 'hr', 'payroll', 'ssn',
            '.pem', '.key', '.pfx', '.p12', 'id_rsa'
        ]
        
        path_lower = file_path.lower()
        return any(pattern in path_lower for pattern in sensitive_patterns)
    
    def _check_exfiltration_pattern(self, profile, current_activity):
        """Detect potential data exfiltration patterns"""
        recent_activities = profile['activities'][-100:]
        
        # Check for mass file access
        file_accesses = [a for a in recent_activities if a.get('file_path')]
        
        if len(file_accesses) > 50:
            # More than 50 file accesses in recent activities
            time_span = (file_accesses[-1]['timestamp'] - file_accesses[0]['timestamp']).total_seconds()
            if time_span < 300:  # 5 minutes
                return True
        
        return False
    
    def _get_risk_level(self, score):
        """Convert risk score to risk level"""
        if score >= 0.8:
            return 'critical'
        elif score >= 0.6:
            return 'high'
        elif score >= 0.4:
            return 'medium'
        elif score >= 0.2:
            return 'low'
        else:
            return 'normal'
    
    def get_high_risk_users(self, threshold=0.5):
        """Get all users with risk score above threshold"""
        high_risk = []
        
        for user, profile in self.user_profiles.items():
            if profile['risk_score'] >= threshold:
                high_risk.append({
                    'user': user,
                    'risk_score': profile['risk_score'],
                    'risk_level': self._get_risk_level(profile['risk_score']),
                    'recent_anomalies': len(profile['activities'][-10:])
                })
        
        return sorted(high_risk, key=lambda x: x['risk_score'], reverse=True)
