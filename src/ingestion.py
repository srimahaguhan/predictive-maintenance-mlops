import os
import requests
import zipfile
import io
import pandas as pd
from src.utils import load_config

def ingest():
    """
    Downloads the UCI Predictive Maintenance dataset and renames it 
    to match the path defined in config.yaml.
    """
    # 1. Initialize Paths from Config
    config = load_config()
    url = config['data_source']['url']
    raw_data_path = config['paths']['raw_data']  # Expected: 'data/raw/sensor_data.csv'
    raw_dir = os.path.dirname(raw_data_path)
    
    # Ensure directory exists
    os.makedirs(raw_dir, exist_ok=True)
    
    print(f" Initializing ingestion from: {url}")
    
    try:
        # 2. Download ZIP into memory
        response = requests.get(url, timeout=30)
        response.raise_for_status() # Raises exception for 404/500 errors
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # The UCI zip specifically contains 'ai4i2020.csv'
            internal_filename = 'ai4i2020.csv'
            
            if internal_filename in z.namelist():
                # Extract to memory first to rename it easily
                with z.open(internal_filename) as source, \
                     open(raw_data_path, 'wb') as target:
                    target.write(source.read())
                
                print(f" Success: Data saved and renamed to {raw_data_path}")
            else:
                available_files = z.namelist()
                raise FileNotFoundError(f"Expected {internal_filename} not found in ZIP. Found: {available_files}")

    except requests.exceptions.RequestException as e:
        print(f" Network Error: {e}")
        raise
    except Exception as e:
        print(f" Ingestion Error: {e}")
        raise

if __name__ == "__main__":
    ingest()