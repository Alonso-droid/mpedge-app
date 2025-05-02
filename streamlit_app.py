# streamlit_app.py

import streamlit as st
import requests
import fitz  # PyMuPDF
from io import BytesIO
from thefuzz import fuzz
import os
from sentence_transformers import SentenceTransformer, util
import torch

# --- App Config ---
st.set_page_config(page_title="MPEdge", layout="wide")
st.title("📘 MPEdge — Ask the MPEP")
st.markdown("""
A simple patent assistant powered by open-source models and the USPTO's MPEP.
""")

# --- Load Embedder Model ---
@st.cache_resource(show_spinner=False)
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_embedder()

def get_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            doc = fitz.open(stream=f.read(), filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return f"[Error extracting PDF]: {e}"

# --- MPEP Chapters ---
chapter_to_url = {
    'Chapter 0 – Table of Contents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0000-table-of-contents.pdf',
    'Chapter 20 – Introduction': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0020-introduction.pdf',
    'Chapter 100 – Secrecy, Access, National Security, and Foreign Filing': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0100.pdf',
    'Chapter 200 – Types and Status of Application; Benefit and Priority Claims': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0200.pdf',
    'Chapter 300 – Ownership and Assignment': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0300.pdf',
    'Chapter 400 – Representative of Applicant or Owner': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0400.pdf',
    'Chapter 500 – Receipt and Handling of Mail and Papers': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0500.pdf',
    'Chapter 600 – Parts, Form, and Content of Application': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0600.pdf',
    'Chapter 700 – Examination of Applications': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0700.pdf',
    'Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0800.pdf',
    'Chapter 900 – Prior Art, Search, Classification, and Routing': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0900.pdf',
    'Chapter 1000 – Matters Decided by Various U.S. Patent and Trademark Office Officials': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1000.pdf',
    'Chapter 1100 – Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub) and Preissuance Submissions': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1100.pdf',
    'Chapter 1200 – Appeal': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1200.pdf',
    'Chapter 1300 – Allowance and Issue': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1300.pdf',
    'Chapter 1400 – Correction of Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1400.pdf',
    'Chapter 1500 – Design Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1500.pdf',
    'Chapter 1600 – Plant Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1600.pdf',
    'Chapter 1700 – Miscellaneous': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1700.pdf',
    'Chapter 1800 – Patent Cooperation Treaty': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1800.pdf',
    'Chapter 1900 – Protest': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1900.pdf',
    'Chapter 2000 – Duty of Disclosure': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2000.pdf',
    'Chapter 2100 – Patentability': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2100.pdf',
    'Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2200.pdf',
    'Chapter 2300 – Interference and Derivation Proceedings': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2300.pdf',
    'Chapter 2400 – Biotechnology': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2400.pdf',
    'Chapter 2500 – Maintenance Fees': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2500.pdf',
    'Chapter 2600 – Optional Inter Partes Reexamination': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2600.pdf',
    'Chapter 2700 – Patent Terms, Adjustments, and Extensions': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2700.pdf',
    'Chapter 2800 – Supplemental Examination': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2800.pdf',
    'Chapter 2900 – International Design Applications': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2900.pdf',
    'Chapter 9005 – Appendix I – Reserved': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9005-appx-i.pdf',
    'Chapter 9010 – Appendix II – List of Decisions Cited': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9010-appx-ii.pdf',
    'Chapter 9015 – Appendix L – Patent Laws': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9015-appx-l.pdf',
    'Chapter 9020 – Appendix R – Patent Rules': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9020-appx-r.pdf',
    'Chapter 9025 – Appendix T – Patent Cooperation Treaty': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9025-appx-t.pdf',
    'Chapter 9030 – Appendix AI – Administrative Instructions Under the PCT': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9030-appx-ai.pdf',
    'Chapter 9035 – Appendix P – Paris Convention': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9035-appx-p.pdf',
    'Chapter 9090 – Subject Matter Index': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9090-subject-matter-index.pdf',
    'Chapter 9095 – Form Paragraphs': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9095-Form-Paragraph-Chapter.pdf'\n}\n\nchapter_names = list(chapter_to_url.keys())"
}
chapter_names = list(chapter_to_url.keys())

# --- UI: Question & Selection ---
st.markdown("### 🔍 Ask a Question")
query = st.text_input("Enter your patent law question", placeholder="e.g. What is a restriction requirement?")
selected_chapters = st.multiselect("Select up to 3 chapters to search", chapter_names, max_selections=3)

@st.cache_data(show_spinner="📥 Downloading and processing PDFs...")
def load_texts(chapter_keys):
    texts = {}
    for key in chapter_keys:
        raw = get_text_from_pdf_url(chapter_to_url[key])
        texts[key] = raw
    return texts

# --- Helper: Retrieve Top Chunks ---
def get_top_matches(query, text_map, top_k=1):
    results = []
    for chapter, text in text_map.items():
        paragraphs = [p for p in text.split("\n\n") if len(p.strip()) > 100]
        para_embeddings = model.encode(paragraphs, convert_to_tensor=True)
        query_embedding = model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, para_embeddings, top_k=top_k)[0]
        for hit in hits:
            para = paragraphs[hit['corpus_id']]
            score = hit['score']
            results.append((chapter, para, score))
    return sorted(results, key=lambda x: -x[2])

# --- Hugging Face API ---
def query_huggingface(prompt):
    key = os.getenv("HUGGINGFACE_API_KEY")
    if not key:
        st.error("Hugging Face API key not set in Streamlit secrets.")
        return ""
    headers = {"Authorization": f"Bearer {key}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 300}
    }
    response = requests.post(
        "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1",
        headers=headers, json=payload)
    try:
        return response.json()[0]['generated_text']
    except:
        return f"[Error from Hugging Face]: {response.text}"

# --- Main Search + Output ---
if st.button("🔍 Search") and query and selected_chapters:
    with st.spinner("🔎 Analyzing MPEP chapters..."):
        chapter_texts = load_texts(selected_chapters)
        top_matches = get_top_matches(query, chapter_texts, top_k=1)

        context = "\n---\n".join(f"{chap}\n{para}" for chap, para, _ in top_matches)
        prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer clearly with MPEP citations."

        llm_output = query_huggingface(prompt)

        st.markdown("## 💡 AI-Generated Answer")
        st.markdown(f"""
        <div style='background: #f0f4f8; padding: 1rem; border-left: 4px solid #007acc; border-radius: 6px;'>
        {llm_output}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## 📚 Source Paragraphs")
        for chap, para, score in top_matches:
            st.markdown(f"**{chap}** (score: {score:.2f})")
            st.code(para[:1000])
