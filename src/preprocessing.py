import os
import yaml
import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from src.utils import load_config

def preprocess():
    config = load_config()
    raw_path = config['paths']['raw_data']
    processed_path = config['paths']['processed_data']
    # Ensure these paths are in your config.yaml
    scaler_path = config['paths'].get('scaling_params', 'data/processed/scaling_params.joblib')
    baseline_path = config['paths'].get('baseline_stats', 'config/baseline_stats.yaml')
    
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data missing at {raw_path}")
    
    df = pd.read_csv(raw_path)
    
    # 1. Drop identifiers
    df = df.drop(columns=['UDI', 'Product ID'], errors='ignore')
    
    # 2. Feature Scaling (The "Math" bit)
    # We use: $$z = \frac{x - \mu}{\sigma}$$
    features = config['preprocessing']['features']
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])
    
    # 3. Save the Scaler (CRITICAL: DVC is waiting for this!)
    os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
    joblib.dump(scaler, scaler_path)
    
    # 4. Save Baselines for Monitoring
    baseline_stats = {}
    for i, col in enumerate(features):
        baseline_stats[col] = {
            "mean": float(scaler.mean_[i]),
            "std": float(scaler.scale_[i])
        }
    
    os.makedirs(os.path.dirname(baseline_path), exist_ok=True)
    with open(baseline_path, 'w') as f:
        yaml.dump(baseline_stats, f)
    
    # 5. Save Processed Data
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    
    print(f"✅ Scaler saved to {scaler_path}")
    print(f"✅ Processed data saved to {processed_path}")
    print(f"✅ Baselines stored in {baseline_path}")

if __name__ == "__main__":
    preprocess()