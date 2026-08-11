from core.settings import LANGUAGE_CODES


def normalize_languages(language_names):
    """Return unique questionnaire languages with English first."""
    cleaned = []

    for language in language_names or []:
        language = str(language).strip()

        if language and language not in cleaned:
            cleaned.append(language)

    cleaned = [
        language
        for language in cleaned
        if language != "English"
    ]

    return ["English"] + cleaned


def language_column(language_name: str) -> str:
    code = LANGUAGE_CODES.get(language_name)

    return (
        f"{language_name} ({code})"
        if code
        else language_name
    )


def translations_to_map(items):
    result = {}

    for item in items or []:
        if isinstance(item, dict):
            language = str(
                item.get("language", "")
            ).strip()

            text = str(
                item.get("text", "")
            ).strip()

            if language and text:
                result[language] = text

    return result
