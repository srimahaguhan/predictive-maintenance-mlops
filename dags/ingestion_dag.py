import os
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.bash import BashOperator

# Custom imports
from src.utils import load_config
from src.ingestion import ingest

# 1. LOAD CONFIGURATION
config = load_config()
RECIPIENT_EMAIL = config['notifications']['recipient_email']

# 2. CUSTOM ALERTING LOGIC (Using smtplib to fix protocol mismatches)
def send_custom_email(subject, html_content):
    """Internal helper to manage the STARTTLS handshake explicitly."""
    msg = MIMEMultipart()
    msg['From'] = "sg637@snu.edu.in"
    msg['To'] = RECIPIENT_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # Use port 2525 and explicit starttls to stop the SSL Version error
        with smtplib.SMTP('sandbox.smtp.mailtrap.io', 2525, timeout=30) as server:
            server.starttls() 
            server.login('b35b64f2f5b4d0', '2b09e6331ce5e4')
            server.send_message(msg)
        print("Successfully sent email alert via smtplib.")
    except Exception as e:
        print(f"Failed to send email alert: {e}")

def notify_ingestion_failure(context):
    """Callback for ingestion failure with HTML formatting."""
    dag_id = context['dag'].dag_id
    task_id = context['task_instance'].task_id
    error_msg = context.get('exception')
    log_url = context.get('task_instance').log_url
    
    subject = f" Ingestion Failed: {dag_id}"
    body = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #ff4d4d; padding: 20px; border-radius: 5px;">
        <h2 style="color: #d9534f;"> Ingestion Failure Detected</h2>
        <p>The automated data ingestion task has failed.</p>
        <hr>
        <p><b>Task ID:</b> {task_id}</p>
        <p><b>Error:</b> <pre style="background:#eee;padding:10px;">{error_msg}</pre></p>
        <p><a href="{log_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Logs</a></p>
    </div>
    """
    send_custom_email(subject, body)

def notify_dry_pipeline(context):
    """Callback for DVC/Pipeline alerts."""
    dag_id = context['dag'].dag_id
    raw_path = config['paths']['raw_data']
    
    subject = " Dry Pipeline Alert"
    body = f"""
    <div style="font-family: Arial, sans-serif; border: 1px solid #f0ad4e; padding: 20px; border-radius: 5px;">
        <h2 style="color: #8a6d3b;"> Dry Directory Warning</h2>
        <p>The pipeline in <b>{dag_id}</b> executed, but no data was found at:</p>
        <code style="background:#eee;padding:5px;">{raw_path}</code>
    </div>
    """
    send_custom_email(subject, body)

# 3. DAG DEFINITION
default_args = {
    'owner': 'guhan',
    'depends_on_past': False,
    'start_date': datetime(2026, 4, 1),
    'email_on_failure': False, 
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'maintenance_etl_pipeline',
    default_args=default_args,
    schedule='@hourly',
    catchup=False,
    tags=['mlops', 'alerting', 'dvc'],
) as dag:

    # Task 1: Ingest Data
    ingest_task = PythonOperator(
        task_id='ingest_sensor_data',
        python_callable=ingest,
        on_failure_callback=notify_ingestion_failure
    )

    # Task 2: Reproduce Pipeline via DVC
    # This runs dvc repro in the root, which checks dvc.yaml for changes
    dvc_repro_task = BashOperator(
        task_id='dvc_repro_pipeline',
        bash_command='dvc status && dvc repro',
        cwd='/opt/airflow', 
        on_failure_callback=notify_dry_pipeline
    )

    ingest_task >> dvc_repro_task