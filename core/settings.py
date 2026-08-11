from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent

TOOLS_FILE = BASE_DIR / "tools.json"
LOGO_FILE = BASE_DIR / "images" / "magicbus_logo.png"

LANGUAGES_FILE = BASE_DIR / "config" / "languages.json"
MODELS_FILE = BASE_DIR / "config" / "models.json"
SYSTEM_PROMPT_FILE = BASE_DIR / "config" / "system_prompt.txt"
INDIA_GEOGRAPHY_FILE = BASE_DIR / "config" / "india_geography.json"

PROMPT_LIBRARY_FILE = (
    BASE_DIR
    / "resources"
    / "ODK_Kobo_XLSForm_AI_Prompts.docx"
)

INDIA_TZ = ZoneInfo("Asia/Kolkata")

CATEGORY_ORDER = [
    "Dashboards",
    "Analytics",
    "Validation",
    "Data Quality",
    "Utilities",
    "Reports",
    "Donor Reports",
]

LANGUAGE_CODES = {
    "English": "en",
    "Hindi": "hi",
    "Bengali": "bn",
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

STATUS_STYLES = {
    "Live": ("●", "status-live"),
    "Under Maintenance": ("●", "status-maintenance"),
    "Offline": ("●", "status-offline"),
    "Coming Soon": ("●", "status-coming"),
}
