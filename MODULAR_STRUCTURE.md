# Magic Impact Tools - Modular Structure

## Main file
- `app.py` - application entry point only.

## Core
- `core/settings.py` - paths, constants, timezone, language codes.
- `core/loaders.py` - JSON/config loaders.
- `core/languages.py` - multilingual helper functions.

## Services
- `services/ai_service.py` - Gemini questionnaire generation.
- `services/xlsform_service.py` - XLSForm Excel generation and choice de-duplication.
- `services/geography_service.py` - State/District master, codes, translations.

## UI Sections
- `sections/styles.py` - global CSS.
- `sections/header_section.py` - title, time, logo.
- `sections/tools_section.py` - search/filter/tool cards.
- `sections/ai_generator_section.py` - complete AI Data Collection Tool Generator.
- `sections/footer_section.py` - footer.

## Existing project folders/files to retain
- `config/`
- `images/`
- `resources/`
- `tools.json`
- `requirements.txt`
- `.streamlit/secrets.toml` locally / Streamlit Cloud secrets.

## Debugging map
- AI boxes/layout issue -> `sections/ai_generator_section.py`
- Tool cards/search issue -> `sections/tools_section.py`
- Header/logo/time issue -> `sections/header_section.py`
- Gemini/API issue -> `services/ai_service.py`
- Duplicate choices/XLSForm issue -> `services/xlsform_service.py`
- State/District issue -> `services/geography_service.py`
