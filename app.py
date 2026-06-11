import io
import os
from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import kagglehub
except ImportError:
    kagglehub = None

# =============================================================
# INDIA WATER QUALITY ACTION MONITOR
# Frontend-improved Streamlit BI dashboard
# =============================================================

st.set_page_config(
    page_title="India Water Quality Monitor",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# Design tokens: aquifer atlas visual system
# -------------------------------------------------------------
PALETTE_MAP = {
    "Iron": "#B45309",      # oxidized sediment
    "Salinity": "#0E7490",  # deep reservoir cyan
    "Fluoride": "#047857",  # mineral green
    "Arsenic": "#BE123C",   # alert ruby
    "Nitrate": "#4338CA",   # analytic indigo
}

PARAMETER_NOTES = {
    "Iron": "Besi / mineral logam",
    "Salinity": "Salinitas / garam terlarut",
    "Fluoride": "Fluorida",
    "Arsenic": "Arsenik",
    "Nitrate": "Nitrat",
}

APP_BG = "#07111F"
INK = "#EAF7F5"
MUTED = "#91A7B3"
CARD = "#0E1B2A"
STROKE = "#1D3346"
AQUIFER = "#14B8A6"
RESERVOIR = "#38BDF8"
SEDIMENT = "#F59E0B"
PANEL = "#0B1724"
DEEP = "#050A12"


def inject_css():
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@500;600&display=swap');

            :root {
                --app-bg: #07111F;
                --app-bg-2: #0A1625;
                --ink: #EAF7F5;
                --ink-soft: #C8DCE0;
                --muted: #91A7B3;
                --card: #0E1B2A;
                --card-2: #111F31;
                --stroke: #1D3346;
                --stroke-soft: rgba(148, 209, 214, 0.18);
                --aquifer: #14B8A6;
                --reservoir: #38BDF8;
                --sediment: #F59E0B;
                --danger: #FB7185;
                --shadow: 0 24px 70px rgba(0, 0, 0, 0.38);
            }

            html, body, [class*="css"] {
                font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
                color: var(--ink);
            }

            .stApp {
                background:
                    radial-gradient(circle at 8% 0%, rgba(56, 189, 248, 0.16), transparent 28rem),
                    radial-gradient(circle at 88% 12%, rgba(20, 184, 166, 0.14), transparent 26rem),
                    radial-gradient(circle at 50% 102%, rgba(245, 158, 11, 0.10), transparent 32rem),
                    linear-gradient(180deg, #050A12 0%, var(--app-bg) 42%, #091827 100%);
                color: var(--ink);
            }

            div[data-testid="stHeader"] {
                background: rgba(5, 10, 18, 0.72);
                backdrop-filter: blur(16px);
                border-bottom: 1px solid rgba(148, 209, 214, 0.12);
            }

            div[data-testid="stToolbar"] {
                color: var(--ink) !important;
            }

            .block-container {
                padding-top: 1.6rem;
                padding-bottom: 2.4rem;
                max-width: 1480px;
            }

            /* Sidebar */
            section[data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, #020617 0%, #07111F 50%, #020617 100%);
                border-right: 1px solid rgba(148, 209, 214, 0.16);
                box-shadow: 18px 0 44px rgba(0, 0, 0, 0.28);
            }

            section[data-testid="stSidebar"] * {
                color: #EAF7F5 !important;
            }

            section[data-testid="stSidebar"] label p,
            section[data-testid="stSidebar"] .stCaptionContainer,
            section[data-testid="stSidebar"] small,
            section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
                color: #9EB6BF !important;
            }

            section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
                color: #F8FEFF !important;
            }

            section[data-testid="stSidebar"] hr {
                border-color: rgba(148, 209, 214, 0.18) !important;
            }

            div[data-baseweb="select"] > div {
                background-color: rgba(14, 27, 42, 0.96) !important;
                border: 1px solid rgba(148, 209, 214, 0.22) !important;
                border-radius: 14px !important;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
            }

            div[data-baseweb="popover"], div[data-baseweb="menu"] {
                background-color: #0B1724 !important;
                color: #EAF7F5 !important;
                border: 1px solid rgba(148, 209, 214, 0.22) !important;
            }

            div[data-baseweb="option"] {
                background-color: #0B1724 !important;
                color: #EAF7F5 !important;
            }

            div[data-baseweb="option"]:hover {
                background-color: rgba(56, 189, 248, 0.16) !important;
            }

            div[data-baseweb="tag"] {
                background-color: rgba(20, 184, 166, 0.18) !important;
                border: 1px solid rgba(94, 234, 212, 0.26) !important;
                border-radius: 999px !important;
                color: #CCFBF1 !important;
            }

            div[data-testid="stRadio"] label {
                background-color: rgba(14, 27, 42, 0.78);
                border: 1px solid rgba(148, 209, 214, 0.20);
                border-radius: 999px;
                padding: 0.35rem 0.7rem;
                margin-right: 0.25rem;
            }

            div[data-testid="stToggle"] label {
                color: #EAF7F5 !important;
            }

            div[data-testid="stFileUploader"] section {
                background: rgba(14, 27, 42, 0.74) !important;
                border: 1px dashed rgba(148, 209, 214, 0.30) !important;
                border-radius: 18px !important;
            }

            /* Hero */
            .hero-shell {
                position: relative;
                overflow: hidden;
                border-radius: 30px;
                padding: 30px 34px;
                min-height: 265px;
                background:
                    linear-gradient(135deg, rgba(2, 6, 23, 0.98) 0%, rgba(7, 17, 31, 0.98) 46%, rgba(15, 23, 42, 0.95) 100%);
                border: 1px solid rgba(148, 209, 214, 0.18);
                box-shadow: var(--shadow);
                margin-bottom: 1.15rem;
            }

            .hero-shell:before {
                content: "";
                position: absolute;
                inset: -42% -18% auto auto;
                width: 560px;
                height: 560px;
                background:
                    radial-gradient(circle, rgba(56, 189, 248, 0.26), transparent 62%);
                filter: blur(1px);
                pointer-events: none;
            }

            .hero-shell:after {
                content: "";
                position: absolute;
                right: 0;
                bottom: 0;
                width: 52%;
                height: 100%;
                opacity: 0.58;
                background:
                    linear-gradient(175deg, transparent 0 14%, rgba(148, 209, 214, 0.10) 14% 15%, transparent 15% 24%, rgba(245,158,11,0.36) 24% 27%, transparent 27% 38%, rgba(20,184,166,0.24) 38% 40%, transparent 40% 57%, rgba(56,189,248,0.34) 57% 60%, transparent 60% 100%),
                    repeating-linear-gradient(160deg, transparent 0 18px, rgba(226, 245, 242, 0.08) 19px, transparent 21px);
                clip-path: polygon(15% 0, 100% 0, 100% 100%, 0 100%);
            }

            .hero-content {
                position: relative;
                z-index: 2;
                max-width: 760px;
            }

            .eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.42rem 0.75rem;
                border-radius: 999px;
                background: rgba(56, 189, 248, 0.10);
                border: 1px solid rgba(125, 211, 252, 0.20);
                color: #BAE6FD;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .hero-title {
                margin: 1.05rem 0 0.75rem 0;
                color: #F8FEFF;
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                font-weight: 700;
                font-size: clamp(2.25rem, 5vw, 5.4rem);
                line-height: 0.92;
                letter-spacing: -0.075em;
                text-shadow: 0 10px 36px rgba(56, 189, 248, 0.12);
            }

            .hero-title span {
                color: #67E8F9;
            }

            .hero-subtitle {
                max-width: 650px;
                color: #C8DCE0;
                font-size: 1.02rem;
                line-height: 1.65;
                margin-bottom: 1.1rem;
            }

            .hero-meta-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.65rem;
                margin-top: 1.2rem;
            }

            .hero-meta {
                display: inline-flex;
                gap: 0.45rem;
                align-items: center;
                border: 1px solid rgba(148, 209, 214, 0.18);
                background: rgba(14, 27, 42, 0.66);
                color: #EAF7F5;
                padding: 0.55rem 0.75rem;
                border-radius: 14px;
                font-size: 0.82rem;
                font-weight: 600;
            }

            /* Active filter */
            .filter-strip {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                align-items: center;
                background: rgba(14, 27, 42, 0.78);
                border: 1px solid rgba(148, 209, 214, 0.18);
                border-radius: 22px;
                padding: 0.78rem 0.9rem;
                box-shadow: 0 16px 42px rgba(0, 0, 0, 0.22);
                margin-bottom: 1.1rem;
            }

            .filter-strip strong {
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #67E8F9;
                margin-right: 0.2rem;
            }

            .filter-chip {
                display: inline-flex;
                align-items: center;
                max-width: 100%;
                border-radius: 999px;
                background: rgba(56, 189, 248, 0.10);
                color: #DDF7FF;
                border: 1px solid rgba(125, 211, 252, 0.22);
                padding: 0.4rem 0.65rem;
                font-size: 0.78rem;
                font-weight: 700;
            }

            /* Cards */
            .metric-card {
                position: relative;
                overflow: hidden;
                min-height: 168px;
                padding: 1.25rem;
                border-radius: 24px;
                background:
                    linear-gradient(180deg, rgba(17, 31, 49, 0.94), rgba(11, 23, 36, 0.92));
                border: 1px solid rgba(148, 209, 214, 0.16);
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.26);
            }

            .metric-card:before {
                content: "";
                position: absolute;
                inset: 0;
                background: linear-gradient(115deg, rgba(255,255,255,0.06), transparent 42%);
                pointer-events: none;
            }

            .metric-card:after {
                content: "";
                position: absolute;
                right: -42px;
                top: -42px;
                width: 118px;
                height: 118px;
                border-radius: 999px;
                background: var(--accent, #38BDF8);
                opacity: 0.18;
                box-shadow: 0 0 44px var(--accent, #38BDF8);
            }

            .metric-label {
                position: relative;
                z-index: 1;
                font-family: 'IBM Plex Mono', monospace;
                color: #8EA7B3;
                font-size: 0.72rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
            }

            .metric-value {
                position: relative;
                z-index: 1;
                color: #F8FEFF;
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                font-size: clamp(1.8rem, 3vw, 2.65rem);
                letter-spacing: -0.06em;
                font-weight: 700;
                margin-top: 0.48rem;
                line-height: 1.05;
            }

            .metric-sub {
                position: relative;
                z-index: 1;
                color: #9EB6BF;
                font-size: 0.82rem;
                line-height: 1.45;
                margin-top: 0.55rem;
                font-weight: 500;
            }

            .section-title {
                display: flex;
                flex-direction: column;
                gap: 0.2rem;
                margin: 1.2rem 0 0.78rem 0;
            }

            .section-title .section-eyebrow {
                color: #67E8F9;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.10em;
                text-transform: uppercase;
            }

            .section-title h2, .section-title h3 {
                margin: 0;
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                font-weight: 700;
                color: #F8FEFF;
                letter-spacing: -0.045em;
            }

            .section-title p {
                margin: 0.15rem 0 0 0;
                color: #9EB6BF;
                font-size: 0.92rem;
                line-height: 1.45;
            }

            .insight-card {
                min-height: 158px;
                border-radius: 22px;
                background:
                    linear-gradient(180deg, rgba(17, 31, 49, 0.94), rgba(11, 23, 36, 0.88));
                border: 1px solid rgba(148, 209, 214, 0.16);
                box-shadow: 0 18px 44px rgba(0, 0, 0, 0.22);
                padding: 1.05rem;
            }

            .insight-kicker {
                font-family: 'IBM Plex Mono', monospace;
                color: #67E8F9;
                font-size: 0.70rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-weight: 700;
                margin-bottom: 0.5rem;
            }

            .insight-title {
                color: #F8FEFF;
                font-family: 'Space Grotesk', 'Inter', sans-serif;
                font-size: 1.1rem;
                font-weight: 700;
                letter-spacing: -0.035em;
                line-height: 1.18;
            }

            .insight-copy {
                color: #9EB6BF;
                font-size: 0.84rem;
                line-height: 1.48;
                margin-top: 0.55rem;
            }

            /* Tabs */
            div[data-testid="stTabs"] button p {
                font-weight: 800;
                color: #9EB6BF;
            }

            div[data-testid="stTabs"] button[aria-selected="true"] p {
                color: #EAF7F5;
            }

            div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
                background-color: #38BDF8;
            }

            div[data-testid="stTabs"] [role="tablist"] {
                border-bottom: 1px solid rgba(148, 209, 214, 0.16);
            }

            .chart-frame {
                border-radius: 24px;
                border: 1px solid rgba(148, 209, 214, 0.16);
                background: rgba(14, 27, 42, 0.72);
                padding: 0.4rem 0.4rem 0.2rem 0.4rem;
                box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
            }

            .empty-state {
                border-radius: 26px;
                background: rgba(251, 113, 133, 0.11);
                border: 1px solid rgba(251, 113, 133, 0.26);
                padding: 1.2rem 1.35rem;
                color: #FFE4E6;
                font-weight: 600;
            }

            .data-note {
                border-left: 4px solid #38BDF8;
                background: rgba(14, 27, 42, 0.78);
                border-radius: 0 18px 18px 0;
                padding: 0.95rem 1rem;
                color: #C8DCE0;
                font-size: 0.88rem;
                line-height: 1.55;
                margin-top: 1rem;
                border-top: 1px solid rgba(148, 209, 214, 0.14);
                border-right: 1px solid rgba(148, 209, 214, 0.14);
                border-bottom: 1px solid rgba(148, 209, 214, 0.14);
            }

            .footer {
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(148, 209, 214, 0.16);
                color: #8EA7B3;
                font-size: 0.78rem;
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                flex-wrap: wrap;
            }

            .stDataFrame {
                border-radius: 22px;
                overflow: hidden;
                border: 1px solid rgba(148, 209, 214, 0.16);
                box-shadow: 0 18px 48px rgba(0, 0, 0, 0.22);
            }

            [data-testid="stDataFrame"] div,
            [data-testid="stDataFrame"] span {
                color: #EAF7F5;
            }

            div[data-testid="stDownloadButton"] button,
            div[data-testid="stButton"] button {
                background: linear-gradient(135deg, #0891B2, #14B8A6) !important;
                color: #F8FEFF !important;
                border: 1px solid rgba(125, 211, 252, 0.26) !important;
                border-radius: 16px !important;
                box-shadow: 0 14px 32px rgba(20, 184, 166, 0.18);
                font-weight: 800 !important;
            }

            div[data-testid="stDownloadButton"] button:hover,
            div[data-testid="stButton"] button:hover {
                border-color: rgba(186, 230, 253, 0.58) !important;
                transform: translateY(-1px);
            }

            .stAlert {
                background-color: rgba(251, 113, 133, 0.10) !important;
                color: #FFE4E6 !important;
                border: 1px solid rgba(251, 113, 133, 0.22) !important;
            }

            @media (max-width: 900px) {
                .hero-shell { padding: 24px; border-radius: 24px; }
                .hero-shell:after { opacity: 0.22; width: 100%; }
                .metric-card, .insight-card { min-height: auto; }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# -------------------------------------------------------------
# Data pipeline
# -------------------------------------------------------------
KAGGLE_DATASET_HANDLE = "venkatramakrishnan/india-water-quality-data"
PREFERRED_CSV_NAME = "IndiaAffectedWaterQualityAreas.csv"
REQUIRED_COLUMNS = [
    "State Name",
    "District Name",
    "Habitation Name",
    "Quality Parameter",
    "Year",
]


def find_dataset_csv(dataset_dir: str | Path) -> Path:
    """Find the most relevant CSV inside the KaggleHub download directory."""
    dataset_dir = Path(dataset_dir)
    csv_files = sorted(dataset_dir.rglob("*.csv"))

    if not csv_files:
        raise FileNotFoundError("Tidak ada file CSV di folder hasil download Kaggle.")

    # Prefer the known filename from the selected Kaggle dataset.
    for csv_file in csv_files:
        if csv_file.name == PREFERRED_CSV_NAME:
            return csv_file

    # Fallback: scan CSV headers and pick the first file containing the required columns.
    for csv_file in csv_files:
        try:
            columns = pd.read_csv(csv_file, encoding="cp1252", nrows=0).columns.tolist()
            if all(col in columns for col in REQUIRED_COLUMNS):
                return csv_file
        except Exception:
            continue

    available = ", ".join(file.name for file in csv_files[:8])
    raise FileNotFoundError(
        "CSV ditemukan, tetapi tidak ada yang memiliki kolom wajib. "
        f"File yang terdeteksi: {available}"
    )


@st.cache_data(show_spinner="Mengunduh dataset dari KaggleHub dan menyiapkan data dashboard...")
def load_and_aggregate_data(file_bytes=None, uploaded_filename=None):
    """Load data from KaggleHub by default, clean fields, and aggregate to State-District-Year-Parameter.

    Priority:
    1. Uploaded CSV from sidebar, when provided.
    2. KaggleHub dataset: venkatramakrishnan/india-water-quality-data.
    """
    source_label = "KaggleHub"
    source_detail = KAGGLE_DATASET_HANDLE

    if file_bytes is not None:
        df = pd.read_csv(io.BytesIO(file_bytes), encoding="cp1252")
        source_label = "Uploaded CSV"
        source_detail = uploaded_filename or "manual_upload.csv"
    else:
        if kagglehub is None:
            return None, [
                "Package `kagglehub` belum terpasang. Tambahkan `kagglehub` ke requirements.txt, "
                "lalu jalankan ulang aplikasi."
            ]

        try:
            dataset_path = kagglehub.dataset_download(KAGGLE_DATASET_HANDLE)
            csv_path = find_dataset_csv(dataset_path)
            df = pd.read_csv(csv_path, encoding="cp1252")
            source_detail = str(csv_path)
        except Exception as exc:
            return None, [
                "Dataset Kaggle belum dapat dimuat.",
                f"Detail error: {exc}",
                "Pastikan koneksi internet tersedia dan, bila diperlukan, konfigurasi KAGGLE_USERNAME serta KAGGLE_KEY sudah benar."
            ]

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return None, ["Kolom wajib tidak ditemukan: " + ", ".join(missing_cols)]

    for col in REQUIRED_COLUMNS:
        df[col] = df[col].fillna("Tidak diketahui")

    df["state"] = (
        df["State Name"]
        .replace("CHATTISGARH", "CHHATTISGARH")
        .astype(str)
        .str.strip()
        .str.upper()
    )
    df["district"] = df["District Name"].astype(str).str.strip().str.upper()
    df["parameter"] = df["Quality Parameter"].astype(str).str.strip()

    # Robust year extraction. This avoids comma/float display problems in the UI.
    df["year"] = pd.to_numeric(
        df["Year"].astype(str).str.extract(r"(\d{4})")[0],
        errors="coerce",
    )
    invalid_years = int(df["year"].isna().sum())
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int).astype(str)

    agg_df = (
        df.groupby(["state", "district", "year", "parameter"], dropna=False)
        .agg(
            habitations=("Habitation Name", "nunique"),
            records=("Habitation Name", "size"),
        )
        .reset_index()
    )
    agg_df["district_key"] = agg_df["state"] + " || " + agg_df["district"]
    agg_df["district_label"] = agg_df["district"].str.title() + " · " + agg_df["state"].str.title()
    agg_df["state_title"] = agg_df["state"].str.title().replace({"Orissa": "Odisha"})

    metadata = {
        "source_label": source_label,
        "source_detail": source_detail,
        "dataset_handle": KAGGLE_DATASET_HANDLE,
        "raw_rows": len(df) + invalid_years,
        "clean_rows": len(df),
        "invalid_years": invalid_years,
        "aggregated_rows": len(agg_df),
    }
    return agg_df, metadata


def apply_optional_multiselect_filter(dataframe, column, selected_values):
    if selected_values:
        return dataframe[dataframe[column].isin(selected_values)]
    return dataframe


def fmt_int(value):
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value):
    return f"{value:.1f}%".replace(".", ",")


def short_list(values, all_label, max_items=3):
    if not values:
        return all_label
    values = list(values)
    if len(values) <= max_items:
        return ", ".join(str(v).title() for v in values)
    return ", ".join(str(v).title() for v in values[:max_items]) + f" +{len(values)-max_items} lainnya"


def section_title(eyebrow, title, description=""):
    st.markdown(
        f"""
        <div class="section-title">
            <div class="section-eyebrow">{escape(eyebrow)}</div>
            <h2>{escape(title)}</h2>
            <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label, value, subtext, accent):
    st.markdown(
        f"""
        <div class="metric-card" style="--accent:{accent};">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(str(value))}</div>
            <div class="metric-sub">{escape(subtext)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(kicker, title, copy):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-kicker">{escape(kicker)}</div>
            <div class="insight-title">{escape(title)}</div>
            <div class="insight-copy">{escape(copy)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig, height=360, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=24, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif", color=INK, size=12),
        hoverlabel=dict(
            bgcolor="#020617",
            bordercolor="#38BDF8",
            font_size=12,
            font_family="Inter",
            font_color="#F8FEFF",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None,
            font=dict(color=MUTED),
        ) if legend else None,
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(148, 209, 214, 0.12)",
        zeroline=False,
        linecolor="rgba(148, 209, 214, 0.22)",
        tickfont=dict(color=MUTED),
        title_font=dict(color=MUTED),
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        linecolor="rgba(148, 209, 214, 0.22)",
        tickfont=dict(color=MUTED),
        title_font=dict(color=MUTED),
    )
    return fig


# -------------------------------------------------------------
# Sidebar controls
# -------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="margin-bottom:1rem;">
        <div class="eyebrow">Aquifer lens</div>
        <h2 style="font-family:'Space Grotesk'; letter-spacing:-0.04em; margin:.8rem 0 .35rem 0; color:#FFFFFF;">Filter kendali</h2>
        <p style="font-size:.82rem; color:#9EB6BF; line-height:1.55; margin:0;">Pilih lebih dari satu nilai untuk membandingkan tahun, parameter, dan wilayah secara bersamaan.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.sidebar.file_uploader(
    "Gunakan CSV manual bila diperlukan",
    type=["csv"],
    help=(
        "Opsional. Jika kosong, aplikasi otomatis mengunduh dataset terbaru dari "
        "KaggleHub: venkatramakrishnan/india-water-quality-data."
    ),
)

file_bytes = uploaded_file.getvalue() if uploaded_file is not None else None
agg_data, load_status = load_and_aggregate_data(
    file_bytes=file_bytes,
    uploaded_filename=uploaded_file.name if uploaded_file is not None else None,
)

if agg_data is None:
    st.error("Data belum dapat dimuat. " + " ".join(load_status))
    st.stop()

st.sidebar.success(f"Sumber data aktif: {load_status['source_label']}")
st.sidebar.caption(f"Detail sumber: {load_status['source_detail']}")

available_states = sorted(agg_data["state"].dropna().unique().tolist())
available_years = sorted(agg_data["year"].dropna().unique().tolist())
available_params = [param for param in PARAMETER_NOTES if param in agg_data["parameter"].unique()]
available_params += sorted([p for p in agg_data["parameter"].dropna().unique().tolist() if p not in available_params])

filter_states = st.sidebar.multiselect(
    "State",
    options=available_states,
    default=[],
    placeholder="Semua state",
    help="Kosongkan untuk menampilkan seluruh state.",
)

district_source = agg_data.copy()
if filter_states:
    district_source = district_source[district_source["state"].isin(filter_states)]

district_options = (
    district_source[["district_key", "district_label"]]
    .drop_duplicates()
    .sort_values("district_label")
)
district_label_lookup = dict(zip(district_options["district_key"], district_options["district_label"]))

filter_district_keys = st.sidebar.multiselect(
    "District",
    options=district_options["district_key"].tolist(),
    default=[],
    format_func=lambda key: district_label_lookup.get(key, key),
    placeholder="Semua district",
    help="Daftar district mengikuti State yang dipilih.",
)

filter_years = st.sidebar.multiselect(
    "Tahun",
    options=available_years,
    default=available_years,
    placeholder="Pilih satu atau lebih tahun",
)

filter_params = st.sidebar.multiselect(
    "Parameter kualitas air",
    options=available_params,
    default=available_params,
    placeholder="Pilih satu atau lebih parameter",
    format_func=lambda p: f"{p} — {PARAMETER_NOTES.get(p, 'Parameter')}",
)

ranking_level = st.sidebar.radio(
    "Peringkat wilayah",
    options=["State", "District"],
    horizontal=True,
    index=1,
)

show_records = st.sidebar.toggle(
    "Tampilkan kolom record mentah",
    value=True,
    help="Aktifkan bila ingin melihat jumlah baris mentah yang membentuk agregasi.",
)

st.sidebar.markdown("---")
st.sidebar.caption("Contoh: pilih 2009 dan 2012 sekaligus, lalu pilih Iron, Nitrate, dan Salinity untuk membandingkan pola parameter.")

# -------------------------------------------------------------
# Filter execution
# -------------------------------------------------------------
filtered_df = agg_data.copy()
filtered_df = apply_optional_multiselect_filter(filtered_df, "state", filter_states)
filtered_df = apply_optional_multiselect_filter(filtered_df, "district_key", filter_district_keys)
filtered_df = apply_optional_multiselect_filter(filtered_df, "year", filter_years)
filtered_df = apply_optional_multiselect_filter(filtered_df, "parameter", filter_params)

# -------------------------------------------------------------
# Header and selected filter strip
# -------------------------------------------------------------
st.markdown(
    """
    <div class="hero-shell">
        <div class="hero-content">
            <div class="eyebrow">Water quality · district drilldown</div>
            <div class="hero-title">India Water<br><span>Quality Atlas</span></div>
            <div class="hero-subtitle">
                Dashboard BI untuk membaca sebaran catatan wilayah terdampak isu kualitas air berdasarkan State, District, Tahun, dan Parameter. Dirancang sebagai ruang kendali eksploratif untuk menentukan wilayah prioritas dan parameter dominan.
            </div>
            <div class="hero-meta-row">
                <div class="hero-meta">🧭 State → District</div>
                <div class="hero-meta">🧪 Iron · Salinity · Fluoride · Arsenic · Nitrate</div>
                <div class="hero-meta">📅 Multi-year comparison</div>
                <div class="hero-meta">🔗 KaggleHub latest dataset</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

selected_district_labels = [district_label_lookup.get(key, key) for key in filter_district_keys]
filter_chips = [
    ("State", short_list(filter_states, "Semua state")),
    ("District", short_list(selected_district_labels, "Semua district")),
    ("Tahun", short_list(filter_years, "Semua tahun")),
    ("Parameter", short_list(filter_params, "Semua parameter")),
]

chips_html = "".join(
    f"<span class='filter-chip'>{escape(label)}: {escape(value)}</span>"
    for label, value in filter_chips
)
st.markdown(
    f"<div class='filter-strip'><strong>Filter aktif</strong>{chips_html}</div>",
    unsafe_allow_html=True,
)

if filtered_df.empty:
    st.markdown(
        """
        <div class="empty-state">
            Tidak ada data pada kombinasi filter yang dipilih. Kurangi pilihan District, aktifkan kembali tahun lain, atau pilih parameter tambahan untuk memperluas cakupan data.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# -------------------------------------------------------------
# KPI calculations
# -------------------------------------------------------------
total_habitations = int(filtered_df["habitations"].sum())
total_records = int(filtered_df["records"].sum())
total_states_active = int(filtered_df["state"].nunique())
total_districts_active = int(filtered_df["district_key"].nunique())

param_totals = filtered_df.groupby("parameter", as_index=False)["habitations"].sum().sort_values("habitations", ascending=False)
top_pollutant = param_totals.iloc[0]["parameter"] if not param_totals.empty else "N/A"
top_pollutant_value = int(param_totals.iloc[0]["habitations"]) if not param_totals.empty else 0
top_pollutant_share = (top_pollutant_value / total_habitations * 100) if total_habitations else 0
color_accent = PALETTE_MAP.get(top_pollutant, RESERVOIR)

top_state_series = filtered_df.groupby("state_title")["habitations"].sum().sort_values(ascending=False)
top_state = top_state_series.index[0] if not top_state_series.empty else "N/A"
top_state_share = (top_state_series.iloc[0] / total_habitations * 100) if total_habitations and not top_state_series.empty else 0

top_district_series = filtered_df.groupby("district_label")["habitations"].sum().sort_values(ascending=False)
top_district = top_district_series.index[0] if not top_district_series.empty else "N/A"
top_district_share = (top_district_series.iloc[0] / total_habitations * 100) if total_habitations and not top_district_series.empty else 0

section_title(
    "Executive pulse",
    "Ringkasan kondisi terfilter",
    "Kartu ini berubah mengikuti pilihan multi-filter di sidebar.",
)

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    metric_card("Habitation terdampak", fmt_int(total_habitations), "Akumulasi habitation unik pada kombinasi data terfilter.", RESERVOIR)
with kpi_col2:
    metric_card("State aktif", fmt_int(total_states_active), "Jumlah state yang masih muncul setelah filter diterapkan.", AQUIFER)
with kpi_col3:
    metric_card("District aktif", fmt_int(total_districts_active), "Jumlah district unik yang tercakup dalam analisis saat ini.", SEDIMENT)
with kpi_col4:
    metric_card("Parameter dominan", top_pollutant, f"Kontribusi {fmt_pct(top_pollutant_share)} dari habitation terfilter.", color_accent)

section_title(
    "Analytical cues",
    "Insight cepat untuk membaca prioritas",
    "Gunakan sebagai narasi awal sebelum masuk ke grafik detail.",
)

ins_col1, ins_col2, ins_col3 = st.columns(3)
with ins_col1:
    insight_card(
        "Dominant pollutant",
        f"{top_pollutant} memimpin pola isu",
        f"Parameter ini menyumbang {fmt_int(top_pollutant_value)} habitation atau {fmt_pct(top_pollutant_share)} dari total data terfilter.",
    )
with ins_col2:
    insight_card(
        "State concentration",
        f"{top_state} menjadi state prioritas",
        f"Wilayah ini menyumbang sekitar {fmt_pct(top_state_share)} dari total habitation terfilter.",
    )
with ins_col3:
    insight_card(
        "District lens",
        f"{top_district} muncul paling tinggi",
        f"District ini berkontribusi sekitar {fmt_pct(top_district_share)} dari total habitation terfilter.",
    )

# -------------------------------------------------------------
# Tabs
# -------------------------------------------------------------
overview_tab, priority_tab, detail_tab = st.tabs([
    "🗺️ Atlas overview",
    "📊 Prioritas wilayah",
    "📋 Data detail",
])

with overview_tab:
    section_title(
        "Spatial view",
        "Dominasi parameter pada peta State",
        "Peta menggunakan batas State. Filter District tetap memengaruhi angka yang diagregasikan ke State terkait.",
    )

    map_data = filtered_df.groupby(["state_title", "parameter"], as_index=False)["habitations"].sum()
    map_data = map_data.sort_values("habitations", ascending=False).drop_duplicates(["state_title"])

    india_geojson_url = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
    fig_map = px.choropleth(
        map_data,
        geojson=india_geojson_url,
        featureidkey="properties.ST_NM",
        locations="state_title",
        color="parameter",
        color_discrete_map=PALETTE_MAP,
        hover_name="state_title",
        hover_data={
            "state_title": False,
            "parameter": True,
            "habitations": ":,",
        },
        labels={"parameter": "Parameter dominan", "habitations": "Habitation terdampak"},
    )
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)", lakecolor="#07111F")
    fig_map.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Arial, sans-serif", color=INK, size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None,
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    comp_col1, comp_col2 = st.columns([0.9, 1.1])
    with comp_col1:
        section_title(
            "Composition",
            "Komposisi parameter",
            "Melihat proporsi tiap parameter terhadap total habitation terfilter.",
        )
        donut_data = param_totals.copy()
        fig_donut = px.pie(
            donut_data,
            names="parameter",
            values="habitations",
            hole=0.62,
            color="parameter",
            color_discrete_map=PALETTE_MAP,
        )
        fig_donut.update_traces(
            textposition="outside",
            textinfo="label+percent",
            marker=dict(line=dict(color="#07111F", width=2)),
        )
        fig_donut.add_annotation(
            text=f"<b>{fmt_int(total_habitations)}</b><br>habitations",
            showarrow=False,
            font=dict(size=16, color=INK),
        )
        style_figure(fig_donut, height=360, legend=False)
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    with comp_col2:
        section_title(
            "Parameter rank",
            "Urutan parameter berdasarkan habitation",
            "Membantu menentukan isu parameter yang paling banyak tercatat.",
        )
        fig_param = px.bar(
            param_totals.sort_values("habitations"),
            x="habitations",
            y="parameter",
            orientation="h",
            color="parameter",
            color_discrete_map=PALETTE_MAP,
            labels={"habitations": "Habitation terdampak", "parameter": "Parameter"},
            text="habitations",
        )
        fig_param.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
        style_figure(fig_param, height=360, legend=False)
        st.plotly_chart(fig_param, use_container_width=True, config={"displayModeBar": False})

with priority_tab:
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        section_title(
            "Time series",
            "Tren temporal berdasarkan parameter",
            "Membandingkan dinamika antarparameter pada tahun yang dipilih.",
        )
        trend_data = (
            filtered_df.groupby(["year", "parameter"], as_index=False)["habitations"]
            .sum()
            .sort_values("year")
        )
        fig_line = px.line(
            trend_data,
            x="year",
            y="habitations",
            color="parameter",
            markers=True,
            color_discrete_map=PALETTE_MAP,
            labels={"year": "Tahun", "habitations": "Habitation terdampak", "parameter": "Parameter"},
        )
        fig_line.update_traces(line=dict(width=3), marker=dict(size=8, line=dict(width=2, color="#07111F")))
        fig_line.update_xaxes(type="category", categoryorder="array", categoryarray=available_years)
        style_figure(fig_line, height=390, legend=True)
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

    with chart_col2:
        label_col = "state_title" if ranking_level == "State" else "district_label"
        label_name = "State" if ranking_level == "State" else "District"
        section_title(
            "Regional rank",
            f"Top 10 {label_name} berdasarkan habitation",
            "Ranking dihitung dari total habitation pada kombinasi filter aktif.",
        )
        ranking_data = filtered_df.groupby([label_col, "parameter"], as_index=False)["habitations"].sum()
        top_regions = (
            filtered_df.groupby(label_col)["habitations"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .index
        )
        ranking_data = ranking_data[ranking_data[label_col].isin(top_regions)].sort_values("habitations", ascending=True)
        fig_bar = px.bar(
            ranking_data,
            y=label_col,
            x="habitations",
            color="parameter",
            orientation="h",
            color_discrete_map=PALETTE_MAP,
            labels={label_col: label_name, "habitations": "Habitation terdampak", "parameter": "Parameter"},
        )
        style_figure(fig_bar, height=390, legend=True)
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    section_title(
        "Cross-section",
        "Heatmap konsentrasi State x Parameter",
        "Menunjukkan kombinasi State dan parameter dengan jumlah habitation tertinggi.",
    )
    top_heat_states = (
        filtered_df.groupby("state_title")["habitations"]
        .sum()
        .sort_values(ascending=False)
        .head(12)
        .index
    )
    heat_df = filtered_df[filtered_df["state_title"].isin(top_heat_states)]
    heat_pivot = (
        heat_df.groupby(["state_title", "parameter"])["habitations"]
        .sum()
        .reset_index()
        .pivot(index="state_title", columns="parameter", values="habitations")
        .fillna(0)
    )
    heat_pivot = heat_pivot.loc[top_heat_states]
    fig_heat = px.imshow(
        heat_pivot,
        aspect="auto",
        text_auto=".0f",
        color_continuous_scale=["#0B1724", "#0E7490", "#38BDF8", "#F59E0B"],
        labels=dict(x="Parameter", y="State", color="Habitation"),
    )
    style_figure(fig_heat, height=430, legend=False)
    fig_heat.update_xaxes(side="top")
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

with detail_tab:
    section_title(
        "Drilldown table",
        "Matriks geografis teragregasi",
        "Gunakan tabel ini untuk membaca rincian State, District, Tahun, Parameter, dan jumlah habitation.",
    )

    table_cols = ["state", "district", "year", "parameter", "habitations"]
    if show_records:
        table_cols.append("records")
    display_table_df = (
        filtered_df[table_cols]
        .sort_values(by="habitations", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        display_table_df,
        column_config={
            "state": st.column_config.TextColumn("State", width="medium"),
            "district": st.column_config.TextColumn("District", width="medium"),
            "year": st.column_config.TextColumn("Tahun", width="small"),
            "parameter": st.column_config.TextColumn("Parameter", width="medium"),
            "habitations": st.column_config.NumberColumn("Habitation unik", format="%d"),
            "records": st.column_config.NumberColumn("Record mentah", format="%d"),
        },
        use_container_width=True,
        hide_index=True,
    )

    csv_bytes = display_table_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Unduh data terfilter (.csv)",
        data=csv_bytes,
        file_name="india_water_quality_filtered.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown(
        f"""
        <div class="data-note">
            <strong>Catatan interpretasi:</strong> angka <em>habitations</em> adalah jumlah nama habitation unik dalam kombinasi State-District-Tahun-Parameter. Angka ini adalah catatan lokasi/wilayah terdampak, bukan kadar kimia air atau tingkat bahaya langsung.<br><br>
            Sumber data aktif: <strong>{escape(str(load_status['source_label']))}</strong> · Dataset: <strong>{escape(str(load_status['dataset_handle']))}</strong><br>
            Baris mentah terbaca: <strong>{fmt_int(load_status['raw_rows'])}</strong> · Baris valid setelah pembersihan tahun: <strong>{fmt_int(load_status['clean_rows'])}</strong> · Tahun tidak valid: <strong>{fmt_int(load_status['invalid_years'])}</strong> · Baris agregat aktif: <strong>{fmt_int(len(display_table_df))}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="footer">
        <span>India Water Quality Atlas · Executive BI Dashboard</span>
        <span>Designed for exploratory monitoring · State–District drilldown</span>
    </div>
    """,
    unsafe_allow_html=True,
)
