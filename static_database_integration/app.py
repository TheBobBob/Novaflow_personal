import streamlit as st
from groq import Groq
from supabase import create_client

SUPABASE_KEY = "sb_secret_TXwlQfw6vFpsM_8Zn8vRVA_PPPN0otO"
SUPABASE_URL = "https://cvlgiurxfqauzxbdomrv.supabase.co"
GROQ_API_KEY = "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"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

st.title("Static Database Demo")

user_prompt = st.text_input("Enter your query about GO terms:")

def process_prompt(prompt):
    instruction = f"""
    You are an assistant that generates database queries in a strict format.

    Database information:
    - Table: GO terms database
    - Columns: 
        - Gene_Name (gene symbols)
        - GO_ID (GO term IDs like GO:0006915)
        - Organism (species name)
        - GO_Name (name of the GO term)

    Instructions:
    1. Given a user query, identify which columns and values need to be used to query the database.
    2. Output each database query as a single line in this exact format:
    Column,Value 
    Example: Gene_Name,TP53
    3. Only return lines in this format. COMMAS ARE REQUIRED
    4. Do NOT add any explanations, notes, numbering, or extra text. DO NOT ADD ANY OTHER INFORMATION OTHER THAN WHAT IS EXPLICITLY SAID IN THE PROMPT.
    5. Each line corresponds to a single column/value filter. 
    6. Do NOT include the table name or any other metadata.

    Here is the user query to process:
    {prompt}

    """
    chat_completion = groq_client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": instruction,
        }],
        model="llama-3.1-8b-instant",
    )
    st.write(chat_completion.choices[0].message.content)
    return chat_completion.choices[0].message.content.strip().split("\n")

def run_database_query(queries):
    returned_values = []
    for query in queries:
        if "GO_Name" in query: 
            continue
        if "," not in query:
            st.write("Found query with no comma")
            continue
        column, value = query.split(",", 1)
        response = supabase.table("GO_Terms").select("*").ilike(column.strip(), value.strip()).execute()
        returned_values.extend(response.data)
    return returned_values

if user_prompt:
    st.info("Processing your query...")
    queries = process_prompt(user_prompt)
    results = run_database_query(queries)

    if results:
        st.success(f"Found {len(results)} matching rows:")
        st.dataframe(results)
    else:
        st.warning("No matches found.")