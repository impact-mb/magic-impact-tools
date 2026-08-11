import json

import streamlit as st

from core.settings import (
    TOOLS_FILE,
    LANGUAGES_FILE,
    MODELS_FILE,
    SYSTEM_PROMPT_FILE,
)


@st.cache_data
def load_tools():
    return json.loads(
        TOOLS_FILE.read_text(encoding="utf-8")
    )


@st.cache_data
def load_languages():
    if not LANGUAGES_FILE.exists():
        return [
            "English",
            "Hindi",
            "Assamese",
            "Bengali",
            "Odia",
            "Gujarati",
            "Marathi",
            "Telugu",
            "Kannada",
            "Malayalam",
            "Tamil",
            "Punjabi",
            "Urdu",
        ]

    values = json.loads(
        LANGUAGES_FILE.read_text(encoding="utf-8")
    )

    if not isinstance(values, list):
        raise ValueError(
            "config/languages.json must contain a JSON list."
        )

    languages = [
        str(value).strip()
        for value in values
        if str(value).strip()
    ]

    if not languages:
        raise ValueError(
            "config/languages.json does not contain any languages."
        )

    return languages


@st.cache_data
def load_model_config():
    fallback = {
        "default_model": "gemini-flash-latest",
        "available_models": [
            "gemini-flash-latest"
        ],
    }

    if not MODELS_FILE.exists():
        return fallback

    config = json.loads(
        MODELS_FILE.read_text(encoding="utf-8")
    )

    default_model = str(
        config.get(
            "default_model",
            fallback["default_model"],
        )
    ).strip()

    available_models = [
        str(model).strip()
        for model in config.get(
            "available_models",
            [],
        )
        if str(model).strip()
    ]

    if default_model not in available_models:
        available_models.insert(
            0,
            default_model,
        )

    return {
        "default_model": default_model,
        "available_models": available_models,
    }


@st.cache_data
def load_system_prompt():
    if not SYSTEM_PROMPT_FILE.exists():
        return (
            "Create a field-ready XLSForm questionnaire "
            "for {platform} in {language}. "
            "User requirement: {requirement}"
        )

    return SYSTEM_PROMPT_FILE.read_text(
        encoding="utf-8"
    )
