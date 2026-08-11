import html

import streamlit as st

from core.settings import (
    CATEGORY_ORDER,
    STATUS_STYLES,
)


def render_tools_section(tools):
    search_col, category_col, status_col = (
        st.columns([2.2, 1, 1])
    )

    with search_col:
        query = st.text_input(
            "Search",
            placeholder=(
                "Search by tool, donor, "
                "category, or purpose..."
            ),
            label_visibility="collapsed",
        ).strip().lower()

    with category_col:
        selected_category = st.selectbox(
            "Category",
            ["All Categories"] + CATEGORY_ORDER,
            label_visibility="collapsed",
        )

    with status_col:
        selected_status = st.selectbox(
            "Status",
            [
                "All Statuses",
                "Live",
                "Coming Soon",
                "Under Maintenance",
                "Offline",
            ],
            label_visibility="collapsed",
        )

    filtered = [
        tool
        for tool in tools
        if (
            selected_category == "All Categories"
            or tool["category"] == selected_category
        )
        and (
            selected_status == "All Statuses"
            or tool["status"] == selected_status
        )
        and (
            not query
            or query in tool["name"].lower()
            or query in tool["category"].lower()
            or query in tool["description"].lower()
        )
    ]

    for category in CATEGORY_ORDER:
        category_tools = [
            tool
            for tool in filtered
            if tool["category"] == category
        ]

        if not category_tools:
            continue

        st.html(
            f"""
            <section class="section-wrap">
                <div class="section-title-row">
                    <h2 class="section-title">
                        {html.escape(category)}
                    </h2>
                    <div class="section-count">
                        {len(category_tools)} tools
                    </div>
                </div>
            """
        )

        cards = []

        for tool in category_tools:
            dot, status_class = (
                STATUS_STYLES.get(
                    tool["status"],
                    ("●", "status-coming"),
                )
            )

            badge = (
                f'<div class="tool-badge">'
                f'{html.escape(tool["badge"])}'
                f'</div>'
                if tool["badge"]
                else "<div></div>"
            )

            body = (
                '<div class="card-top">'
                + badge
                + (
                    f'<div class="status-pill '
                    f'{status_class}">'
                    f'{dot} '
                    f'{html.escape(tool["status"])}'
                    f'</div>'
                )
                + '</div>'
                + (
                    f'<div class="tool-name">'
                    f'{html.escape(tool["name"])}'
                    f'</div>'
                )
                + (
                    f'<div class="tool-description">'
                    f'{html.escape(tool["description"])}'
                    f'</div>'
                )
            )

            if tool["url"].startswith(
                ("https://", "http://")
            ):
                cards.append(
                    (
                        f'<a class="tool-card" '
                        f'href="'
                        f'{html.escape(tool["url"], quote=True)}'
                        f'" target="_blank" '
                        f'rel="noopener noreferrer">'
                        f'{body}'
                        '<div class="tool-link">'
                        'Open tool →'
                        '</div></a>'
                    )
                )
            else:
                cards.append(
                    (
                        '<div class="tool-card-disabled">'
                        f'{body}'
                        '<div class="tool-link-disabled">'
                        'URL to be added'
                        '</div></div>'
                    )
                )

        st.html(
            '<div class="tool-grid">'
            + ''.join(cards)
            + '</div></section>'
        )
