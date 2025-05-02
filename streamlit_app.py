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
def auto_detect_chapters(question):
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

# === Part 5: UI Inputs and Query Options ===

st.markdown("### 🔍 Ask a Patent Law Question")

query = st.text_input("Enter your question", placeholder="e.g. What is a restriction requirement?")
model_name = st.selectbox("Choose a free AI model", list(available_models.keys()))

# 📘 Optional MPEP Index Reference
st.markdown("#### 📘 Need help finding the right chapter?")
st.markdown("[🔗 View the MPEP Subject Matter Index (PDF)](https://www.uspto.gov/web/offices/pac/mpep/mpep-9090-subject-matter-index.pdf)")

# Attempt auto-detect if no chapter is manually selected
suggested = auto_detect_chapters(query)
suggested_chapters = [suggested] if suggested else []


# Show auto-suggestion before selection
if suggested_chapters:
    st.markdown("💡 Suggested Chapters:")
    for chapter in suggested_chapters:
        st.markdown(f"- {chapter}")

# Let user manually override chapter selection
selected_chapters = st.multiselect(
    "Select up to 3 MPEP chapters to search",
    chapter_names,
    default=suggested_chapters[:1] if suggested_chapters else [],
    max_selections=3
)

# === Part 6: Model Query with Fallback Support ===

available_models = {
    "Mistral 7B (HF)": {"id": "huggingface/mistral-7b-instruct", "source": "huggingface"},
    "DeepSeek LLM (OR)": {"id": "deepseek-ai/deepseek-llm-7b", "source": "openrouter"},
    "OpenChat 7B (OR)": {"id": "openchat/openchat-7b", "source": "openrouter"},
    "Phi-3 (OR)": {"id": "microsoft/phi-3-medium-128k-instruct", "source": "openrouter"},
    "OLMo 2 (OR)": {"id": "allenai/OLMo-2-0425-1B-Instruct", "source": "openrouter"},
}

def query_llm(prompt, primary_model_name):
    primary = available_models[primary_model_name]
    fallback = available_models["Mistral 7B (HF)"] if primary_model_name != "Mistral 7B (HF)" else available_models["Phi-3 (OR)"]

    def call_model(model):
        source = model["source"]
        model_id = model["id"]

        try:
            if source == "huggingface":
                key = os.getenv("HUGGINGFACE_API_KEY")
                if not key:
                    return {"error": "Missing Hugging Face API key", "model": model_id}

                url = f"https://api-inference.huggingface.co/models/{model_id}"
                headers = {"Authorization": f"Bearer {key}"}
                payload = {"inputs": prompt, "parameters": {"max_new_tokens": 300}}

                response = requests.post(url, headers=headers, json=payload)
                raw = response.text

                try:
                    result = response.json()
                    if isinstance(result, list) and "generated_text" in result[0]:
                        return {"output": result[0]["generated_text"], "model": model_id, "source": source}
                    else:
                        return {"error": "Unexpected HF format", "raw": result, "model": model_id}
                except Exception as e:
                    return {"error": f"HF JSON decode failed: {str(e)}", "raw": raw, "model": model_id}

            elif source == "openrouter":
                key = os.getenv("OPENROUTER_API_KEY")
                if not key:
                    return {"error": "Missing OpenRouter API key", "model": model_id}

                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {"Authorization": f"Bearer {key}"}
                payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}

                response = requests.post(url, headers=headers, json=payload)
                raw = response.text

                try:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    return {"output": content, "model": model_id, "source": source}
                except Exception as e:
                    return {"error": f"OpenRouter JSON decode failed: {str(e)}", "raw": raw, "model": model_id}

        except Exception as e:
            return {"error": f"Unhandled request error: {str(e)}", "model": model_id}

    # --- Try primary
    result = call_model(primary)

    if "output" in result:
        return result

    # --- Fallback
    st.warning(f"⚠️ Primary model failed: {result.get('error', 'unknown error')}. Using fallback.")
    fallback_result = call_model(fallback)

    return fallback_result if "output" in fallback_result else {"error": "Both models failed", "raw": fallback_result}

# === Part 7: AI Execution and Output Display ===

if st.button("🔍 Search") and query and selected_chapters:
    with st.spinner("🔍 Retrieving relevant text and analyzing..."):
        chapter_texts = {c: get_text_from_pdf_url(chapter_to_url[c]) for c in selected_chapters}
        top_matches = get_top_matches(query, chapter_texts, top_k=1)

        if not top_matches:
            st.error("❌ No relevant text found in selected chapters.")
            st.stop()

        context = "\n---\n".join(f"{chap}\n{para}" for chap, para, _ in top_matches)
        prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer clearly and cite MPEP sections where applicable."

        # --- Call LLM with fallback + structured debug info ---
        llm_result = query_llm(prompt, model_name)

        # --- Debug Log: Always show raw structure for dev
        st.markdown("### 🐞 Debug Output (developer view)")
        st.json(llm_result)
        
        # --- Error Handling or Extract Response ---
        if "output" not in llm_result:
            st.error(f"❌ No usable LLM response.\n\n**Error**: {llm_result.get('error', 'Unknown error')}")
            if "raw" in llm_result:
                st.code(str(llm_result["raw"])[:1500], language="json")
            st.stop()
        
        llm_response = llm_result["output"]  # Safe extract
        
        # --- Save state
        st.session_state["last_query"] = query
        st.session_state["last_answer"] = llm_response
        st.session_state["history"].append({
            "query": query,
            "answer": llm_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        # --- Highlight citations ---
        llm_response = re.sub(r"(MPEP[\s-]*\d+|§[\s]*\d+(\.\d+)*)", r"**\1**", llm_response)
        
        # --- Render AI Answer ---
        st.markdown("## 💡 AI Answer")
        st.markdown(f"""
        <div style='background: #eef6ff; padding: 1rem; border-left: 4px solid #007acc; border-radius: 6px;'>
            {llm_response}
        </div>
        """, unsafe_allow_html=True)


        if not llm_response:
            st.error("❌ AI model failed to respond. Try a different model or retry.")
            st.stop()

        # Save in session state
        st.session_state["last_query"] = query
        st.session_state["last_answer"] = llm_response
        st.session_state["history"].append({
            "query": query,
            "answer": llm_response,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

    # --- Display Answer ---
    st.markdown("## 💡 AI Answer")
    llm_response = re.sub(r"(MPEP[\s-]*\d+|§[\s]*\d+(\.\d+)*)", r"**\1**", llm_response)  # highlight citations
    st.markdown(f"""
    <div style='background: #eef6ff; padding: 1rem; border-left: 4px solid #007acc; border-radius: 6px;'>
        {llm_response}
    </div>
    """, unsafe_allow_html=True)

    # --- Display Source Evidence ---
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
