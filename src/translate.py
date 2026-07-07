from __future__ import annotations

from langdetect import detect, LangDetectException

from .llm import build_chat_model, translate_text


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def translate_query_to_english(query: str, model_name: str | None = None) -> tuple[str, str]:
    language = detect_language(query)
    if language == "en":
        return language, query
    model = build_chat_model(model_name=model_name or None, temperature=0.0) if model_name else build_chat_model(temperature=0.0)
    translated = translate_text(model, query, "English")
    return language, translated


def translate_answer_from_english(answer: str, target_language: str, model_name: str | None = None) -> str:
    if target_language == "en":
        return answer
    model = build_chat_model(model_name=model_name or None, temperature=0.0) if model_name else build_chat_model(temperature=0.0)
    return translate_text(model, answer, target_language)
