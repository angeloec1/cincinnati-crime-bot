import pandas as pd
from sodapy import Socrata
import os
import time
from huggingface_hub import HfApi

# === CONFIGURATION ===
DOMAIN = "data.cincinnati-oh.gov"
DATASET_ID = "gexm-h6bt"
LIMIT = 50000
USERNAME = "mlsystemsg1"  # Change this to your Hugging Face username
HF_REPO_ID = f"{USERNAME}/cincinnati-crime-data"
HF_TOKEN = os.getenv("HF_TOKEN")  # Use environment variable for security

# === PREP OUTPUT DIR ===
OUTPUT_DIR = "data"
FILENAME_LATEST = "calls_for_service_latest.csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)
# === STEP 1: FETCH DATA FROM SOCRATA ===
def fetch_cincinnati_data():
    print("🚓 Pulling data from Socrata...")
    client = Socrata(DOMAIN, None)
    offset = 0
    all_results = []

    while True:
        print(f"  → Records {offset} to {offset + LIMIT}...")
        results = client.get(DATASET_ID, limit=LIMIT, offset=offset)
        if not results:
            break
        all_results.extend(results)
        offset += LIMIT
        time.sleep(0.5)

    df = pd.DataFrame.from_records(all_results)
    print(f"✅ Retrieved {len(df)} records.")
    return df

# === STEP 1.5: TRANSFORM DATA ===
def transform_data(df):
    print("🔄 Transforming data...")

    # Columns to keep
    keep_columns = [
        'create_time_incident',
        'incident_type_desc',
        'incident_type_id',
        'disposition_text',
        'event_number',
        'sna_neighborhood',
        'cpd_neighborhood',
        'priority'
    ]
    df = df[keep_columns].copy()

    # Convert 'create_time_incident' to datetime
    df['create_time_incident'] = pd.to_datetime(df['create_time_incident'], errors='coerce')

    # Convert 'priority' to numeric
    df['priority'] = pd.to_numeric(df['priority'], errors='coerce')

    # If 'incident_type_desc' is missing, fill it with 'disposition_text'
    df['incident_type_desc'] = df['incident_type_desc'].fillna(df['disposition_text'])

    # If 'sna_neighborhood' is missing, fill it with 'cpd_neighborhood'
    df['sna_neighborhood'] = df['sna_neighborhood'].fillna(df['cpd_neighborhood'])
    
    print(f" Data transformed: {df.shape[0]} rows, {df.shape[1]} columns")
    return df



# === STEP 2: SAVE LOCALLY ===
def save_csv(df):
    local_path = os.path.join(OUTPUT_DIR, FILENAME_LATEST)
    df.to_csv(local_path, index=False)
    print(f"✅ Saved latest dataset: {FILENAME_LATEST}")
    return local_path

# === STEP 3: UPLOAD TO HUGGING FACE ===
def upload_to_huggingface(local_file):
    try:
        print("🔁 Starting upload to Hugging Face...")
        api = HfApi()
        api.upload_file(
            path_or_fileobj=local_file,
            path_in_repo="calls_for_service_latest.csv",
            repo_id="mlsystemsg1/cincinnati-crime-data",
            repo_type="dataset",
            token=os.getenv("HF_TOKEN")
        )
        print("✅ Upload complete!")
    except Exception as e:
        print("❌ Upload to Hugging Face failed:", e)
        raise e

# === MAIN ===
if __name__ == "__main__":
    df = fetch_cincinnati_data()
    df = transform_data(df)
    local_path = save_csv(df)
    upload_to_huggingface(local_path)
