import re

import streamlit as st

from core.settings import CATEGORY_ORDER


# ============================================================
# DASHBOARD GROUPING
# ============================================================

DASHBOARD_ORDER = [
    "Magic Dashboard",
    "MSP Insights",
    "CPRF Validation Tool",
    "MB Excel Merger",
    "Child-wise Curriculum Delivery Report",
    "CPRF Data Quality Checker",
]

DASHBOARD_NAMES = set(
    DASHBOARD_ORDER
)


# ============================================================
# CATEGORY DESCRIPTIONS
# ============================================================

CATEGORY_DESCRIPTIONS = {
    "Dashboards": (
        "Access programme dashboards, validation tools, "
        "data-quality checks and recurring reporting utilities."
    ),

    "Analytics": (
        "Explore analytical tools for programme "
        "and impact data."
    ),

    "Validation": (
        "Validate programme data before "
        "reporting and analysis."
    ),

    "Data Quality": (
        "Identify missing, duplicate and "
        "inconsistent programme data."
    ),

    "Utilities": (
        "Use quick utilities that simplify "
        "recurring data-system tasks."
    ),

    "Reports": (
        "Generate structured programme "
        "and management reports."
    ),

    "Donor Reports": (
        "Access donor-specific reporting dashboards "
        "and recurring reporting outputs."
    ),
}


# ============================================================
# CATEGORY ICONS
# ============================================================

CATEGORY_ICONS = {
    "Dashboards": "📊",
    "Analytics": "📈",
    "Validation": "✅",
    "Data Quality": "🔍",
    "Utilities": "🛠️",
    "Reports": "📄",
    "Donor Reports": "🤝",
}


# ============================================================
# EFFECTIVE CATEGORY
# ============================================================

def effective_category(tool):
    """
    Homepage category.

    The six agreed tools are grouped under Dashboards
    regardless of their original tools.json category.
    """

    name = str(
        tool.get(
            "name",
            "",
        )
    ).strip()

    if name in DASHBOARD_NAMES:
        return "Dashboards"

    return str(
        tool.get(
            "category",
            "",
        )
    ).strip()


# ============================================================
# DASHBOARD SORT
# ============================================================

def dashboard_sort_key(tool):
    """
    Keep Dashboard tools in the agreed order.
    """

    name = str(
        tool.get(
            "name",
            "",
        )
    ).strip()

    try:
        return DASHBOARD_ORDER.index(
            name
        )

    except ValueError:
        return len(
            DASHBOARD_ORDER
        )


# ============================================================
# SAFE STREAMLIT KEY
# ============================================================

def safe_key(value):
    """
    Create a safe Streamlit widget key.
    """

    value = str(
        value
    ).strip().lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "_",
        value,
    )

    return value.strip(
        "_"
    )


# ============================================================
# TOOL CARD
# ============================================================

def render_tool_card(
    tool,
    category,
    position,
):
    """
    Render one individual tool card using
    native Streamlit components.
    """

    name = str(
        tool.get(
            "name",
            "",
        )
    ).strip()

    description = str(
        tool.get(
            "description",
            "",
        )
    ).strip()

    status = str(
        tool.get(
            "status",
            "Coming Soon",
        )
    ).strip()

    badge = str(
        tool.get(
            "badge",
            "",
        )
    ).strip()

    url = str(
        tool.get(
            "url",
            "",
        )
    ).strip()

    with st.container(
        border=True
    ):

        # ====================================================
        # BADGE + STATUS
        # ====================================================

        badge_col, status_col = (
            st.columns(
                [
                    1.3,
                    1,
                ]
            )
        )

        with badge_col:

            if badge:

                st.caption(
                    badge.upper()
                )

            else:

                st.caption(
                    " "
                )

        with status_col:

            if status == "Live":

                st.caption(
                    "🟢 Live"
                )

            elif status == "Under Maintenance":

                st.caption(
                    "🟠 Under Maintenance"
                )

            elif status == "Offline":

                st.caption(
                    "🔴 Offline"
                )

            else:

                st.caption(
                    "⚪ Coming Soon"
                )

        # ====================================================
        # TOOL NAME
        # ====================================================

        st.markdown(
            f"#### {name}"
        )

        # ====================================================
        # DESCRIPTION
        # ====================================================

        if description:

            st.caption(
                description
            )

        else:

            st.caption(
                "No description available."
            )

        st.markdown(
            ""
        )

        # ====================================================
        # OPEN BUTTON
        # ====================================================

        if url.startswith(
            (
                "https://",
                "http://",
            )
        ):

            st.link_button(
                "Open Tool →",
                url,
                use_container_width=True,
            )

        else:

            st.button(
                "URL to be added",
                disabled=True,
                use_container_width=True,
                key=(
                    f"disabled_"
                    f"{safe_key(category)}_"
                    f"{position}_"
                    f"{safe_key(name)}"
                ),
            )


# ============================================================
# TOOL GRID
# ============================================================

def render_tool_rows(
    category,
    category_tools,
):
    """
    Render three tool cards per row.
    """

    tools_per_row = 3

    for start in range(
        0,
        len(category_tools),
        tools_per_row,
    ):

        row_tools = (
            category_tools[
                start:
                start + tools_per_row
            ]
        )

        columns = st.columns(
            tools_per_row,
            gap="large",
        )

        for index, tool in enumerate(
            row_tools
        ):

            with columns[
                index
            ]:

                render_tool_card(
                    tool=tool,
                    category=category,
                    position=(
                        start
                        + index
                    ),
                )

        if (
            start
            + tools_per_row
            < len(category_tools)
        ):

            st.markdown(
                ""
            )


# ============================================================
# CATEGORY EXPANDER
# ============================================================

def render_category_expander(
    category,
    category_tools,
):
    """
    Render one compact clickable category.

    Collapsed by default to reduce homepage height.
    """

    tool_count = len(
        category_tools
    )

    icon = CATEGORY_ICONS.get(
        category,
        "📁",
    )

    description = (
        CATEGORY_DESCRIPTIONS.get(
            category,
            (
                "Access available "
                "programme tools."
            ),
        )
    )

    tool_word = (
        "tool"
        if tool_count == 1
        else "tools"
    )

    expander_title = (
        f"{icon} "
        f"{category} "
        f"• {tool_count} "
        f"{tool_word}"
    )

    with st.expander(
        expander_title,
        expanded=False,
    ):

        st.caption(
            description
        )

        st.divider()

        render_tool_rows(
            category,
            category_tools,
        )


# ============================================================
# MAIN TOOLS SECTION
# ============================================================

def render_tools_section(
    tools,
):
    """
    Render filters and all tool categories.

    All categories are clickable/collapsible
    to reduce homepage vertical space.
    """

    # ========================================================
    # SEARCH / FILTER BAR
    # ========================================================

    (
        search_col,
        category_col,
        status_col,
    ) = st.columns(
        [
            2.2,
            1,
            1,
        ]
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    with search_col:

        query = (
            st.text_input(
                "Search",
                placeholder=(
                    "Search by tool, donor, "
                    "category or purpose..."
                ),
                label_visibility=(
                    "collapsed"
                ),
            )
            .strip()
            .lower()
        )

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    with category_col:

        selected_category = (
            st.selectbox(
                "Category",
                (
                    ["All Categories"]
                    + CATEGORY_ORDER
                ),
                label_visibility=(
                    "collapsed"
                ),
            )
        )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    with status_col:

        selected_status = (
            st.selectbox(
                "Status",
                [
                    "All Statuses",
                    "Live",
                    "Coming Soon",
                    "Under Maintenance",
                    "Offline",
                ],
                label_visibility=(
                    "collapsed"
                ),
            )
        )

    # ========================================================
    # FILTER TOOLS
    # ========================================================

    filtered_tools = []

    for tool in tools:

        display_category = (
            effective_category(
                tool
            )
        )

        # ----------------------------------------------------
        # CATEGORY MATCH
        # ----------------------------------------------------

        category_match = (
            selected_category
            == "All Categories"
            or display_category
            == selected_category
        )

        # ----------------------------------------------------
        # STATUS MATCH
        # ----------------------------------------------------

        status_match = (
            selected_status
            == "All Statuses"
            or str(
                tool.get(
                    "status",
                    "",
                )
            ).strip()
            == selected_status
        )

        # ----------------------------------------------------
        # SEARCH MATCH
        # ----------------------------------------------------

        searchable_text = " ".join(
            [
                str(
                    tool.get(
                        "name",
                        "",
                    )
                ),

                display_category,

                str(
                    tool.get(
                        "description",
                        "",
                    )
                ),

                str(
                    tool.get(
                        "badge",
                        "",
                    )
                ),
            ]
        ).lower()

        search_match = (
            not query
            or query
            in searchable_text
        )

        # ----------------------------------------------------
        # INCLUDE
        # ----------------------------------------------------

        if (
            category_match
            and status_match
            and search_match
        ):

            filtered_tools.append(
                tool
            )

    # ========================================================
    # NOTHING FOUND
    # ========================================================

    if not filtered_tools:

        st.info(
            (
                "No tools match the "
                "selected filters."
            )
        )

        return

    # ========================================================
    # RENDER CATEGORY EXPANDERS
    # ========================================================

    for category in CATEGORY_ORDER:

        category_tools = [
            tool
            for tool in filtered_tools
            if effective_category(
                tool
            )
            == category
        ]

        if not category_tools:
            continue

        # ----------------------------------------------------
        # DASHBOARD AGREED ORDER
        # ----------------------------------------------------

        if category == "Dashboards":

            category_tools = sorted(
                category_tools,
                key=dashboard_sort_key,
            )

        # ----------------------------------------------------
        # CLICKABLE / COLLAPSIBLE CATEGORY
        # ----------------------------------------------------

        render_category_expander(
            category,
            category_tools,
        )