# Test Plan & Test Cases

---

## 1. Introduction & Objectives

The objective of this test plan is to ensure the **functional correctness**, **performance reliability**, and **system stability** of the machine failure prediction service. We follow a **"Shift-Left"** testing approach where validation occurs within the containerized production environment.

---

## 2. Test Environment

| Component | Details |
| :--- | :--- |
| **Platform** | Linux (Debian-based Docker Container) |
| **API Framework** | FastAPI |
| **Model** | Random Forest Classifier (Scikit-Learn 1.8.0) |
| **Tooling** | Pytest, HTTPX, Prometheus *(for stress monitoring)* |

---

## 3. Acceptance Criteria (AC)

For the software to be considered **"Ready for Production"**, it must meet all of the following:

| ID | Criterion |
| :--- | :--- |
| **AC-1** | 100% pass rate on core API health and readiness probes. |
| **AC-2** | Average inference latency must be `<200ms` under normal load. |
| **AC-3** | System must reject malformed JSON inputs with a `422 Unprocessable Entity` error. |
| **AC-4** | Accuracy on the test validation set must exceed **70%**. |

---

## 4. Detailed Test Cases

| Test ID | Title | Priority | Input / Action | Expected Result |
| :--- | :--- | :--- | :--- | :--- |
| **TS-01** | Liveness Probe |  High | `GET /health` | Status `200`; Response: `{"status": "healthy"}` |
| **TS-02** | Readiness Probe |  High | `GET /ready` | Status `200`; Response: `{"status": "ready"}` |
| **TS-03** | Valid Prediction |  High | Valid JSON with sensor data *(Temps, Torque)* | Status `200`; Prediction string returned. |
| **TS-04** | Data Validation |  Medium | Sending `"string"` instead of `"float"` for `torque` | Status `422`; Specific error message for data type. |
| **TS-05** | Extreme Values |  Medium | `air_temp = 1000K` *(Physical impossibility)* | System processes without crashing; flags as outlier/failure. |
| **TS-06** | Missing Features |  High | JSON payload missing the `tool_wear` key | Status `422`; Validation error highlighting missing field. |
| **TS-07** | Stress Test | Low | 100 requests in `<2s` | P95 Latency remains below `500ms`. |

---

---

# 📖 User Manual (Non-Technical Operator)

---

## 1. Overview

Welcome to the **Predictive Maintenance Hub**. This application is designed for factory floor managers and maintenance engineers. It uses Artificial Intelligence to analyze sensor data from your machinery and alert you **before a breakdown occurs**, saving costs and preventing downtime.

---

## 2. Accessing the Application

1. Ensure the system is started by your IT department.
2. Open your web browser *(Chrome or Edge recommended)*.
3. Navigate to the internal URL:

```
http://localhost:8501
```

---

## 3. Understanding the Dashboard

The screen is divided into three main sections:

| Section | Location | Purpose |
| :--- | :--- | :--- |
| **Input Panel** | Left | Enter current readings from your machine's sensors. |
| **Prediction Zone** | Center | Displays the AI's analysis in real-time. |
| **Alert Logs** | Bottom | History of recent predictions and any high-risk alerts. |

---

## 4. How to Predict a Failure (Step-by-Step)

**Step 1 — Enter Sensor Data**
Adjust the sliders for the following based on your machine's display:
- Air Temperature
- Process Temperature
- Rotational Speed
- Torque
- Tool Wear

**Step 2 — Run Analysis**
Click the large **"Check Machine Health"** button.

**Step 3 — Read the Result**

| Result | Meaning | Action |
| :--- | :--- | :--- |
|  **"No Failure"** | Machine is operating within safe parameters. | No action needed. |
|  **"Failure Detected"** | AI has found a pattern matching a known fault. | Notify maintenance immediately. |

**Step 4 — Identify the Type**
If a failure is detected, the app will specify the failure type (e.g., `"Heat Dissipation"` or `"Power Failure"`). Pass this specific information to your maintenance team.

---

## 5. Troubleshooting Common Issues

| Error | Likely Cause | Resolution |
| :--- | :--- | :--- |
| **"Connection Error"** | Background intelligence service is offline. | Contact IT to restart the *"API Container."* |
| **"Invalid Input"** | Slider values are outside the normal operating range. | Correct the highlighted fields and retry. |
| **"Stale Data"** | Dashboard has not updated recently. | Refresh the page using your browser's refresh button. |

---

## 6.  Safety Notice

> While the AI provides highly accurate predictions, it is an **assistant tool**.
>
> Always follow **standard factory safety protocols** and conduct **physical inspections** if you notice unusual noise or vibrations from the machinery — regardless of the application's output.