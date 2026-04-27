import os
import yaml
import socket
import joblib
import json
import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from sklearn.metrics import (
    f1_score, 
    confusion_matrix, 
    accuracy_score, 
    precision_recall_fscore_support
)
from src.utils import load_config

def push_metrics_to_prometheus(metrics_dict):
    """
    Pushes calculated metrics to the Prometheus Pushgateway.
    This allows Prometheus to 'scrape' batch job results.
    """
    registry = CollectorRegistry()
    
    # We create Gauges for our primary metrics. 
    # Using 'training_' prefix helps organize them in Grafana later.
    for metric_name, value in metrics_dict.items():
        # Clean name for Prometheus (replaces spaces with underscores)
        clean_name = f"training_{metric_name.replace(' ', '_')}"
        g = Gauge(clean_name, f'{metric_name} from latest training run', registry=registry)
        g.set(value)
    
    try:
        # 'pushgateway:9091' is the internal Docker service name defined in compose
        push_to_gateway('http://pushgateway:9091', job='predictive_maintenance_training', registry=registry)
        print(" Metrics successfully pushed to Prometheus Pushgateway!")
    except Exception as e:
        print(f" Failed to push metrics to Prometheus: {e}")

def train():
    config = load_config()

    # --- Robust Networking Block ---
    # We pop proxies to ensure the container talks directly to internal services.
    for env_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        os.environ.pop(env_var, None)
    
    # CRITICAL: Added 'pushgateway' to NO_PROXY so requests don't loop back
    os.environ['NO_PROXY'] = 'mlflow,pushgateway,localhost,127.0.0.1'

    try:
        # Resolving service name to IP bypasses the 'Invalid Host header' security check
        mlflow_ip = socket.gethostbyname('mlflow')
        tracking_uri = f"http://{mlflow_ip}:5000"
    except Exception as e:
        print(f" DNS Resolution failed, falling back to config: {e}")
        tracking_uri = config['mlflow']['tracking_uri']

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(config['mlflow']['experiment_name'])

    # --- Data Preparation ---
    processed_path = config['paths']['processed_data']
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Processed data missing at {processed_path}. Run ETL first.")
    
    df = pd.read_csv(processed_path)
    X = df[config['preprocessing']['features']]
    y = df[df.columns[df.columns.isin([config['preprocessing']['target']])]] # Robust column selection
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config['training'].get('test_size', 0.2), 
        random_state=config['training'].get('random_state', 42)
    )

    # --- MLflow Run with Enhanced Metrics ---
    with mlflow.start_run(run_name="Random_Forest_Enhanced_Metrics"):
        params = {
            "n_estimators": 100, 
            "max_depth": 10, 
            "random_state": 42
        }
        mlflow.log_params(params)

        # Training the classifier
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train.values.ravel())

        # 1. Prediction & Comprehensive Metric Calculation
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        
        # Calculate Macro (treats classes equally) and Micro (weighted)
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
        p_micro, r_micro, f1_micro, _ = precision_recall_fscore_support(y_test, y_pred, average='micro')
        
        cm = confusion_matrix(y_test, y_pred)

        # 2. Package Metrics
        metrics = {
            "accuracy": acc,
            "f1_macro": f1_macro,
            "f1_micro": f1_micro,
            "precision_macro": p_macro,
            "recall_macro": r_macro
        }

        # 3. Push to Prometheus & Log to MLflow
        push_metrics_to_prometheus(metrics)
        mlflow.log_metrics(metrics)

        # 4. Save Local Artifacts for DVC Tracking
        os.makedirs('reports', exist_ok=True)
        with open('reports/metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)
            
        cm_df = pd.DataFrame(cm)
        cm_df.to_csv('reports/confusion_matrix.csv', index=False)

        # 5. Save Model Artifacts
        os.makedirs('models', exist_ok=True)
        model_output_path = config['paths']['model_path']
        joblib.dump(model, model_output_path)
        
        # Register the model
        mlflow.sklearn.log_model(model, "random_forest_model")

    print(f" Training Complete with Enhanced Metrics!")
    print(f" F1 Macro: {f1_macro:.4f} | Accuracy: {acc:.4f}")

if __name__ == "__main__":
    train()