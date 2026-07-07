from __future__ import annotations

import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="SchemeSense AI", layout="wide", initial_sidebar_state="collapsed")

# Inject custom CSS for premium UI
st.markdown("""
<style>
    /* Hide Streamlit default header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Gradient Title */
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Improve subheaders */
    h3 {
        color: #4ECDC4;
        font-weight: 600;
    }
    
    /* Style forms for a card-like appearance */
    [data-testid="stForm"] {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Make buttons slightly more rounded and prominent */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="font-weight:800; font-size:3rem; padding-bottom:0.5rem;">🏛️ <span class="gradient-text">SchemeSense AI</span></h1>', unsafe_allow_html=True)
st.markdown("""
**Ask questions about Indian Government Schemes using official documents with verifiable citations.**

<div style="font-size: 0.95rem; color: #4ECDC4; margin-top: 5px;">
✓ Grounded Answers &nbsp;&nbsp; ✓ Page Citations &nbsp;&nbsp; ✓ Hindi Support &nbsp;&nbsp; ✓ Hallucination Safe
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; margin-bottom: 5px;">
    <span style="background: rgba(78, 205, 196, 0.15); color: #4ECDC4; border: 1px solid rgba(78, 205, 196, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🌾 PM-KISAN</span>
    <span style="background: rgba(255, 107, 107, 0.15); color: #FF6B6B; border: 1px solid rgba(255, 107, 107, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🛠️ PM Vishwakarma</span>
    <span style="background: rgba(69, 183, 209, 0.15); color: #45B7D1; border: 1px solid rgba(69, 183, 209, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🏥 PM-JAY (Ayushman Bharat)</span>
    <span style="background: rgba(167, 139, 250, 0.15); color: #A78BFA; border: 1px solid rgba(167, 139, 250, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🩺 PM Arogya Mitra</span>
    <span style="background: rgba(249, 168, 37, 0.15); color: #F9A825; border: 1px solid rgba(249, 168, 37, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">💼 PM Mudra Yojana</span>
    <span style="background: rgba(102, 187, 106, 0.15); color: #66BB6A; border: 1px solid rgba(102, 187, 106, 0.4); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">🚀 Stand Up India</span>
</div>
""", unsafe_allow_html=True)

st.divider()


def post_json(url: str, payload: dict) -> dict:
    response = requests.post(url, json=payload, timeout=300)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"API Error {response.status_code}: {response.text}") from e
    return response.json()


def get_json(url: str) -> list | dict:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_document_list() -> list[str]:
    """Fetch available PDF names from the API."""
    try:
        docs = get_json(f"{API_BASE_URL}/documents")
        names = [d["filename"] for d in docs]
        return names if names else []
    except Exception:
        return []


ask_tab, contradict_tab = st.tabs(["📝 Ask", "⚖️ Contradict"])

with ask_tab:
    with st.form("ask_form"):
        query = st.text_area(
            "Ask a question",
            height=120,
            placeholder="e.g. What is the eligibility for PM-KISAN?",
        )
        ask_submitted = st.form_submit_button("Ask", type="primary")

    with st.expander("💡 Example Questions"):
        st.markdown("""
        - Who is eligible for PM Vishwakarma?
        - पीएम-किसान योजना का लाभ किन किसानों को मिलता है?
        - What are the major benefits provided under PM Vishwakarma?
        - पीएम विश्वकर्मा योजना के क्या लाभ हैं?
        - What documents are required for PM-KISAN?
        - पीएम विश्वकर्मा योजना के तहत कितना ऋण मिलता है?
        - Does Ayushman Bharat cover cancer treatment?
        - प्रधानमंत्री मुद्रा योजना के अंतर्गत अधिकतम कितना ऋण मिल सकता है?
        - Who is eligible to apply for a MUDRA loan?
        - What is the role of a Pradhan Mantri Arogya Mitra during beneficiary verification?
        - What is the maximum loan amount available under the MUDRA Loan Scheme?
        - What training is provided under PM Vishwakarma?
        """)


    if ask_submitted:
        if query.strip():
            with st.spinner("Searching documents and generating answer..."):
                try:
                    result = post_json(f"{API_BASE_URL}/ask", {"query": query})

                    st.subheader("Answer")
                    st.markdown(result["answer"])

                    lang = result["detected_language"]
                    if lang != "en":
                        st.info(f"🌐 Detected language: **{lang}**")
                    if result.get("translated_query"):
                        st.info(f"🔄 Translated query: {result['translated_query']}")

                    st.subheader("Citations")
                    for i, citation in enumerate(result.get("citations", []), start=1):
                        source = citation.get("source_file", "Unknown")
                        page = citation.get("document_page_number", "?")
                        chunk_id = citation.get("chunk_id", "")
                        title = citation.get("title")
                        author = citation.get("author")
                        subject = citation.get("subject")
                        creation_date = citation.get("creation_date")
                        notes = citation.get("extraction_notes")
                        snippet = citation.get("snippet", "")

                        with st.expander(f"📄 {source} | Page {page}", expanded=(i == 1)):
                            meta_md = ""
                            if title: meta_md += f"**Title:** {title}  \n"
                            if subject: meta_md += f"**Subject:** {subject}  \n"
                            if author: meta_md += f"**Author:** {author}  \n"
                            if creation_date: meta_md += f"**Date:** {creation_date}  \n"
                            if notes: meta_md += f"**Notes:** {notes}  \n"
                            
                            if meta_md:
                                st.info(meta_md)
                            
                            st.markdown(f"**Chunk ID:** `{chunk_id}`")
                            st.markdown(snippet)

                except requests.exceptions.ConnectionError:
                    st.error(
                        "⚠️ Cannot connect to the API server. "
                        "Make sure `uvicorn api.main:app --port 8000` is running."
                    )
                except Exception as exc:
                    st.error(f"Error: {exc}")
        else:
            st.warning("Enter a query first.")


with contradict_tab:
    doc_names = fetch_document_list()

    with st.form("contradict_form"):
        if not doc_names:
            st.warning(
                "Could not load document list from the API. "
                "Make sure the API server is running."
            )
            col1, col2 = st.columns(2)
            with col1:
                document_a = st.text_input("Document A", value="PM-KISSAN FAQ.pdf")
            with col2:
                document_b = st.text_input(
                    "Document B",
                    value="RevisedPM-KISANOperationalGuidelines(English).pdf",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                document_a = st.selectbox(
                    "Document A",
                    options=doc_names,
                    index=0,
                    key="doc_a",
                )
            with col2:
                default_b = min(1, len(doc_names) - 1)
                document_b = st.selectbox(
                    "Document B",
                    options=doc_names,
                    index=default_b,
                    key="doc_b",
                )

        topic = st.text_input("Topic", placeholder="e.g. eligibility, loan amount, benefits")
        submitted = st.form_submit_button("Compare documents", type="primary")

    if submitted:
        if not topic.strip():
            st.warning("Enter a topic to compare on.")
        elif document_a == document_b:
            st.warning("Please select two different documents.")
        else:
            with st.spinner("Analyzing documents for contradictions..."):
                try:
                    result = post_json(
                        f"{API_BASE_URL}/contradict",
                        {
                            "document_a": document_a,
                            "document_b": document_b,
                            "topic": topic,
                        },
                    )
                    st.subheader("Result")
                    st.markdown(result["result"])
                except requests.exceptions.ConnectionError:
                    st.error(
                        "⚠️ Cannot connect to the API server. "
                        "Make sure `uvicorn api.main:app --port 8000` is running."
                    )
                except Exception as exc:
                    st.error(f"Error: {exc}")

