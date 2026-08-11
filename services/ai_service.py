import json
import os

import streamlit as st

from core.languages import normalize_languages
from core.loaders import load_system_prompt


def generate_questionnaire(
    requirement: str,
    language_names: list[str],
    platform: str,
    model_name: str,
):
    """Generate structured questionnaire JSON using Gemini."""
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "The google-genai package is not installed. "
            "Run: pip install google-genai"
        ) from exc

    api_key = st.secrets.get(
        "GEMINI_API_KEY",
        os.getenv(
            "GEMINI_API_KEY",
            "",
        ),
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to .streamlit/secrets.toml "
            "or Streamlit Cloud Secrets."
        )

    language_names = normalize_languages(
        language_names
    )

    questionnaire_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "form_id": {"type": "string"},
            "languages": {
                "type": "array",
                "items": {"type": "string"},
            },
            "default_language": {
                "type": "string"
            },
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "text",
                                "integer",
                                "decimal",
                                "date",
                                "select_one",
                                "select_multiple",
                                "note",
                            ],
                        },
                        "name": {
                            "type": "string"
                        },
                        "labels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "language": {
                                        "type": "string"
                                    },
                                    "text": {
                                        "type": "string"
                                    },
                                },
                                "required": [
                                    "language",
                                    "text",
                                ],
                            },
                        },
                        "required": {
                            "type": "boolean"
                        },
                        "list_name": {
                            "type": "string"
                        },
                        "choices": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string"
                                    },
                                    "labels": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "language": {
                                                    "type": "string"
                                                },
                                                "text": {
                                                    "type": "string"
                                                },
                                            },
                                            "required": [
                                                "language",
                                                "text",
                                            ],
                                        },
                                    },
                                },
                                "required": [
                                    "name",
                                    "labels",
                                ],
                            },
                        },
                        "relevant": {
                            "type": "string"
                        },
                        "constraint": {
                            "type": "string"
                        },
                        "choice_filter": {
                            "type": "string"
                        },
                        "constraint_messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "language": {
                                        "type": "string"
                                    },
                                    "text": {
                                        "type": "string"
                                    },
                                },
                                "required": [
                                    "language",
                                    "text",
                                ],
                            },
                        },
                    },
                    "required": [
                        "type",
                        "name",
                        "labels",
                        "required",
                        "list_name",
                        "choices",
                        "relevant",
                        "constraint",
                        "choice_filter",
                        "constraint_messages",
                    ],
                },
            },
        },
        "required": [
            "title",
            "form_id",
            "languages",
            "default_language",
            "questions",
        ],
    }

    prompt_template = load_system_prompt()

    prompt = prompt_template.format(
        platform=platform,
        language=", ".join(
            language_names
        ),
        requirement=requirement,
    ) + (
        f"\n\nExact output languages: "
        f"{language_names}. "
        "English is the primary/default language. "
        "Every question label, choice label, and "
        "constraint message must contain one "
        "translation per requested language. "
        "When questions reuse a choice list, reuse "
        "the same list_name and identical choice codes. "
        "Do not generate duplicate choice names "
        "within the same list."
    )

    client = genai.Client(
        api_key=api_key
    )

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=questionnaire_schema,
                temperature=0.2,
            ),
        )

        if not response.text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        result = json.loads(
            response.text
        )

        result["languages"] = (
            language_names
        )
        result["default_language"] = (
            language_names[0]
        )

        return result

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned an invalid questionnaire structure."
        ) from exc

    except Exception as exc:
        raise RuntimeError(
            f"Gemini generation failed: {exc}"
        ) from exc
