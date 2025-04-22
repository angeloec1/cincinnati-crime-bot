import streamlit as st
import pandas as pd
import calendar
import re
from datetime import timedelta
from transformers import pipeline
from huggingface_hub import hf_hub_download

# Load dataset
@st.cache_data
def load_crime_data():
    csv_path = hf_hub_download(
        repo_id="mlsystemsg1/cincinnati-crime-data",
        repo_type="dataset",
        filename="calls_for_service_latest.csv"
    )
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = [col.lower() for col in df.columns]
    df.dropna(subset=['cpd_neighborhood'], inplace=True)
    df['create_time_incident'] = pd.to_datetime(df['create_time_incident'], errors='coerce')
    return df

OFFENSE_GROUPS = {
    "robbery": ["ROBBERY PERSONAL (JO)(W)", "ROBBERY PERSONAL (IP)", "ROBBERY BUSINESS (NIP)"],
    "assault": ["ASSAULT (IP)(W)", "ASSAULT (JO)(W)(E)", "SEX ASSAULT ADULT (S)",
                "SEX ASSAULT CHILD (IP)", "SEX ASSAULT CHILD (S)(W)(E)", "RAPER"],
    "disturbance": ["DISTURBANCE VERB (IP)(W)", "DISTURBANCE VERB (S)", "DISTURBANCE PHYS (JO)",
                    "DISTURBANCE VERB (S)(W)", "DISTURBANCE PHYS (S)(E)",
                    "FAMILY DIST PHYS (JO)(E)", "FAMILY DIST PHYS (S)", "FAMILY DIST UNKN (JO)"],
    "theft": ["VEHICLE THEFT (JO)(W)", "U-AUTO THEFT/RECOVERY RPT",
              "THEFT (IP)(W)", "OCR THEFT ATTEMPT (NIP)"],
    "drug": ["DRUG USE/POSSESS (IP)(W)(E)", "DRUG SALE (IP)(W)(E)", "ADV - DRUG SALE (NIP)"]
}

def get_relevant_rows(question, df):
    q = question.lower()
    filtered = df.copy()
    neighborhoods = df['cpd_neighborhood'].dropna().unique()
    matched_hood = next((hood for hood in neighborhoods if hood.lower() in q), None)
    if matched_hood:
        filtered = filtered[filtered['cpd_neighborhood'].str.lower() == matched_hood.lower()]
    for group, values in OFFENSE_GROUPS.items():
        if group in q:
            filtered = filtered[filtered['incident_type_id'].isin(values)]
            break
    now = pd.Timestamp.now()
    if match := re.search(r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})", q):
        y, m, d = map(int, match.groups())
        filtered = filtered[filtered['create_time_incident'].dt.date == pd.Timestamp(y, m, d).date()]
    if "last week" in q or "past week" in q:
        filtered = filtered[filtered['create_time_incident'] >= now - timedelta(days=7)]
    elif "last month" in q or "past month" in q:
        filtered = filtered[filtered['create_time_incident'] >= now - timedelta(days=30)]
    elif "yesterday" in q:
        filtered = filtered[filtered['create_time_incident'].dt.date == (now - timedelta(days=1)).date()]
    elif "today" in q:
        filtered = filtered[filtered['create_time_incident'].dt.date == now.date()]
    elif match := re.search(r"(past|last)\s+(\d+)\s+day", q):
        days = int(match.group(2))
        filtered = filtered[filtered['create_time_incident'] >= now - timedelta(days=days)]
    months = {month.lower(): i for i, month in enumerate(calendar.month_name) if month}
    for name, num in months.items():
        if name in q:
            filtered = filtered[filtered['create_time_incident'].dt.month == num]
            break
    if year_match := re.search(r"(20\d{2})", q):
        filtered = filtered[filtered['create_time_incident'].dt.year == int(year_match.group(1))]
    if any(x in q for x in ["latest", "most recent", "last offense", "last incident", "recent"]):
        filtered = filtered.sort_values(by='create_time_incident', ascending=False)
    return filtered.dropna(subset=['create_time_incident'])

def generate_summary(question, df):
    if df.empty:
        return "No matching records found."
    if any(word in question.lower() for word in ["how many", "count", "number of"]):
        return f"There were {len(df)} incidents matching your query."
    examples = []
    for _, row in df.head(5).iterrows():
        date = row.get('create_time_incident', 'N/A')
        try:
            date_str = pd.to_datetime(date).date()
        except:
            date_str = date
        offense = row.get('incident_type_id', 'N/A')
        hood = row.get('cpd_neighborhood', 'N/A')
        incident = row.get('event_number', 'N/A')
        priority = row.get('priority', 'N/A')
        examples.append(f"On {date_str}, a {offense} (Priority {priority}) occurred in {hood} (Incident #{incident}).")
    return "\n".join(examples)

def answer_with_llm(question, data_rows, model):
    if data_rows.empty:
        return "Sorry, I couldn't find any data matching that question."
    context = generate_summary(question, data_rows)
    prompt = f"""
You are a friendly and helpful assistant analyzing recent crime data from Cincinnati.
Use the provided incident summaries below to answer the user's question. 
If the question is asking for a number, respond with the count clearly. 
If the question is more open-ended (like "why"), provide a thoughtful, 
conversational explanation based on the data. 
Be polite and informative, and aim to help the user understand the data better.
Here are some relevant data points:
{context}
Now answer this question based on the above:
{question}
    """.strip()
    result = model(prompt, max_new_tokens=150)[0]['generated_text']
    return result.strip()

@st.cache_resource
def load_model():
    return pipeline("text2text-generation", model="google/flan-t5-small")

# Streamlit UI
st.title("🔍 Cincinnati Crime Chatbot")
st.write("Ask about recent crime incidents by neighborhood, offense type, or time.")
llm_model = load_model()
df = load_crime_data()
question = st.text_input("Ask a question:")
if question:
    with st.spinner("Analyzing data..."):
        filtered = get_relevant_rows(question, df)
        response = answer_with_llm(question, filtered, llm_model)
        st.success("Done!")
       
 
