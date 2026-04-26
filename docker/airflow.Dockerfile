FROM apache/airflow:3.1.1

# 1. Switch to root to install system-level git
USER root
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 2. Switch BACK to the airflow user for Python installations
USER airflow

# 3. Install dvc and your requirements as the 'airflow' user
# (This satisfies the safety check that caused your error)
RUN pip install --no-cache-dir dvc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt