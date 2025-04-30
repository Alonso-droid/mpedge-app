
import streamlit as st
import requests
from PyPDF2 import PdfReader
import io
import re
from thefuzz import fuzz

st.set_page_config(page_title="📘 MPEdge – AI-Powered MPEP", layout="wide")

# === LOGO ===
st.image("https://raw.githubusercontent.com/Alonso-droid/mpedge-app/main/MPEEdge%20logo.png", width=80)
st.title("📘 MPEdge")
st.markdown("##### AI-powered answers from the MPEP, straight from the USPTO")

# === HARDCODED MPEP CHAPTERS ===
chapter_to_url = {'Chapter 20 – Introduction': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0020-introduction.pdf', 'Chapter 0 – Table of Contents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0000-table-of-contents.pdf', 'Chapter 100 – Secrecy, Access, National Security, and Foreign Filing': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0100.pdf', 'Chpater 200 – \xa0Types and Status of Application; Benefit and Priority Claims': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0200.pdf', 'Chapter 300 – \xa0Ownership and Assignment': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0300.pdf', 'Chapter 400 – \xa0Representative of Applicant or Owner': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0400.pdf', 'Chpater 500 – \xa0Receipt and Handling of Mail and Papers': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0500.pdf', 'Chapter 600 – \xa0Parts, Form, and Content of Application': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0600.pdf', 'Chapter 700 – \xa0Examination of Applications': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0700.pdf', 'Chpater 800 – \xa0Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0800.pdf', 'Chapter 900 – \xa0Prior Art, Search, Classification, and Routing': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-0900.pdf', 'Chapter 1000 – \xa0Matters Decided by Various U.S. Patent and Trademark Office Officials': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1000.pdf', 'Chapter 1100  – \xa0Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub) and Preissuance Submissions': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1100.pdf', 'Chapter 1200 – \xa0\xa0Appeal': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1200.pdf', 'Chapter 1300 – \xa0Allowance and Issue': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1300.pdf', 'Chapter 1400 – \xa0Correction of Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1400.pdf', 'Chapter 1500 – \xa0Design Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1500.pdf', 'Chapter 1600 – \xa0Plant Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1600.pdf', 'Chapter 1700 – \xa0Miscellaneous': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1700.pdf', 'Chapter 1800 – \xa0\xa0Patent Cooperation Treaty': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1800.pdf', 'Chapter 1900 – \xa0Protest': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-1900.pdf', 'Chapter 2000 – \xa0Duty of Disclosure': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2000.pdf', 'Chapter 2100 – \xa0Patentability': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2100.pdf', 'Chapter 2200 – \xa0Citation of Prior Art and Ex Parte Reexamination of Patents': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2200.pdf', 'Chapter 2300 – \xa0Interference and Derivation Proceedings': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2300.pdf', 'Chapter 2400 – \xa0Biotechnology': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2400.pdf', 'Chapter 2500 – \xa0Maintenance Fees': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2500.pdf', 'Chapter 2600 – \xa0Optional Inter Partes Reexamination': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2600.pdf', 'Chapter 2700 – \xa0Patent Terms, Adjustments, and Extensions': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2700.pdf', 'Chapter 2800 – \xa0Supplemental Examination': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2800.pdf', 'Chapter 2900 – \xa0International Design Applications': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-2900.pdf', 'Chapter 9005 – Appendix I - \xa0 \xa0\xa0PDF\xa0 \xa0Reserved': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9005-appx-i.pdf', 'Chapter 9010 – Appendix II - \xa0 \xa0\xa0PDF\xa0 \xa0List of Decisions Cited': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9010-appx-ii.pdf', 'Chapter 9015 – Appendix L - \xa0 \xa0PDF\xa0 \xa0Patent Laws': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9015-appx-l.pdf', 'Chapter 9020 – Appendix R - \xa0 \xa0\xa0PDF\xa0 \xa0Patent Rules': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9020-appx-r.pdf', 'Chapter 9025 – Appendix T - \xa0 \xa0\xa0PDF\xa0 \xa0Patent Cooperation Treaty': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9025-appx-t.pdf', 'Chapter 9030 – Appendix AI - \xa0 \xa0\xa0PDF\xa0 \xa0Administrative Instructions Under the PCT': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9030-appx-ai.pdf', 'Chapter 9035 – Appendix P - \xa0 \xa0PDF\xa0 \xa0Paris Convention': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9035-appx-p.pdf', 'Chapter 9090 – Subject Matter Index\xa0\xa0 \xa0 \xa0PDF': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9090-subject-matter-index.pdf', 'Chapter 9095 – Form Paragraphs\xa0\xa0 \xa0 \xa0PDF': 'https://www.uspto.gov/web/offices/pac/mpep/mpep-9095-Form-Paragraph-Chapter.pdf'}

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
    api_url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = { "Authorization": "Bearer YOUR_HUGGINGFACE_API_KEY" }
    prompt = f"""Answer the following patent law question using the context.

Question: {query}

Context:
{context}

Answer:"""    
    response = requests.post(api_url, headers=headers, json={"inputs": prompt})
    if response.status_code == 200:
        return response.json()[0]["generated_text"].split("Answer:")[-1].strip()
    else:
        return "⚠️ Error from Hugging Face API: " + response.text

# === MAIN ===
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
