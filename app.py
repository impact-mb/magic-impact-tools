import html
import io
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Magic Impact Tools",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
TOOLS_FILE = BASE_DIR / "tools.json"
LOGO_FILE = BASE_DIR / "images" / "magicbus_logo.png"
LANGUAGES_FILE = BASE_DIR / "config" / "languages.json"
MODELS_FILE = BASE_DIR / "config" / "models.json"
SYSTEM_PROMPT_FILE = BASE_DIR / "config" / "system_prompt.txt"
INDIA_TZ = ZoneInfo("Asia/Kolkata")

PROMPT_TEMPLATE_FILE = (
    BASE_DIR
    / "resources"
    / "ODK_Kobo_XLSForm_AI_Prompts.docx"
)

CATEGORY_ORDER = [
    "Dashboards",
    "Analytics",
    "Validation",
    "Data Quality",
    "Utilities",
    "Reports",
    "Donor Reports",
    "AI Data Collection",
]


LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Bangla": "bn",
    "Tamil": "ta",
    "Marathi": "mr",
    "Assamese": "as",
    "Telugu": "te",
    "Kannada": "kn",
    "Malayalam": "ml",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "Odia": "or",
    "Urdu": "ur",
    "Nepali": "ne",
}


def normalize_languages(language_names):
    """Return unique questionnaire languages with English first."""
    cleaned = []
    for language in language_names or []:
        language = str(language).strip()
        if language and language not in cleaned:
            cleaned.append(language)

    cleaned = [language for language in cleaned if language != "English"]
    return ["English"] + cleaned


def language_column(language_name: str) -> str:
    code = LANGUAGE_CODES.get(language_name)
    return f"{language_name} ({code})" if code else language_name


def translations_to_map(items):
    result = {}
    for item in items or []:
        if isinstance(item, dict):
            language = str(item.get("language", "")).strip()
            text = str(item.get("text", "")).strip()
            if language and text:
                result[language] = text
    return result

STATUS_STYLES = {
    "Live": ("●", "status-live"),
    "Under Maintenance": ("●", "status-maintenance"),
    "Offline": ("●", "status-offline"),
    "Coming Soon": ("●", "status-coming"),
}


@st.cache_data
def load_tools():
    return json.loads(TOOLS_FILE.read_text(encoding="utf-8"))


@st.cache_data
def load_languages():
    if not LANGUAGES_FILE.exists():
        return ["English", "Hindi", "Assamese", "Bangla", "Odia", "Gujarati", "Marathi", "Telugu", "Kannada", "Malayalam", "Tamil", "Punjabi", "Urdu"]
    values = json.loads(LANGUAGES_FILE.read_text(encoding="utf-8"))
    if not isinstance(values, list):
        raise ValueError("config/languages.json must contain a JSON list.")
    languages = [str(value).strip() for value in values if str(value).strip()]
    if not languages:
        raise ValueError("config/languages.json does not contain any languages.")
    return languages


@st.cache_data
def load_model_config():
    fallback = {
        "default_model": "gemini-flash-latest",
        "available_models": ["gemini-flash-latest"],
    }
    if not MODELS_FILE.exists():
        return fallback
    config = json.loads(MODELS_FILE.read_text(encoding="utf-8"))
    default_model = str(config.get("default_model", fallback["default_model"])).strip()
    available_models = [
        str(model).strip()
        for model in config.get("available_models", [])
        if str(model).strip()
    ]
    if default_model not in available_models:
        available_models.insert(0, default_model)
    return {
        "default_model": default_model,
        "available_models": available_models,
    }


@st.cache_data
def load_system_prompt():
    if not SYSTEM_PROMPT_FILE.exists():
        return (
            "Create a field-ready XLSForm questionnaire for {platform} in {language}. "
            "User requirement: {requirement}"
        )
    return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")


def safe_json_loads(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "", 1).replace("```", "").strip()
    return json.loads(cleaned)


def build_xlsform(questionnaire: dict) -> bytes:
    survey_rows = []
    choices_rows = []

    form_languages = questionnaire.get("languages") or ["English"]
    default_language = questionnaire.get("default_language") or form_languages[0]
    multilingual = len(form_languages) > 1

    def add_translated_columns(row, prefix, translations, fallback=""):
        translation_map = translations_to_map(translations)
        if multilingual:
            for language_name in form_languages:
                column_name = f"{prefix}::{language_column(language_name)}"
                row[column_name] = translation_map.get(language_name, fallback)
        else:
            row[prefix] = translation_map.get(form_languages[0], fallback)

    for qtype, name, default_text in [
        ("start", "start", "Start time"),
        ("end", "end", "End time"),
    ]:
        row = {
            "type": qtype,
            "name": name,
            "required": "",
            "relevant": "",
            "constraint": "",
        }
        add_translated_columns(
            row,
            "label",
            [{"language": language, "text": default_text} for language in form_languages],
            default_text,
        )
        survey_rows.append(row)

    for index, question in enumerate(questionnaire.get("questions", []), start=1):
        qtype = question.get("type", "text")
        name = question.get("name") or f"question_{index}"
        required = "yes" if question.get("required", False) else ""
        relevant = question.get("relevant", "")
        constraint = question.get("constraint", "")

        if qtype in {"select_one", "select_multiple"}:
            list_name = question.get("list_name") or f"list_{index}"
            xls_type = f"{qtype} {list_name}"
            for choice_index, choice in enumerate(question.get("choices", []), start=1):
                choice_name = choice.get("name", f"option_{choice_index}")
                choice_row = {"list_name": list_name, "name": choice_name}
                add_translated_columns(
                    choice_row,
                    "label",
                    choice.get("labels", []),
                    choice_name,
                )
                choices_rows.append(choice_row)
        else:
            xls_type = qtype

        survey_row = {
            "type": xls_type,
            "name": name,
            "required": required,
            "relevant": relevant,
            "constraint": constraint,
        }
        add_translated_columns(
            survey_row,
            "label",
            question.get("labels", []),
            f"Question {index}",
        )
        add_translated_columns(
            survey_row,
            "constraint_message",
            question.get("constraint_messages", []),
            "",
        )
        survey_rows.append(survey_row)

    settings_rows = [{
        "form_title": questionnaire.get("title", "AI Generated Data Collection Tool"),
        "form_id": questionnaire.get("form_id", "ai_generated_form"),
        "version": datetime.now(INDIA_TZ).strftime("%Y%m%d%H%M"),
        "default_language": language_column(default_language),
    }]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(survey_rows).to_excel(writer, sheet_name="survey", index=False)
        pd.DataFrame(choices_rows or [{"list_name": "", "name": "", "label": ""}]).to_excel(
            writer, sheet_name="choices", index=False
        )
        pd.DataFrame(settings_rows).to_excel(writer, sheet_name="settings", index=False)

    return output.getvalue()



def generate_questionnaire(
    requirement: str,
    language_names: list[str],
    platform: str,
    model_name: str,
):
    """Generate a structured questionnaire using Google Gemini."""

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
        os.getenv("GEMINI_API_KEY", ""),
    )

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to .streamlit/secrets.toml or Streamlit Cloud Secrets."
        )

    client = genai.Client(api_key=api_key)
    language_names = normalize_languages(language_names)

    questionnaire_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "form_id": {"type": "string"},
            "languages": {
                "type": "array",
                "items": {"type": "string"},
            },
            "default_language": {"type": "string"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "text", "integer", "decimal", "date",
                                "select_one", "select_multiple", "note",
                            ],
                        },
                        "name": {"type": "string"},
                        "labels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "language": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                                "required": ["language", "text"],
                            },
                        },
                        "required": {"type": "boolean"},
                        "list_name": {"type": "string"},
                        "choices": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "labels": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "language": {"type": "string"},
                                                "text": {"type": "string"},
                                            },
                                            "required": ["language", "text"],
                                        },
                                    },
                                },
                                "required": ["name", "labels"],
                            },
                        },
                        "relevant": {"type": "string"},
                        "constraint": {"type": "string"},
                        "constraint_messages": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "language": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                                "required": ["language", "text"],
                            },
                        },
                    },
                    "required": [
                        "type", "name", "labels", "required", "list_name",
                        "choices", "relevant", "constraint", "constraint_messages",
                    ],
                },
            },
        },
        "required": ["title", "form_id", "languages", "default_language", "questions"],
    }


    prompt_template = load_system_prompt()
    language_display = ", ".join(language_names)
    prompt = prompt_template.format(
    language=language_display,
    requirement=requirement,
    ) + f"\n\nExact output languages: {language_names}. " \
        "English is the primary and default language. " \
        "Every question label, choice label, and constraint message must include one translation for every listed language. " \
        "Use the exact language names in the JSON language fields. " \
        "Never combine translations from different languages into a single label value."


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
            raise RuntimeError("Gemini returned an empty response.")

        result = json.loads(response.text)
        result["languages"] = language_names
        result["default_language"] = language_names[0]
        return result

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Gemini returned an invalid questionnaire structure. Please try again."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"Gemini generation failed: {exc}") from exc


tools = load_tools()
languages = load_languages()
model_config = load_model_config()
default_model = model_config["default_model"]
available_models = model_config["available_models"]
st_autorefresh(interval=60_000, key="clock_refresh")
now = datetime.now(INDIA_TZ)

st.html(
    """
    <style>
    .stApp { background: #f6f8fc; }
    .block-container { max-width: 1450px; padding: 1.2rem 1rem 3rem; }

    .time-box {
        background: #ffffff;
        border: 1px solid #dbe4f0;
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 6px 18px rgba(15,23,42,.06);
    }
    .time-value { font-size: 1.55rem; font-weight: 850; color: #0f172a; }
    .time-label { color: #64748b; font-size: .78rem; margin-top: .25rem; }

    .main-title {
        text-align: center;
        padding: .25rem 1rem;
    }
    .main-title h1 {
        margin: 0;
        color: #0f172a;
        font-size: clamp(2rem, 4vw, 3.25rem);
        line-height: 1.1;
    }
    .main-title p {
        margin: .55rem auto .35rem;
        color: #475569;
        max-width: 780px;
        line-height: 1.55;
    }
    .current-date {
        display: inline-block;
        margin-top: .3rem;
        padding: .35rem .8rem;
        border-radius: 999px;
        background: #eff6ff;
        color: #1d4ed8;
        font-size: .82rem;
        font-weight: 750;
    }

    .logo-wrap {
        height: 110px;
        display: flex;
        justify-content: center;
        align-items: center;
        background: #ffffff;
        border: 1px solid #dbe4f0;
        border-radius: 16px;
        padding: .75rem;
        box-shadow: 0 6px 18px rgba(15,23,42,.06);
    }

    .section-wrap { margin-top: 2.1rem; }
    .section-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #dbe4f0;
        padding-bottom: .55rem;
        margin-bottom: 1rem;
    }
    .section-title { margin: 0; color: #0f172a; font-size: 1.4rem; }
    .section-count { color: #64748b; font-size: .82rem; }

    .tool-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0,1fr));
        gap: 1.1rem;
    }
    .tool-card, .tool-card-disabled {
        display: flex;
        flex-direction: column;
        min-height: 205px;
        padding: 1.3rem;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        color: #0f172a !important;
        text-decoration: none !important;
        box-shadow: 0 6px 18px rgba(15,23,42,.06);
    }
    .tool-card { transition: .18s ease; }
    .tool-card:hover {
        transform: translateY(-6px);
        border-color: #2563eb;
        box-shadow: 0 18px 35px rgba(37,99,235,.16);
    }
    .tool-card-disabled { opacity: .82; background: #f8fafc; }
    .card-top { display:flex; justify-content:space-between; margin-bottom:.8rem; }
    .status-pill {
        border-radius: 999px;
        padding: .3rem .55rem;
        font-size: .7rem;
        font-weight: 800;
    }
    .status-live { background:#ecfdf5; color:#047857; }
    .status-maintenance { background:#fffbeb; color:#b45309; }
    .status-offline { background:#fef2f2; color:#b91c1c; }
    .status-coming { background:#f1f5f9; color:#475569; }
    .tool-badge {
        width: fit-content;
        padding: .22rem .5rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #4338ca;
        font-size: .68rem;
        font-weight: 800;
        text-transform: uppercase;
    }
    .tool-name { font-size:1.12rem; font-weight:850; margin-bottom:.55rem; }
    .tool-description { color:#64748b; line-height:1.5; font-size:.91rem; }
    .tool-link, .tool-link-disabled { margin-top:auto; font-weight:800; font-size:.9rem; }
    .tool-link { color:#1d4ed8; }
    .tool-link-disabled { color:#64748b; }

    .ai-box {
        background: linear-gradient(135deg,#eef2ff,#f8fafc);
        border: 1px solid #c7d2fe;
        border-radius: 20px;
        padding: 1.3rem;
        margin-top: 2rem;
        text-align: center;
    }

    .ai-box h2 {
        margin: 0 0 .45rem 0;
        color: #0f172a;
    }

    .ai-box p {
        margin: 0 auto;
        max-width: 860px;
        color: #475569;
        line-height: 1.55;
    }

    .footer {
        margin-top: 3rem;
        padding: 1.4rem;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        color: #64748b;
        font-size: .84rem;
        line-height: 1.7;
    }

    @media(max-width:950px) {
        .tool-grid { grid-template-columns: repeat(2,minmax(0,1fr)); }
    }
    @media(max-width:650px) {
        .tool-grid { grid-template-columns: 1fr; }
        .tool-card,.tool-card-disabled { min-height:0; }
    }
    </style>
    """
)

left, center, right = st.columns([1, 3.2, 1])

with left:
    st.html(
        f"""
        <div class="time-box">
            <div class="time-value">{now.strftime("%I:%M %p")}</div>
            <div class="time-label">India Standard Time</div>
        </div>
        """
    )

with center:
    st.html(
        f"""
        <div class="main-title">
            <h1>Magic Impact Tools</h1>
            <p>One platform for reporting, analytics, validation, data quality, donor reporting, and digital utilities.</p>
            <div class="current-date">{now.strftime("%A, %d %B %Y")}</div>
        </div>
        """
    )

with right:
    if LOGO_FILE.exists():
        st.image(str(LOGO_FILE), use_container_width=True)
    else:
        st.html(
            """
            <div class="logo-wrap">
                <div style="text-align:center;color:#64748b;font-size:.8rem">
                    Add<br><strong>images/magicbus_logo.png</strong>
                </div>
            </div>
            """
        )

st.divider()

search_col, category_col, status_col = st.columns([2.2, 1, 1])
with search_col:
    query = st.text_input(
        "Search",
        placeholder="Search by tool, donor, category, or purpose...",
        label_visibility="collapsed",
    ).strip().lower()
with category_col:
    selected_category = st.selectbox(
        "Category",
        ["All Categories"] + CATEGORY_ORDER[:-1],
        label_visibility="collapsed",
    )
with status_col:
    selected_status = st.selectbox(
        "Status",
        ["All Statuses", "Live", "Coming Soon", "Under Maintenance", "Offline"],
        label_visibility="collapsed",
    )

filtered = [
    tool for tool in tools
    if (selected_category == "All Categories" or tool["category"] == selected_category)
    and (selected_status == "All Statuses" or tool["status"] == selected_status)
    and (
        not query
        or query in tool["name"].lower()
        or query in tool["category"].lower()
        or query in tool["description"].lower()
    )
]

for category in CATEGORY_ORDER[:-1]:
    category_tools = [tool for tool in filtered if tool["category"] == category]
    if not category_tools:
        continue

    st.html(
        f"""
        <section class="section-wrap">
            <div class="section-title-row">
                <h2 class="section-title">{html.escape(category)}</h2>
                <div class="section-count">{len(category_tools)} tools</div>
            </div>
        """
    )

    cards = []
    for tool in category_tools:
        dot, status_class = STATUS_STYLES.get(
            tool["status"], ("●", "status-coming")
        )
        badge = (
            f'<div class="tool-badge">{html.escape(tool["badge"])}</div>'
            if tool["badge"] else "<div></div>"
        )
        body = (
            '<div class="card-top">' +
            badge +
            f'<div class="status-pill {status_class}">{dot} {html.escape(tool["status"])}</div>' +
            '</div>' +
            f'<div class="tool-name">{html.escape(tool["name"])}</div>' +
            f'<div class="tool-description">{html.escape(tool["description"])}</div>'
        )

        if tool["url"].startswith(("https://", "http://")):
            cards.append(
                f'<a class="tool-card" href="{html.escape(tool["url"], quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">{body}'
                '<div class="tool-link">Open tool →</div></a>'
            )
        else:
            cards.append(
                f'<div class="tool-card-disabled">{body}'
                '<div class="tool-link-disabled">URL to be added</div></div>'
            )

    st.html('<div class="tool-grid">' + ''.join(cards) + '</div></section>')

st.html(
    """
    <div class="ai-box">
        <h2>AI Data Collection Tool Generator</h2>
        <p>
            Describe the survey or monitoring tool you need. The AI will generate
            structured questions and an XLSForm-compatible Excel draft.
        </p>
    </div>
    """
)

st.markdown(
    """
    <div style="
        text-align:center;
        margin-top:12px;
        margin-bottom:18px;
        color:#64748b;
        font-size:0.92rem;
    ">
        Not sure what to write?
        Refer to our ready-to-use ODK / Kobo questionnaire prompt templates.
    </div>
    """,
    unsafe_allow_html=True,
)

if PROMPT_TEMPLATE_FILE.exists():
    with open(PROMPT_TEMPLATE_FILE, "rb") as prompt_file:
        st.download_button(
            label="📘 Download Ready-to-Use Prompt Templates",
            data=prompt_file.read(),
            file_name="ODK_Kobo_XLSForm_AI_Prompts.docx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            use_container_width=True,
        )

requirement = st.text_area(
    "What data collection tool do you need?",
    placeholder=(
        "Example: Create a school monitoring form with school name, district, "
        "visit date, attendance, infrastructure checklist, facilitator feedback, "
        "GPS consent, and mandatory validation rules."
    ),
    height=160,
)

language_count_col = st.container()

with language_count_col:
    language_count = st.selectbox(
        "Number of questionnaire languages",
        options=[1, 2, 3, 4],
        index=0,
        format_func=lambda value: f"{value} Language" if value == 1 else f"{value} Languages",
        help="English is always included as the primary/default language.",
    )

platform = "ODK / KoboToolbox XLSForm"

st.caption("English is always the primary/default questionnaire language.")

additional_language_options = [
    language for language in languages
    if language != "English" and " and " not in language
]

if language_count > 1:
    additional_languages = st.multiselect(
        "Select additional questionnaire languages",
        options=additional_language_options,
        max_selections=language_count - 1,
        placeholder=f"Select {language_count - 1} additional language"
        if language_count == 2
        else f"Select {language_count - 1} additional languages",
        help=(
            f"Select exactly {language_count - 1} additional language"
            if language_count == 2
            else f"Select exactly {language_count - 1} additional languages"
        ),
    )
else:
    additional_languages = []

language_names = normalize_languages(["English"] + additional_languages)
language_selection_valid = len(language_names) == language_count

if language_count > 1 and not language_selection_valid:
    remaining = language_count - len(language_names)
    st.info(
        f"Please select {remaining} more "
        f"{'language' if remaining == 1 else 'languages'}."
    )

if language_selection_valid:
    st.caption("Selected languages: " + " • ".join(language_names))

generate_button = st.button(
    "Generate Data Collection Tool",
    type="primary",
    use_container_width=True,
    disabled=not language_selection_valid,
)

if generate_button:
    if not requirement.strip():
        st.warning("Please describe the data collection tool you need.")
    else:
        try:
            with st.spinner("Generating questionnaire structure..."):
                questionnaire = generate_questionnaire(
                    requirement=requirement,
                    language_names=language_names,
                    platform=platform,
                    model_name=default_model,
                )
            st.session_state["generated_questionnaire"] = questionnaire
            st.session_state["generated_language_option"] = language_names
            st.success("Questionnaire draft generated.")
        except Exception as exc:
            st.error(str(exc))

questionnaire = st.session_state.get("generated_questionnaire")
if questionnaire:
    st.subheader(questionnaire.get("title", "Generated Questionnaire"))

    preview_rows = []
    for number, question in enumerate(questionnaire.get("questions", []), start=1):
        preview_rows.append({
            "No.": number,
            "Variable": question.get("name", ""),
            "Type": question.get("type", ""),
            "Question": translations_to_map(question.get("labels", [])).get(
                questionnaire.get("default_language", "English"), ""
            ),
            "Required": "Yes" if question.get("required") else "No",
        })

    if preview_rows:
        st.dataframe(preview_rows, use_container_width=True, hide_index=True)

    excel_bytes = build_xlsform(questionnaire)
    st.download_button(
        "Download XLSForm Excel",
        data=excel_bytes,
        file_name=f'{questionnaire.get("form_id", "ai_generated_form")}.xlsx',
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    with st.expander("View generated JSON"):
        st.json(questionnaire)

st.html(
    """
    <footer class="footer">
        <strong>Magic Bus India Foundation</strong><br>
        Digital Transformation & Impact Systems<br>
        Version 2.0.0 · Developed by Narendra Shekhawat
    </footer>
    """
)
