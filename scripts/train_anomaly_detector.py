#!/usr/bin/env python3
"""
FortifAI Anomaly Detector Training
===================================

Trains the anomaly detector by collecting baseline data from YOUR system.
This learns what "normal" looks like for your environment.

Usage:
------
# Quick baseline (2 minutes)
python scripts/train_anomaly_detector.py --quick

# Full baseline (5 minutes - recommended)
python scripts/train_anomaly_detector.py --train

# Extended baseline (15 minutes - most accurate)
python scripts/train_anomaly_detector.py --train --duration 900

# Train inside Docker container
docker cp scripts/train_anomaly_detector.py fortifai-ml:/app/
docker exec fortifai-ml python /app/train_anomaly_detector.py --train
"""

import os
import sys
import json
import time
import argparse
import psutil
import numpy as np
import joblib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# Configuration
OUTPUT_DIR = Path('/app/models/trained') if os.path.exists('/app') else Path(__file__).parent.parent / 'ml-models' / 'anomaly-detection' / 'trained'


class BaselineCollector:
    """Collects baseline data from the system"""
    
    def __init__(self):
        self.samples = []
        self.process_history = defaultdict(list)
        
    def collect_snapshot(self) -> list:
        """Collect current system state"""
        snapshot = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                          'memory_percent', 'num_threads']):
            try:
                info = proc.info
                
                # Get connection count separately
                try:
                    connections = len(proc.net_connections()) if hasattr(proc, 'net_connections') else 0
                except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                    try:
                        connections = len(proc.connections()) if hasattr(proc, 'connections') else 0
                    except:
                        connections = 0
                
                sample = {
                    'timestamp': datetime.now().isoformat(),
                    'pid': info['pid'],
                    'process_name': info['name'] or 'unknown',
                    'user': info['username'] or 'unknown',
                    'cpu_usage': info['cpu_percent'] or 0,
                    'memory_usage': info['memory_percent'] or 0,
                    'num_threads': info['num_threads'] or 1,
                    'connections': connections,
                }
                
                snapshot.append(sample)
                self.process_history[info['name']].append(sample)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        return snapshot
    
    def collect_baseline(self, duration_seconds: int = 300, interval: int = 5) -> list:
        """
        Collect baseline data over time
        
        Args:
            duration_seconds: How long to collect (default 5 minutes)
            interval: Seconds between snapshots (default 5)
        """
        print(f"\n{'='*60}")
        print("COLLECTING BASELINE DATA")
        print(f"{'='*60}")
        print(f"Duration: {duration_seconds} seconds ({duration_seconds//60} min {duration_seconds%60} sec)")
        print(f"Interval: {interval} seconds")
        print(f"\nPlease use your computer normally during collection...")
        print("(Browse web, run programs, do typical work)\n")
        
        start_time = time.time()
        snapshots_collected = 0
        
        while time.time() - start_time < duration_seconds:
            elapsed = int(time.time() - start_time)
            remaining = duration_seconds - elapsed
            
            # Progress bar
            progress = elapsed / duration_seconds
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f"\r[{bar}] {progress*100:.0f}% | {remaining}s remaining | {len(self.samples)} samples", end='')
            
            snapshot = self.collect_snapshot()
            self.samples.extend(snapshot)
            snapshots_collected += 1
            
            time.sleep(interval)
        
        print(f"\n\n✓ Collected {len(self.samples)} samples from {snapshots_collected} snapshots")
        print(f"  Unique processes: {len(self.process_history)}")
        
        return self.samples
    
    def get_statistics(self) -> dict:
        """Calculate baseline statistics"""
        if not self.samples:
            return {}
        
        stats = {
            'total_samples': len(self.samples),
            'unique_processes': len(self.process_history),
            'collection_time': datetime.now().isoformat(),
        }
        
        # Per-process statistics
        process_stats = {}
        for proc_name, samples in self.process_history.items():
            cpu_values = [s['cpu_usage'] for s in samples]
            mem_values = [s['memory_usage'] for s in samples]
            
            process_stats[proc_name] = {
                'count': len(samples),
                'cpu_mean': np.mean(cpu_values),
                'cpu_std': np.std(cpu_values),
                'cpu_max': max(cpu_values),
                'memory_mean': np.mean(mem_values),
                'memory_std': np.std(mem_values),
                'memory_max': max(mem_values),
            }
        
        stats['process_stats'] = process_stats
        
        return stats


def extract_features(sample: dict) -> list:
    """Extract features for anomaly detection"""
    return [
        sample.get('cpu_usage', 0) or 0,
        sample.get('memory_usage', 0) or 0,
        sample.get('num_threads', 1) or 1,
        sample.get('connections', 0) or 0,
        len(sample.get('process_name', '')) or 0,
    ]


def train_anomaly_detector(samples: list, output_dir: Path) -> dict:
    """Train the Isolation Forest model"""
    print(f"\n{'='*60}")
    print("TRAINING ANOMALY DETECTOR")
    print(f"{'='*60}")
    
    if len(samples) < 100:
        print(f"✗ Need at least 100 samples, got {len(samples)}")
        return {'status': 'insufficient_data'}
    
    # Extract features
    print("\nExtracting features...")
    features = np.array([extract_features(s) for s in samples])
    
    feature_names = ['cpu_usage', 'memory_usage', 'num_threads', 'connections', 'name_length']
    
    # Scale features
    print("Scaling features...")
    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    
    # Train Isolation Forest
    print("Training Isolation Forest...")
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,  # Expect 5% anomalies
        max_samples='auto',
        random_state=42,
        n_jobs=-1
    )
    model.fit(features_scaled)
    
    # Calculate baseline statistics
    print("Calculating baseline statistics...")
    baseline_stats = {
        'cpu_mean': float(np.mean(features[:, 0])),
        'cpu_std': float(np.std(features[:, 0])),
        'cpu_p95': float(np.percentile(features[:, 0], 95)),
        'memory_mean': float(np.mean(features[:, 1])),
        'memory_std': float(np.std(features[:, 1])),
        'memory_p95': float(np.percentile(features[:, 1], 95)),
        'threads_mean': float(np.mean(features[:, 2])),
        'connections_mean': float(np.mean(features[:, 3])),
    }
    
    # Test the model on training data
    predictions = model.predict(features_scaled)
    anomaly_ratio = (predictions == -1).sum() / len(predictions)
    print(f"  Training anomaly ratio: {anomaly_ratio:.2%}")
    
    # Save models
    output_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(model, output_dir / 'isolation_forest.joblib')
    joblib.dump(scaler, output_dir / 'anomaly_scaler.joblib')
    
    with open(output_dir / 'baseline_stats.json', 'w') as f:
        json.dump(baseline_stats, f, indent=2)
    
    with open(output_dir / 'feature_names.json', 'w') as f:
        json.dump(feature_names, f)
    
    metadata = {
        'trained_at': datetime.now().isoformat(),
        'samples': len(samples),
        'contamination': 0.05,
        'anomaly_ratio': float(anomaly_ratio),
        'baseline_stats': baseline_stats,
        'feature_names': feature_names,
    }
    with open(output_dir / 'anomaly_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Anomaly detector saved to {output_dir}")
    
    return metadata


def test_anomaly_detector(output_dir: Path):
    """Test the trained anomaly detector"""
    print(f"\n{'='*60}")
    print("TESTING ANOMALY DETECTOR")
    print(f"{'='*60}")
    
    model_file = output_dir / 'isolation_forest.joblib'
    if not model_file.exists():
        print("✗ No trained model found")
        return
    
    model = joblib.load(model_file)
    scaler = joblib.load(output_dir / 'anomaly_scaler.joblib')
    
    with open(output_dir / 'baseline_stats.json') as f:
        baseline = json.load(f)
    
    print(f"\nBaseline Statistics:")
    print(f"  CPU: {baseline['cpu_mean']:.1f}% ± {baseline['cpu_std']:.1f}% (95th: {baseline['cpu_p95']:.1f}%)")
    print(f"  Memory: {baseline['memory_mean']:.1f}% ± {baseline['memory_std']:.1f}%")
    
    # Test with current processes
    print(f"\nTesting with current processes...")
    
    anomalies = []
    normal = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'num_threads']):
        try:
            info = proc.info
            
            try:
                connections = len(proc.net_connections())
            except:
                connections = 0
            
            sample = {
                'process_name': info['name'],
                'cpu_usage': info['cpu_percent'] or 0,
                'memory_usage': info['memory_percent'] or 0,
                'num_threads': info['num_threads'] or 1,
                'connections': connections,
            }
            
            features = np.array([extract_features(sample)])
            features_scaled = scaler.transform(features)
            
            prediction = model.predict(features_scaled)[0]
            score = model.score_samples(features_scaled)[0]
            
            if prediction == -1:
                anomalies.append((info['name'], score, sample))
            else:
                normal.append((info['name'], score))
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    print(f"\nResults:")
    print(f"  Normal processes: {len(normal)}")
    print(f"  Anomalies detected: {len(anomalies)}")
    
    if anomalies:
        print(f"\n⚠️ Anomalous Processes:")
        for name, score, sample in sorted(anomalies, key=lambda x: x[1])[:10]:
            print(f"  {name}: score={score:.3f}, CPU={sample['cpu_usage']:.1f}%, MEM={sample['memory_usage']:.1f}%")
    
    print(f"\n✓ Anomaly detector is working")


def update_ml_engine_to_load_anomaly_model():
    """Update ML engine to load anomaly detector on startup"""
    
    anomaly_detector_code = '''
    def load_trained_model(self, path: str):
        """Load pre-trained anomaly detector"""
        import os
        import joblib
        import json
        
        try:
            self.model = joblib.load(f'{path}/isolation_forest.joblib')
            self.scaler = joblib.load(f'{path}/anomaly_scaler.joblib')
            
            with open(f'{path}/baseline_stats.json', 'r') as f:
                self.baseline_stats = json.load(f)
            
            with open(f'{path}/feature_names.json', 'r') as f:
                self.feature_names = json.load(f)
            
            self.is_trained = True
            print(f"✓ Loaded anomaly detector from {path}")
            return True
        except Exception as e:
            print(f"Could not load anomaly model: {e}")
            return False
'''
    return anomaly_detector_code


def main():
    parser = argparse.ArgumentParser(description='FortifAI Anomaly Detector Training')
    parser.add_argument('--quick', action='store_true', help='Quick baseline (2 minutes)')
    parser.add_argument('--train', action='store_true', help='Full baseline (5 minutes)')
    parser.add_argument('--duration', type=int, default=300, help='Collection duration in seconds')
    parser.add_argument('--interval', type=int, default=5, help='Collection interval in seconds')
    parser.add_argument('--test', action='store_true', help='Test existing model')
    parser.add_argument('--output', type=str, default=str(OUTPUT_DIR), help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    if args.test:
        test_anomaly_detector(output_dir)
        return
    
    if args.quick:
        duration = 120  # 2 minutes
    elif args.train:
        duration = args.duration
    else:
        parser.print_help()
        print(f"\n{'='*60}")
        print("ANOMALY DETECTOR TRAINING")
        print(f"{'='*60}")
        print("""
The anomaly detector learns what's "normal" for YOUR system.
It can then detect unusual behavior that might indicate:
- Zero-day attacks
- Insider threats  
- Unusual resource usage
- Suspicious network activity

Quick Start:
  python train_anomaly_detector.py --quick    # 2 min collection
  python train_anomaly_detector.py --train    # 5 min collection (recommended)
  
During collection, use your computer normally so it learns
your typical patterns (browsing, coding, etc.)
""")
        return
    
    # Collect baseline
    collector = BaselineCollector()
    samples = collector.collect_baseline(duration_seconds=duration, interval=args.interval)
    
    # Get statistics
    stats = collector.get_statistics()
    
    # Train model
    metadata = train_anomaly_detector(samples, output_dir)
    
    # Test
    test_anomaly_detector(output_dir)
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("""
1. Update the anomaly detector to load the model:
   Add load_trained_model() to anomaly_detector.py

2. Or copy to Docker container:
   docker cp ml-models/anomaly-detection/trained/. fortifai-ml:/app/models/anomaly/

3. Restart ML engine:
   docker-compose restart ml-engine
""")


if __name__ == '__main__':
    main()
