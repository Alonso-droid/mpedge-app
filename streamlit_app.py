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
    {"Chapter": "2700", "Title": "Patent Terms, Adjustments, and Extensions", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2700.pdf"},
    {"Chapter": "2800", "Title": "Supplemental Examination", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2800.pdf"},
    {"Chapter": "2900", "Title": "International Design Applications", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2900.pdf"},
    {"Chapter": "1500", "Title": "Design Patents", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-1500.pdf"},
    {"Chapter": "2100", "Title": "Patentability", "PDF": "https://www.uspto.gov/web/offices/pac/mpep/mpep-2100.pdf"}
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
