# import streamlit as st
# import requests
# import json
# import os

# # Page Config
# st.set_page_config(page_title="AI Predictive Maintenance", page_icon="⚙️")

# st.title(" Industrial Predictive Maintenance")
# st.markdown("---")

# st.sidebar.header("Machine Sensor Input")

# # Create inputs based on your model's features
# air_temp = st.sidebar.slider("Air Temperature [K]", 295.0, 310.0, 300.0)
# process_temp = st.sidebar.slider("Process Temperature [K]", 305.0, 320.0, 310.0)
# speed = st.sidebar.slider("Rotational Speed [rpm]", 1300, 2900, 1500)
# torque = st.sidebar.slider("Torque [Nm]", 3.0, 80.0, 40.0)
# tool_wear = st.sidebar.slider("Tool Wear [min]", 0, 250, 50)

# # The UI Button
# if st.button("Predict Machine Health"):
#     # Prepare the payload for FastAPI
#     payload = {
#         "air_temp": air_temp,
#         "process_temp": process_temp,
#         "rotational_speed": speed,
#         "torque": torque,
#         "tool_wear": tool_wear,
#         "client_id": "streamlit_user_interface"
#     }

#     try:
#         # Note: We use 'api' as the hostname because they are in the same Docker network
#         API_URL = os.getenv("API_URL", "http://localhost:8000")
#         response = requests.post(f"{API_URL}/predict", json=payload)
#         # response = requests.post("http://api:8000/predict", json=payload)
#         result = response.json()

#         st.subheader("Result:")
#         if result["prediction"] == "Machine Failure":
#             st.error(f" Warning: {result['prediction']}")
#         else:
#             st.success(f" Status: {result['prediction']}")

#         # Show metrics
#         col1, col2 = st.columns(2)
#         col1.metric("Confidence", f"{result['confidence']*100:.2f}%")
#         col2.metric("Inference Time", result['inference_time'])

#     except Exception as e:
#         st.error(f"Connection to API failed: {e}")

import streamlit as st
import requests
import pandas as pd
import os
import json

# --- Configuration ---
# Use 'api' for Docker networking, fallback to 'localhost' for local Mac terminal
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
PREDICT_URL = f"{API_BASE_URL}/predict"

st.set_page_config(page_title="MLOps Predictive Maintenance", page_icon="⚙️", layout="wide")

# --- UI Header ---
st.title(" Industrial Predictive Maintenance System")
st.markdown("""
This system uses a Random Forest model to predict potential machine failures based on real-time sensor data.
Select an input method below to get started.
""")
st.divider()

# --- Input Methods ---
tab1, tab2 = st.tabs([" Single Machine Prediction", " Batch CSV Upload"])

# --- TAB 1: Manual Input (Sliders) ---
with tab1:
    st.header("Manual Sensor Input")
    st.info("Adjust the sliders to represent the current state of a specific machine.")
    
    # Organize sliders into columns for better look
    col1, col2, col3 = st.columns(3)
    
    with col1:
        air_temp = st.slider("Air Temperature [K]", 295.0, 310.0, 300.0, step=0.1)
        process_temp = st.slider("Process Temperature [K]", 305.0, 320.0, 310.0, step=0.1)
    
    with col2:
        rot_speed = st.slider("Rotational Speed [rpm]", 1300, 3000, 1500)
        torque = st.slider("Torque [Nm]", 3.0, 80.0, 40.0, step=0.5)
        
    with col3:
        tool_wear = st.slider("Tool Wear [min]", 0, 250, 50)
        client_id = st.text_input("Operator Name/ID", value="Shift_Manager_01")

    if st.button("Predict Machine Health", type="primary"):
        payload = {
            "air_temp": air_temp,
            "process_temp": process_temp,
            "rotational_speed": rot_speed,
            "torque": torque,
            "tool_wear": tool_wear,
            "client_id": client_id
        }
        
        try:
            with st.spinner('Querying Inference API...'):
                response = requests.post(PREDICT_URL, json=payload)
                response.raise_for_status()
                result = response.json()
            
            st.divider()
            
            # Display Result with dynamic styling
            if result["prediction"] == "Machine Failure":
                st.error(f"###  Status: {result['prediction']}")
            else:
                st.success(f"###  Status: {result['prediction']}")
            
            # Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("Confidence Score", f"{result.get('confidence', 0)*100:.2f}%")
            m2.metric("Inference Time", result.get('inference_time', 'N/A'))
            m3.metric("Model Version", "RF-v1.0")
            
        except Exception as e:
            st.error(f"Failed to connect to API at {PREDICT_URL}. Error: {e}")

# --- TAB 2: Batch Upload (CSV) ---
with tab2:
    st.header("Bulk Sensor Data Analysis")
    st.markdown("Upload a CSV file containing columns for `air_temp`, `process_temp`, `rotational_speed`, `torque`, and `tool_wear`.")
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Read the file
        df = pd.read_csv(uploaded_file)
        
        st.subheader("Preview of Uploaded Data")
        st.dataframe(df.head(10), use_container_width=True)
        
        if st.button("Analyze Entire Fleet"):
            predictions = []
            progress_bar = st.progress(0)
            
            try:
                # Iterate through rows and call API for each (simulating a batch)
                for index, row in df.iterrows():
                    payload = {
                        "air_temp": row['air_temp'],
                        "process_temp": row['process_temp'],
                        "rotational_speed": row['rotational_speed'],
                        "torque": row['torque'],
                        "tool_wear": row['tool_wear'],
                        "client_id": "batch_upload_ui"
                    }
                    resp = requests.post(PREDICT_URL, json=payload)
                    predictions.append(resp.json()["prediction"])
                    
                    # Update progress
                    progress_bar.progress((index + 1) / len(df))
                
                # Add results to dataframe
                df['Prediction_Result'] = predictions
                
                st.divider()
                st.subheader("Fleet Health Summary")
                
                # Display Summary Chart
                status_counts = df['Prediction_Result'].value_counts()
                st.bar_chart(status_counts)
                
                # Display Results Table
                st.dataframe(df, use_container_width=True)
                
                # Option to download results
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Predictions CSV", data=csv, file_name="machine_predictions.csv", mime="text/csv")

            except Exception as e:
                st.error(f"Batch processing failed: {e}")

# --- Sidebar Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("Predictive Maintenance MLOps Project")
st.sidebar.caption(f"API Target: `{PREDICT_URL}`")