
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

# --- Model Selection ---
model_options = {
    "🪶 Phi-3 Mini": "microsoft/Phi-3-mini-4k-instruct",
    "🔎 OLMo 1B": "allenai/OLMo-2-0425-1B",
    "🧠 Mistral 7B": "mistralai/Mistral-7B-Instruct-v0.1"
}
model_choice = st.selectbox("🧠 Choose a model to use", list(model_options.keys()))
model_id = model_options[model_choice]

# --- Full MPEP Chapter List ---
chapter_data = pd.read_csv("https://raw.githubusercontent.com/Alonso-droid/mpedge-app/main/mpep_chapter_index.csv").to_dict(orient='records')
chapter_df = pd.DataFrame(chapter_data)
chapter_to_url = dict(zip(
    ["Chapter " + row["Chapter"] + " – " + row["Title"] for row in chapter_data],
    [row["PDF"] for row in chapter_data]
))
chapter_names = list(chapter_to_url.keys())

# --- Inputs ---
with st.container():
    st.markdown("### 🔎 Ask a Patent Question")
    question = st.text_input("💬 Enter your patent law question", placeholder="e.g. What is a restriction requirement?")
    selected_chapters = st.multiselect("📚 Select up to 3 MPEP chapters", chapter_names, max_selections=3)
    deep_search = st.checkbox("🔎 Enable Detailed Search Mode (runs separate searches for each chapter)")

# --- Auto-detect chapter ---
@st.cache_data(show_spinner="📥 Loading PDF...")
def download_pdf_text(url, max_chars=5000):
    response = requests.get(url)
    response.raise_for_status()
    with BytesIO(response.content) as f:
        doc = fitz.open(stream=f.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in doc])[:max_chars]

# Simple keyword matching for auto-detection
def auto_detect_chapter(question):
    keywords = {
        "delay": "2700", "adjustment": "2700", "term": "2700", "extension": "2700",
        "supplemental": "2800", "international": "2900", "design": "2900"
    }
    q = question.lower()
    for word, chap in keywords.items():
        if word in q:
            matches = chapter_df[chapter_df["Chapter"] == chap]
            if not matches.empty:
                row = matches.iloc[0]
                return f"Chapter {row['Chapter']} – {row['Title']}"
    return None

if st.button("🔍 Search") and question:
    if not selected_chapters:
        auto_chap = auto_detect_chapter(question)
        if auto_chap:
            selected_chapters = [auto_chap]
            st.info(f"✅ Auto-detected likely chapter: **{auto_chap}**")
        else:
            st.warning("⚠️ Please select at least one chapter.")
    if selected_chapters:
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
                        prompt = f"Question: {question}\n\nContext:\n{raw}"
                        payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
                        r = requests.post(f"https://api-inference.huggingface.co/models/{model_id}", headers=headers, json=payload)
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
                prompt = f"Question: {question}\n\nContext:\n{context[:15000]}"
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
                r = requests.post(f"https://api-inference.huggingface.co/models/{model_id}", headers=headers, json=payload)
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
