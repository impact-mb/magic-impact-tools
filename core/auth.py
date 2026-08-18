import hashlib
import hmac

import streamlit as st


PBKDF2_ITERATIONS = 310_000


def _parse_password_hash(stored_hash: str):
    """Parse pbkdf2_sha256$iterations$salt$hash format."""
    try:
        algorithm, iterations, salt, digest = stored_hash.split(
            "$",
            3,
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid password hash format in Streamlit secrets."
        ) from exc

    if algorithm != "pbkdf2_sha256":
        raise ValueError(
            "Unsupported password hash algorithm."
        )

    return int(iterations), salt, digest


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    """Verify a plain password against the stored PBKDF2 hash."""

    if not password or not stored_hash:
        return False

    try:
        (
            iterations,
            salt,
            expected_digest,
        ) = _parse_password_hash(
            stored_hash
        )

    except (TypeError, ValueError):
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()

    return hmac.compare_digest(
        actual_digest,
        expected_digest,
    )


def _get_user_config(
    username: str,
):
    """
    Return one user from Streamlit Secrets.

    Expected format:

    [users.narendra]
    display_name = "Narendra"
    team = "Central Team"
    role = "admin"
    active = true
    ai_daily_limit = 10
    password_hash = "..."

    [users.ajay]
    display_name = "Ajay"
    team = "Central Team"
    role = "user"
    active = true
    ai_daily_limit = 5
    password_hash = "..."
    """

    try:
        users = st.secrets[
            "users"
        ]

    except KeyError:
        return None

    if username not in users:
        return None

    record = users[
        username
    ]

    if not bool(
        record.get(
            "active",
            True,
        )
    ):
        return None

    return {
        "username": username,

        "display_name": str(
            record.get(
                "display_name",
                username,
            )
        ).strip(),

        "team": str(
            record.get(
                "team",
                "Central Team",
            )
        ).strip(),

        "role": str(
            record.get(
                "role",
                "user",
            )
        ).strip(),

        # Default = 5 if not defined
        "ai_daily_limit": int(
            record.get(
                "ai_daily_limit",
                5,
            )
        ),

        "password_hash": str(
            record.get(
                "password_hash",
                "",
            )
        ).strip(),
    }


def current_user():
    """
    Return the authenticated user stored
    in the current Streamlit session.
    """

    if not st.session_state.get(
        "authenticated",
        False,
    ):
        return None

    return {
        "username": st.session_state.get(
            "username",
            "",
        ),

        "display_name": st.session_state.get(
            "display_name",
            "",
        ),

        "team": st.session_state.get(
            "team",
            "",
        ),

        "role": st.session_state.get(
            "role",
            "user",
        ),

        "ai_daily_limit": st.session_state.get(
            "ai_daily_limit",
            5,
        ),
    }


def logout():
    """
    Clear authentication-related
    session values.
    """

    for key in [
        "authenticated",
        "username",
        "display_name",
        "team",
        "role",
        "ai_daily_limit",
    ]:
        st.session_state.pop(
            key,
            None,
        )

    st.rerun()


def _render_login_page():
    """
    Render the login gate
    for Magic Impact Tools.
    """

    st.markdown("")

    left, middle, right = (
        st.columns(
            [
                1,
                1.15,
                1,
            ]
        )
    )

    with middle:

        with st.container(
            border=True
        ):

            st.markdown(
                (
                    "<h2 style='"
                    "text-align:center;"
                    "margin-bottom:4px;'>"
                    "Magic Impact Tools"
                    "</h2>"
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                (
                    "<div style='"
                    "text-align:center;"
                    "color:#64748b;"
                    "margin-bottom:18px;'>"
                    "Central Team Login"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

            with st.form(
                "central_team_login_form"
            ):

                username = (
                    st.text_input(
                        "User ID",
                        placeholder=(
                            "Enter your user ID"
                        ),
                    )
                    .strip()
                    .lower()
                )

                password = (
                    st.text_input(
                        "Password",
                        type="password",
                        placeholder=(
                            "Enter your password"
                        ),
                    )
                )

                submitted = (
                    st.form_submit_button(
                        "Login",
                        type="primary",
                        use_container_width=True,
                    )
                )

            if submitted:

                user = (
                    _get_user_config(
                        username
                    )
                )

                if (
                    user
                    and verify_password(
                        password,
                        user[
                            "password_hash"
                        ],
                    )
                ):

                    # -----------------------------------------
                    # SAVE USER INTO SESSION
                    # -----------------------------------------

                    st.session_state[
                        "authenticated"
                    ] = True

                    st.session_state[
                        "username"
                    ] = user[
                        "username"
                    ]

                    st.session_state[
                        "display_name"
                    ] = user[
                        "display_name"
                    ]

                    st.session_state[
                        "team"
                    ] = user[
                        "team"
                    ]

                    st.session_state[
                        "role"
                    ] = user[
                        "role"
                    ]

                    st.session_state[
                        "ai_daily_limit"
                    ] = user[
                        "ai_daily_limit"
                    ]

                    st.rerun()

                st.error(
                    "Invalid user ID or password."
                )

            st.caption(
                (
                    "Access is restricted to "
                    "authorised Magic Bus users."
                )
            )


def require_login():
    """
    Require an authenticated session.

    Returns the logged-in user.

    If the user is not authenticated,
    the login page is shown and the
    remainder of the Streamlit app stops.
    """

    user = current_user()

    if user:
        return user

    _render_login_page()

    st.stop()


def render_user_sidebar(
    user: dict,
):
    """
    Show logged-in user details
    and AI generation limit.
    """

    with st.sidebar:

        st.markdown(
            "### Signed in"
        )

        st.write(
            user.get(
                "display_name",
                user.get(
                    "username",
                    "",
                ),
            )
        )

        st.caption(
            user.get(
                "team",
                "Central Team",
            )
        )

        role = user.get(
            "role",
            "user",
        )

        if role:
            st.caption(
                f"Role: {role.title()}"
            )

        # -----------------------------------------
        # SHOW AI LIMIT
        # -----------------------------------------

        ai_daily_limit = (
            user.get(
                "ai_daily_limit",
                5,
            )
        )

        st.caption(
            (
                f"AI limit: "
                f"{ai_daily_limit} "
                f"generations / day"
            )
        )

        st.divider()

        if st.button(
            "Logout",
            use_container_width=True,
            key="logout_button",
        ):
            logout()