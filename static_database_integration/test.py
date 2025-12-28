
SUPABASE_KEY = "sb_secret_TXwlQfw6vFpsM_8Zn8vRVA_PPPN0otO"
SUPABASE_URL = "https://cvlgiurxfqauzxbdomrv.supabase.co"
GROQ_API_KEY = "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"
from supabase import create_client, Client

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Query with exact column names (no quotes needed in Supabase client)
response = supabase.table("GO_Terms").select("Gene_Name, GO_ID, Organism").limit(5).execute()
print(response.data)

# Or to search for that specific GO_ID:
response = supabase.table("GO_Terms").select("*").eq("GO_ID", "GO:0000423").execute()
print(response.data)