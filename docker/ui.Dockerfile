FROM python:3.12-slim
WORKDIR /app


COPY ui_requirements.txt .


RUN pip install --no-cache-dir --default-timeout=1000 -r ui_requirements.txt


COPY . .

EXPOSE 8501
# ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
ENTRYPOINT ["sh", "-c", "PYTHONPATH=. streamlit run src/streamlit_app.py --server.port=8501 --server.address=0.0.0.0"]