import requests
pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1525307/pdf"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
pdf_response = requests.get(pdf_url, headers=headers)

if pdf_response.status_code != 200:
        raise FileNotFoundError(f"PDF not found for PMC1525307")