import streamlit as st
import requests
import fitz  # PyMuPDF
from io import BytesIO
import pandas as pd
import re
import os
from thefuzz import fuzz

st.set_page_config(page_title="MPEdge", layout="wide")

# --- Dark Mode Toggle ---
dark_mode = st.toggle("🌙 Dark Mode")
background = "#0e1117" if dark_mode else "#f9f9f9"
text_color = "#fafafa" if dark_mode else "#1a1a1a"
accent = "#00acc1" if dark_mode else "#007acc"
box_shadow = "rgba(255,255,255,0.05)" if dark_mode else "rgba(0,0,0,0.08)"

st.markdown(f"""
    <style>
        body {{
            font-family: 'Segoe UI', sans-serif;
            background-color: {background};
            color: {text_color};
        }}
        .chapter-tag {{
            display: inline-block;
            padding: 0.25em 0.6em;
            font-size: 0.85rem;
            font-weight: 600;
            background: {accent};
            color: white;
            border-radius: 0.5rem;
            margin-right: 0.5rem;
        }}
    </style>
""", unsafe_allow_html=True)

# --- Logo/Header ---
with st.container():
    st.markdown(f"""
        <div style="text-align: center; padding-top: 1rem;">
            <img src="https://raw.githubusercontent.com/Alonso-droid/mpedge-app/main/MPEdge%20logo.png" width="300">
            <h1 style="font-size: 2.5rem; color: {text_color};">📘 MPEdge</h1>
            <p style="font-size: 1.2rem; color: #999;">AI-powered answers from the MPEP, straight from the USPTO</p>
        </div>
    """, unsafe_allow_html=True)

# --- Help Link ---
st.markdown("""
    <div style='margin: 1rem 0; font-size: 1.05rem;'>
        📖 <strong>Need help choosing a chapter?</strong><br>
        <a href='https://www.uspto.gov/web/offices/pac/mpep/mpep-index-a.html' target='_blank'>Click here to access the MPEP Subject Matter Index</a>
    </div>
""", unsafe_allow_html=True)

# --- Repaired Chapter Data ---
chapter_data = [
    {"Chapter": "Foreword", "Title": "Foreword", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0015-foreword.pdf"},
    {"Chapter": "Introduction", "Title": "Introduction", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0020-introduction.pdf"},
    {"Chapter": "TOC", "Title": "Table of Contents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0000-table-of-contents.pdf"},
    {"Chapter": "100", "Title": "Secrecy, Access, National Security, and Foreign Filing", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0100.pdf"},
    {"Chapter": "200", "Title": "Types and Status of Application; Benefit and Priority Claims", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0200.pdf"},
    {"Chapter": "300", "Title": "Ownership and Assignment", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0300.pdf"},
    {"Chapter": "400", "Title": "Representative of Applicant or Owner", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0400.pdf"},
    {"Chapter": "500", "Title": "Receipt and Handling of Mail and Papers", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0500.pdf"},
    {"Chapter": "600", "Title": "Parts, Form, and Content of Application", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0600.pdf"},
    {"Chapter": "700", "Title": "Examination of Applications", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0700.pdf"},
    {"Chapter": "800", "Title": "Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0800.pdf"},
    {"Chapter": "900", "Title": "Prior Art, Classification, and Search", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-0900.pdf"},
    {"Chapter": "1000", "Title": "Matters Decided by Various U.S. Patent and Trademark Office Officials", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1000.pdf"},
    {"Chapter": "1100", "Title": "Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub)", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1100.pdf"},
    {"Chapter": "1200", "Title": "Appeal", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1200.pdf"},
    {"Chapter": "1300", "Title": "Allowances and Issue", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1300.pdf"},
    {"Chapter": "1400", "Title": "Correction of Patents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1400.pdf"},
    {"Chapter": "1500", "Title": "Design Patents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1500.pdf"},
    {"Chapter": "1600", "Title": "Plant Patents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1600.pdf"},
    {"Chapter": "1700", "Title": "Miscellaneous", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1700.pdf"},
    {"Chapter": "1800", "Title": "Patent Cooperation Treaty", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1800.pdf"},
    {"Chapter": "1900", "Title": "Protest and Pre-Issuance Opposition", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1900.pdf"},
    {"Chapter": "2000", "Title": "Duty of Disclosure", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2000.pdf"},
    {"Chapter": "2100", "Title": "Patentability", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2100.pdf"},
    {"Chapter": "2200", "Title": "Citation of Prior Art and Ex Parte Reexamination of Patents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2200.pdf"},
    {"Chapter": "2300", "Title": "Interference Proceedings", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2300.pdf"},
    {"Chapter": "2400", "Title": "Biotechnology", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2400.pdf"},
    {"Chapter": "2500", "Title": "Maintenance Fees", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2500.pdf"},
    {"Chapter": "2600", "Title": "Optional Inter Partes Reexamination", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2600.pdf"},
    {"Chapter": "2700", "Title": "Patent Terms, Adjustments, and Extensions", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2700.pdf"},
    {"Chapter": "2800", "Title": "Supplemental Examination", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2800.pdf"},
    {"Chapter": "2900", "Title": "International Design Applications", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2900.pdf"},
    {"Chapter": "Appendix R", "Title": "Patent Rules", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-appendix-r-patent-rules.pdf"},
    {"Chapter": "Appendix T", "Title": "Patent Cooperation Treaty", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-appendix-t-pct.pdf"},
    {"Chapter": "Appendix AI", "Title": "Administrative Instructions", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-appendix-ai-admininstr.pdf"},
    {"Chapter": "Appendix P", "Title": "Paris Convention", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-appendix-p-paris.pdf"},
    {"Chapter": "Index", "Title": "Subject Matter Index", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-index.pdf"}
]

chapter_df = pd.DataFrame(chapter_data)
chapter_to_url = dict(zip(
    ["Chapter " + row["Chapter"] + " – " + row["Title"] for _, row in chapter_df.iterrows()],
    chapter_df["PDF"]
))
chapter_names = list(chapter_to_url.keys())

# --- Inputs ---
with st.container():
    st.markdown("### 🔎 Ask a Patent Question")
    question = st.text_input("💬 Enter your patent law question", placeholder="e.g. What is a restriction requirement?")
    selected_chapters = st.multiselect("📚 Select up to 3 MPEP chapters", chapter_names, max_selections=3)
    deep_search = st.checkbox("🔎 Enable Detailed Search Mode (runs separate searches for each chapter)")

@st.cache_data(show_spinner="📥 Loading chapter PDF...")
def download_pdf_text(url, max_chars=5000):
    response = requests.get(url)
    response.raise_for_status()
    with BytesIO(response.content) as f:
        doc = fitz.open(stream=f.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])[:max_chars]

if st.button("🔍 Search") and question:
    if not selected_chapters:
        st.warning("⚠️ Please select at least one chapter.")
    else:
        key = os.getenv("HUGGINGFACE_API_KEY")
        if not key:
            st.error("🔐 Hugging Face API key not found.")
        else:
            headers = {"Authorization": f"Bearer {key}"}
            if deep_search:
                st.markdown("## 🔬 Chapter-by-Chapter Results")
                for chap in selected_chapters:
                    try:
                        raw = download_pdf_text(chapter_to_url[chap])
                        payload = {
                            "inputs": f"Question: {question}\n\nContext:\n{raw}",
                            "parameters": {"max_new_tokens": 200}
                        }
                        r = requests.post("https://api-inference.huggingface.co/models/google/flan-t5-base", headers=headers, json=payload)
                        if r.status_code == 200:
                            out = r.json()
                            ans = out[0]['generated_text'] if isinstance(out, list) else out
                            st.markdown(f"""
                                <div style='background: {background}; border-left: 6px solid {accent}; padding: 1rem; margin: 1rem 0; border-radius: 12px; box-shadow: 2px 2px 8px {box_shadow};'>
                                    <span class='chapter-tag'>{chap}</span>
                                    <div style='margin-top: 0.5rem; font-size: 1rem; color: {text_color};'>{ans}</div>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning(f"⚠️ Failed on {chap}: {r.text}")
                    except Exception as e:
                        st.warning(f"⚠️ Could not process {chap}: {e}")
            else:
                context = ""
                for chap in selected_chapters:
                    try:
                        context += f"\n\n---\n\n{chap}\n" + download_pdf_text(chapter_to_url[chap])
                    except Exception as e:
                        st.warning(f"⚠️ Skipping {chap}: {e}")
                payload = {
                    "inputs": f"Question: {question}\n\nContext:\n{context[:15000]}",
                    "parameters": {"max_new_tokens": 200}
                }
                r = requests.post("https://api-inference.huggingface.co/models/google/flan-t5-base", headers=headers, json=payload)
                if r.status_code == 200:
                    out = r.json()
                    ans = out[0]['generated_text'] if isinstance(out, list) else out
                    st.markdown("## 💡 Combined AI Answer")
                    st.markdown(f"""
                        <div style='background: linear-gradient(to right, #e0f7fa, #e1f5fe); border-left: 6px solid {accent}; padding: 1.2rem; margin-top: 1rem; border-radius: 10px;'>
                            <div style='font-size: 1.1rem; color: {text_color};'>{ans}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Error: {r.text}")
