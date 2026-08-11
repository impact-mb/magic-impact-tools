import streamlit as st


def render_global_styles():
    st.html(
        """
        <style>
        .stApp {
            background: #f6f8fc;
        }

        .block-container {
            max-width: 1450px;
            padding: 1.2rem 1rem 3rem;
        }

        .time-box {
            background: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 6px 18px rgba(15,23,42,.06);
        }

        .time-value {
            font-size: 1.55rem;
            font-weight: 850;
            color: #0f172a;
        }

        .time-label {
            color: #64748b;
            font-size: .78rem;
            margin-top: .25rem;
        }

        .main-title {
            text-align: center;
            padding: .25rem 1rem;
        }

        .main-title h1 {
            margin: 0;
            color: #0f172a;
            font-size: clamp(2rem,4vw,3.25rem);
            line-height: 1.1;
        }

        .main-title p {
            margin: .55rem auto .35rem;
            color: #475569;
            max-width: 780px;
            line-height: 1.55;
        }

        .current-date {
            display: inline-block;
            margin-top: .3rem;
            padding: .35rem .8rem;
            border-radius: 999px;
            background: #eff6ff;
            color: #1d4ed8;
            font-size: .82rem;
            font-weight: 750;
        }

        .logo-wrap {
            height: 110px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #ffffff;
            border: 1px solid #dbe4f0;
            border-radius: 16px;
            padding: .75rem;
            box-shadow: 0 6px 18px rgba(15,23,42,.06);
        }

        .section-wrap {
            margin-top: 2.1rem;
        }

        .section-title-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #dbe4f0;
            padding-bottom: .55rem;
            margin-bottom: 1rem;
        }

        .section-title {
            margin: 0;
            color: #0f172a;
            font-size: 1.4rem;
        }

        .section-count {
            color: #64748b;
            font-size: .82rem;
        }

        .tool-grid {
            display: grid;
            grid-template-columns:
                repeat(3,minmax(0,1fr));
            gap: 1.1rem;
        }

        .tool-card,
        .tool-card-disabled {
            display: flex;
            flex-direction: column;
            min-height: 205px;
            padding: 1.3rem;
            border-radius: 18px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            color: #0f172a !important;
            text-decoration: none !important;
            box-shadow:
                0 6px 18px rgba(15,23,42,.06);
        }

        .tool-card {
            transition: .18s ease;
        }

        .tool-card:hover {
            transform: translateY(-6px);
            border-color: #2563eb;
            box-shadow:
                0 18px 35px rgba(37,99,235,.16);
        }

        .tool-card-disabled {
            opacity: .82;
            background: #f8fafc;
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            margin-bottom: .8rem;
        }

        .status-pill {
            border-radius: 999px;
            padding: .3rem .55rem;
            font-size: .7rem;
            font-weight: 800;
        }

        .status-live {
            background: #ecfdf5;
            color: #047857;
        }

        .status-maintenance {
            background: #fffbeb;
            color: #b45309;
        }

        .status-offline {
            background: #fef2f2;
            color: #b91c1c;
        }

        .status-coming {
            background: #f1f5f9;
            color: #475569;
        }

        .tool-badge {
            width: fit-content;
            padding: .22rem .5rem;
            border-radius: 999px;
            background: #eef2ff;
            color: #4338ca;
            font-size: .68rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .tool-name {
            font-size: 1.12rem;
            font-weight: 850;
            margin-bottom: .55rem;
        }

        .tool-description {
            color: #64748b;
            line-height: 1.5;
            font-size: .91rem;
        }

        .tool-link,
        .tool-link-disabled {
            margin-top: auto;
            font-weight: 800;
            font-size: .9rem;
        }

        .tool-link {
            color: #1d4ed8;
        }

        .tool-link-disabled {
            color: #64748b;
        }

        .footer {
            margin-top: 3rem;
            padding: 1.4rem;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            color: #64748b;
            font-size: .84rem;
            line-height: 1.7;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px;
        }

        @media(max-width:950px) {
            .tool-grid {
                grid-template-columns:
                    repeat(2,minmax(0,1fr));
            }
        }

        @media(max-width:650px) {
            .tool-grid {
                grid-template-columns: 1fr;
            }

            .tool-card,
            .tool-card-disabled {
                min-height: 0;
            }
        }
        </style>
        """
    )
