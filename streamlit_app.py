
import streamlit as st
import pandas as pd
import requests
from PyPDF2 import PdfReader
import io
import re
from thefuzz import fuzz

st.set_page_config(page_title="📘 MPEdge – AI-Powered MPEP", layout="wide")

# === CONFIG ===
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_HEADERS = {"Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY"}  # Set this in Streamlit secrets

# === LOGO ===
st.image("https://github.com/Alonso-droid/mpedge-app/blob/main/MPEdge%20logo.png", width=80)
st.title("📘 MPEdge")
st.markdown("##### AI-powered answers from the MPEP, straight from the USPTO")

# === Load MPEP Overview from USPTO Excel ===
@st.cache_data
def load_chapter_index():
    url = "https://raw.githubusercontent.com/Alonso-droid/mpedge-app/blob/main/MPEP%20overview.xlsx"  # You will need to host this Excel file somewhere public
    df = pd.read_excel(url, skiprows=3)
    df = df.dropna(subset=["PDF Link from USPTO Website"])
    df["MPEP Chapter"] = df["MPEP Chapter"].astype(str).str.strip()
    df["Title"] = df["Title"].str.strip()
    df["PDF Link from USPTO Website"] = df["PDF Link from USPTO Website"].str.strip()
    df["display_name"] = "Chapter " + df["MPEP Chapter"] + " – " + df["Title"]
    return dict(zip(df["display_name"], df["PDF Link from USPTO Website"]))

chapter_to_url = load_chapter_index()
chapter_names = list(chapter_to_url.keys())

# === INPUT ===
user_question = st.text_input("🔍 Ask your patent law question:", placeholder="e.g. What triggers a patent term adjustment?")
selected_chapter = st.selectbox("📂 Or pick a chapter manually:", chapter_names)

# === FUNCTIONS ===
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
    prompt = f"Answer the following patent law question using the context.\n\nQuestion: {query}\n\nContext:\n{context}\n\nAnswer:"
    response = requests.post(HF_API_URL, headers=HF_HEADERS, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]["generated_text"].split("Answer:")[-1].strip()
    else:
        return "⚠️ Error from Hugging Face API: " + response.text

# === MAIN LOGIC ===
if st.button("🧠 Get AI Answer"):
    if not user_question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("Processing..."):
            try:
                url = chapter_to_url[selected_chapter]
                raw_text = download_pdf_text(url)
                top_matches = search_content(user_question, raw_text)
                context = "\n\n".join(top_matches)
                llm_answer = summarize_with_llm(user_question, context)

                st.markdown("### ✅ Answer")
                st.markdown(f"<div style='background:#f0f9ff;padding:1rem;border-left:4px solid #2196f3;border-radius:6px'>{llm_answer}</div>", unsafe_allow_html=True)

                st.markdown("### 📚 Source Snippets")
                for i, para in enumerate(top_matches, 1):
                    with st.expander(f"Match {i}"):
                        st.write(para.strip())

            except Exception as e:
                st.error(f"❌ Something went wrong: {e}")
