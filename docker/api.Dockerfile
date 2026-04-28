# Use a slim version of Python to keep the image small
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Install system dependencies needed for some Python packages (like psutil)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# 3. Copy the source code and configuration
# We only copy what the API needs to run
# COPY src/ ./src/
# COPY config/ ./config/

COPY . .

# 4. Set environment variables
# This ensures Python can find your 'src' module
ENV PYTHONPATH=/app

# 5. Expose the port FastAPI will run on
EXPOSE 8000

# 6. Start the application using uvicorn
# --host 0.0.0.0 is critical for Docker to route traffic correctly
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]