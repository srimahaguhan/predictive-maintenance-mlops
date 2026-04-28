# Appendix: AI Usage & Disclosure Statement

This appendix details the extent to which Artificial Intelligence was utilized during the development of the **Predictive Maintenance MLOps System**, ensuring full transparency and adherence to the evaluation guidelines of the **IIT Madras Master's program**.

---

## 1. AI-Assisted Components *(Drafting & Boilerplate)*

In accordance with the permitted use of AI for non-core logic and documentation drafting, **Gemini 3 Flash** provided assistance in the following areas:

| Area | Description |
| :--- | :--- |
| **Documentation Synthesis** | AI was utilized to draft the initial structures for the HLD, LLD, and User Manual, which were then refined and validated against the actual project implementation. |
| **Boilerplate UI/UX** | The basic layout for the Streamlit dashboard and the skeleton for the FastAPI endpoints (including `/health` and `/ready`) were generated with AI assistance. |
| **Infrastructure Troubleshooting** | AI assisted in diagnosing Docker build timeouts related to bandwidth constraints, suggesting specific configurations for `--default-timeout` and layer caching strategies. |
| **Testing Framework** | The initial template for the Pytest suite in `tests/test_api.py` was drafted to ensure alignment with the API's Pydantic schemas. |

---

## 2. Student-Authored Components *(Core MLOps Orchestration)*

The following elements represent the core technical **"heavy lifting"** and were authored, configured, and integrated **entirely by the student**:

| Component | Description |
| :--- | :--- |
| **Architecture Ownership** | Design of the Multi-Container Microservice Architecture, including the networking between the API, Prometheus, and Grafana. |
| **Data Pipeline Orchestration** | Implementation of the Apache Airflow DAG and DVC (Data Version Control) pipeline, ensuring that data ingestion and preprocessing follow a reproducible workflow. |
| **Observability Instrumentation** | Manual configuration of Prometheus metrics *(e.g., custom counters for inference results)* and the creation of Grafana dashboards to monitor system health in Near-Real-Time (NRT). |
| **Alerting Logic** | Design of `alert_rules.yml`, including the logic for triggering notifications when error rates exceed 5% or when Data Drift is detected. |
| **Model Integration** | Custom logic for loading the Random Forest model and the feature engineering pipeline within `src/train.py` and `src/app.py`. |

---

## 3. Technical Mastery & Problem Solving

To maintain academic integrity and demonstrate mastery over the MLOps stack, the following challenges were independently resolved:

- **Docker Optimization** — Resolved complex build-context issues where the `tests/` folder was initially missing from the container, necessitating a deep understanding of Docker's immutable image structure and build context.

- **CI/CD Implementation** — Conceptually designed and executed the **"CI Gate"** by running `pytest` directly inside a running Linux-based Docker container via `docker exec`, verifying Environment Parity.

- **Environment Debugging** — Manually identified and resolved pathing mismatches *(e.g., `src/` vs root)* within the Dockerfiles to ensure correct service startup.

---

## 4. Integrity & Attribution

> All engineering decisions and final implementations remain the **sole responsibility of the student**.

| Principle | Statement |
| :--- | :--- |
| **Authenticity of Results** | All metrics logged in MLflow, visualizations in Grafana, and test results in Pytest are the direct result of executing the code on local hardware. No logs or performance metrics were fabricated using AI. |
| **Documentation Consistency** | The HLD, LLD, and Architecture diagrams are accurate reflections of the physical code structure submitted in the repository. |
| **Tool Usage** | AI was used as a collaborative assistant for speed and documentation quality, while all engineering decisions and final implementations remain the sole responsibility of the student. |