import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core.auth import (
    require_login,
    render_user_sidebar,
)

from core.loaders import (
    load_languages,
    load_model_config,
    load_tools,
)
from sections.ai_generator_section import (
    render_ai_generator,
)
from sections.footer_section import (
    render_footer,
)
from sections.header_section import (
    render_header,
)
from sections.styles import (
    render_global_styles,
)
from sections.tools_section import (
    render_tools_section,
)
from services.geography_service import (
    load_india_geography,
)


st.set_page_config(
    page_title="Magic Impact Tools",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main():
    render_global_styles()

    # ========================================================
    # LOGIN / AUTHENTICATION
    # ========================================================
    user = require_login()
    render_user_sidebar(user)

    # ========================================================
    # LOAD APPLICATION DATA
    # ========================================================
    tools = load_tools()
    languages = load_languages()

    india_geography = (
        load_india_geography()
    )

    model_config = (
        load_model_config()
    )

    default_model = (
        model_config["default_model"]
    )

    # ========================================================
    # AUTO REFRESH
    # ========================================================
    st_autorefresh(
        interval=60_000,
        key="clock_refresh",
    )

    # ========================================================
    # PAGE SECTIONS
    # ========================================================
    render_header()

    # ========================================================
    # AI GENERATOR FIRST
    # ========================================================

    render_ai_generator(
        languages=languages,
        india_geography=india_geography,
        default_model=default_model,
    )

    render_tools_section(
        tools
    )

    render_footer()


if __name__ == "__main__":
    main()