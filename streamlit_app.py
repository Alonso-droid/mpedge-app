
import streamlit as st
import requests
from PyPDF2 import PdfReader
import io
import re
from thefuzz import fuzz

st.set_page_config(page_title="📘 MPEdge – AI-Powered MPEP", layout="wide")

# -- CONFIGURATION --
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_HEADERS = {"Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY"}  # Replace in secrets

MPEP_FILES = {
    "mpep-2700.pdf": {
        "title": "Chapter 2700 – Patent Terms, Adjustments, and Extensions",
        "url": "https://drive.google.com/uc?export=download&id=1JrKFc-TYpKi9yx2w52Aj-VzTiYO9AzXJ"
    },
    "mpep-2800.pdf": {
        "title": "Chapter 2800 – Supplemental Examination",
        "url": "https://drive.google.com/uc?export=download&id=1neThbfH-CHGxyGDjr0txEpgOqFskmF1x"
    },
    "mpep-2900.pdf": {
        "title": "Chapter 2900 – International Design Applications",
        "url": "https://drive.google.com/uc?export=download&id=1GHjohcfCO1ZmdZugUNtZoD2WcnXbmnNn"
    }
}

# -- HELPER FUNCTIONS --
@st.cache_data
def download_pdf_text(pdf_url):
    response = requests.get(pdf_url)
    response.raise_for_status()
    reader = PdfReader(io.BytesIO(response.content))
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content + "\n"
    return text

def search_content(query, full_text):
    paragraphs = re.split(r'\n{2,}', full_text)
    ranked = sorted(paragraphs, key=lambda x: fuzz.token_set_ratio(query, x), reverse=True)
    return ranked[:2]

def summarize_with_llm(query, context):
    prompt = f"Answer the following patent question using the context below.\n\nQuestion: {query}\n\nContext:\n{context}\n\nAnswer:"
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]["generated_text"].split("Answer:")[-1].strip()
    else:
        return "⚠️ Error from Hugging Face API: " + response.text

# -- UI LAYOUT --
st.title("📘 MPEdge")
st.markdown("#### Your AI-Powered MPEP Assistant")
st.markdown("> _Ask legal or procedural questions. We'll search the MPEP and provide helpful responses._")

query = st.text_input("🔍 What patent law question do you have?", placeholder="e.g. What causes a patent term adjustment?")

dropdown_labels = [info["title"] for info in MPEP_FILES.values()]
filename_lookup = {info["title"]: fname for fname, info in MPEP_FILES.items()}
selected_title = st.selectbox("📂 Choose MPEP Chapter", dropdown_labels)
selected_file = filename_lookup[selected_title]
selected_url = MPEP_FILES[selected_file]["url"]

if st.button("🧠 Analyze with AI"):
    with st.spinner("Reading MPEP and generating response..."):
        try:
            text = download_pdf_text(selected_url)
            matches = search_content(query, text)
            context = "\n\n".join(matches)
            answer = summarize_with_llm(query, context)

            st.markdown("### ✅ AI-Generated Answer")
            st.markdown(f"<div style='background:#f4faff;border-left:4px solid #2196f3;padding:1rem;border-radius:8px;'>{answer}</div>", unsafe_allow_html=True)

            st.markdown("### 📚 Relevant MPEP Excerpts")
            for i, match in enumerate(matches, 1):
                with st.expander(f"Match {i}"):
                    st.write(match.strip())

        except Exception as e:
            st.error(f"⚠️ Failed to retrieve or process PDF: {e}")
