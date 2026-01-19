import streamlit as st
import requests
from supabase import create_client

SUPABASE_KEY = "sb_secret_TXwlQfw6vFpsM_8Zn8vRVA_PPPN0otO"
SUPABASE_URL = "https://cvlgiurxfqauzxbdomrv.supabase.co"

# Load your OpenRouter API key from Streamlit secrets
OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("Static Database Demo (OpenRouter Version)")

user_prompt = st.text_input("Enter your query about GO terms:")

def process_prompt(prompt):
    """Send instruction + user query to OpenRouter and return raw model output."""
    
    instruction = f"""
    You are an assistant that generates database queries in a strict format.

    Database information:
    - Table: GO terms database
        - Columns: 
            - Gene_Name
            - GO_ID (GO term IDs like GO:0006915)
            - Organism (species name)
            
    Databases you do not have access to:
    - Gene ID conversions
    - Protein databases
    - Transcriptome databases
    
    Instructions:
    1. Given a user query, identify which columns and values need to be used to query the database.
    2. Output each database query as a single line in this exact format:
       Column,Value
       Example: Gene_Name,TP53

    3. Only return lines in this format. COMMAS ARE REQUIRED.
    4. Do NOT add explanations, notes, numbering, or extra text.
    5. Each line corresponds to one column/value filter.
    6. Do NOT include the table name or any metadata.

    ALWAYS ASSUME YOU WILL BE DOING A DATABASE SEARCH UNLESS OTHERWISE.

    Examples where NOT to do a search:
    - "What is a dog?"
    - "Analyze this RNA seq data"
    - "What is RNA seq?"

    Examples where you SHOULD do a search:
    - "Is X gene and Y gene both in the same GO term?"
    - "What GO term is X gene in?"

    User query to process:
    {prompt}
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": "qwen/qwen-2.5-72b-instruct",  # you can change to any OpenRouter model
        "messages": [
            {"role": "user", "content": instruction}
        ],
        "temperature": 0.0,
        "max_tokens": 200
    }

    response = requests.post(url, headers=headers, json=body)
    data = response.json()

    return data["choices"][0]["message"]["content"].strip()

def run_database_query(lines):
    returned_values = []

    for line in lines:
        if "," not in line:
            st.write("Skipping malformed line (no comma):", line)
            continue
        
        column, value = line.split(",", 1)
        column = column.strip()
        value = value.strip()

        # Run Supabase query
        response = supabase.table("GO_Terms").select("*").ilike(column, value).execute()
        
        if response.data:
            returned_values.extend(response.data)

    return returned_values
    
if user_prompt:
    st.info("Processing your query with OpenRouter...")

    # Model output (a block of lines)
    raw_output = process_prompt(user_prompt)

    # Split into individual query lines
    queries = [q.strip() for q in raw_output.splitlines() if q.strip()]

    # Run the database queries
    results = run_database_query(queries)

    if results:
        st.success(f"Found {len(results)} matching rows:")
        st.dataframe(results)
    else:
        st.warning("No matches found.")
