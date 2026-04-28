# Predictive Maintenance MLOps System
**Student Name:** Sri Mahaguhan S  
**Academic Roll Number:** DA25S021  


---

## 1. System Architecture
The system is built as a containerized microservices architecture to ensure scalability, observability, and reproducibility across the machine learning lifecycle.

### Block Explanation:
* **Data Orchestration (Airflow & DVC):** Apache Airflow manages the end-to-end workflow (ETL to Training). DVC ensures data versioning, tracking approximately 2GB of scientific metadata and raw sensor logs.
* **Experiment Tracking (MLflow):** Every training run is logged with hyperparameters and metrics, providing a historical record of model evolution and artifact storage.
* **Model Serving (FastAPI):** A high-performance REST API that exposes the Random Forest model for real-time inference using a production-ready Uvicorn server.
* **User Interface (Streamlit):** A non-technical dashboard allowing operators to input sensor data manually or via bulk CSV upload for fleet-wide analysis.
* **Observability Stack (Prometheus & Grafana):** Prometheus scrapes system and application metrics (via Pushgateway). Grafana provides a real-time visual dashboard for model performance and system health.
* **Alerting (AlertManager):** Automatically triggers email notifications (via SMTP/Mailtrap) if model accuracy drops or infrastructure hits critical thresholds (e.g., High CPU usage).

---

## 2. High-Level Design (HLD)
### Design Rationale:
* **Algorithm Choice:** Random Forest was selected for its robustness against industrial sensor noise and its high interpretability via feature importance, which is critical for maintenance engineers.
* **Modular Pipeline:** By separating ingestion, preprocessing, and training into discrete scripts, the system allows for targeted updates (e.g., swapping the model without touching the ETL logic).
* **Observability-First Design:** Unlike standard ML projects, this system treats monitoring as a core component. The integration of Prometheus ensures that model drift and system latency are detected in real-time.

---

## 3. Low-Level Design (LLD)
### Endpoint Specifications (`FastAPI`)
* **POST `/predict`**
    * **Description:** Receives sensor data and returns machine health prediction.
    * **Input (JSON):**
        ```json
        {
          "air_temp": 300.5,
          "process_temp": 310.2,
          "rotational_speed": 1500,
          "torque": 40.5,
          "tool_wear": 50,
          "client_id": "operator_01"
        }
        ```
    * **Output (JSON):**
        ```json
        {
          "prediction": "No Failure",
          "confidence": 0.9825,
          "inference_time": "0.004s",
          "timestamp": "2026-04-28T..."
        }
        ```

### Environment Configuration
* `MLFLOW_TRACKING_URI`: `http://mlflow:5000`
* `PUSHGATEWAY_URL`: `http://pushgateway:9091`
* `API_URL`: `http://api:8000`

---

## 4. Test Plan & Test Cases
### Test Phase 1: Integration Testing
* **TC-01:** Verify `train.py` successfully pushes metrics to Pushgateway.
* **TC-02:** Ensure FastAPI returns the correct prediction class when given high-stress sensor inputs (e.g., Torque > 60Nm).

### Test Phase 2: Stress & Alerting
* **TC-03 (High CPU Alert):** Simulate high load during model training.
    * *Success Criteria:* AlertManager sends an email to the configured recipient via Mailtrap.
* **TC-04 (DVC Reproduction):** Run `dvc repro`.
    * *Success Criteria:* All stages execute in order and `reports/confusion_matrix.csv` is updated.

---

## 5. User Manual
### For Non-Technical Operators:
1.  **Launch the System:** Run `docker compose up -d`.
2.  **Access the UI:** Open your browser and navigate to `http://localhost:8501`.
3.  **Predict Individual Machine:** * Navigate to the **"Manual Prediction"** tab.
    * Adjust the sliders to match the machine's current sensor readings.
    * Click **"Predict Machine Health"**.
4.  **Bulk Analysis:**
    * Navigate to the **"Batch CSV Upload"** tab.
    * Upload your factory sensor log (CSV).
    * Click **"Analyze Fleet"** to view a summary of machine health across the entire plant.

---

## 6. Model Performance Metrics
The following metrics were obtained from the latest `random_forest_model` training run:

| Metric | Value |
| :--- | :--- |
| **Accuracy** | 0.9825 |
| **F1 Macro** | 0.8222 |
| **Precision Macro** | 0.9054 |
| **Recall Macro** | 0.7687 |
| **F1 Micro** | 0.9825 |

---

## 7. Tech Stack Used
* **Languages:** Python 3.12, C++, LaTeX
* **ML Frameworks:** Scikit-Learn, MLflow
* **Ops Tools:** Apache Airflow, DVC, Docker, Docker-Compose
* **Web/UI:** FastAPI, Streamlit
* **Monitoring:** Prometheus, Grafana, AlertManager, Node Exporter, Pushgateway

---

## 8. Directory Structure
```text
predictive-maintenance-mlops/
├── airflow.cfg             # Airflow configuration
├── config/                 # Monitoring and System Configs
│   ├── alert_rules.yml     # Prometheus alerting thresholds
│   ├── alertmanager.yml    # Alert routing (Email/SMTP)
│   ├── baseline_stats.yaml # Reference stats for model drift
│   ├── config.yaml         # Main project paths and hyperparameters
│   └── prometheus.yml      # Scrape configurations
├── dags/                   # Airflow DAG Definitions
│   └── ingestion_dag.py    # Main MLOps pipeline DAG
├── data/                   # Data storage (Tracked by DVC)
├── docker/                 # Service Dockerfiles
│   └── ui.Dockerfile       # Streamlit UI build instructions
├── docker-compose.yml      # Multi-container orchestration
├── dvc.lock                # DVC state lock
├── dvc.yaml                # DVC pipeline stages (ETL -> Train)
├── dvc_plots/              # Visualization artifacts from DVC
├── logs/                   # System and Airflow logs
├── mlruns/                 # MLflow experiment tracking data
├── models/                 # Saved model artifacts (.pkl)
├── reports/                # Evaluation reports (metrics, confusion matrix)
├── requirements.txt        # Backend dependencies
├── src/                    # Source Code
│   ├── app.py              # FastAPI inference service
│   ├── ingestion.py        # Data ingestion logic
│   ├── preprocessing.py    # Feature engineering logic
│   ├── streamlit_app.py    # User interface script
│   ├── train.py            # Model training & tracking script
│   └── utils.py            # Common helper functions
└── ui_requirements.txt     # Frontend-specific dependencies

## 9. Testing & Continuous Integration (CI)
```text 
This project implements a containerized testing strategy to ensure **Environment Parity** and **Inference Integrity**. Instead of testing on the host machine (macOS), all validations are performed within the production-grade Linux environment of the Docker container.

---

## The "CI Gate" Command

To verify the application health and model logic, execute the following command:

```bash
docker exec -it predictive-maintenance-mlops-api-1 pytest tests/test_api.py
```

---

## What is Being Verified?

### 1. API Health (`/health`)
Confirms the FastAPI server is live and networking is routed correctly.

### 2. Model Readiness (`/ready`)
Verifies that the `.pkl` model artifact is successfully loaded into memory.

### 3. Inference Logic (`/predict`)
Simulates a real-world sensor payload to ensure the preprocessing pipeline and model decision boundaries are functioning as expected.