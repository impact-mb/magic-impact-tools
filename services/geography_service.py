import json
import re

import streamlit as st

from core.languages import normalize_languages
from core.settings import INDIA_GEOGRAPHY_FILE


# ============================================================
# LOAD INDIA GEOGRAPHY MASTER
# ============================================================

@st.cache_data
def load_india_geography():
    """
    Load India State/UT -> District master.

    The JSON structure contains:
    - English state name
    - State local language
    - State labels
    - District names
    - District labels

    The function returns a simple structure expected
    by the Streamlit UI:

        {
            "Rajasthan": ["Ajmer", "Jaipur", ...],
            "Tamil Nadu": ["Chennai", ...]
        }
    """

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

    states = geography.get("states", {})

    if not isinstance(states, dict):
        raise ValueError(
            "config/india_geography.json "
            "must contain a 'states' object."
        )

    cleaned = {}

    for state_data in states.values():

        if not isinstance(state_data, dict):
            continue

        state_name = str(
            state_data.get("name", "")
        ).strip()

        if not state_name:
            continue

        districts = state_data.get(
            "districts",
            {}
        )

        if not isinstance(districts, dict):
            continue

        district_names = []

        for district_data in districts.values():

            if not isinstance(
                district_data,
                dict,
            ):
                continue

            district_name = str(
                district_data.get(
                    "name",
                    "",
                )
            ).strip()

            if district_name:
                district_names.append(
                    district_name
                )

        if district_names:
            cleaned[state_name] = sorted(
                set(district_names)
            )

    return dict(
        sorted(cleaned.items())
    )


# ============================================================
# CREATE XLSFORM SAFE MACHINE CODE
# ============================================================

def geography_code(value: str) -> str:
    """
    Create an XLSForm-safe machine code.

    Example:

        Rajasthan
            -> rajasthan

        Gautam Buddha Nagar
            -> gautam_buddha_nagar

        Jammu & Kashmir
            -> jammu_and_kashmir

    Machine codes always remain English based.
    """

    value = str(value).strip().lower()

    value = value.replace(
        "&",
        " and ",
    )

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip("_")


# ============================================================
# BUILD GEOGRAPHY LOOKUP
# ============================================================

@st.cache_data
def _load_geography_label_lookup():
    """
    Build a lookup table containing translations already
    stored in india_geography.json.

    Example:

        {
            "Rajasthan": {
                "English": "Rajasthan",
                "Hindi": "राजस्थान"
            },

            "Jaipur": {
                "English": "Jaipur",
                "Hindi": "Jaipur"
            }
        }

    This avoids calling Gemini for geography translation.
    """

    if not INDIA_GEOGRAPHY_FILE.exists():
        return {}

    geography = json.loads(
        INDIA_GEOGRAPHY_FILE.read_text(
            encoding="utf-8"
        )
    )

    states = geography.get(
        "states",
        {}
    )

    lookup = {}

    for state_data in states.values():

        if not isinstance(
            state_data,
            dict,
        ):
            continue

        state_name = str(
            state_data.get(
                "name",
                "",
            )
        ).strip()

        if not state_name:
            continue

        # ------------------------------------------
        # STATE LABELS
        # ------------------------------------------

        state_labels = state_data.get(
            "labels",
            {},
        )

        lookup[state_name] = {
            "English": state_name
        }

        if isinstance(
            state_labels,
            dict,
        ):
            for language, label in (
                state_labels.items()
            ):

                label = str(
                    label
                ).strip()

                if label:
                    lookup[state_name][
                        str(language)
                    ] = label

        # ------------------------------------------
        # DISTRICT LABELS
        # ------------------------------------------

        districts = state_data.get(
            "districts",
            {},
        )

        if not isinstance(
            districts,
            dict,
        ):
            continue

        for district_data in (
            districts.values()
        ):

            if not isinstance(
                district_data,
                dict,
            ):
                continue

            district_name = str(
                district_data.get(
                    "name",
                    "",
                )
            ).strip()

            if not district_name:
                continue

            district_labels = (
                district_data.get(
                    "labels",
                    {},
                )
            )

            lookup[district_name] = {
                "English": district_name
            }

            if isinstance(
                district_labels,
                dict,
            ):

                for language, label in (
                    district_labels.items()
                ):

                    label = str(
                        label
                    ).strip()

                    if label:
                        lookup[
                            district_name
                        ][
                            str(language)
                        ] = label

    return lookup


# ============================================================
# TRANSLATE GEOGRAPHY LABELS
# ============================================================

def translate_geography_labels(
    selected_states,
    selected_districts,
    language_names,
    model_name=None,
):
    """
    Return translated geography labels using the local
    india_geography.json master.

    IMPORTANT:
    Gemini is NOT called by this function.

    This reduces:
    - Gemini API usage
    - token consumption
    - generation latency
    - 503 errors
    - translation inconsistency

    Machine-readable XLSForm codes remain English based.

    model_name is retained only for compatibility with
    existing application code.
    """

    language_names = normalize_languages(
        language_names
    )

    geography_names = []

    # --------------------------------------------------------
    # COLLECT SELECTED STATES AND DISTRICTS
    # --------------------------------------------------------

    for state in selected_states or []:

        if state not in geography_names:
            geography_names.append(
                state
            )

        districts = (
            selected_districts or {}
        ).get(
            state,
            [],
        )

        for district in districts:

            if district not in geography_names:
                geography_names.append(
                    district
                )

    # --------------------------------------------------------
    # LOAD LOCAL TRANSLATION LOOKUP
    # --------------------------------------------------------

    lookup = (
        _load_geography_label_lookup()
    )

    result = {}

    # --------------------------------------------------------
    # CREATE LANGUAGE LABELS
    # --------------------------------------------------------

    for name in geography_names:

        result[name] = {
            "English": name
        }

        stored_labels = lookup.get(
            name,
            {},
        )

        for language in language_names:

            if language == "English":
                result[name][
                    "English"
                ] = name

                continue

            translated_label = (
                stored_labels.get(
                    language
                )
            )

            # If reviewed translation exists,
            # use it.
            if translated_label:
                result[name][
                    language
                ] = translated_label

            # Otherwise safely fall back
            # to English.
            else:
                result[name][
                    language
                ] = name

    return result