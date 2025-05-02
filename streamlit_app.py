# streamlit_app.py

# === Part 1: Setup and Imports ===

import streamlit as st
import requests
import fitz  # PyMuPDF
from io import BytesIO
import os
import re
import json
import base64
from datetime import datetime
from thefuzz import fuzz
from sentence_transformers import SentenceTransformer, util
import torch

# --- Load Embedder Model ---
@st.cache_resource(show_spinner="🔌 Loading embedding model...")
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")

model = load_embedder()

# --- Initialize Session State ---
if "history" not in st.session_state:
    st.session_state["history"] = []

if "last_query" not in st.session_state:
    st.session_state["last_query"] = None

if "last_answer" not in st.session_state:
    st.session_state["last_answer"] = None

# === Part 2: Logo, Page Setup, and UI Theme ===

# --- Page Configuration ---
st.set_page_config(page_title="MPEdge", layout="wide")

# --- Header with Logo ---
def render_logo_and_header():
    logo_url = "https://github.com/Alonso-droid/mpedge-app/raw/main/MPEdge%20logo.png"
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 1rem;">
            <img src="{logo_url}" alt="MPEdge Logo" width="60"/>
            <h1 style="margin: 0;">MPEdge: AI Patent Assistant</h1>
        </div>
    """, unsafe_allow_html=True)

render_logo_and_header()

# --- Intro Text ---
st.markdown("AI-powered search and analysis of the MPEP (Manual of Patent Examining Procedure). Ask a question, and receive an answer with citations from USPTO source material.")


# --- Hardcoded MPEP Chapters (Official USPTO PDFs) ---
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
    'Chapter 9095 – Form Paragraphs': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9095-Form-Paragraph-Chapter.pdf'
}

chapter_names = list(chapter_to_url.keys())

# --- Supported Free LLMs with fallback
available_models = {
    "Mistral 7B (Hugging Face)": {
        "id": "huggingface/mistral-7b-instruct",
        "source": "huggingface"
    },
    "DeepSeek Chat (OpenRouter)": {
        "id": "deepseek-ai/deepseek-llm-7b",
        "source": "openrouter"
    },
    "OpenChat 7B (OpenRouter)": {
        "id": "openchat/openchat-7b",
        "source": "openrouter"
    },
    "Phi-3 Medium (OpenRouter)": {
        "id": "microsoft/phi-3-medium-128k-instruct",
        "source": "openrouter"
    },
    "OLMo 2 (OpenRouter)": {
        "id": "allenai/OLMo-2-0425-1B-Instruct",
        "source": "openrouter"
    }
}

# --- Chapter Auto-Suggestion ---
def auto_detect_chapter(question):
    keywords = {
        # General Procedures
        "application filing": "Chapter 600 – Parts, Form, and Content of Application",
        "drawings": "Chapter 600 – Parts, Form, and Content of Application",
        "claims": "Chapter 600 – Parts, Form, and Content of Application",
        "specification": "Chapter 600 – Parts, Form, and Content of Application",

        # Patentability & Examination
        "obviousness": "Chapter 2100 – Patentability",
        "35 usc 103": "Chapter 2100 – Patentability",
        "novelty": "Chapter 2100 – Patentability",
        "35 usc 102": "Chapter 2100 – Patentability",
        "patentable subject matter": "Chapter 2100 – Patentability",
        "section 101": "Chapter 2100 – Patentability",
        "double patenting": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "unity of invention": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "restriction": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "examination": "Chapter 700 – Examination of Applications",
        "interview": "Chapter 700 – Examination of Applications",
        "final rejection": "Chapter 700 – Examination of Applications",

        # Appeals & Rejections
        "appeal": "Chapter 1200 – Appeal",
        "ptab": "Chapter 1200 – Appeal",
        "rehearing": "Chapter 1200 – Appeal",
        "pre-appeal": "Chapter 1200 – Appeal",

        # Prior Art & References
        "prior art": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",
        "103 rejection": "Chapter 2100 – Patentability",
        "102 rejection": "Chapter 2100 – Patentability",
        "publication": "Chapter 1100 – Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub)",
        "non-patent literature": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",

        # Representation & Access
        "power of attorney": "Chapter 400 – Representative of Applicant or Owner",
        "attorney": "Chapter 400 – Representative of Applicant or Owner",
        "access to application": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",
        "secrecy order": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",

        # Assignments & Ownership
        "assignment": "Chapter 300 – Ownership and Assignment",
        "change of ownership": "Chapter 300 – Ownership and Assignment",

        # National & International Filing
        "foreign filing license": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",
        "pct application": "Chapter 1800 – Patent Cooperation Treaty",
        "international phase": "Chapter 1800 – Patent Cooperation Treaty",
        "national stage": "Chapter 1800 – Patent Cooperation Treaty",
        "wipo": "Chapter 1800 – Patent Cooperation Treaty",

        # Special Application Types
        "design patent": "Chapter 1500 – Design Patents",
        "plant patent": "Chapter 1600 – Plant Patents",
        "reissue": "Chapter 1400 – Correction of Patents",
        "continuation": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "continuation-in-part": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "divisional": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",

        # Disclosure & Duty
        "duty of disclosure": "Chapter 2000 – Duty of Disclosure",
        "ids": "Chapter 2000 – Duty of Disclosure",
        "rule 56": "Chapter 2000 – Duty of Disclosure",

        # Other
        "protest": "Chapter 1900 – Protest",
        "maintenance fees": "Chapter 2500 – Maintenance Fees",
        "subject matter index": "Chapter 9090 – Subject Matter Index",
        "petition": "Chapter 1000 – Matters Decided by Various U.S. Patent and Trademark Office Officials"
    }

    question_lower = question.lower()
    for keyword, chapter in keywords.items():
        if keyword in question_lower:
            return chapter
    return None

# --- PDF Loader with Caching ---
@st.cache_data(show_spinner="📄 Reading selected MPEP chapters...")
def get_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            doc = fitz.open(stream=f.read(), filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return f"[PDF Error] {e}"

# --- Embedding Search ---
def get_top_matches(query, chapter_texts, top_k=1):
    results = []
    for chapter, full_text in chapter_texts.items():
        paragraphs = [p for p in full_text.split("\n\n") if len(p.strip()) > 100]
        if not paragraphs:
            continue
        para_embeddings = model.encode(paragraphs, convert_to_tensor=True)
        query_embedding = model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, para_embeddings, top_k=top_k)[0]
        for hit in hits:
            para = paragraphs[hit["corpus_id"]]
            score = hit["score"]
            results.append((chapter, para.strip(), score))
    return sorted(results, key=lambda x: -x[2])

# --- UI Inputs ---
st.markdown("### 🔍 Ask Your Question")
query = st.text_input("Enter a patent law question", placeholder="e.g. What is a restriction requirement?")
selected_chapters = st.multiselect("Select up to 3 chapters to search", chapter_names, max_selections=3)
model_choice = st.selectbox("Choose a free model to answer with", list(available_models.keys()))

# --- Unified LLM Query with Fallback ---
def query_llm(prompt, primary_model_name):
    primary = available_models[primary_model_name]
    backup = available_models["Mistral 7B (Hugging Face)"] if primary_model_name != "Mistral 7B (Hugging Face)" else available_models["Phi-3 Medium (OpenRouter)"]

    def call_model(model_info):
        if model_info["source"] == "huggingface":
            key = os.getenv("HUGGINGFACE_API_KEY")
            if not key:
                return "[Hugging Face API key not set]"
            headers = {"Authorization": f"Bearer {key}"}
            url = f"https://api-inference.huggingface.co/models/{model_info['id']}"
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300}}
            response = requests.post(url, headers=headers, json=payload)
            try:
                return response.json()[0]["generated_text"]
            except Exception:
                return None

        elif model_info["source"] == "openrouter":
            key = os

# --- Final Execution ---
if st.button("🔍 Search") and query:
    # Auto-detect if nothing selected
    if not selected_chapters:
        auto = auto_detect_chapter(query)
        if auto:
            selected_chapters = [auto]
            st.info(f"📘 Auto-selected likely chapter: **{auto}**")
        else:
            st.warning("⚠️ Please select at least one chapter or clarify your question.")
            st.stop()

    # Extract text from PDFs
    with st.spinner("📄 Reading and analyzing selected chapters..."):
        chapter_texts = {c: get_text_from_pdf_url(chapter_to_url[c]) for c in selected_chapters}
        top_matches = get_top_matches(query, chapter_texts, top_k=1)

        if not top_matches:
            st.error("❌ No relevant content found.")
            st.stop()

        context = "\n---\n".join(f"{chap}\n{para}" for chap, para, _ in top_matches)
        prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer clearly and cite specific MPEP sections if appropriate."

        llm_response = query_llm(prompt, model_choice)

    # --- Show Answer ---
    st.markdown("## 💡 AI Answer")
    st.markdown(f"""
    <div style='background: #f0f4f8; padding: 1rem; border-left: 4px solid #007acc; border-radius: 6px;'>
        {llm_response}
    </div>
    """, unsafe_allow_html=True)

    # --- Show Source ---
    st.markdown("## 📚 Source Paragraph(s)")
    for chap, para, score in top_matches:
        with st.expander(f"{chap} — Relevance Score: {score:.2f}", expanded=False):
            st.code(para[:1500])  # limit for UX
