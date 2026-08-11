from datetime import datetime

import streamlit as st

from core.settings import (
    INDIA_TZ,
    LOGO_FILE,
)


def render_header():
    now = datetime.now(
        INDIA_TZ
    )

    left, center, right = st.columns(
        [1, 3.2, 1]
    )

    with left:
        st.html(
            f"""
            <div class="time-box">
                <div class="time-value">
                    {now.strftime("%I:%M %p")}
                </div>
                <div class="time-label">
                    India Standard Time
                </div>
            </div>
            """
        )

    with center:
        st.html(
            f"""
            <div class="main-title">
                <h1>Magic Impact Tools</h1>
                <p>
                    One platform for reporting,
                    analytics, validation, data quality,
                    donor reporting, and digital utilities.
                </p>
                <div class="current-date">
                    {now.strftime("%A, %d %B %Y")}
                </div>
            </div>
            """
        )

    with right:
        if LOGO_FILE.exists():
            st.image(
                str(LOGO_FILE),
                use_container_width=True,
            )
        else:
            st.html(
                """
                <div class="logo-wrap">
                    <div style="
                        text-align:center;
                        color:#64748b;
                        font-size:.8rem;
                    ">
                        Add<br>
                        <strong>
                            images/magicbus_logo.png
                        </strong>
                    </div>
                </div>
                """
            )

    st.divider()
