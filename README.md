# Cincinnati Crime Bot - Data Pipeline

This repository powers an automated data pipeline that downloads daily police call records from the [Cincinnati Open Data Portal](https://data.cincinnati-oh.gov/safety/PDI-Police-Data-Initiative-Police-Calls-for-Servic/gexm-h6bt/about_data) and uploads the latest dataset to the [Hugging Face Hub](https://huggingface.co/datasets/mlsystemsg1/cincinnati-crime-data) for seamless access by chatbots and data tools.
--- 
## Project Purpose
To improve public access to Cincinnati crime data by developing a conversational AI chatbot that enables users to intuitively query neighborhood-level safety information. This tool aims to increase transparency, foster civic engagement, and support informed decision-making among residents, city officials, realtors, and insurers by transforming complex datasets into accessible, real-time insights. In a final state, our chatbot would accompany the existing dashboard, so that users can have a more interactive way to view the data and its impact on citizens' lives. 


---
## Group Members
Eliza Angelo, Seba Al Ubaidani, Vighnesh Raj, Adama Dembele, Ariela Kurtzer

---

## What It Does

- 📥 Pulls **all police calls for service** from Cincinnati's public safety API using pagination
- 🧹 Cleans and saves the latest copy to a CSV
- ☁️ Uploads the final dataset to [Hugging Face Datasets](https://huggingface.co/datasets/mlsystemsg1/cincinnati-crime-data)
- 🔁 Scheduled to run daily via GitHub Actions (`.github/workflows/daily_upload.yml`)

---

## Dataset Snapshot

The dataset includes:
- Incident timestamp and location
- Call type and priority level
- Response times and disposition codes

---

## 🛠 Project Structure

```bash
cincinnati-crime-bot/
├── daily_pipeline.py          # Main ETL script (fetch, clean, upload)
├── datapull.ipynb             # Notebook version for manual testing
├── requirements.txt           # Dependencies for GitHub Actions runner
├── .github/workflows/
│   └── daily_upload.yml       # GitHub Actions workflow (runs daily)
└── test.ipynb                 # Optional experiments or testing

