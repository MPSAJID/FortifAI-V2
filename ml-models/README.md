# ML Models

This directory contains pre-trained and custom machine learning models for FortifAI.

## Directory Structure

- `anomaly-detection/` - Anomaly detection models (Isolation Forest, Autoencoders)
- `threat-classification/` - Threat classification models (Random Forest, Deep Learning)
- `behavior-analysis/` - User behavior analytics models

## Model Formats

- `.joblib` - Scikit-learn models
- `.h5` / `.keras` - TensorFlow/Keras models
- `.json` - Model metadata and configurations

## Usage

Models are loaded by the ML Engine service at startup. To update models:

1. Train new model using training scripts
2. Save to appropriate directory
3. Restart ML Engine service

## Training

See `scripts/train_models.py` for training pipelines.
