import streamlit as st
from groq import Groq
from supabase import create_client

SUPABASE_KEY = "sb_publishable_ARfI0U_-UF8kRPExFHm23Q_p_uh1QaC"
SUPABASE_URL = "https://cvlgiurxfqauzxbdomrv.supabase.co"
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

st.title("Static Database Demo")

user_prompt = st.text_input("Enter your query about GO terms:")

def process_prompt(prompt):
    instruction = f"""
    Given this prompt, please find all necessary database queries for the following database:
    GO terms database: Gene_Name, GO_ID, Organism, GO_Name

    For every query, put it on a newline in this format: Column,Value
    Example: Gene_Name,TP53
    """
    chat_completion = groq_client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": prompt + "\n" + instruction,
        }],
        model="llama-3.1-8b-instant",
    )
    return chat_completion.choices[0].message.content.strip().split("\n")

def make_database_query(queries):
    returned_values = []
    for query in queries:
        if "," not in query:
            continue
        column, value = query.split(",", 1)
        response = supabase.table("go_terms").select("*").eq(column.strip(), value.strip()).execute()
        if response.error:
            st.error(f"Error querying column {column}: {response.error}")
            continue
        returned_values.extend(response.data)
    return returned_values

if user_prompt:
    st.info("Processing your query...")
    queries = process_prompt(user_prompt)
    results = make_database_query(queries)

    if results:
        st.success(f"Found {len(results)} matching rows:")
        st.dataframe(results)
    else:
        st.warning("No matches found.")