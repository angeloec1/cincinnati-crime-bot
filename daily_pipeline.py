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

# === STEP 2: SAVE LOCALLY ===
def save_csv(df):
    local_path = os.path.join(OUTPUT_DIR, FILENAME_LATEST)
    df.to_csv(local_path, index=False)
    print(f"✅ Saved latest dataset: {FILENAME_LATEST}")
    return local_path

# === STEP 3: UPLOAD TO HUGGING FACE ===
def upload_to_huggingface(local_path):
    print("🚀 Uploading to Hugging Face...")
    api = HfApi(token=HF_TOKEN)
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=FILENAME_LATEST,
        repo_id=HF_REPO_ID,
        repo_type="dataset",
        repo_type_write_token=HF_TOKEN
    )
    print("✅ Upload complete.")

# === MAIN ===
if __name__ == "__main__":
    df = fetch_cincinnati_data()
    local_path = save_csv(df)
    upload_to_huggingface(local_path)