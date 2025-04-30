
import streamlit as st
import requests
from PyPDF2 import PdfReader
import io
import re
from thefuzz import fuzz

st.set_page_config(page_title="MPEdge - Ask the MPEP", layout="wide")

# --- CONFIG ---
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_HEADERS = {"Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY"}  # Replace with your HF token

PDF_LINKS = {
    "mpep-2700.pdf": "https://drive.google.com/uc?export=download&id=1JrKFc-TYpKi9yx2w52Aj-VzTiYO9AzXJ",
    "mpep-2800.pdf": "https://drive.google.com/uc?export=download&id=1neThbfH-CHGxyGDjr0txEpgOqFskmF1x",
    "mpep-2900.pdf": "https://drive.google.com/uc?export=download&id=1GHjohcfCO1ZmdZugUNtZoD2WcnXbmnNn"
}

# --- FUNCTIONS ---

@st.cache_data
def download_pdf_text(url):
    response = requests.get(url)
    response.raise_for_status()
    reader = PdfReader(io.BytesIO(response.content))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def search_pdf_content(query, pdf_text):
    paragraphs = re.split(r'\n{2,}', pdf_text)
    best = sorted(paragraphs, key=lambda x: fuzz.token_set_ratio(x, query), reverse=True)
    return best[:2]

def call_huggingface_llm(question, context):
    prompt = f"Answer the following patent law question using the given context.\n\nQuestion: {question}\n\nContext:\n{context}\n\nAnswer:"
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]["generated_text"].split("Answer:")[-1].strip()
    else:
        return "Error from Hugging Face API: " + str(response.content)

# --- UI ---

st.title("🔍 MPEdge")
st.subheader("Ask the MPEP – AI-Powered Patent Guidance")

query = st.text_input("What is your patent law question?", placeholder="e.g. What constitutes prior art under 102?")
selected_file = st.selectbox("Choose MPEP Section to Search", list(PDF_LINKS.keys()))

if st.button("Get Answer"):
    with st.spinner("Searching and analyzing..."):
        text = download_pdf_text(PDF_LINKS[selected_file])
        top_matches = search_pdf_content(query, text)
        combined_context = "\n\n".join(top_matches)
        llm_response = call_huggingface_llm(query, combined_context)

        st.markdown("### 🧠 AI-Generated Answer")
        st.success(llm_response)

        st.markdown("### 📚 Source Highlights")
        for idx, para in enumerate(top_matches, 1):
            with st.expander(f"Match {idx} from {selected_file}"):
                st.write(para)
