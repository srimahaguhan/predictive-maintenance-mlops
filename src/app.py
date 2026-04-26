import os
import time
import joblib
import psutil
import pandas as pd
from fastapi import FastAPI, Request, Response, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Gauge, Histogram, Summary, generate_latest, CONTENT_TYPE_LATEST
from src.utils import load_config

# --- 1. INITIALIZATION & CONFIG ---
config = load_config()
app = FastAPI(title="Maintenance AI Inference Service")
MODEL_PATH = config['paths']['model_path']

# Load the model once at startup
def load_trained_model():
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Model file not found at {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

model = load_trained_model()

# --- 2. DATA VALIDATION (Requirement II.D) ---
class SensorInput(BaseModel):
    air_temp: float
    process_temp: float
    rotational_speed: float
    torque: float
    tool_wear: float
    client_id: str = "unknown_source"  # Custom label source

# --- 3. PROMETHEUS INSTRUMENTATION (Requirement A) ---

# 1. Counter: Total Predictions (with result and client_id labels)
PREDICTION_COUNTER = Counter(
    'api_predictions_total', 
    'Total predictions categorized by result',
    ['result', 'client_id']
)

# 2. Gauge: Memory Usage
MODEL_MEMORY_GAUGE = Gauge(
    'api_model_memory_usage_bytes', 
    'Current memory (RSS) usage of the API process'
)

# 3. Histogram: Inference Latency
INFERENCE_LATENCY = Histogram(
    'api_inference_duration_seconds', 
    'Inference latency in seconds',
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# 4. Summary: Request Payload Size
REQUEST_SUMMARY = Summary(
    'api_request_payload_bytes', 
    'Summary of incoming request payload sizes'
)

# --- 4. ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "healthy", "model_loaded": True}

@app.get("/metrics")
def get_metrics():
    """Endpoint for Prometheus to scrape."""
    # Update Gauge with current memory usage before returning metrics
    MODEL_MEMORY_GAUGE.set(psutil.Process(os.getpid()).memory_info().rss)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/predict")
async def predict(data: SensorInput, request: Request):
    # Track payload size for Summary
    body = await request.body()
    REQUEST_SUMMARY.observe(len(body))
    
    start_time = time.perf_counter()
    
    try:
        # Convert to DataFrame (Matching training feature names)
        input_df = pd.DataFrame([{
            "Air temperature [K]": data.air_temp,
            "Process temperature [K]": data.process_temp,
            "Rotational speed [rpm]": data.rotational_speed,
            "Torque [Nm]": data.torque,
            "Tool wear [min]": data.tool_wear
        }])
        
        # Perform Inference with Latency Tracking
        with INFERENCE_LATENCY.time():
            prediction = int(model.predict(input_df)[0])
            probability = model.predict_proba(input_df)[0].tolist()
        
        result_label = "failure" if prediction == 1 else "success"
        
        # Increment Counter with Custom Labels
        PREDICTION_COUNTER.labels(
            result=result_label, 
            client_id=data.client_id
        ).inc()
        
        return {
            "prediction": "Machine Failure" if prediction == 1 else "Normal",
            "confidence": round(max(probability), 4),
            "inference_time": f"{time.perf_counter() - start_time:.4f}s"
        }
        
    except Exception as e:
        PREDICTION_COUNTER.labels(result="error", client_id=data.client_id).inc()
        raise HTTPException(status_code=500, detail=str(e))