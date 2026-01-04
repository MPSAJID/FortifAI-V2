#!/usr/bin/env python3
"""
FortifAI Model Training Script
Trains all ML models with sample or provided data
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime
import joblib

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.ml_engine.threat_classifier import ThreatClassifier
from backend.ml_engine.anomaly_detector import AnomalyDetector

def generate_sample_data(n_samples=1000):
    """Generate sample training data"""
    np.random.seed(42)
    
    data = []
    labels = []
    
    threat_types = ['normal', 'malware', 'ransomware', 'brute_force', 'data_exfiltration']
    
    for _ in range(n_samples):
        threat_type = np.random.choice(threat_types, p=[0.7, 0.1, 0.05, 0.1, 0.05])
        
        if threat_type == 'normal':
            cpu = np.random.normal(30, 15)
            memory = np.random.normal(40, 20)
            connections = np.random.poisson(10)
        elif threat_type == 'malware':
            cpu = np.random.normal(70, 20)
            memory = np.random.normal(60, 25)
            connections = np.random.poisson(50)
        elif threat_type == 'ransomware':
            cpu = np.random.normal(80, 15)
            memory = np.random.normal(70, 20)
            connections = np.random.poisson(5)
        elif threat_type == 'brute_force':
            cpu = np.random.normal(40, 20)
            memory = np.random.normal(30, 15)
            connections = np.random.poisson(200)
        else:  # data_exfiltration
            cpu = np.random.normal(50, 20)
            memory = np.random.normal(50, 20)
            connections = np.random.poisson(100)
        
        data.append({
            'cpu_usage': max(0, min(100, cpu)),
            'memory_usage': max(0, min(100, memory)),
            'connection_count': max(0, connections),
            'process_count': np.random.poisson(20),
            'file_access_count': np.random.poisson(50),
            'timestamp': datetime.now().isoformat()
        })
        labels.append(threat_type)
    
    return data, labels

def train_threat_classifier(data, labels, output_dir):
    """Train threat classifier"""
    print("Training Threat Classifier...")
    
    classifier = ThreatClassifier()
    result = classifier.train(data, labels)
    
    print(f"Training result: {result}")
    
    # Save models
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(classifier.rf_model, os.path.join(output_dir, 'random_forest.joblib'))
    joblib.dump(classifier.gb_model, os.path.join(output_dir, 'gradient_boosting.joblib'))
    joblib.dump(classifier.scaler, os.path.join(output_dir, 'scaler.joblib'))
    joblib.dump(classifier.label_encoder, os.path.join(output_dir, 'label_encoder.joblib'))
    
    print(f"Models saved to {output_dir}")

def train_anomaly_detector(data, output_dir):
    """Train anomaly detector"""
    print("Training Anomaly Detector...")
    
    detector = AnomalyDetector()
    result = detector.fit(data)
    
    print(f"Training result: {result}")
    
    # Save model
    os.makedirs(output_dir, exist_ok=True)
    joblib.dump(detector.model, os.path.join(output_dir, 'isolation_forest.joblib'))
    joblib.dump(detector.scaler, os.path.join(output_dir, 'scaler.joblib'))
    
    # Save baseline stats
    with open(os.path.join(output_dir, 'baseline_stats.json'), 'w') as f:
        stats = {k: v.tolist() for k, v in detector.baseline_stats.items()}
        json.dump(stats, f)
    
    print(f"Model saved to {output_dir}")

def main():
    """Main training function"""
    print("=" * 50)
    print("FortifAI Model Training")
    print("=" * 50)
    
    # Generate sample data
    print("\nGenerating sample training data...")
    data, labels = generate_sample_data(n_samples=1000)
    print(f"Generated {len(data)} samples")
    
    # Output directories
    threat_dir = os.path.join('ml-models', 'threat-classification')
    anomaly_dir = os.path.join('ml-models', 'anomaly-detection')
    
    # Train models
    train_threat_classifier(data, labels, threat_dir)
    train_anomaly_detector(data, anomaly_dir)
    
    print("\n" + "=" * 50)
    print("Training Complete!")
    print("=" * 50)

if __name__ == '__main__':
    main()
