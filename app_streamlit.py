from __future__ import annotations

import requests
import streamlit as st


st.set_page_config(page_title="SchemeSense AI", layout="wide")
st.title("SchemeSense AI")
st.caption("Grounded Q&A and contradiction checks for Indian government scheme documents.")


def post_json(url: str, payload: dict) -> dict:
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()


api_base_url = st.sidebar.text_input("API base URL", value="http://localhost:8000")

ask_tab, contradict_tab = st.tabs(["Ask", "Contradict"])

with ask_tab:
    query = st.text_area("Ask a question", height=120, placeholder="e.g. What is the eligibility for PM-KISAN?")
    if st.button("Ask", type="primary"):
        if query.strip():
            try:
                result = post_json(f"{api_base_url}/ask", {"query": query})
                st.subheader("Answer")
                st.write(result["answer"])
                st.caption(f"Detected language: {result['detected_language']}")
                if result.get("translated_query"):
                    st.info(f"Translated query: {result['translated_query']}")
                st.subheader("Citations")
                for citation in result.get("citations", []):
                    with st.expander(f"{citation.get('source_file')} | p.{citation.get('document_page_number')}"):
                        st.write(citation.get("snippet"))
            except Exception as exc:
                st.error(str(exc))
        else:
            st.warning("Enter a query first.")

with contradict_tab:
    col1, col2 = st.columns(2)
    with col1:
        document_a = st.text_input("Document A", value="PM-KISSAN FAQ")
    with col2:
        document_b = st.text_input("Document B", value="RevisedPM-KISANOperationalGuidelines(English)")
    topic = st.text_input("Topic", value="eligibility")
    if st.button("Compare documents"):
        try:
            result = post_json(f"{api_base_url}/contradict", {"document_a": document_a, "document_b": document_b, "topic": topic})
            st.subheader("Result")
            st.write(result["result"])
        except Exception as exc:
            st.error(str(exc))
