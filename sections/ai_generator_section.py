import streamlit as st

from core.languages import (
    normalize_languages,
    translations_to_map,
)
from core.settings import PROMPT_LIBRARY_FILE
from core.auth import current_user
from services.ai_service import (
    generate_questionnaire,
)
from services.geography_service import (
    geography_code,
    translate_geography_labels,
)
from services.xlsform_service import (
    build_xlsform,
)
from services.usage_service import (
    format_next_available,
    get_usage,
    record_successful_generation,
)


READY_PROMPT = (
    "Create a field-ready school monitoring XLSForm "
    "for ODK / Kobo. Include school identification, "
    "visit date, attendance, infrastructure, teacher "
    "availability, classroom observations, sanitation, "
    "digital facilities, safety, GPS, photographs, "
    "mandatory validation rules and relevant skip logic. "
    "Group questions into logical sections and use stable, "
    "analysis-friendly variable names."
)


def render_ai_generator(
    languages,
    india_geography,
    default_model,
):
    if "ai_requirement" not in st.session_state:
        st.session_state[
            "ai_requirement"
        ] = ""

    def use_ready_prompt():
        st.session_state[
            "ai_requirement"
        ] = READY_PROMPT

    platform = (
        "ODK / KoboToolbox XLSForm"
    )

    user = current_user() or {}
    username = str(user.get("username", "")).strip().lower()
    display_name = str(user.get("display_name", username)).strip()
    team = str(user.get("team", "")).strip()
    daily_limit = int(user.get("ai_daily_limit", 5))

    usage_error = None
    try:
        usage = get_usage(
            username=username,
            daily_limit=daily_limit,
        )
    except Exception as exc:
        usage_error = str(exc)
        # Fail closed so a broken ledger cannot create untracked AI usage.
        usage = {
            "limit": daily_limit,
            "used": 0,
            "remaining": 0,
            "allowed": False,
            "next_available_at": None,
            "window_hours": 24,
        }

    # ========================================================
    # ONE LARGE AI GENERATOR CONTAINER
    # ========================================================
    with st.container(border=True):
        st.markdown(
            """
            <div style="
                text-align:center;
                margin-bottom:14px;
            ">
                <h2 style="
                    margin-bottom:6px;
                ">
                    AI Data Collection Tool Generator
                </h2>
                <p style="
                    color:#64748b;
                    margin-top:0;
                ">
                    Build a field-ready ODK / KoboToolbox
                    XLSForm using your own requirement or
                    one of the ready-to-use prompts.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()

        with st.container(border=True):
            st.markdown("### AI Generation Usage")

            if usage_error:
                st.error(
                    "AI usage tracking is temporarily unavailable. "
                    "Generation is disabled to protect the usage limit."
                )
            else:
                st.markdown(
                    f"**{display_name or username}** — "
                    f"**{usage['used']} / {usage['limit']}** "
                    "generations used in the last 24 hours"
                )

                if usage["allowed"]:
                    st.caption(
                        f"{usage['remaining']} generation"
                        f"{'' if usage['remaining'] == 1 else 's'} remaining."
                    )
                else:
                    next_time = format_next_available(
                        usage.get("next_available_at")
                    )
                    if next_time:
                        st.warning(
                            "AI generation limit reached. "
                            f"One generation becomes available after "
                            f"{next_time} IST."
                        )
                    else:
                        st.warning("AI generation limit reached.")

        # ====================================================
        # ROW 1: PROMPT | READY PROMPT | PROMPT LIBRARY
        # ====================================================
        (
            prompt_box,
            ready_box,
            library_box,
        ) = st.columns(
            [1.35, 1.05, .90],
            gap="large",
        )

        # ----------------------------------------------------
        # BOX 1
        # ----------------------------------------------------
        with prompt_box:
            with st.container(border=True):
                st.markdown(
                    "### 1. Your Prompt"
                )

                st.caption(
                    "Describe the data collection "
                    "tool you want to generate."
                )

                st.text_area(
                    (
                        "Your data collection "
                        "requirement"
                    ),
                    key="ai_requirement",
                    placeholder=(
                        "Example: Create a school "
                        "monitoring form with school "
                        "profile, attendance, "
                        "infrastructure, GPS and "
                        "validation rules."
                    ),
                    height=250,
                    label_visibility="collapsed",
                )

        # ----------------------------------------------------
        # BOX 2
        # ----------------------------------------------------
        with ready_box:
            with st.container(border=True):
                st.markdown(
                    "### 2. Ready-to-Use Prompt"
                )

                st.caption(
                    "Use this example directly "
                    "in Box 1."
                )

                st.info(
                    "**School Monitoring Visit**\n\n"
                    + READY_PROMPT
                )

                st.button(
                    "Use This Prompt",
                    on_click=use_ready_prompt,
                    use_container_width=True,
                    key="use_ready_prompt",
                )

        # ----------------------------------------------------
        # BOX 3
        # ----------------------------------------------------
        with library_box:
            with st.container(border=True):
                st.markdown(
                    "### 3. Prompt Library"
                )

                st.caption(
                    "Download 10 ready-to-use "
                    "ODK / Kobo prompt templates."
                )

                st.markdown(
                    """
                    Includes prompts for:

                    - Household Survey
                    - School Monitoring
                    - CLC Monitoring
                    - House Visit
                    - Training Feedback
                    - Baseline / Endline
                    - Health Camp
                    - Field Checklist
                    """
                )

                if PROMPT_LIBRARY_FILE.exists():
                    with open(
                        PROMPT_LIBRARY_FILE,
                        "rb",
                    ) as prompt_file:
                        st.download_button(
                            (
                                "📘 Download "
                                "10 Prompt Templates"
                            ),
                            data=prompt_file.read(),
                            file_name=(
                                "ODK_Kobo_XLSForm_"
                                "AI_Prompts.docx"
                            ),
                            mime=(
                                "application/vnd."
                                "openxmlformats-officedocument."
                                "wordprocessingml.document"
                            ),
                            use_container_width=True,
                        )
                else:
                    st.warning(
                        "Prompt library file not "
                        "found in resources folder."
                    )

        st.markdown("")

        # ====================================================
        # ROW 2: LANGUAGE | GEOGRAPHY
        # ====================================================
        (
            language_box,
            geography_box,
        ) = st.columns(
            2,
            gap="large",
        )

        # ----------------------------------------------------
        # BOX 4
        # ----------------------------------------------------
        with language_box:
            with st.container(border=True):
                st.markdown(
                    "### 4. Language Settings"
                )

                st.caption(
                    "English is always the "
                    "primary/default language."
                )

                language_count = st.selectbox(
                    (
                        "Number of questionnaire "
                        "languages"
                    ),
                    options=[1, 2, 3, 4],
                    index=0,
                    format_func=lambda value: (
                        f"{value} Language"
                        if value == 1
                        else f"{value} Languages"
                    ),
                    key="language_count",
                )

                additional_options = [
                    language
                    for language in languages
                    if language != "English"
                ]

                if language_count > 1:
                    additional_languages = (
                        st.multiselect(
                            "Additional languages",
                            options=(
                                additional_options
                            ),
                            max_selections=(
                                language_count - 1
                            ),
                            placeholder=(
                                "Select additional "
                                "languages"
                            ),
                            key=(
                                "additional_languages"
                            ),
                        )
                    )
                else:
                    additional_languages = []

                language_names = (
                    normalize_languages(
                        ["English"]
                        + additional_languages
                    )
                )

                language_valid = (
                    len(language_names)
                    == language_count
                )

                if language_valid:
                    st.success(
                        "Selected: "
                        + " • ".join(
                            language_names
                        )
                    )
                else:
                    remaining = (
                        language_count
                        - len(language_names)
                    )

                    st.info(
                        f"Select {remaining} more "
                        f"{'language' if remaining == 1 else 'languages'}."
                    )

        # ----------------------------------------------------
        # BOX 5
        # ----------------------------------------------------
        with geography_box:
            with st.container(border=True):
                st.markdown(
                    "### 5. Geography Selection"
                )

                st.caption(
                    "Optionally add State/UT "
                    "and District cascading."
                )

                include_geography = (
                    st.checkbox(
                        (
                            "Include State/UT "
                            "and District"
                        ),
                        value=False,
                        key="include_geography",
                    )
                )

                selected_states = []
                selected_districts = {}
                geography_valid = True

                if include_geography:
                    if not india_geography:
                        st.error(
                            "India geography master "
                            "is unavailable."
                        )
                        geography_valid = False
                    else:
                        selected_states = (
                            st.multiselect(
                                (
                                    "State / "
                                    "Union Territory"
                                ),
                                options=list(
                                    india_geography.keys()
                                ),
                                placeholder=(
                                    "Select one or more "
                                    "States / UTs"
                                ),
                                key="selected_states",
                            )
                        )

                        if not selected_states:
                            geography_valid = False

                            st.info(
                                "Select at least one "
                                "State / Union Territory."
                            )

                        for state in selected_states:
                            all_districts = (
                                india_geography.get(
                                    state,
                                    [],
                                )
                            )

                            with st.expander(
                                (
                                    f"{state} — "
                                    "Districts"
                                ),
                                expanded=True,
                            ):
                                select_all = (
                                    st.checkbox(
                                        (
                                            "Select all "
                                            "districts in "
                                            f"{state}"
                                        ),
                                        key=(
                                            "select_all_"
                                            + geography_code(
                                                state
                                            )
                                        ),
                                    )
                                )

                                selected_districts[
                                    state
                                ] = st.multiselect(
                                    "Districts",
                                    options=(
                                        all_districts
                                    ),
                                    default=(
                                        all_districts
                                        if select_all
                                        else []
                                    ),
                                    key=(
                                        "districts_"
                                        + geography_code(
                                            state
                                        )
                                    ),
                                    label_visibility=(
                                        "collapsed"
                                    ),
                                )

                                if not selected_districts[
                                    state
                                ]:
                                    geography_valid = (
                                        False
                                    )

                        if (
                            selected_states
                            and geography_valid
                        ):
                            total_districts = sum(
                                len(values)
                                for values
                                in selected_districts.values()
                            )

                            st.success(
                                f"{len(selected_states)} "
                                f"{'State/UT' if len(selected_states) == 1 else 'States/UTs'} "
                                f"and {total_districts} "
                                f"{'district' if total_districts == 1 else 'districts'} selected."
                            )

        st.divider()

        generate_enabled = (
            language_valid
            and geography_valid
            and usage["allowed"]
            and not usage_error
        )

        generate_button = st.button(
            "✨ Generate Data Collection Tool",
            type="primary",
            use_container_width=True,
            disabled=not generate_enabled,
            key="generate_ai_xlsform",
        )

    requirement = st.session_state.get(
        "ai_requirement",
        "",
    ).strip()

    if generate_button:
        if not requirement:
            st.warning(
                "Please describe the data "
                "collection tool you need."
            )
        else:
            try:
                with st.spinner(
                    (
                        "Generating questionnaire "
                        "structure..."
                    )
                ):
                    questionnaire = (
                        generate_questionnaire(
                            requirement=requirement,
                            language_names=language_names,
                            platform=platform,
                            model_name=default_model,
                        )
                    )

                    geography_translations = {}

                    if selected_states:
                        geography_translations = (
                            translate_geography_labels(
                                selected_states=(
                                    selected_states
                                ),
                                selected_districts=(
                                    selected_districts
                                ),
                                language_names=(
                                    language_names
                                ),
                                model_name=(
                                    default_model
                                ),
                            )
                        )

                record_successful_generation(
                    username=username,
                    display_name=display_name,
                    team=team,
                )

                st.session_state[
                    "generated_questionnaire"
                ] = questionnaire

                st.session_state[
                    "generated_language_option"
                ] = language_names

                st.session_state[
                    "generated_states"
                ] = selected_states

                st.session_state[
                    "generated_districts"
                ] = selected_districts

                st.session_state[
                    "generated_geography_translations"
                ] = geography_translations

                updated_used = min(
                    usage["used"] + 1,
                    usage["limit"],
                )
                updated_remaining = max(
                    0,
                    usage["limit"] - updated_used,
                )

                st.success(
                    "Questionnaire draft generated successfully. "
                    f"AI usage: {updated_used} / {usage['limit']} used; "
                    f"{updated_remaining} remaining."
                )

            except Exception as exc:
                st.error(
                    str(exc)
                )

    render_generated_questionnaire()


def render_generated_questionnaire():
    questionnaire = st.session_state.get(
        "generated_questionnaire"
    )

    if not questionnaire:
        return

    st.subheader(
        questionnaire.get(
            "title",
            "Generated Questionnaire",
        )
    )

    generated_states = (
        st.session_state.get(
            "generated_states",
            [],
        )
    )

    generated_districts = (
        st.session_state.get(
            "generated_districts",
            {},
        )
    )

    if generated_states:
        total_districts = sum(
            len(values)
            for values
            in generated_districts.values()
        )

        st.caption(
            f"Included geography: "
            f"{len(generated_states)} "
            f"{'State/UT' if len(generated_states) == 1 else 'States/UTs'} "
            f"• {total_districts} "
            f"{'district' if total_districts == 1 else 'districts'}"
        )

    preview_rows = []

    for number, question in enumerate(
        questionnaire.get(
            "questions",
            [],
        ),
        start=1,
    ):
        preview_rows.append({
            "No.": number,
            "Variable": question.get(
                "name",
                "",
            ),
            "Type": question.get(
                "type",
                "",
            ),
            "Question": (
                translations_to_map(
                    question.get(
                        "labels",
                        [],
                    )
                ).get(
                    questionnaire.get(
                        "default_language",
                        "English",
                    ),
                    "",
                )
            ),
            "Required": (
                "Yes"
                if question.get(
                    "required"
                )
                else "No"
            ),
        })

    if preview_rows:
        st.dataframe(
            preview_rows,
            use_container_width=True,
            hide_index=True,
        )

    excel_bytes = build_xlsform(
        questionnaire,
        selected_states=(
            st.session_state.get(
                "generated_states",
                [],
            )
        ),
        selected_districts=(
            st.session_state.get(
                "generated_districts",
                {},
            )
        ),
        geography_translations=(
            st.session_state.get(
                "generated_geography_translations",
                {},
            )
        ),
    )

    st.download_button(
        "Download XLSForm Excel",
        data=excel_bytes,
        file_name=(
            f"{questionnaire.get('form_id', 'ai_generated_form')}.xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )

    with st.expander(
        "View generated JSON"
    ):
        st.json(
            questionnaire
        )
