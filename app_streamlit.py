from __future__ import annotations

import requests
import streamlit as st


API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="SchemeSense AI", layout="wide")
st.title("🏛️ SchemeSense AI")
st.caption("Grounded Q&A and contradiction checks for Indian government scheme documents.")


def post_json(url: str, payload: dict) -> dict:
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
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
                        snippet = citation.get("snippet", "")

                        with st.expander(
                            f"📄 {source} | Page {page} | {chunk_id}",
                            expanded=(i == 1),
                        ):
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

