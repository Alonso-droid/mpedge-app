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
from sentence_transformers import SentenceTransformer
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



# --- Chapter Auto-Suggestion ---
def auto_detect_chapter(question):
    keyword_to_chapter = {
        # --- Patentability & Rejections ---
        "101": "Chapter 2100 – Patentability",
        "section 101": "Chapter 2100 – Patentability",
        "section 102": "Chapter 2100 – Patentability",
        "section 103": "Chapter 2100 – Patentability",
        "35 usc 102": "Chapter 2100 – Patentability",
        "35 usc 103": "Chapter 2100 – Patentability",
        "obviousness": "Chapter 2100 – Patentability",
        "non-obvious": "Chapter 2100 – Patentability",
        "novelty": "Chapter 2100 – Patentability",
        "enablement": "Chapter 2100 – Patentability",
        "written description": "Chapter 2100 – Patentability",
        "best mode": "Chapter 2100 – Patentability",
        "utility": "Chapter 2100 – Patentability",
        "abstract idea": "Chapter 2100 – Patentability",
        "statutory subject matter": "Chapter 2100 – Patentability",
        "algorithm": "Chapter 2100 – Patentability",
        "103 rejection": "Chapter 2100 – Patentability",
        "102 rejection": "Chapter 2100 – Patentability",

        # --- Examination ---
        "office action": "Chapter 700 – Examination of Applications",
        "final rejection": "Chapter 700 – Examination of Applications",
        "non-final rejection": "Chapter 700 – Examination of Applications",
        "amendment": "Chapter 700 – Examination of Applications",
        "examination": "Chapter 700 – Examination of Applications",
        "reply brief": "Chapter 700 – Examination of Applications",
        "interview": "Chapter 700 – Examination of Applications",

        # --- Filing and Specification ---
        "claims": "Chapter 600 – Parts, Form, and Content of Application",
        "abstract": "Chapter 600 – Parts, Form, and Content of Application",
        "drawings": "Chapter 600 – Parts, Form, and Content of Application",
        "specification": "Chapter 600 – Parts, Form, and Content of Application",

        # --- Restriction & Double Patenting ---
        "restriction requirement": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "double patenting": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "generic claim": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",
        "unity of invention": "Chapter 800 – Restriction in Applications Filed Under 35 U.S.C. 111; Double Patenting",

        # --- Application Types ---
        "continuation": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "continuation-in-part": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "divisional": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "provisional application": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",
        "priority claim": "Chapter 200 – Types and Status of Application; Benefit and Priority Claims",

        # --- Appeals ---
        "appeal": "Chapter 1200 – Appeal",
        "ptab": "Chapter 1200 – Appeal",
        "board of appeals": "Chapter 1200 – Appeal",
        "rehearing": "Chapter 1200 – Appeal",
        "pre-appeal": "Chapter 1200 – Appeal",

        # --- Disclosure Requirements ---
        "ids": "Chapter 2000 – Duty of Disclosure",
        "information disclosure statement": "Chapter 2000 – Duty of Disclosure",
        "duty of disclosure": "Chapter 2000 – Duty of Disclosure",
        "rule 56": "Chapter 2000 – Duty of Disclosure",

        # --- Prior Art & Reexamination ---
        "prior art": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",
        "non-patent literature": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",
        "reexamination": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",
        "ex parte": "Chapter 2200 – Citation of Prior Art and Ex Parte Reexamination of Patents",

        # --- International Filing ---
        "pct": "Chapter 1800 – Patent Cooperation Treaty",
        "pct application": "Chapter 1800 – Patent Cooperation Treaty",
        "foreign filing": "Chapter 1800 – Patent Cooperation Treaty",
        "foreign filing license": "Chapter 1800 – Patent Cooperation Treaty",
        "wipo": "Chapter 1800 – Patent Cooperation Treaty",
        "national phase": "Chapter 1800 – Patent Cooperation Treaty",
        "international phase": "Chapter 1800 – Patent Cooperation Treaty",

        # --- Design & Plant Patents ---
        "design patent": "Chapter 1500 – Design Patents",
        "ornamental": "Chapter 1500 – Design Patents",
        "plant patent": "Chapter 1600 – Plant Patents",

        # --- Correction & Reissue ---
        "reissue": "Chapter 1400 – Correction of Patents",

        # --- Assignments ---
        "assignment": "Chapter 300 – Ownership and Assignment",
        "ownership": "Chapter 300 – Ownership and Assignment",
        "change of ownership": "Chapter 300 – Ownership and Assignment",

        # --- Representation & Power of Attorney ---
        "power of attorney": "Chapter 400 – Representative of Applicant or Owner",
        "attorney": "Chapter 400 – Representative of Applicant or Owner",
        "attorney of record": "Chapter 400 – Representative of Applicant or Owner",

        # --- Secrecy & National Security ---
        "secrecy order": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",
        "classified": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",
        "access to application": "Chapter 100 – Secrecy, Access, National Security, and Foreign Filing",

        # --- Biotechnology ---
        "deposit": "Chapter 2400 – Biotechnology",
        "biological material": "Chapter 2400 – Biotechnology",

        # --- Publication & Pre-Grant Disclosure ---
        "publication": "Chapter 1100 – Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub)",
        "pre-grant": "Chapter 1100 – Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub)",
        "sir": "Chapter 1100 – Statutory Invention Registration (SIR); Pre-Grant Publication (PGPub)",

        # --- Protests & Petitions ---
        "protest": "Chapter 1900 – Protest",
        "petition": "Chapter 1000 – Matters Decided by Various U.S. Patent and Trademark Office Officials",

        # --- Fees ---
        "maintenance fee": "Chapter 2500 – Maintenance Fees",
        "fee payment": "Chapter 2500 – Maintenance Fees",
        "late fee": "Chapter 2500 – Maintenance Fees",

        # --- Misc & Index ---
        "subject matter index": "Chapter 9090 – Subject Matter Index"
    }

    question_lower = question.lower()
    for keyword, chapter in keyword_to_chapter.items():
        if keyword in question_lower:
            return chapter
    return None


# === Part 4: PDF Processing and Embedding ===

@st.cache_data(show_spinner="📄 Loading and extracting MPEP PDF...")
def get_text_from_pdf_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        with BytesIO(response.content) as f:
            doc = fitz.open(stream=f.read(), filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
    except Exception as e:
        return f"[Error loading PDF] {e}"

def get_top_matches(query, chapter_texts, top_k=1):
    results = []
    for chapter, full_text in chapter_texts.items():
        paragraphs = [p.strip() for p in full_text.split("\n\n") if len(p.strip()) > 100]
        if not paragraphs:
            continue
        para_embeddings = model.encode(paragraphs, convert_to_tensor=True)
        query_embedding = model.encode(query, convert_to_tensor=True)
        hits = util.semantic_search(query_embedding, para_embeddings, top_k=top_k)[0]
        for hit in hits:
            para = paragraphs[hit["corpus_id"]]
            score = hit["score"]
            results.append((chapter, para, score))
    return sorted(results, key=lambda x: -x[2])

# === Part 5: UI Inputs and Model Selection ===

# === Part 5: UI Inputs and Model Selection (Corrected) ===

st.markdown("### 🔍 Ask a Patent Law Question")

# User input
query = st.text_input("Enter your question", placeholder="e.g. What is a restriction requirement?")

# ✅ Model dictionary with real, working model IDs (free variants where possible)
available_models = {
    "Mistral 7B (Hugging Face)": {
        "id": "mistralai/Mistral-7B-Instruct-v0.3",  # correct HF repo
        "source": "huggingface"
    },
    "Phi-3 Medium (OpenRouter)": {
        "id": "microsoft/phi-3-medium-128k-instruct:free",
        "source": "openrouter"
    },
    "OpenChat 7B (OpenRouter)": {
        "id": "openchat/openchat-7b:free",
        "source": "openrouter"
    },
    "DeepSeek Chat (OpenRouter)": {
        "id": "deepseek/deepseek-llm-7b-chat:free",
        "source": "openrouter"
    },
    "OLMo 2 (OpenRouter)": {
        "id": "allenai/OLMo-2-0425-1B-Instruct:free",
        "source": "openrouter"
    }
}

# Dropdown for selecting a model
model_name = st.selectbox("Choose a free AI model", list(available_models.keys()))

# Help link for chapter selection
st.markdown("#### 📘 Need help finding the right chapter?")
st.markdown("[🔗 View the MPEP Subject Matter Index](https://www.uspto.gov/web/offices/pac/mpep/mpep-9090-subject-matter-index.pdf)")

# Suggest chapters from question
suggested = auto_detect_chapters(query)
suggested_chapters = [suggested] if suggested else []

# Manual chapter picker
selected_chapters = st.multiselect(
    "Select up to 3 MPEP chapters to search",
    chapter_names,
    default=suggested_chapters[:1] if suggested_chapters else [],
    max_selections=3
)


# === Part 6: Query LLM with Fallback & Proper API Handling ===

def query_llm(prompt, primary_model_name):
    if primary_model_name not in available_models:
        return {"error": f"Unknown model selected: {primary_model_name}"}

    primary = available_models[primary_model_name]
    fallback_key = "Mistral 7B (Hugging Face)" if primary_model_name != "Mistral 7B (Hugging Face)" else "Phi-3 Medium (OpenRouter)"
    fallback = available_models.get(fallback_key)

    def call_model(model):
        source = model["source"]
        model_id = model["id"]

        try:
            if source == "huggingface":
                key = os.getenv("HUGGINGFACE_API_KEY")
                if not key:
                    return {"error": "Missing Hugging Face API key"}
                url = f"https://api-inference.huggingface.co/models/{model_id}"
                headers = {"Authorization": f"Bearer {key}"}
                payload = {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 300}
                }
                r = requests.post(url, headers=headers, json=payload)
                if r.status_code != 200:
                    return {"error": f"Hugging Face error: {r.status_code}", "raw": r.text}
                data = r.json()
                if isinstance(data, list) and "generated_text" in data[0]:
                    return {"output": data[0]["generated_text"], "model": model_id}
                return {"error": "Unexpected HF output format", "raw": data}

            elif source == "openrouter":
                key = os.getenv("OPENROUTER_API_KEY")
                if not key:
                    return {"error": "Missing OpenRouter API key"}
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {"Authorization": f"Bearer {key}"}
                payload = {
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}]
                }
                r = requests.post(url, headers=headers, json=payload)
                if r.status_code == 402:
                    return {"error": "OpenRouter: Insufficient credits", "raw": r.text}
                if r.status_code == 429:
                    return {"error": "OpenRouter: Rate limit hit", "raw": r.text}
                if r.status_code != 200:
                    return {"error": f"OpenRouter error: {r.status_code}", "raw": r.text}
                data = r.json()
                return {"output": data["choices"][0]["message"]["content"], "model": model_id}

        except Exception as e:
            return {"error": f"Unhandled error calling {model_id}: {e}"}

    # Try primary
    result = call_model(primary)
    if "output" in result:
        return result

    # Fallback attempt
    st.warning(f"⚠️ Primary model failed: {result.get('error')}. Switching to fallback model...")
    result_fallback = call_model(fallback)
    return result_fallback if "output" in result_fallback else {"error": "Both models failed", "details": result_fallback}


# === Part 7: Execute Search, Query Model, and Display Answer ===

if st.button("🔍 Search") and query and selected_chapters:
    with st.spinner("🔍 Retrieving relevant text and analyzing..."):
        # Load and extract relevant text
        chapter_texts = {c: get_text_from_pdf_url(chapter_to_url[c]) for c in selected_chapters}
        top_matches = get_top_matches(query, chapter_texts, top_k=1)

        if not top_matches:
            st.error("❌ No relevant text found in selected chapters.")
            st.stop()

        # Build context from top paragraphs
        context = "\n---\n".join(f"{chap}\n{para}" for chap, para, _ in top_matches)

        # Clean, structured prompt
        prompt = f"""
Using the following text from the MPEP chapter(s), answer the user's question concisely and clearly. Do not repeat the question or the full context.

User question:
{query}

MPEP context:
{context}

Answer:
""".strip()

        # Call LLM
        result = query_llm(prompt, model_name)

        # --- Debug Output ---
        st.markdown("### 🐞 Debug Output (developer view)")
        st.json(result)

        if "output" not in result:
            st.error(f"❌ No usable LLM response.\n\nError: {result.get('error', 'Unknown error')}")
            if "raw" in result:
                st.code(str(result["raw"])[:1500], language="json")
            st.stop()

        # Strip prompt echo
        raw_output = result["output"]
        answer_start = "Answer:"
        llm_response = raw_output.split(answer_start, 1)[-1].strip() if answer_start in raw_output else raw_output.strip()

        # Highlight MPEP citations
        llm_response = re.sub(r"(MPEP[\s-]*\d+|§[\s]*\d+(\.\d+)*)", r"**\1**", llm_response)

        # Save state
        st.session_state["last_query"] = query
        st.session_state["last_answer"] = llm_response
        st.session_state["history"].append({
            "query": query,
            "answer": llm_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    # --- Display Final Answer ---
    st.markdown("## 💡 AI Answer")
    st.markdown(f"""
    <div style='background: #eef6ff; padding: 1rem; border-left: 4px solid #007acc; border-radius: 6px;'>
        {llm_response}
    </div>
    """, unsafe_allow_html=True)

    # --- Source Evidence ---
    st.markdown("## 📚 Source Paragraph(s)")
    for chap, para, score in top_matches:
        with st.expander(f"{chap} — Match Score: {score:.2f}", expanded=False):
            st.code(para.strip()[:1500])


# === Part 8: Rating + History Tracker ===

# --- Rating Section ---
if st.session_state["last_answer"]:
    st.markdown("### ⭐ Rate This Answer")
    rating = st.slider("How helpful was this response?", 1, 5, 3)
    if rating:
        st.success("✅ Thanks for your feedback!")

# --- Session History ---
st.markdown("### 🕘 Previous Questions")
if st.session_state["history"]:
    for i, entry in enumerate(reversed(st.session_state["history"][-3:]), 1):
        with st.expander(f"{i}. {entry['query']} ({entry['timestamp']})"):
            st.markdown(entry["answer"])
else:
    st.info("Ask your first question to see history here.")

# === Part 9: Export Answer ===

def generate_download(text, filename, filetype):
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/{filetype};base64,{b64}" download="{filename}">📥 Download as .{filetype}</a>'
    return href

if st.session_state["last_query"] and st.session_state["last_answer"]:
    st.markdown("### 📁 Export This Response")

    query = st.session_state["last_query"]
    answer = st.session_state["last_answer"]
    now = datetime.now().strftime("%Y%m%d_%H%M")

    export_txt = f"Question: {query}\n\nAnswer:\n{answer}"
    export_md = f"### Question\n{query}\n\n### Answer\n{answer}"

    st.markdown(generate_download(export_txt, f"mpe_edge_answer_{now}.txt", "txt"), unsafe_allow_html=True)
    st.markdown(generate_download(export_md, f"mpe_edge_answer_{now}.md", "markdown"), unsafe_allow_html=True)

# === Part 10: Performance Optimizations ===

@st.cache_data(show_spinner=False)
def cache_embeddings(text_list):
    return model.encode(text_list, convert_to_tensor=True)

def get_top_matches_optimized(query, chapter_texts, top_k=1):
    results = []
    query_embedding = model.encode(query, convert_to_tensor=True)

    for chapter, text in chapter_texts.items():
        paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        if not paras:
            continue
        para_embeddings = cache_embeddings(paras)
        hits = util.semantic_search(query_embedding, para_embeddings, top_k=top_k)[0]
        for hit in hits:
            para = paras[hit["corpus_id"]]
            results.append((chapter, para, hit["score"]))

    return sorted(results, key=lambda x: -x[2])
