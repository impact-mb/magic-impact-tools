import io
from datetime import datetime

import pandas as pd

from core.languages import (
    language_column,
    translations_to_map,
)
from core.settings import INDIA_TZ
from services.geography_service import geography_code


def build_xlsform(
    questionnaire: dict,
    selected_states=None,
    selected_districts=None,
    geography_translations=None,
) -> bytes:
    survey_rows = []
    choices_rows = []

    selected_states = (
        selected_states or []
    )
    selected_districts = (
        selected_districts or {}
    )
    geography_translations = (
        geography_translations or {}
    )

    form_languages = (
        questionnaire.get("languages")
        or ["English"]
    )

    default_language = (
        questionnaire.get(
            "default_language"
        )
        or form_languages[0]
    )

    multilingual = (
        len(form_languages) > 1
    )

    def add_translated_columns(
        row,
        prefix,
        translations,
        fallback="",
    ):
        translation_map = (
            translations_to_map(
                translations
            )
        )

        if multilingual:
            for language_name in form_languages:
                column_name = (
                    f"{prefix}::"
                    f"{language_column(language_name)}"
                )

                row[column_name] = (
                    translation_map.get(
                        language_name,
                        fallback,
                    )
                )
        else:
            row[prefix] = (
                translation_map.get(
                    form_languages[0],
                    fallback,
                )
            )

    # --------------------------------------------------------
    # Metadata questions
    # --------------------------------------------------------
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
            "choice_filter": "",
        }

        add_translated_columns(
            row,
            "label",
            [
                {
                    "language": language,
                    "text": default_text,
                }
                for language in form_languages
            ],
            default_text,
        )

        survey_rows.append(row)

    # --------------------------------------------------------
    # Geography
    # --------------------------------------------------------
    if selected_states:
        state_row = {
            "type": "select_one state_list",
            "name": "state",
            "required": "yes",
            "relevant": "",
            "constraint": "",
            "choice_filter": "",
        }

        add_translated_columns(
            state_row,
            "label",
            [
                {
                    "language": language,
                    "text": (
                        "State / Union Territory"
                    ),
                }
                for language in form_languages
            ],
            "State / Union Territory",
        )

        survey_rows.append(
            state_row
        )

        district_row = {
            "type": "select_one district_list",
            "name": "district",
            "required": "yes",
            "relevant": "",
            "constraint": "",
            "choice_filter": (
                "state_code=${state}"
            ),
        }

        add_translated_columns(
            district_row,
            "label",
            [
                {
                    "language": language,
                    "text": "District",
                }
                for language in form_languages
            ],
            "District",
        )

        survey_rows.append(
            district_row
        )

        for state in selected_states:
            state_code = geography_code(
                state
            )

            state_label_map = (
                geography_translations.get(
                    state,
                    {"English": state},
                )
            )

            state_choice = {
                "list_name": "state_list",
                "name": state_code,
                "state_code": "",
            }

            add_translated_columns(
                state_choice,
                "label",
                [
                    {
                        "language": language,
                        "text": state_label_map.get(
                            language,
                            state,
                        ),
                    }
                    for language in form_languages
                ],
                state,
            )

            choices_rows.append(
                state_choice
            )

            for district in (
                selected_districts.get(
                    state,
                    [],
                )
            ):
                district_label_map = (
                    geography_translations.get(
                        district,
                        {"English": district},
                    )
                )

                district_choice = {
                    "list_name": (
                        "district_list"
                    ),
                    "name": geography_code(
                        district
                    ),
                    "state_code": state_code,
                }

                add_translated_columns(
                    district_choice,
                    "label",
                    [
                        {
                            "language": language,
                            "text": (
                                district_label_map.get(
                                    language,
                                    district,
                                )
                            ),
                        }
                        for language in form_languages
                    ],
                    district,
                )

                choices_rows.append(
                    district_choice
                )

    # --------------------------------------------------------
    # AI-generated questions
    # --------------------------------------------------------
    existing_choice_keys = {
        (
            str(row.get(
                "list_name",
                "",
            )).strip(),
            str(row.get(
                "name",
                "",
            )).strip(),
        )
        for row in choices_rows
    }

    for index, question in enumerate(
        questionnaire.get(
            "questions",
            [],
        ),
        start=1,
    ):
        qtype = question.get(
            "type",
            "text",
        )

        name = (
            question.get("name")
            or f"question_{index}"
        )

        required = (
            "yes"
            if question.get(
                "required",
                False,
            )
            else ""
        )

        relevant = question.get(
            "relevant",
            "",
        )

        constraint = question.get(
            "constraint",
            "",
        )

        if qtype in {
            "select_one",
            "select_multiple",
        }:
            list_name = (
                question.get("list_name")
                or f"list_{index}"
            )

            xls_type = (
                f"{qtype} {list_name}"
            )

            for choice_index, choice in enumerate(
                question.get(
                    "choices",
                    [],
                ),
                start=1,
            ):
                choice_name = str(
                    choice.get(
                        "name",
                        f"option_{choice_index}",
                    )
                ).strip()

                choice_key = (
                    list_name,
                    choice_name,
                )

                if (
                    choice_key
                    in existing_choice_keys
                ):
                    continue

                choice_row = {
                    "list_name": list_name,
                    "name": choice_name,
                }

                add_translated_columns(
                    choice_row,
                    "label",
                    choice.get(
                        "labels",
                        [],
                    ),
                    choice_name,
                )

                choices_rows.append(
                    choice_row
                )

                existing_choice_keys.add(
                    choice_key
                )

        else:
            xls_type = qtype

        survey_row = {
            "type": xls_type,
            "name": name,
            "required": required,
            "relevant": relevant,
            "constraint": constraint,
            "choice_filter": (
                question.get(
                    "choice_filter",
                    "",
                )
            ),
        }

        add_translated_columns(
            survey_row,
            "label",
            question.get(
                "labels",
                [],
            ),
            f"Question {index}",
        )

        add_translated_columns(
            survey_row,
            "constraint_message",
            question.get(
                "constraint_messages",
                [],
            ),
            "",
        )

        survey_rows.append(
            survey_row
        )

    settings_rows = [{
        "form_title": questionnaire.get(
            "title",
            "AI Generated Data Collection Tool",
        ),
        "form_id": questionnaire.get(
            "form_id",
            "ai_generated_form",
        ),
        "version": datetime.now(
            INDIA_TZ
        ).strftime(
            "%Y%m%d%H%M"
        ),
        "default_language": (
            language_column(
                default_language
            )
        ),
    }]

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        pd.DataFrame(
            survey_rows
        ).to_excel(
            writer,
            sheet_name="survey",
            index=False,
        )

        pd.DataFrame(
            choices_rows
            or [{
                "list_name": "",
                "name": "",
                "label": "",
            }]
        ).to_excel(
            writer,
            sheet_name="choices",
            index=False,
        )

        pd.DataFrame(
            settings_rows
        ).to_excel(
            writer,
            sheet_name="settings",
            index=False,
        )

    return output.getvalue()
