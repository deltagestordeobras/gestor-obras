import streamlit as st


def aplicar_estilo():
    st.markdown("""
    <style>
    :root {
        --delta-bg: #0b1017;
        --delta-surface: #121923;
        --delta-surface-2: #17212d;
        --delta-border: rgba(148, 163, 184, 0.16);
        --delta-text: #eef3f8;
        --delta-muted: #92a0b2;
        --delta-blue: #62a8ff;
        --delta-green: #37d67a;
        --delta-yellow: #f5c451;
        --delta-red: #ff6376;
    }

    html, body, [class*="css"], .stApp {
        font-family: Inter, "Segoe UI", Arial, sans-serif;
    }

    .stApp { background: var(--delta-bg); }

    /* Oculta o chrome padrao do Streamlit no ambiente de producao. */
    [data-testid="stToolbar"],
    [data-testid="stHeader"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stMainMenu"],
    [data-testid="stAppDeployButton"],
    [data-testid="stDeployButton"],
    [data-testid="stViewerBadge"],
    #MainMenu,
    .stDeployButton,
    .viewerBadge_container__r5tak,
    header[data-testid="stHeader"],
    footer {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        pointer-events: none !important;
    }

    .block-container {
        max-width: 1540px;
        padding-top: 1rem;
        padding-left: 1.4rem;
        padding-right: 1.4rem;
        padding-bottom: 2rem;
    }

    .delta-login-title {
        margin: 0.35rem 0 0.75rem;
        text-align: center;
    }
    .delta-login-title span {
        color: var(--delta-blue);
        font-size: 0.74rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .delta-login-title h1 {
        margin: 0.18rem 0 0;
        color: var(--delta-text);
        font-size: 1.45rem;
        line-height: 1.12;
    }
    .delta-login-footer {
        margin-top: 0.55rem;
        color: var(--delta-muted);
        font-size: 0.7rem;
        text-align: center;
    }

    .delta-admin-hero {
        margin-bottom: 1rem;
        padding: 1rem 1.1rem;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-admin-hero span {
        color: var(--delta-blue);
        font-size: 0.68rem;
        font-weight: 800;
        text-transform: uppercase;
    }
    .delta-admin-hero h1 {
        margin: 0.2rem 0;
        color: var(--delta-text);
        font-size: 1.75rem;
    }
    .delta-admin-hero p {
        margin: 0;
        color: var(--delta-muted);
        font-size: 0.78rem;
    }
    .delta-admin-card {
        min-height: 174px;
        padding: 1.15rem;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: linear-gradient(180deg, rgba(23, 33, 45, 0.98), rgba(18, 25, 35, 0.98));
        box-shadow: 0 14px 28px rgba(0, 0, 0, 0.16);
        transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, background 160ms ease;
    }
    .delta-admin-card:hover {
        border-color: rgba(98, 168, 255, 0.34);
        background: linear-gradient(180deg, rgba(27, 40, 56, 0.98), rgba(18, 28, 40, 0.98));
        box-shadow: 0 18px 34px rgba(0, 0, 0, 0.22);
        transform: translateY(-1px);
    }
    .delta-admin-card__icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 8px;
        background: rgba(98, 168, 255, 0.12);
        color: var(--delta-blue);
        font-weight: 800;
    }
    .delta-admin-card h3 {
        margin: 0.7rem 0 0.25rem;
        color: var(--delta-text);
        font-size: 0.98rem;
    }
    .delta-admin-card p {
        margin: 0;
        color: var(--delta-muted);
        font-size: 0.72rem;
        line-height: 1.45;
    }

    h1, h2, h3, h4 { letter-spacing: 0; }
    hr { margin: 0.75rem 0; border-color: var(--delta-border); }

    .delta-section-title {
        margin: 1rem 0 0.55rem;
        color: var(--delta-text);
        font-size: 0.86rem;
        line-height: 1.2;
        font-weight: 700;
        text-transform: uppercase;
    }

    .delta-header {
        margin-bottom: 0.35rem;
        padding: 0.2rem 0;
    }
    .delta-header__eyebrow, .delta-investor__eyebrow {
        color: var(--delta-muted);
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .delta-header__row {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin: 0.12rem 0 0.55rem;
    }
    .delta-header__row h1 {
        margin: 0;
        color: var(--delta-text);
        font-size: 1.65rem;
        line-height: 1.15;
        font-weight: 720;
    }
    .delta-status, .delta-badge {
        display: inline-flex;
        align-items: center;
        min-height: 24px;
        padding: 0.18rem 0.55rem;
        border: 1px solid rgba(55, 214, 122, 0.3);
        border-radius: 999px;
        background: rgba(55, 214, 122, 0.1);
        color: var(--delta-green);
        font-size: 0.7rem;
        font-weight: 700;
    }
    .delta-header__progress-row, .delta-score-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.3rem;
        color: var(--delta-muted);
        font-size: 0.72rem;
    }
    .delta-header__progress-row strong, .delta-score-label strong { color: var(--delta-text); }
    .delta-progress {
        height: 5px;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.14);
    }
    .delta-progress span {
        display: block;
        height: 100%;
        border-radius: inherit;
        background: var(--delta-blue);
    }
    .delta-progress--score span { background: var(--delta-green); }

    .delta-kpi {
        position: relative;
        min-height: 132px;
        padding: 0.9rem 1rem;
        overflow: hidden;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-kpi::before {
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 3px;
        background: var(--delta-blue);
    }
    .delta-kpi--verde::before { background: var(--delta-green); }
    .delta-kpi--amarelo::before { background: var(--delta-yellow); }
    .delta-kpi--vermelho::before { background: var(--delta-red); }
    .delta-kpi__top { display: flex; align-items: center; gap: 0.5rem; }
    .delta-kpi__icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 27px;
        height: 27px;
        border-radius: 6px;
        background: rgba(98, 168, 255, 0.12);
        color: var(--delta-blue);
        font-weight: 800;
    }
    .delta-kpi--verde .delta-kpi__icon { color: var(--delta-green); background: rgba(55, 214, 122, 0.1); }
    .delta-kpi--amarelo .delta-kpi__icon { color: var(--delta-yellow); background: rgba(245, 196, 81, 0.1); }
    .delta-kpi--vermelho .delta-kpi__icon { color: var(--delta-red); background: rgba(255, 99, 118, 0.1); }
    .delta-kpi__label { color: var(--delta-muted); font-size: 0.76rem; font-weight: 650; }
    .delta-kpi__value { margin-top: 0.75rem; color: var(--delta-text); font-size: 1.55rem; line-height: 1; font-weight: 760; }
    .delta-kpi__sub { margin-top: 0.45rem; color: var(--delta-muted); font-size: 0.68rem; }

    .delta-investor {
        padding: 1rem 1.1rem;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-investor__head { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .delta-investor__head h3 { margin: 0.15rem 0 0; color: var(--delta-text); font-size: 1rem; }
    .delta-investor__metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.6rem; margin: 0.9rem 0; }
    .delta-investor__metrics div { padding-right: 0.7rem; border-right: 1px solid var(--delta-border); }
    .delta-investor__metrics div:last-child { border-right: 0; }
    .delta-investor__metrics span { display: block; color: var(--delta-muted); font-size: 0.67rem; }
    .delta-investor__metrics strong { display: block; margin-top: 0.2rem; color: var(--delta-text); font-size: 1rem; }
    .delta-badge--medio { color: var(--delta-yellow); border-color: rgba(245, 196, 81, 0.3); background: rgba(245, 196, 81, 0.1); }
    .delta-badge--alto, .delta-badge--critico { color: var(--delta-red); border-color: rgba(255, 99, 118, 0.3); background: rgba(255, 99, 118, 0.1); }

    .delta-stage-card, .delta-empty {
        min-height: 290px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 1.1rem;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-stage-card__icon { color: var(--delta-blue); font-size: 1rem; }
    .delta-stage-card__percent { margin-top: 0.8rem; color: var(--delta-text); font-size: 2.2rem; font-weight: 780; }
    .delta-stage-card h3 { margin: 0.2rem 0; color: var(--delta-text); font-size: 1rem; }
    .delta-stage-card p, .delta-empty { color: var(--delta-muted); font-size: 0.74rem; }
    .delta-stage-card .delta-progress { margin-top: 1rem; }

    .delta-message {
        min-height: 94px;
        display: flex;
        align-items: flex-start;
        gap: 0.7rem;
        padding: 0.75rem 0.85rem;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-message__icon { font-size: 1rem; line-height: 1.35; }
    .delta-message__title { color: var(--delta-text); font-size: 0.78rem; font-weight: 720; }
    .delta-message__description { margin-top: 0.22rem; color: var(--delta-muted); font-size: 0.68rem; line-height: 1.4; }
    .delta-message--critico { border-left: 3px solid var(--delta-red); }
    .delta-message--alerta { border-left: 3px solid var(--delta-yellow); }
    .delta-message--sucesso { border-left: 3px solid var(--delta-green); }
    .delta-message--recomendacao { border-left: 3px solid var(--delta-blue); }

    .delta-ops-summary {
        min-height: 94px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        padding: 0.8rem 0.9rem;
        border: 1px solid var(--delta-border);
        border-left: 3px solid var(--delta-green);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-ops-summary span, .delta-ops-summary small { color: var(--delta-muted); font-size: 0.68rem; }
    .delta-ops-summary strong { margin: 0.25rem 0; color: var(--delta-text); font-size: 1.35rem; }
    .delta-ops-summary strong.delta-negative { color: var(--delta-red); }

    .delta-evolution-head h3 {
        margin: 0.45rem 0 0.25rem;
        color: var(--delta-text);
        font-size: 1rem;
    }
    .delta-evolution-head p {
        margin: 0 0 0.35rem;
        color: var(--delta-muted);
        font-size: 0.76rem;
        line-height: 1.5;
    }
    .delta-evolution-head small, .delta-evolution-date {
        color: var(--delta-muted);
        font-size: 0.68rem;
    }
    .delta-evolution-date { margin-right: 0.5rem; font-weight: 700; }
    .delta-evolution-summary, .delta-stage-photo {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 86px;
        padding: 0.8rem 0.9rem;
        border: 1px solid var(--delta-border);
        border-left: 3px solid var(--delta-blue);
        border-radius: 8px;
        background: var(--delta-surface);
    }
    .delta-evolution-summary span, .delta-evolution-summary small,
    .delta-stage-photo span {
        color: var(--delta-muted);
        font-size: 0.68rem;
    }
    .delta-evolution-summary strong, .delta-stage-photo strong {
        margin: 0.22rem 0;
        color: var(--delta-text);
        font-size: 0.9rem;
    }
    .delta-stage-photo { min-height: 74px; margin-bottom: 0.35rem; }

    div[data-testid="stPlotlyChart"] {
        overflow: hidden;
        border: 1px solid var(--delta-border);
        border-radius: 8px;
        background: var(--delta-surface);
    }

    .stButton > button {
        min-height: 38px;
        border-radius: 6px;
        border-color: var(--delta-border);
        font-weight: 650;
    }
    .stButton > button[kind="primary"] { background: #2d7ff9; }

    /* Navegacao principal no padrao DELTA Vendas. */
    [data-testid="stSidebar"] {
        width: 18rem !important;
        min-width: 17rem !important;
        border-right: 1px solid rgba(34, 211, 238, 0.22);
        background: linear-gradient(180deg, #081526 0%, #0b1e34 58%, #081321 100%);
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 18rem !important;
        max-height: 100vh;
        overflow-y: auto;
        overflow-x: hidden;
        scrollbar-width: thin;
        scrollbar-color: rgba(98, 168, 255, 0.42) rgba(148, 163, 184, 0.08);
    }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar { width: 5px; }
    [data-testid="stSidebar"] > div:first-child::-webkit-scrollbar-thumb {
        border-radius: 999px;
        background: rgba(98, 168, 255, 0.42);
    }
    [data-testid="stSidebar"] .block-container { padding: 0.25rem 0.65rem 0.65rem; }
    [data-testid="stSidebar"] [data-testid="stImage"] {
        max-width: 13.4rem;
        margin: 0 auto;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        margin-bottom: 0.08rem;
        color: #91a4ba;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-top: 0.45rem; }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label p {
        color: #8294aa;
        font-size: 0.64rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .delta-menu-label {
        margin: 0.55rem 0 0.3rem;
        padding: 0 0.2rem;
        color: #71849a;
        font-size: 0.6rem;
        font-weight: 800;
        letter-spacing: 0.09em;
    }
    .delta-sidebar-profile {
        margin: 0.25rem 0 0.72rem;
        padding: 0.68rem 0.72rem;
        border: 1px solid rgba(98, 168, 255, 0.18);
        border-radius: 8px;
        background: linear-gradient(180deg, rgba(15, 36, 61, 0.72), rgba(8, 19, 33, 0.62));
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 12px 24px rgba(0, 0, 0, 0.14);
    }
    .delta-sidebar-profile span,
    .delta-sidebar-profile small {
        display: block;
        color: #8192a7;
        font-size: 0.68rem;
    }
    .delta-sidebar-profile strong {
        display: block;
        margin: 0.1rem 0;
        color: #d8e6f8;
        font-size: 0.82rem;
    }
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        border-radius: 0.6rem;
        font-weight: 700;
        transition: border-color 150ms ease, background 150ms ease, box-shadow 150ms ease, transform 150ms ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        border-color: rgba(34, 211, 238, 0.34);
        background: rgba(34, 211, 238, 0.11);
        color: #f8fdff;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        border-color: rgba(103, 232, 249, 0.48);
        background: linear-gradient(135deg, #1d4ed8, #0284c7 58%, #0891b2);
        color: #fff;
        box-shadow: 0 7px 18px rgba(8, 145, 178, 0.2);
    }
    [class*="st-key-grupo_"] { margin-bottom: 0.34rem; }
    [class*="st-key-grupo_"] button {
        min-height: 2.78rem;
        padding: 0.48rem 0.68rem;
        border: 1px solid rgba(96, 165, 250, 0.18);
        background: linear-gradient(180deg, rgba(20, 48, 78, 0.78), rgba(14, 37, 62, 0.78));
        color: #c5d4e6;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035), 0 9px 18px rgba(0, 0, 0, 0.12);
    }
    [class*="st-key-grupo_"] button p {
        width: 100%;
        color: inherit;
        text-align: center;
        font-size: 0.84rem;
        font-weight: 700;
    }
    [data-testid="stSidebar"] .st-key-logout_sidebar button {
        min-height: 2.35rem;
        margin-top: 0.22rem;
        border-color: rgba(96, 165, 250, 0.12);
        background: rgba(14, 35, 58, 0.64);
    }
    .delta-sidebar-footer {
        margin-top: 0.45rem;
        padding-top: 0.4rem;
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        color: #60768d;
        font-size: 0.6rem;
        text-align: center;
    }

    /* Submenu contextual compacto. */
    .delta-submenu-context {
        display: flex;
        align-items: baseline;
        gap: 0.42rem;
        margin: 0 0 0.3rem;
        color: var(--delta-muted);
    }
    .delta-submenu-context span {
        font-size: 0.61rem;
        font-weight: 800;
        text-transform: uppercase;
    }
    .delta-submenu-context strong {
        color: var(--delta-text);
        font-size: 0.77rem;
        font-weight: 700;
    }
    [class*="st-key-submenu_"] { margin-bottom: 0.06rem; }
    [class*="st-key-submenu_"] button {
        min-height: 2.2rem;
        padding: 0.32rem 0.58rem;
        border: 1px solid rgba(148, 163, 184, 0.13);
        border-radius: 0.42rem;
        background: rgba(17, 31, 48, 0.66);
        color: #9fb0c3;
        box-shadow: none;
    }
    [class*="st-key-submenu_"] button p {
        color: inherit;
        font-size: 0.73rem;
        font-weight: 680;
        white-space: normal;
    }
    [class*="st-key-submenu_"] button:hover {
        border-color: rgba(34, 211, 238, 0.28);
        background: rgba(34, 211, 238, 0.08);
        color: #eaf8ff;
    }
    [class*="st-key-submenu_"] button[kind="primary"] {
        border-color: rgba(96, 165, 250, 0.34);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.72), rgba(8, 145, 178, 0.72));
        color: #fff;
        box-shadow: none;
    }
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        flex-wrap: nowrap;
        gap: 2px;
        overflow-x: auto;
        overflow-y: hidden;
        max-width: 100%;
        padding: 0 0 4px;
        border-bottom: 1px solid var(--delta-border);
        scroll-behavior: smooth;
        scrollbar-width: thin;
        scrollbar-color: rgba(98, 168, 255, 0.48) rgba(148, 163, 184, 0.08);
        overscroll-behavior-x: contain;
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { height: 5px; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.08);
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
        border-radius: 999px;
        background: rgba(98, 168, 255, 0.48);
    }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover {
        background: rgba(98, 168, 255, 0.72);
    }
    .stTabs [data-baseweb="tab"] {
        flex: 0 0 auto;
        min-width: max-content;
        min-height: 38px;
        padding: 7px 8px;
        border-radius: 5px 5px 0 0;
        font-size: 0.85rem;
        font-weight: 650;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"] p {
        margin: 0;
        white-space: nowrap;
    }
    .stTabs [aria-selected="true"] { background: var(--delta-surface-2); }

    @media (max-width: 900px) {
        .delta-investor__metrics { grid-template-columns: repeat(2, 1fr); }
        .delta-investor__metrics div { border-right: 0; }
        .delta-header__row { align-items: flex-start; flex-direction: column; gap: 0.35rem; }
        .delta-kpi { min-height: 118px; }
    }
    </style>
    """, unsafe_allow_html=True)
