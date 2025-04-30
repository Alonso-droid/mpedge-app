import streamlit as st
import requests
import fitz  # PyMuPDF
from io import BytesIO
import pandas as pd
import re
import os
from thefuzz import fuzz

st.set_page_config(page_title="MPEdge", layout="centered")

st.image("https://raw.githubusercontent.com/Alonso-droid/mpedge-app/main/MPEdge%20logo.png", width=300)
st.title("📘 MPEdge")
st.subheader("AI-powered answers from the MPEP, straight from the USPTO")

# Link to subject matter index
st.markdown(
    "📖 **Need help choosing a chapter?**  \n"
    "[Click here to access the MPEP Subject Matter Index](https://www.uspto.gov/web/offices/pac/mpep/mpep-index-a.html)",
    unsafe_allow_html=True
)

# Load full chapter data from Excel
@st.cache_data
def load_chapter_data():
    df = pd.read_excel("MPEP overview.xlsx", skiprows=3)
    df = df.dropna()
    df = df[df.columns[:3]]
    df.columns = ["Chapter", "Title", "PDF"]
    df["Label"] = df["Chapter"].astype(str).str.strip().str.replace("Chpater", "Chapter").str.replace(" ", "", regex=True) + " – " + df["Title"].astype(str).str.strip()
    return df

chapter_df = load_chapter_data()
chapter_to_url = dict(zip(chapter_df["Label"], chapter_df["PDF"]))
chapter_names = list(chapter_to_url.keys())

# Keyword map (can be expanded)
keyword_map = {
    "delay": "2700",
    "adjustment": "2700",
    "extension": "2700",
    "term": "2700",
    "supplemental": "2800",
    "international": "2900",
    "design": "2900"
}

def detect_chapter_from_question(question):
    question_lower = question.lower()
    for keyword, chapter_code in keyword_map.items():
        match = chapter_df[chapter_df["Chapter"].astype(str) == chapter_code]
        if keyword in question_lower and not match.empty:
            return match.iloc[0]["Label"]
    return None

question = st.text_input("💬 What is your patent law question?")
selected_chapter = st.selectbox(
    "📂 Choose MPEP Chapter to Search (Optional – AI will pick if left blank)",
    [""] + chapter_names
)

if st.button("🔍 Search"):
    if question:
        if not selected_chapter:
            detected_chapter = detect_chapter_from_question(question)
            if detected_chapter:
                selected_chapter = detected_chapter
                st.success(f"✅ Based on your question, we matched it to **{detected_chapter}**")
            else:
                st.warning("⚠️ We couldn't auto-detect a chapter. Please choose one manually.")

        if selected_chapter:
            pdf_url = chapter_to_url[selected_chapter]

            @st.cache_data(show_spinner="📥 Downloading MPEP section...")
            def download_pdf_text(pdf_url):
                response = requests.get(pdf_url)
                response.raise_for_status()
                with BytesIO(response.content) as f:
                    doc = fitz.open(stream=f.read(), filetype="pdf")
                    return "\n".join([page.get_text() for page in doc])

            try:
                text = download_pdf_text(pdf_url)

                with st.spinner("🤖 Analyzing your question..."):
                    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
                    if not HUGGINGFACE_API_KEY:
                        st.error("🔐 Hugging Face API key not found. Please set it in Streamlit secrets.")
                    else:
                        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
                        payload = {
                            "inputs": f"Question: {question}\n\nContext:\n{text}",
                            "parameters": {"max_new_tokens": 200}
                        }
                        response = requests.post(
                            "https://api-inference.huggingface.co/models/google/flan-t5-base",
                            headers=headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            output = response.json()
                            answer = output[0]['generated_text'] if isinstance(output, list) else output

                            with st.container():
                                st.markdown("### 🧠 AI Response")
                                st.markdown(
                                    f"""
                                    <div style='padding: 1rem; border-radius: 10px; background-color: #f8f9fa; box-shadow: 0 0 10px rgba(0,0,0,0.05);'>
                                    {answer}
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                        else:
                            st.error(f"⚠️ Error from Hugging Face API: {response.text}")

            except Exception as e:
                st.error(f"❌ Error processing MPEP content: {e}")
