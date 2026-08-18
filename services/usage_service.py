from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

from core.settings import INDIA_TZ


DEFAULT_WORKSHEET_NAME = "AI_Usage"
USAGE_WINDOW_HOURS = 24

USAGE_HEADERS = [
    "generated_at_utc",
    "generated_at_ist",
    "username",
    "display_name",
    "team",
    "status",
]


def _get_google_sheet_config():
    """
    Read Google Sheet configuration from Streamlit Secrets.

    Expected Streamlit Secrets:

    [usage_sheet]
    spreadsheet_id = "YOUR_GOOGLE_SHEET_ID"
    worksheet_name = "AI_Usage"

    [gcp_service_account]
    type = "service_account"
    project_id = "..."
    private_key_id = "..."
    private_key = \"\"\"-----BEGIN PRIVATE KEY-----
    ...
    -----END PRIVATE KEY-----
    \"\"\"
    client_email = "..."
    client_id = "..."
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "..."
    universe_domain = "googleapis.com"
    """

    try:
        usage_sheet = st.secrets["usage_sheet"]
    except KeyError as exc:
        raise RuntimeError(
            "Missing [usage_sheet] configuration in Streamlit Secrets."
        ) from exc

    spreadsheet_id = str(
        usage_sheet.get(
            "spreadsheet_id",
            "",
        )
    ).strip()

    worksheet_name = str(
        usage_sheet.get(
            "worksheet_name",
            DEFAULT_WORKSHEET_NAME,
        )
    ).strip()

    if not spreadsheet_id:
        raise RuntimeError(
            "usage_sheet.spreadsheet_id is not configured."
        )

    try:
        service_account = dict(
            st.secrets["gcp_service_account"]
        )
    except KeyError as exc:
        raise RuntimeError(
            "Missing [gcp_service_account] in Streamlit Secrets."
        ) from exc

    if not service_account.get("client_email"):
        raise RuntimeError(
            "gcp_service_account.client_email is missing."
        )

    if not service_account.get("private_key"):
        raise RuntimeError(
            "gcp_service_account.private_key is missing."
        )

    return (
        spreadsheet_id,
        worksheet_name,
        service_account,
    )


def _get_worksheet():
    """
    Open the persistent AI usage worksheet.

    The worksheet is created automatically if it does not exist.
    """

    try:
        import gspread
        from google.oauth2.service_account import (
            Credentials,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Google Sheet usage tracking requires gspread and google-auth. "
            "Add gspread>=6.1,<7.0 to requirements.txt."
        ) from exc

    (
        spreadsheet_id,
        worksheet_name,
        service_account,
    ) = _get_google_sheet_config()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        service_account,
        scopes=scopes,
    )

    client = gspread.authorize(
        credentials
    )

    spreadsheet = client.open_by_key(
        spreadsheet_id
    )

    try:
        worksheet = spreadsheet.worksheet(
            worksheet_name
        )
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=1000,
            cols=len(USAGE_HEADERS),
        )

    _ensure_headers(
        worksheet
    )

    return worksheet


def _ensure_headers(worksheet):
    """
    Ensure the usage worksheet starts with the expected headers.
    """

    first_row = worksheet.row_values(
        1
    )

    if first_row == USAGE_HEADERS:
        return

    if not first_row:
        worksheet.append_row(
            USAGE_HEADERS,
            value_input_option="RAW",
        )
        return

    # If the worksheet exists but does not have the expected structure,
    # stop rather than silently corrupting the ledger.
    raise RuntimeError(
        "The AI usage worksheet has unexpected column headers. "
        f"Expected: {USAGE_HEADERS}"
    )


def _parse_utc_timestamp(value: str):
    """
    Parse one UTC ISO timestamp stored in the usage ledger.
    """

    value = str(
        value
    ).strip()

    if not value:
        return None

    try:
        timestamp = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError:
        return None

    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(
            tzinfo=timezone.utc
        )

    return timestamp.astimezone(
        timezone.utc
    )


def _successful_events_for_user(
    username: str,
):
    """
    Return successful usage timestamps for one user.

    Only rows whose status is exactly 'success' count toward the limit.
    """

    username = str(
        username
    ).strip().lower()

    if not username:
        return []

    worksheet = _get_worksheet()

    rows = worksheet.get_all_records(
        expected_headers=USAGE_HEADERS
    )

    timestamps = []

    for row in rows:
        row_username = str(
            row.get(
                "username",
                "",
            )
        ).strip().lower()

        row_status = str(
            row.get(
                "status",
                "",
            )
        ).strip().lower()

        if (
            row_username != username
            or row_status != "success"
        ):
            continue

        timestamp = _parse_utc_timestamp(
            row.get(
                "generated_at_utc",
                "",
            )
        )

        if timestamp:
            timestamps.append(
                timestamp
            )

    timestamps.sort()

    return timestamps


def get_usage(
    username: str,
    daily_limit: int,
) -> dict:
    """
    Get rolling 24-hour AI usage for one user.

    Returns:
        {
            "limit": 10,
            "used": 3,
            "remaining": 7,
            "allowed": True,
            "next_available_at": None,
            "window_hours": 24
        }
    """

    try:
        daily_limit = int(
            daily_limit
        )
    except (TypeError, ValueError):
        daily_limit = 5

    daily_limit = max(
        daily_limit,
        0,
    )

    now_utc = datetime.now(
        timezone.utc
    )

    cutoff = now_utc - timedelta(
        hours=USAGE_WINDOW_HOURS
    )

    all_events = _successful_events_for_user(
        username
    )

    active_events = [
        timestamp
        for timestamp in all_events
        if timestamp > cutoff
    ]

    used = len(
        active_events
    )

    remaining = max(
        0,
        daily_limit - used,
    )

    allowed = (
        daily_limit > 0
        and used < daily_limit
    )

    next_available_at = None

    if (
        not allowed
        and active_events
        and daily_limit > 0
    ):
        # When the oldest active event falls outside the 24-hour
        # window, one generation becomes available again.
        next_available_utc = (
            active_events[0]
            + timedelta(
                hours=USAGE_WINDOW_HOURS
            )
        )

        next_available_at = (
            next_available_utc.astimezone(
                INDIA_TZ
            )
        )

    return {
        "limit": daily_limit,
        "used": used,
        "remaining": remaining,
        "allowed": allowed,
        "next_available_at": (
            next_available_at
        ),
        "window_hours": (
            USAGE_WINDOW_HOURS
        ),
    }


def can_generate(
    username: str,
    daily_limit: int,
) -> bool:
    """
    Convenience function: True when the user can make another AI generation.
    """

    return bool(
        get_usage(
            username=username,
            daily_limit=daily_limit,
        )["allowed"]
    )


def record_successful_generation(
    username: str,
    display_name: str = "",
    team: str = "",
):
    """
    Record ONE successful Gemini questionnaire generation.

    Call this function only AFTER generate_questionnaire()
    returns successfully.

    Do not call for:
    - Gemini 429
    - Gemini 503
    - invalid JSON
    - other failed AI requests
    - XLSForm download
    - geography selection
    """

    username = str(
        username
    ).strip().lower()

    if not username:
        raise ValueError(
            "username is required to record AI usage."
        )

    now_utc = datetime.now(
        timezone.utc
    )

    now_ist = now_utc.astimezone(
        INDIA_TZ
    )

    worksheet = _get_worksheet()

    worksheet.append_row(
        [
            now_utc.isoformat(
                timespec="seconds"
            ),
            now_ist.isoformat(
                timespec="seconds"
            ),
            username,
            str(
                display_name
            ).strip(),
            str(
                team
            ).strip(),
            "success",
        ],
        value_input_option="RAW",
    )


def format_next_available(
    next_available_at,
) -> str:
    """
    Format the next available generation time for display.
    """

    if not next_available_at:
        return ""

    return next_available_at.strftime(
        "%d %b %Y, %I:%M %p"
    )
