import chromadb 
from groq import Groq
import pathlib
from io import StringIO, BytesIO
import tiktoken
import requests 
from lxml import etree
import os 
from pathlib import Path
from urllib.parse import quote
import xml.etree.ElementTree as ET
from pdfminer.high_level import extract_text 
from pypdf import PdfReader
import time

class LLMAgent: 
    def __init__(
            self, 
            api_key: str, 
            context_collection: chromadb, 
            client: Groq, 
            model: str, 
        ):
        self.api_key = api_key 
        self.context_collection = context_collection 
        self.client = client 
        self.model = model 

    def _trim_tokens(self, text, max_token=45): 
        return text[:max_token]
    
    def _return_context(self, relevant_docs): 
        context = ""
        for i, (metadata, doc) in enumerate(zip(relevant_docs["metadatas"][0], relevant_docs["documents"][0])):
            context += f"[Chunk {i+1}]\nDocument:\n{doc}\nMetadata:\n{metadata}\n\n"
        return context

    def _file_extraction(self, uploaded_file): 
        if uploaded_file is not None:
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            lines = stringio.read().split(" ")[:1000]
            file_extension = pathlib.Path(uploaded_file.name).suffix 
        else: 
            file_extension = "No file provided"
            lines = "No file provided"
        
        return lines, file_extension
    
    def _get_biological_context(self, query_keywords, num_results): 
        #TODO: Implement getting images into actual search
        formatted_query = self._keywords_split(query_keywords)
        results = self._search_pubmed(formatted_query, num_results)
        articles = results.get("resultList", {}).get("result", [])
        if not articles:
            print("No results found.")
            return
        
        final_context = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title")
            pmcid = article.get("pmcid")
            if not pmcid:
                continue 
            
            #ret = []
            
            try: 
                final_context += title + "\n"+ self._trim_tokens(self._extract_text(self._get_file(pmcid)))
            except FileNotFoundError: 
                print(f"No file found{pmcid}")
                #abstract = self._get_abstract_from_pmc(pmcid) 
                #ret.append(self._trim_tokens(abstract))
            except ValueError: 
                print(f"No file found{pmcid}")
                
        #for re in ret: 
            #final_context += self._trim_tokens(re) + "\n"

        return final_context
        
    def _keywords_split(self, query_keywords):
        return " AND ".join([kw.strip() for kw in query_keywords.split(",") if kw.strip()])

    def _search_pubmed(self, query, num_results):
        base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        params = {
            "query": f"{query} AND OPEN_ACCESS:Y",  
            "format": "json",
            "pageSize": num_results
        }
        response = requests.get(base_url, params=params)
        time.sleep(2)
        response.raise_for_status()
        return response.json()

    def _get_abstract_from_pmc(self, pmcid):
        base_url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/abstract"
        params = {"format": "json"}
        response = requests.get(base_url, params=params)
        time.sleep(2)
        response.raise_for_status()
        data = response.json()
        return data.get("abstractText")

    def _get_file(self, pmcid): 
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        pdf_response = requests.get(pdf_url, headers=headers)
        time.sleep(2)
        if pdf_response.status_code != 200:
            raise FileNotFoundError(f"PDF not found for {pmcid}")

        return BytesIO(pdf_response.content)
    
    def _extract_text(self, pdf_stream): 
        pdf_stream.seek(0)
        text = extract_text(pdf_stream) 
        return text

    def chat(self, query, uploaded_file, prev_convo, query_keywords) -> str:
        relevant_docs = self.context_collection.query(
            query_texts=[query],
            n_results=2
        )
        
        #Getting all info to embed into prompt
        lines, file_extension = self._file_extraction(uploaded_file)
        previous_conversation = prev_convo[-5:]
        context = self._return_context(relevant_docs)

        formatted_query = f"""
        Answer the question using the provided context and file input (if available). If unsure, say so.

        Experimental Context:\n{self._trim_tokens(context)}...

        Conversation Summary:\n{self._trim_tokens(previous_conversation)}...

        File info: This file is of the format: {file_extension} and contains this kind of content: \n{lines}. Use that in conjuction with the experimental context.

        Question:\n{query}

        IF YOU DO NOT HAVE ENOUGH INFORMATION, SAY WHAT INFORMATION YOU NEED
        """

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role":"user", 
                    "content": formatted_query,
                }
            ], 
            model=self.model,
        )
        response = response.choices[0].message.content

        return response 