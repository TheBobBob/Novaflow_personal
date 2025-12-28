API_KEY = "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"
MODEL = "llama-3.3-70b-versatile"
import rag
import chromadb 
from langchain_text_splitters import CharacterTextSplitter 
import re
import os
from requests_html import HTMLSession
import PyPDF2
from PyPDF2 import PdfReader
import lxml_html_clean
from lxml_html_clean import Cleaner
import requests
import lxml.html
from groq import Groq
import streamlit as st
import time

#Setup codes
chroma_client = chromadb.Client() 
collection = chroma_client.get_or_create_collection(name="novaflow_demo_rag", metadata={"hnsw:space": "cosine"})
text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base", chunk_size=500, chunk_overlap=100
)


rna_seq_urls = {"https://seqera.io/pipelines/rnaseq--nf-core/", "https://bioconductor.org/packages/devel/bioc/vignettes/DESeq2/inst/doc/DESeq2.html", "https://hbctraining.github.io/Training-modules/planning_successful_rnaseq/lessons/data_visualization.html"}

#TODO: Add extracting images feature
for url in rna_seq_urls: 
    response = requests.get(url)
    doc = lxml.html.fromstring(response.content)

    cleaner = Cleaner(
        scripts=True,     
        javascript=True,
        style=True,       
        inline_style=True,
        links=True,      
        meta=True,
        page_structure=False,
        safe_attrs_only=True
    )

    cleaned_doc = cleaner.clean_html(doc)
    web_text = cleaned_doc.text_content()

    #Text splitter warnings come from this
    docs = text_splitter.split_text(web_text)
    #Doesn't add if unique ID
    for count, doc in enumerate(docs): 
        collection.add(
            ids=[f"{url}_{count}"], 
            documents=[doc], 
            metadatas=[{"source": "nf_core_rna_seq"}]
        )

client = Groq(
    api_key=API_KEY,
)

llm_agent = rag.LLMAgent(API_KEY, collection, client, MODEL)

client_keyword = Groq( 
    api_key = API_KEY
)

#Streamlit UI
import streamlit as st
import time

st.title("RNAseq Interaction Chat - Novaflow Demo 9/19/2025")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

uploaded_file = st.file_uploader("Please upload a file if you wish")

query = st.chat_input("Ask your RNA-seq question...")

def response_generator(text):
    words = text.split(" ")
    for word in words:
        yield word + " "
        time.sleep(0.05)

if query is not None:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    query_keywords = client.chat.completions.create(
        messages = [
            {
                "role": "user", 
                "content": f"""Given the following query: {query}, choose 2 keywords that best describe it IF IT REFERENCES SPECIFIC BIOLOGICAL PROCESSES, NOT GENERAL PROCEDURES. 
                RETURN ONLY THE KEYWORDS SEPARATED BY COMMAS."""
            }
        ], 
        model = MODEL,
    )

    query_keywords = query_keywords.choices[0].message.content 
    
    if uploaded_file is not None:
        response_text = llm_agent.chat(query, uploaded_file, st.session_state.messages, query_keywords)
        print("sent query with file")
    else:
        response_text = llm_agent.chat(query, None, st.session_state.messages, query_keywords)
        print("sent query without file")

    with st.chat_message("assistant"):
        st.write_stream(response_generator(response_text))

    st.session_state.messages.append({"role": "assistant", "content": response_text})
elif uploaded_file is not None: 
    st.write("Please write a query as well.")