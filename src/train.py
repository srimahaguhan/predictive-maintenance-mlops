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
    registry = CollectorRegistry()
    for metric_name, value in metrics_dict.items():
        clean_name = f"training_{metric_name.replace(' ', '_')}"
        g = Gauge(clean_name, f'{metric_name} from latest training run', registry=registry)
        g.set(value)
    
    gateway_url = os.getenv('PUSHGATEWAY_URL', 'http://localhost:9091')
    try:
        push_to_gateway(gateway_url, job='predictive_maintenance_training', registry=registry)
        print(f" Metrics successfully pushed to Pushgateway at: {gateway_url}")
    except Exception as e:
        print(f" Failed to push metrics to Prometheus at {gateway_url}: {e}")

def train():
    config = load_config()

    # --- Networking Setup ---
    for env_var in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        os.environ.pop(env_var, None)
    os.environ['NO_PROXY'] = 'mlflow,pushgateway,localhost,127.0.0.1'

    tracking_uri = os.getenv('MLFLOW_TRACKING_URI')
    if not tracking_uri:
        try:
            mlflow_ip = socket.gethostbyname('mlflow')
            tracking_uri = f"http://{mlflow_ip}:5000"
        except Exception:
            tracking_uri = config['mlflow']['tracking_uri']

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(config['mlflow']['experiment_name'])

    # --- Data Preparation ---
    processed_path = config['paths']['processed_data']
    df = pd.read_csv(processed_path)
    X = df[config['preprocessing']['features']]
    y = df[df.columns[df.columns.isin([config['preprocessing']['target']])]]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config['training'].get('test_size', 0.2), 
        random_state=config['training'].get('random_state', 42)
    )

    # --- MLflow Run ---
    with mlflow.start_run(run_name="Random_Forest_Training_Run"):
        training_config = config.get('training', {})
        model_params = {
            "n_estimators": training_config.get("n_estimators", 100),
            "max_depth": training_config.get("max_depth", 10),
            "random_state": training_config.get("random_state", 42)
        }
        mlflow.log_params(model_params)

        model = RandomForestClassifier(**model_params)
        model.fit(X_train, y_train.values.ravel())

        y_pred = model.predict(X_test)
        
        # 1. Metric Calculation
        acc = accuracy_score(y_test, y_pred)
        p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')
        
        # 2. Confusion Matrix (CRITICAL FOR DVC)
        # cm = confusion_matrix(y_test, y_pred)
        
        metrics = {
            "accuracy": acc,
            "f1_macro": f1_macro,
            "precision_macro": p_macro,
            "recall_macro": r_macro
        }

        # 3. Log/Push Data
        mlflow.log_metrics(metrics)
        push_metrics_to_prometheus(metrics)

        # 4. Saving Artifacts (DVC expects these exact paths)
        os.makedirs('reports', exist_ok=True)
        with open('reports/metrics.json', 'w') as f:
            json.dump(metrics, f, indent=4)
            
        # Re-adding the missing confusion matrix file
        # cm_df = pd.DataFrame(cm)
        # cm_df.to_csv('reports/confusion_matrix.csv', index=False)

        df_plot = pd.DataFrame({
            'actual': y_test.values.ravel(),
            'predicted': y_pred
        })
        df_plot.to_csv('reports/confusion_matrix.csv', index=False)
            
        os.makedirs('models', exist_ok=True)
        joblib.dump(model, config['paths']['model_path'])
        
        mlflow.sklearn.log_model(model, "random_forest_model")

    print(f" Training Complete! F1 Macro: {f1_macro:.4f} | Accuracy: {acc:.4f}")

if __name__ == "__main__":
    train()