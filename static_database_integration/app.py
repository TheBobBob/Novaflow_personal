import streamlit as st
from groq import Groq
from supabase import create_client
from transformers import AutoModelForCausalLM, AutoTokenizer, TextGenerationPipeline

SUPABASE_KEY = "sb_secret_TXwlQfw6vFpsM_8Zn8vRVA_PPPN0otO"
SUPABASE_URL = "https://cvlgiurxfqauzxbdomrv.supabase.co"

model_name = "verseAI/databricks-dolly-v2-3b"

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", torch_dtype="auto")

# Create the text generation pipeline
generator = TextGenerationPipeline(model=model, tokenizer=tokenizer)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
st.title("Static Database Demo")

user_prompt = st.text_input("Enter your query about GO terms:")

def process_prompt(prompt):
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
    
    3. Only return lines in this format. COMMAS ARE REQUIRED
    4. Do NOT add any explanations, notes, numbering, or extra text. DO NOT ADD ANY OTHER INFORMATION OTHER THAN WHAT IS EXPLICITLY SAID IN THE PROMPT.
    5. Each line corresponds to a single column/value filter. 
    6. Do NOT include the table name or any other metadata.


    ALWAYS ASSUME YOU WILL BE DOING A DATABASE SEARCH UNLESS OTHERWISE. INFORM YOUR DECISIONS WITH THE EXAMPLES BELOW:
    Here are some examples of when not to do a database search:
    1. "What is a dog?"
    2. "Analyze this RNA seq data"
    3. "What is RNA seq?"

    Here are some examples of when to DO a database search:
    1. "Is X gene and Y gene both in the same GO term?"
    2. "What GO term is X gene in?"
    
    Here is the user query to process:
    {prompt}
    """    
    outputs = generator(
        instruction,
        max_new_tokens=200,
        temperature=0.0,   
    )
    
    return outputs[0]['generated_text'].strip()


def run_database_query(queries):
    returned_values = []
    for query in queries:
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
