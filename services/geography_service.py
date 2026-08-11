import json
import os
import re

import streamlit as st

from core.languages import normalize_languages
from core.settings import INDIA_GEOGRAPHY_FILE


@st.cache_data
def load_india_geography():
    """Load State/UT -> District master."""
    if not INDIA_GEOGRAPHY_FILE.exists():
        return {}

    geography = json.loads(
        INDIA_GEOGRAPHY_FILE.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(geography, dict):
        raise ValueError(
            "config/india_geography.json "
            "must contain a JSON object."
        )

    cleaned = {}

    for state, districts in geography.items():
        state_name = str(state).strip()

        if (
            not state_name
            or not isinstance(districts, list)
        ):
            continue

        district_names = sorted({
            str(district).strip()
            for district in districts
            if str(district).strip()
        })

        if district_names:
            cleaned[state_name] = district_names

    return dict(sorted(cleaned.items()))


def geography_code(value: str) -> str:
    """Create an XLSForm-safe machine code."""
    value = str(value).strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )
    return value.strip("_")


def translate_geography_labels(
    selected_states,
    selected_districts,
    language_names,
    model_name,
):
    """
    Translate selected display labels only.
    Machine codes always remain English-based.
    """
    language_names = normalize_languages(
        language_names
    )

    geography_names = []

    for state in selected_states or []:
        if state not in geography_names:
            geography_names.append(state)

        for district in (
            selected_districts or {}
        ).get(state, []):
            if district not in geography_names:
                geography_names.append(district)

    result = {
        name: {"English": name}
        for name in geography_names
    }

    target_languages = [
        language
        for language in language_names
        if language != "English"
    ]

    if (
        not geography_names
        or not target_languages
    ):
        return result

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "The google-genai package is not installed."
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
            "GEMINI_API_KEY is not configured."
        )

    schema = {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {
                            "type": "string"
                        },
                        "translations": {
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
                        "source",
                        "translations",
                    ],
                },
            }
        },
        "required": ["items"],
    }

    prompt = f"""
Translate the following Indian State/UT
and District names for display in an
ODK/Kobo XLSForm.

Source names:
{geography_names}

Target languages:
{target_languages}

Rules:
- Preserve the exact English source value.
- Provide every requested language.
- Use standard native-script place names.
- Never change machine-readable codes.
- Return JSON only.
"""

    client = genai.Client(
        api_key=api_key
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema,
            temperature=0.0,
        ),
    )

    if not response.text:
        return result

    payload = json.loads(
        response.text
    )

    for item in payload.get("items", []):
        source = str(
            item.get("source", "")
        ).strip()

        if source not in result:
            continue

        for translation in item.get(
            "translations",
            [],
        ):
            language = str(
                translation.get(
                    "language",
                    "",
                )
            ).strip()

            translated_text = str(
                translation.get(
                    "text",
                    "",
                )
            ).strip()

            if (
                language in target_languages
                and translated_text
            ):
                result[source][language] = (
                    translated_text
                )

    for source in geography_names:
        for language in target_languages:
            result[source].setdefault(
                language,
                source,
            )

    return result
