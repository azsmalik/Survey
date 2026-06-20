# ============================================================
# LPG Country Demand Survey Dashboard
# Country-level Streamlit dashboard for Pakistan LPG survey analysis.
#
# Run locally:
#   pip install -r requirements.txt
#   streamlit run DashLPG.py
#
# Primary data path requested by user:
#   C:\Ahmed Zahid Malik\Python\LPG Survey Dashboard\Clean-Data-lpg-survey.csv
#
# Deployment note:
#   For Streamlit Cloud, keep Clean-Data-lpg-survey.csv in the same GitHub
#   repository folder as this app file, or upload the CSV from the sidebar.
# ============================================================

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence, List, Dict, Tuple
import ast
import re
import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="Pakistan LPG Survey Dashboard",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
BRAND = {
    "green": "#0B9F4D",
    "green_dark": "#08783B",
    "red": "#E4312B",
    "orange": "#F59E0B",
    "blue": "#1D4ED8",
    "navy": "#102A43",
    "ink": "#111827",
    "muted": "#64748B",
    "bg": "#F6F8FB",
    "card": "#FFFFFF",
    "line": "#E5E7EB",
    "purple": "#7C3AED",
    "teal": "#0F766E",
    "gray": "#64748B",
}

REQUESTED_WINDOWS_PATH = Path(r"C:\Ahmed Zahid Malik\Python\LPG Survey Dashboard\Clean-Data-lpg-survey.csv")
DEFAULT_PATHS = [
    REQUESTED_WINDOWS_PATH,
    Path(__file__).resolve().with_name("Clean-Data-lpg-survey.csv"),
    Path(__file__).resolve().with_name("LPG_Survey_Country_Level_Cleaned_PowerBI.csv"),
    Path("/mnt/data/Clean-Data-lpg-survey.csv"),
]

CITY_ANALYSIS_RULE = (
    "City-level analysis is intentionally limited to: "
    "(1) respondent count by city and (2) current LPG user/adoption percentage by city. "
    "All deep behaviour analysis is shown at Pakistan/country level."
)

APP_FLAGS = {
    "Cooking": "D1 LPG Cooking",
    "Space Heating": "D1 LPG Space Heating",
    "Water Heating": "D1 LPG Water Heating",
    "Generator Use": "D1 LPG Generator Use",
    "Business / Process Use": "D1 LPG Business Process",
}

FUEL_PREFIXES = {
    "LPG": "D1 LPG",
    "Natural Gas": "D1 Natural Gas",
    "Electricity": "D1 Electricity",
    "Solar": "D1 Solar",
    "Solid Fuel": "D1 Solid Fuel",
    "Kerosene": "D1 Kerosene",
    "Diesel / Petrol": "D1 Diesel Petrol",
    "Other Fuel": "D1 Other Fuel",
}

APPLICATION_SUFFIXES = ["Cooking", "Space Heating", "Water Heating", "Generator Use", "Business Process"]

CATEGORY_MAP = {
    "Restaurant / Hotel / Catering / Dhaba": "Restaurant / Hotel / Catering",
    "Residential / Household": "Residential",
    "Transport / Vehicle Fuel User": "Transport",
    "LPG Supplier / Distributor / Dealer / Refill Point": "Supplier / Distributor",
    "Tandoor Shop / Bakery / Food Outlet": "Tandoor / Bakery",
    "Other Commercial Business": "Other Commercial",
    "Hospital / School / Institutional Kitchen": "Institutional Kitchen",
    "Other Consumer / User": "Other Consumer",
    "Industrial / Factory": "Industrial",
    "Residential Apartment / Society Management Office": "Society / Apartment Mgmt",
}

# ------------------------------------------------------------
# CSS Styling
# ------------------------------------------------------------
st.markdown(
    f"""
    <style>
        :root {{
            --green: {BRAND['green']};
            --red: {BRAND['red']};
            --navy: {BRAND['navy']};
            --ink: {BRAND['ink']};
            --muted: {BRAND['muted']};
            --line: {BRAND['line']};
        }}
        html, body, [class*="css"] {{
            font-family: Inter, Segoe UI, Arial, sans-serif;
        }}
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(11,159,77,0.18), transparent 33%),
                radial-gradient(circle at top right, rgba(228,49,43,0.14), transparent 33%),
                linear-gradient(135deg, #F8FAFC 0%, #FFFFFF 48%, #FFF7F7 100%);
        }}
        .block-container {{
            max-width: 1660px;
            padding-top: 0.65rem;
            padding-bottom: 2.4rem;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border-right: 5px solid var(--green);
        }}
        .hero {{
            background: #FFFFFF;
            border: 1px solid var(--line);
            border-top: 8px solid var(--green);
            border-bottom: 4px solid var(--red);
            border-radius: 28px;
            box-shadow: 0 16px 38px rgba(16,42,67,0.14);
            padding: 24px 28px;
            margin: 0 0 18px 0;
        }}
        .hero-title {{
            color: var(--navy);
            font-size: 38px;
            line-height: 1.08;
            font-weight: 950;
            margin-bottom: 6px;
        }}
        .hero-subtitle {{
            color: #475569;
            font-size: 15px;
            line-height: 1.48;
            max-width: 1200px;
        }}
        .pill {{
            display: inline-block;
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            color: #334155;
            border-radius: 999px;
            padding: 7px 12px;
            margin: 12px 6px 0 0;
            font-size: 12px;
            font-weight: 850;
        }}
        .rule-box {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-left: 7px solid var(--red);
            border-radius: 18px;
            box-shadow: 0 8px 22px rgba(16,42,67,0.06);
            padding: 13px 16px;
            color: #334155;
            font-size: 13.5px;
            line-height: 1.48;
            margin: 6px 0 17px 0;
        }}
        .section-title {{
            color: var(--navy);
            font-size: 30px;
            font-weight: 950;
            margin: 12px 0 4px 0;
        }}
        .section-subtitle {{
            color: #64748B;
            font-size: 14px;
            margin-bottom: 14px;
        }}
        .kpi-card {{
            background: #FFFFFF;
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 16px 17px 14px 17px;
            min-height: 122px;
            box-shadow: 0 9px 23px rgba(16,42,67,0.09);
            position: relative;
            overflow: hidden;
        }}
        .kpi-card:before {{
            content: "";
            height: 7px;
            background: var(--accent);
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
        }}
        .kpi-label {{
            color: #64748B;
            font-size: 11px;
            line-height: 1.25;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: .06em;
        }}
        .kpi-value {{
            color: var(--navy);
            font-size: 27px;
            line-height: 1.1;
            font-weight: 950;
            margin-top: 9px;
        }}
        .kpi-note {{
            color: #475569;
            font-size: 12px;
            margin-top: 8px;
        }}
        .chart-card {{
            background: #FFFFFF;
            border: 1px solid var(--line);
            border-top: 5px solid var(--accent);
            border-radius: 22px;
            box-shadow: 0 9px 23px rgba(16,42,67,0.09);
            padding: 10px 12px 11px 12px;
            margin: 0 0 18px 0;
        }}
        .analysis-box {{
            margin-top: 7px;
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            border-left: 5px solid var(--accent);
            border-radius: 14px;
            padding: 10px 12px;
            color: #334155;
            font-size: 12.8px;
            line-height: 1.45;
        }}
        .analysis-box b {{ color: var(--navy); }}
        .sidebar-note {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-left: 5px solid var(--green);
            border-radius: 15px;
            padding: 10px 12px;
            margin: 6px 0 10px 0;
            color: #334155;
            font-size: 12.8px;
            line-height: 1.4;
        }}
        .note-box {{
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-left: 7px solid var(--green);
            border-right: 4px solid var(--red);
            border-radius: 17px;
            box-shadow: 0 6px 18px rgba(16,42,67,0.06);
            padding: 14px 16px;
            color: #334155;
            font-size: 14px;
            line-height: 1.5;
            margin: 8px 0 18px 0;
        }}
        .js-plotly-plot .xtick text,
        .js-plotly-plot .ytick text,
        .js-plotly-plot .gtitle,
        .js-plotly-plot .xtitle,
        .js-plotly-plot .ytitle,
        .js-plotly-plot .legendtext,
        .js-plotly-plot .bartext {{
            fill: #111827 !important;
            opacity: 1 !important;
            color: #111827 !important;
            font-weight: 700 !important;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def existing_path(paths: Sequence[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


def normalize_text(x) -> str:
    if pd.isna(x):
        return "Unknown"
    text = re.sub(r"\s+", " ", str(x).strip())
    if text == "" or text.lower() in {"nan", "none", "null"}:
        return "Unknown"
    return text


def to_num(x) -> float:
    try:
        if pd.isna(x):
            return np.nan
        text = str(x).strip().replace(",", "")
        if text == "":
            return np.nan
        return float(text)
    except Exception:
        return np.nan


def yes_flag(x) -> int:
    text = normalize_text(x).lower()
    return int(text.startswith("yes") or text in {"true", "1", "selected", "y"})


def bool_flag(x) -> int:
    text = normalize_text(x).lower()
    return int(text in {"true", "1", "yes", "selected", "y"})


def non_blank_series(s: pd.Series) -> pd.Series:
    return s.notna() & s.astype(str).str.strip().ne("") & ~s.astype(str).str.strip().str.lower().isin(["nan", "none", "null"])


def safe_div(num: float, den: float) -> float:
    if den is None or pd.isna(den) or den == 0:
        return np.nan
    return float(num) / float(den)


def pct(num: float, den: float) -> float:
    value = safe_div(num, den)
    return value * 100 if pd.notna(value) else np.nan


def fmt_int(x) -> str:
    if pd.isna(x):
        return "-"
    return f"{float(x):,.0f}"


def fmt_1(x) -> str:
    if pd.isna(x):
        return "-"
    return f"{float(x):,.1f}"


def fmt_pct(x) -> str:
    if pd.isna(x):
        return "-"
    return f"{float(x):,.1f}%"


def fmt_pkr(x) -> str:
    if pd.isna(x):
        return "-"
    return f"PKR {float(x):,.0f}"


def sample_band(n: float) -> str:
    try:
        n = float(n)
    except Exception:
        return "Unknown sample"
    if n >= 50:
        return "Strong sample"
    if n >= 20:
        return "Use carefully"
    if n > 0:
        return "Indicative only"
    return "No valid base"


def parse_multi(value) -> List[str]:
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return [normalize_text(v) for v in value if normalize_text(v) != "Unknown"]
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null"}:
        return []
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, (list, tuple)):
                return [normalize_text(v) for v in parsed if normalize_text(v) != "Unknown"]
        except Exception:
            pass
    parts = re.split(r",|;|\|", text)
    return [normalize_text(p) for p in parts if normalize_text(p) != "Unknown"]


def cylinder_kg_from_row(row: pd.Series, prefix: str = "C4") -> float:
    weights = {
        "5kg Cylinders": 5,
        "11 8kg Cylinders": 11.8,
        "15kg Cylinders": 15,
        "45kg Cylinders": 45,
    }
    total = 0.0
    for suffix, kg in weights.items():
        col = f"{prefix} {suffix}"
        if col in row.index:
            count = to_num(row.get(col))
            if pd.notna(count):
                total += count * kg
    other_count = to_num(row.get(f"{prefix} Other Cylinder Count")) if f"{prefix} Other Cylinder Count" in row.index else np.nan
    other_size = to_num(row.get(f"{prefix} Other Cylinder Size")) if f"{prefix} Other Cylinder Size" in row.index else np.nan
    if pd.notna(other_count) and pd.notna(other_size):
        total += other_count * other_size
    return total if total > 0 else np.nan


def likely_cylinder_size_kg(row: pd.Series) -> float:
    # Prefer the selected cylinder size with positive count. Default to common 11.8kg domestic cylinder.
    checks = [
        ("C4 5kg Cylinders", 5),
        ("C4 11 8kg Cylinders", 11.8),
        ("C4 15kg Cylinders", 15),
        ("C4 45kg Cylinders", 45),
    ]
    for col, kg in checks:
        if col in row.index and pd.notna(to_num(row.get(col))) and to_num(row.get(col)) > 0:
            return kg
    other = to_num(row.get("C4 Other Cylinder Size")) if "C4 Other Cylinder Size" in row.index else np.nan
    if pd.notna(other) and other > 0:
        return other
    return 11.8


def monthly_lpg_kg(row: pd.Series) -> float:
    value = to_num(row.get("C3 LPG Monthly Quantity Value"))
    unit = normalize_text(row.get("C3 LPG Monthly Quantity Unit")).lower()
    if pd.isna(value):
        return np.nan
    if "kg" in unit:
        return value
    if unit == "mt" or "metric" in unit:
        return value * 1000
    if "cylinder" in unit:
        from_counts = cylinder_kg_from_row(row, "C4")
        if pd.notna(from_counts):
            return from_counts
        return value * likely_cylinder_size_kg(row)
    return np.nan


def price_pkr_per_kg(row: pd.Series) -> float:
    value = to_num(row.get("C6 LPG Price Value"))
    unit = normalize_text(row.get("C6 LPG Price Unit")).lower()
    if pd.isna(value):
        return np.nan
    if "kg" in unit:
        return value
    if unit == "per mt" or "mt" in unit:
        return value / 1000
    if "cylinder" in unit:
        size = likely_cylinder_size_kg(row)
        return value / size if size else np.nan
    return np.nan


def transport_lpg_kg(row: pd.Series) -> float:
    value = to_num(row.get("K6 Transport LPG Monthly Quantity Value"))
    unit = normalize_text(row.get("K6 Transport LPG Monthly Quantity Unit")).lower()
    if pd.isna(value):
        return np.nan
    if "kg" in unit:
        return value
    if "mt" in unit:
        return value * 1000
    return np.nan


def supplier_sold_mt(row: pd.Series) -> float:
    value = to_num(row.get("SP5 Monthly LPG Sold Value"))
    unit = normalize_text(row.get("SP5 Monthly LPG Sold Unit")).lower()
    if pd.isna(value):
        return np.nan
    if "kg" in unit:
        return value / 1000
    if "mt" in unit:
        return value
    return np.nan


def get_col(df: pd.DataFrame, name: str, default=np.nan) -> pd.Series:
    if name in df.columns:
        return df[name]
    return pd.Series(default, index=df.index)


_CHART_RENDER_COUNTER = 0


def style_fig(fig: go.Figure, title: str, height: int = 520) -> go.Figure:
    """Apply one clean visual standard across the dashboard.

    The larger top/bottom margins and hidden Plotly modebar prevent the overlap
    visible in screenshots while preserving readable labels.
    """
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.02, y=0.985, font=dict(size=20, color=BRAND["navy"])),
        height=height,
        margin=dict(l=150, r=55, t=104, b=104),
        font=dict(size=13, color=BRAND["ink"]),
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1, font=dict(size=12, color=BRAND["ink"])),
        uniformtext=dict(minsize=11, mode="show"),
        hoverlabel=dict(bgcolor="white", font_size=12, font_color=BRAND["ink"]),
    )
    fig.update_xaxes(showgrid=False, automargin=True, title_standoff=16, title_font=dict(size=14, color=BRAND["ink"]), tickfont=dict(size=12, color=BRAND["ink"]), linecolor="#CBD5E1", tickcolor="#CBD5E1")
    fig.update_yaxes(gridcolor="rgba(16,42,67,0.12)", automargin=True, title_standoff=16, title_font=dict(size=14, color=BRAND["ink"]), tickfont=dict(size=12, color=BRAND["ink"]), separatethousands=True, linecolor="#CBD5E1", tickcolor="#CBD5E1")

    # Do not call fig.update_traces(textfont=...) globally. Plotly Box/Histogram traces
    # do not support every text property and can raise ValueError.
    for trace in fig.data:
        if getattr(trace, "type", "") in {"bar", "scatter", "pie", "treemap", "sunburst"}:
            try:
                trace.textfont = dict(color=BRAND["ink"], size=12)
            except Exception:
                pass
    return fig


def empty_fig(title: str, msg: str = "No data available for the selected filters") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=16, color=BRAND["muted"]))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return style_fig(fig, title, 430)


def kpi(label: str, value: str, note: str, accent: str) -> str:
    return f"""
    <div class="kpi-card" style="--accent:{accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-note">{note}</div>
    </div>
    """


def kpi_row(cards: Sequence[str], columns: int = 4) -> None:
    cols = st.columns(columns, gap="medium")
    for i, card in enumerate(cards):
        with cols[i % columns]:
            st.markdown(card, unsafe_allow_html=True)


def section(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def chart_card(title: str, fig: go.Figure, purpose: str, formula: str, axis_note: str, accent: str = "green") -> None:
    global _CHART_RENDER_COUNTER
    _CHART_RENDER_COUNTER += 1
    color = BRAND.get(accent, BRAND["green"])
    safe_key = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:70]
    chart_key = f"chart_{_CHART_RENDER_COUNTER}_{safe_key}"
    st.markdown(f'<div class="chart-card" style="--accent:{color};">', unsafe_allow_html=True)
    st.plotly_chart(
        fig,
        use_container_width=True,
        theme=None,
        config={"displayModeBar": False, "responsive": True},
        key=chart_key,
    )
    st.markdown(
        f"""
        <div class="analysis-box" style="--accent:{color};">
            <b>Purpose:</b> {purpose}<br>
            <b>Formula / Logic:</b> {formula}<br>
            <b>Axis / Unit Rule:</b> {axis_note}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------------------------------------------------
# Data loading / preparation
# ------------------------------------------------------------
def read_csv(uploaded_file=None) -> pd.DataFrame:
    if uploaded_file is not None:
        return pd.read_csv(uploaded_file, encoding="utf-8-sig")
    path = existing_path(DEFAULT_PATHS)
    if path is None:
        raise FileNotFoundError("Clean-Data-lpg-survey.csv not found. Upload it from the sidebar or place it beside this app file.")
    return pd.read_csv(path, encoding="utf-8-sig")


@st.cache_data(show_spinner="Loading and preparing country-level LPG survey dataset...")
def prepare_data(uploaded_file=None) -> pd.DataFrame:
    raw = read_csv(uploaded_file)
    df = raw.copy()

    # Standard dimensions
    for c in ["Respondent Category", "Province", "City", "City Raw", "Area", "Area Raw", "Area Type", "Pathway"]:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = df[c].apply(normalize_text)

    df["Category"] = df["Respondent Category"].map(CATEGORY_MAP).fillna(df["Respondent Category"])
    df["Category"] = df["Category"].apply(normalize_text)
    df["City Clean"] = df["City"].replace({"Unknown": "Not Captured", "": "Not Captured"})
    df["Province Clean"] = df["Province"].replace({"Unknown": "Not Captured", "": "Not Captured"})
    df["Area Type Clean"] = df["Area Type"].replace({"Unknown": "Not Captured", "": "Not Captured"})

    # Flags and denominators
    # Country-level LPG adoption logic:
    # - Normal consumer/commercial/industrial records use the direct LPG-use question.
    # - Transport records use the current vehicle fuel question because B1 is intentionally blank for transport.
    # - Supplier/distributor and society-management records are excluded from the adoption denominator
    #   because they are not end-consumer LPG adoption records.
    direct_lpg_flag = get_col(df, "Currently Uses LPG").apply(yes_flag)
    if direct_lpg_flag.sum() == 0:
        direct_lpg_flag = get_col(df, "B1 Current LPG User").apply(yes_flag)
    transport_lpg_flag = get_col(df, "K2 Current Vehicle Fuel").astype(str).str.contains("LPG", case=False, na=False).astype(int)

    is_supplier_record = df["Category"].str.contains("Supplier", case=False, na=False)
    is_society_record = df["Category"].str.contains("Society / Apartment Mgmt", case=False, na=False)
    is_transport_record = df["Category"].str.contains("Transport", case=False, na=False)

    df["Current LPG User Flag"] = np.where(is_transport_record, transport_lpg_flag, direct_lpg_flag).astype(int)
    direct_known = non_blank_series(get_col(df, "Currently Uses LPG")) | non_blank_series(get_col(df, "B1 Current LPG User"))
    transport_known = is_transport_record & non_blank_series(get_col(df, "K2 Current Vehicle Fuel"))
    df["LPG Adoption Denominator"] = np.where((is_supplier_record | is_society_record), 0, (direct_known | transport_known).astype(int))

    df["Natural Gas Connection Flag"] = get_col(df, "B2 Natural Gas Connection").apply(yes_flag)
    df["Solar Installed Flag"] = get_col(df, "B4 Solar Installed").apply(yes_flag)
    df["Safety Incident Flag"] = get_col(df, "F3 Safety Incident").apply(yes_flag)
    df["Safety Denominator"] = non_blank_series(get_col(df, "F3 Safety Incident")).astype(int)

    # Uses by fuel/application
    for fuel, prefix in FUEL_PREFIXES.items():
        cols = [f"{prefix} {suffix}" for suffix in APPLICATION_SUFFIXES if f"{prefix} {suffix}" in df.columns]
        if cols:
            df[f"Uses {fuel}"] = df[cols].apply(lambda r: int(any(bool_flag(v) for v in r)), axis=1)
        else:
            df[f"Uses {fuel}"] = 0
    for label, column in APP_FLAGS.items():
        df[f"LPG Application - {label}"] = get_col(df, column).apply(bool_flag)

    df["LPG Application Count"] = df[[f"LPG Application - {x}" for x in APP_FLAGS]].sum(axis=1)

    # Converted values
    df["Monthly LPG Usage KG"] = df.apply(monthly_lpg_kg, axis=1)
    df["Monthly LPG Usage MT"] = df["Monthly LPG Usage KG"] / 1000
    df["LPG Price PKR per KG"] = df.apply(price_pkr_per_kg, axis=1)
    df["Monthly LPG Spend PKR"] = pd.to_numeric(get_col(df, "C5 Monthly LPG Spend PKR"), errors="coerce")
    df["Transport LPG KG Month"] = df.apply(transport_lpg_kg, axis=1)
    df["Supplier Monthly Sold MT"] = df.apply(supplier_sold_mt, axis=1)
    df["Industrial Additional LPG MT"] = pd.to_numeric(get_col(df, "J21 Additional LPG MT Per Month"), errors="coerce")
    df["Solar Capacity kW"] = pd.to_numeric(get_col(df, "B5 Solar Capacity"), errors="coerce")

    # Clean analysis validity flags
    df["Valid Usage Flag"] = ((df["Monthly LPG Usage KG"].notna()) & (df["Monthly LPG Usage KG"] > 0)).astype(int)
    df["Valid Price Flag"] = (df["LPG Price PKR per KG"].between(100, 1000, inclusive="both")).astype(int)
    df["Valid Spend Flag"] = ((df["Monthly LPG Spend PKR"].notna()) & (df["Monthly LPG Spend PKR"] > 0)).astype(int)

    # Broad sector flags
    df["Is Supplier"] = df["Category"].str.contains("Supplier", case=False, na=False)
    df["Is Industrial"] = df["Category"].str.contains("Industrial", case=False, na=False)
    df["Is Transport"] = df["Category"].str.contains("Transport", case=False, na=False)
    df["Is Residential"] = df["Category"].isin(["Residential", "Society / Apartment Mgmt"])
    df["Is Commercial"] = df["Category"].str.contains("Restaurant|Tandoor|Commercial|Institutional", case=False, na=False)
    df["Country Analysis Flag"] = 1
    df["City Analysis Allowed Flag"] = 1

    # Simple price sensitivity scale
    sensitivity_map = {
        "Not sensitive": 1,
        "Slightly sensitive": 2,
        "Moderately sensitive": 3,
        "Very sensitive": 4,
        "Extremely sensitive": 5,
    }
    df["Price Sensitivity Score"] = get_col(df, "D2 Price Sensitivity").map(sensitivity_map)

    # Data quality indicators
    important = ["Respondent Category", "City", "B1 Current LPG User", "B2 Natural Gas Connection", "B4 Solar Installed"]
    df["Missing Critical Fields"] = df[important].apply(lambda r: int(sum(normalize_text(v) == "Unknown" for v in r)), axis=1)
    df["Data Completeness %"] = 100 * (1 - df["Missing Critical Fields"] / len(important))
    df["Sample Strength"] = "Country-level record"

    return df

# ------------------------------------------------------------
# Aggregation and chart helpers
# ------------------------------------------------------------
def response_count(df: pd.DataFrame, by: str, name: str = "Number of Respondents") -> pd.DataFrame:
    if by not in df.columns:
        return pd.DataFrame(columns=[by, name])
    out = df.groupby(by, dropna=False).size().reset_index(name=name)
    return out.sort_values(name, ascending=False)


def adoption_rate(df: pd.DataFrame, by: Optional[str] = None, min_n: int = 1) -> pd.DataFrame:
    if by is None:
        den = df["LPG Adoption Denominator"].sum()
        num = df["Current LPG User Flag"].sum()
        return pd.DataFrame({"Current LPG Users": [num], "Known LPG Responses": [den], "LPG Adoption Rate (%)": [pct(num, den)]})
    g = df.groupby(by, dropna=False).agg(
        **{
            "Current LPG Users": ("Current LPG User Flag", "sum"),
            "Known LPG Responses": ("LPG Adoption Denominator", "sum"),
            "Total Responses": ("ID", "count") if "ID" in df.columns else (by, "count"),
        }
    ).reset_index()
    g["LPG Adoption Rate (%)"] = np.where(g["Known LPG Responses"] > 0, g["Current LPG Users"] / g["Known LPG Responses"] * 100, np.nan)
    g["Sample Strength"] = g["Known LPG Responses"].apply(sample_band)
    g["Label"] = g.apply(lambda r: f"{r['LPG Adoption Rate (%)']:.1f}% | n={int(r['Known LPG Responses'])}" if pd.notna(r["LPG Adoption Rate (%)"]) else "n/a", axis=1)
    return g[g["Known LPG Responses"] >= min_n].sort_values("LPG Adoption Rate (%)", ascending=False)


def demand_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    d = df[df["Valid Usage Flag"].eq(1)].copy()
    if d.empty or by not in d.columns:
        return pd.DataFrame()
    g = d.groupby(by, dropna=False).agg(
        **{
            "Valid Usage Records": ("Monthly LPG Usage KG", "count"),
            "Total LPG Usage KG/month": ("Monthly LPG Usage KG", "sum"),
            "Total LPG Usage MT/month": ("Monthly LPG Usage MT", "sum"),
            "Median LPG Usage KG/month": ("Monthly LPG Usage KG", "median"),
            "Average LPG Usage KG/month": ("Monthly LPG Usage KG", "mean"),
        }
    ).reset_index()
    return g.sort_values("Total LPG Usage MT/month", ascending=False)


def median_price_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    d = df[df["Valid Price Flag"].eq(1)].copy()
    if d.empty or by not in d.columns:
        return pd.DataFrame()
    g = d.groupby(by, dropna=False).agg(
        **{
            "Valid Price Records": ("LPG Price PKR per KG", "count"),
            "Median LPG Price PKR/KG": ("LPG Price PKR per KG", "median"),
            "Average LPG Price PKR/KG": ("LPG Price PKR per KG", "mean"),
        }
    ).reset_index()
    return g.sort_values("Median LPG Price PKR/KG", ascending=False)


def categorical_count(df: pd.DataFrame, column: str, label: str = "Response", top_n: Optional[int] = None) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=[label, "Number of Respondents"])
    d = df[non_blank_series(df[column])].copy()
    if d.empty:
        return pd.DataFrame(columns=[label, "Number of Respondents"])
    out = d[column].apply(normalize_text).value_counts().reset_index()
    out.columns = [label, "Number of Respondents"]
    return out.head(top_n) if top_n else out


def count_multiselect(df: pd.DataFrame, column: str, top_n: int = 20) -> pd.DataFrame:
    rows = []
    if column not in df.columns:
        return pd.DataFrame(columns=["Item", "Number of Respondents"])
    for value in df[column].dropna():
        rows.extend(parse_multi(value))
    if not rows:
        return pd.DataFrame(columns=["Item", "Number of Respondents"])
    out = pd.Series(rows).value_counts().reset_index()
    out.columns = ["Item", "Number of Respondents"]
    return out.head(top_n)


def rate_summary(df: pd.DataFrame, by: str, numerator: str, denominator: str, rate_name: str, min_n: int) -> pd.DataFrame:
    if by not in df.columns:
        return pd.DataFrame()
    g = df.groupby(by, dropna=False).agg(
        numerator=(numerator, "sum"),
        denominator=(denominator, "sum"),
        total=(by, "count"),
    ).reset_index()
    g[rate_name] = np.where(g["denominator"] > 0, g["numerator"] / g["denominator"] * 100, np.nan)
    g["Sample Strength"] = g["denominator"].apply(sample_band)
    g["Label"] = g.apply(lambda r: f"{r[rate_name]:.1f}% | n={int(r['denominator'])}" if pd.notna(r[rate_name]) else "n/a", axis=1)
    return g[g["denominator"] >= min_n].sort_values(rate_name, ascending=False)


def bar_count(df: pd.DataFrame, x: str, y: str, title: str, x_title: str, y_title: str, horizontal: bool = True, color_scale: str = "RdYlGn") -> go.Figure:
    if df.empty or x not in df.columns or y not in df.columns:
        return empty_fig(title)
    d = df.copy()
    if horizontal:
        d = d.sort_values(y, ascending=True)
        fig = px.bar(d, x=y, y=x, orientation="h", text=y, color=y, color_continuous_scale=color_scale)
        fig.update_layout(xaxis_title=y_title, yaxis_title=x_title, coloraxis_showscale=False)
    else:
        fig = px.bar(d, x=x, y=y, text=y, color=y, color_continuous_scale=color_scale)
        fig.update_xaxes(tickangle=-35)
        fig.update_layout(xaxis_title=x_title, yaxis_title=y_title, coloraxis_showscale=False)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    return style_fig(fig, title, height=max(480, min(790, 380 + len(d) * 28)))


def fig_adoption(df: pd.DataFrame, by: str, title: str, min_n: int, top_n: int) -> go.Figure:
    d = adoption_rate(df, by, min_n).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    fig = px.bar(d, x="LPG Adoption Rate (%)", y=by, orientation="h", text="Label", color="Known LPG Responses", color_continuous_scale="RdYlGn", hover_data=["Current LPG Users", "Known LPG Responses", "Total Responses", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="LPG Adoption Rate (% of Known Responses)", yaxis_title=by, coloraxis_colorbar_title="Known n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_city_user_pct(df: pd.DataFrame, min_n: int, top_n: int) -> go.Figure:
    d = adoption_rate(df, "City Clean", min_n).head(top_n)
    if d.empty:
        return empty_fig("City-wise Current LPG User %")
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    fig = px.bar(d, x="LPG Adoption Rate (%)", y="City Clean", orientation="h", text="Label", color="Current LPG Users", color_continuous_scale="Greens", hover_data=["Current LPG Users", "Known LPG Responses", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="Current LPG Users (% of Known Responses)", yaxis_title="City", coloraxis_colorbar_title="LPG Users")
    return style_fig(fig, "City-wise LPG Adoption Rate / Current LPG Users %", height=max(520, min(850, 380 + len(d) * 30)))


def fig_demand_total(df: pd.DataFrame, by: str, title: str, top_n: int) -> go.Figure:
    d = demand_summary(df, by).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Total LPG Usage MT/month", ascending=True)
    fig = px.bar(d, x="Total LPG Usage MT/month", y=by, orientation="h", text="Total LPG Usage MT/month", color="Median LPG Usage KG/month", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Total LPG Usage (MT/month)", yaxis_title=by, coloraxis_colorbar_title="Median KG/month")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_median_usage(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    d = demand_summary(df, by)
    d = d[d["Valid Usage Records"] >= min_n].sort_values("Median LPG Usage KG/month", ascending=False).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Median LPG Usage KG/month", ascending=True)
    fig = px.bar(d, x="Median LPG Usage KG/month", y=by, orientation="h", text="Median LPG Usage KG/month", color="Valid Usage Records", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Median LPG Usage (KG/month)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_price_by(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    d = median_price_summary(df, by)
    d = d[d["Valid Price Records"] >= min_n].head(top_n)
    if d.empty:
        return empty_fig(title, "No valid price records after sample filter")
    d = d.sort_values("Median LPG Price PKR/KG", ascending=True)
    fig = px.bar(d, x="Median LPG Price PKR/KG", y=by, orientation="h", text="Median LPG Price PKR/KG", color="Valid Price Records", color_continuous_scale="RdYlGn_r")
    fig.update_traces(texttemplate="PKR %{text:,.0f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Median LPG Price (PKR/KG)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_distribution(df: pd.DataFrame, column: str, title: str, x_title: str, y_title: str, log_x: bool = False) -> go.Figure:
    if column not in df.columns:
        return empty_fig(title)

    d = df[df[column].notna() & (df[column] > 0)].copy()
    if d.empty:
        return empty_fig(title)

    values = pd.to_numeric(d[column], errors="coerce").dropna()
    values = values[values > 0]
    if values.empty:
        return empty_fig(title)

    # The monthly LPG usage field is highly skewed: households report cylinders/KG,
    # while commercial/industrial users can report thousands of KG. A log-axis histogram
    # made the bars visually disappear in some browsers. For this chart, use clean
    # business-readable bands instead.
    if log_x or column == "Monthly LPG Usage KG":
        bins = [0, 12, 25, 50, 100, 250, 500, 1000, 5000, 10000, 50000, float("inf")]
        labels = [
            "≤12", "13–25", "26–50", "51–100", "101–250", "251–500",
            "501–1,000", "1,001–5,000", "5,001–10,000", "10,001–50,000", ">50,000"
        ]
        temp = pd.DataFrame({column: values})
        temp["Usage Band"] = pd.cut(temp[column], bins=bins, labels=labels, include_lowest=True, right=True)
        grouped = temp.groupby("Usage Band", observed=False).size().reset_index(name="Number of Respondents")
        grouped = grouped[grouped["Number of Respondents"] > 0].copy()
        if grouped.empty:
            return empty_fig(title)
        grouped["Usage Band"] = grouped["Usage Band"].astype(str)
        grouped["Share (%)"] = grouped["Number of Respondents"] / grouped["Number of Respondents"].sum() * 100
        grouped["Label"] = grouped.apply(lambda r: f"{int(r['Number of Respondents'])} | {r['Share (%)']:.1f}%", axis=1)
        fig = px.bar(
            grouped,
            x="Usage Band",
            y="Number of Respondents",
            text="Label",
            color="Number of Respondents",
            color_continuous_scale="Greens",
        )
        fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
        fig.update_layout(
            xaxis_title="Monthly LPG Usage Band (KG/month)",
            yaxis_title=y_title,
            coloraxis_showscale=False,
            bargap=0.18,
        )
        fig.update_xaxes(tickangle=-25)
        return style_fig(fig, title, height=max(560, 420 + len(grouped) * 12))

    # For other numeric distributions, use a standard histogram with safe formatting.
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=28,
            marker=dict(color=BRAND["green"], line=dict(color="white", width=1)),
            hovertemplate=f"{x_title}: %{{x:,.2f}}<br>{y_title}: %{{y:,.0f}}<extra></extra>",
            name=title,
        )
    )
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title, bargap=0.08, showlegend=False)
    return style_fig(fig, title, height=575)


def fig_categorical(df: pd.DataFrame, column: str, title: str, label: str, top_n: int, color_scale: str = "RdYlGn") -> go.Figure:
    d = categorical_count(df, column, label, top_n)
    return bar_count(d, label, "Number of Respondents", title, label, "Number of Respondents", True, color_scale)


def fig_application_counts(df: pd.DataFrame) -> go.Figure:
    lpg_users = max(df["Current LPG User Flag"].sum(), 1)
    rows = []
    for label in APP_FLAGS:
        users = df[f"LPG Application - {label}"].sum()
        rows.append({"LPG Application": label, "Number of Respondents": users, "% of LPG Users": pct(users, lpg_users)})
    d = pd.DataFrame(rows).sort_values("Number of Respondents", ascending=True)
    fig = px.bar(d, x="Number of Respondents", y="LPG Application", orientation="h", text="% of LPG Users", color="Number of Respondents", color_continuous_scale="Greens")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Number of Respondents", yaxis_title="LPG Application", coloraxis_showscale=False)
    return style_fig(fig, "Country-level LPG Usage by Application", 515)


def fig_application_heatmap(df: pd.DataFrame) -> go.Figure:
    rows = []
    for cat, sub in df.groupby("Category"):
        denom = max(sub["Current LPG User Flag"].sum(), 1)
        for label in APP_FLAGS:
            rows.append({"Sector": cat, "Application": label, "% of LPG Users": pct(sub[f"LPG Application - {label}"].sum(), denom)})
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig("Country-level LPG Application Mix by Sector")
    pivot = d.pivot(index="Sector", columns="Application", values="% of LPG Users").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="% of LPG Users"))
    fig.update_layout(xaxis_title="LPG Application", yaxis_title="Sector")
    return style_fig(fig, "Country-level LPG Application Mix by Sector", height=max(520, 300 + len(pivot) * 34))


def fig_fuel_sources_country(df: pd.DataFrame) -> go.Figure:
    rows = []
    for fuel in FUEL_PREFIXES:
        col = f"Uses {fuel}"
        if col in df.columns:
            users = df[col].sum()
            rows.append({"Fuel Source": fuel, "Respondents Using Fuel": users, "% of Total Responses": pct(users, len(df))})
    d = pd.DataFrame(rows).sort_values("Respondents Using Fuel", ascending=True)
    if d.empty:
        return empty_fig("Country-level Fuel Source Mix")
    fig = px.bar(d, x="Respondents Using Fuel", y="Fuel Source", orientation="h", text="% of Total Responses", color="Respondents Using Fuel", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Number of Respondents", yaxis_title="Fuel Source", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Fuel Source Mix", 560)


def fig_safety_rate(df: pd.DataFrame, by: str, min_n: int, top_n: int) -> go.Figure:
    d = rate_summary(df, by, "Safety Incident Flag", "Safety Denominator", "Safety Incident Rate (%)", min_n).head(top_n)
    if d.empty:
        return empty_fig("Country-level Safety Incident Rate")
    d = d.sort_values("Safety Incident Rate (%)", ascending=True)
    fig = px.bar(d, x="Safety Incident Rate (%)", y=by, orientation="h", text="Label", color="denominator", color_continuous_scale="RdYlGn_r", hover_data=["numerator", "denominator", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%")
    fig.update_layout(xaxis_title="Safety Incident Rate (% of Known Safety Responses)", yaxis_title=by, coloraxis_colorbar_title="Known n")
    return style_fig(fig, "Country-level LPG Safety Incident Rate by Sector", height=max(520, min(820, 380 + len(d) * 30)))


def fig_supplier_ratings(df: pd.DataFrame) -> go.Figure:
    cols = [
        "E2 Price Fairness", "E2 Availability When Needed", "E2 Delivery Refill Timing",
        "E2 Product Cylinder Quality", "E2 Customer Service", "E2 Ease Of Ordering", "E2 Overall Satisfaction",
    ]
    rows = []
    for c in cols:
        if c in df.columns:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().sum() > 0:
                rows.append({"Supplier Experience Area": c.replace("E2 ", ""), "Average Rating": s.mean(), "Valid Ratings": s.notna().sum()})
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig("Country-level Supplier Experience Rating")
    d = d.sort_values("Average Rating", ascending=True)
    fig = px.bar(d, x="Average Rating", y="Supplier Experience Area", orientation="h", text="Average Rating", color="Average Rating", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig.update_xaxes(range=[0, 5])
    fig.update_layout(xaxis_title="Average Rating (1-5)", yaxis_title="Supplier Experience Area", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Supplier Experience Rating", 525)


def fig_pain_scores(df: pd.DataFrame) -> go.Figure:
    score_cols = [c for c in df.columns if c.startswith("Pain ") and c.endswith(" Score")]
    rows = []
    for c in score_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() > 0:
            rows.append({"Pain Area": c.replace("Pain ", "").replace(" Score", ""), "Average Pain Score": s.mean(), "Valid Records": s.notna().sum()})
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig("Country-level Pain Severity Score")
    d = d.sort_values("Average Pain Score", ascending=True)
    fig = px.bar(d, x="Average Pain Score", y="Pain Area", orientation="h", text="Average Pain Score", color="Average Pain Score", color_continuous_scale="Reds")
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside", cliponaxis=False)
    fig.update_layout(xaxis_title="Average Pain Score (Frequency × Seriousness)", yaxis_title="Pain Area", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Pain Severity Score", 560)


def fig_missing_quality(df: pd.DataFrame) -> go.Figure:
    check_cols = [
        ("Respondent Category", "Respondent Category"),
        ("City", "City"),
        ("Current LPG User", "B1 Current LPG User"),
        ("LPG Monthly Quantity", "C3 LPG Monthly Quantity Value"),
        ("LPG Price", "C6 LPG Price Value"),
        ("Monthly Spend", "C5 Monthly LPG Spend PKR"),
        ("Natural Gas Connection", "B2 Natural Gas Connection"),
        ("Natural Gas Reliability", "B3 Natural Gas Reliability"),
        ("Solar Installed", "B4 Solar Installed"),
        ("Safety Incident", "F3 Safety Incident"),
    ]
    rows = []
    n = len(df)
    for label, column in check_cols:
        if column in df.columns:
            missing = (~non_blank_series(df[column])).sum()
            rows.append({"Field": label, "Missing Records": missing, "Missing %": pct(missing, n), "Captured Records": n - missing})
    d = pd.DataFrame(rows).sort_values("Missing %", ascending=True)
    fig = px.bar(d, x="Missing %", y="Field", orientation="h", text="Missing %", color="Missing %", color_continuous_scale="Reds")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%")
    fig.update_layout(xaxis_title="Missing Responses (%)", yaxis_title="Survey Field", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Data Completeness / Missing Field Analysis", 620)

# ------------------------------------------------------------
# Load data and render header/sidebar
# ------------------------------------------------------------
st.sidebar.markdown("## Data Source")
st.sidebar.markdown(
    f'<div class="sidebar-note">Primary local path:<br><b>{REQUESTED_WINDOWS_PATH}</b><br><br>For online deployment, keep <b>Clean-Data-lpg-survey.csv</b> beside this app file.</div>',
    unsafe_allow_html=True,
)
with st.sidebar.expander("Optional CSV upload", expanded=False):
    uploaded = st.file_uploader("Upload Clean-Data-lpg-survey.csv", type=["csv"])

try:
    df_all = prepare_data(uploaded)
except Exception as exc:
    st.error("Could not load Clean-Data-lpg-survey.csv. Upload the file from the sidebar or place it beside the app.")
    st.exception(exc)
    st.stop()

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-title">Pakistan LPG Country Demand Survey Dashboard</div>
        <div class="hero-subtitle">
            Fancy, deployable Streamlit dashboard focused on Pakistan-level LPG demand, adoption, fuel switching, price sensitivity, natural gas reliability, solar usage, safety, commercial/industrial/transport needs and supplier market feedback. The dashboard intentionally avoids deep area/city-level interpretation except for respondent coverage and city LPG adoption percentage.
        </div>
        <span class="pill">Country-level analysis first</span>
        <span class="pill">City analysis limited by design</span>
        <span class="pill">Consistent units: KG/month, MT/month, PKR/KG, %</span>
        <span class="pill">Deployable on Streamlit Cloud</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<div class="rule-box"><b>Analysis rule:</b> {CITY_ANALYSIS_RULE}</div>', unsafe_allow_html=True)

# Sidebar: no city/area filter, so country-level results are not unintentionally biased by location.
st.sidebar.markdown("## Country-level Filters")
st.sidebar.caption("City and Area filters are intentionally not included. City is shown only on the City Snapshot page.")
category_options = sorted([x for x in df_all["Category"].dropna().unique().tolist() if x != "Unknown"])
category_mode = st.sidebar.selectbox("Respondent Category", ["All Categories", "Custom Selection"])
selected_categories: Optional[List[str]] = None
if category_mode == "Custom Selection":
    selected_categories = st.sidebar.multiselect("Select respondent categories", category_options, default=[])

scope = st.sidebar.selectbox("Analysis Scope", ["All responses", "Consumer / user responses only", "Supplier / distributor responses only"])
lpg_filter = st.sidebar.selectbox("Current LPG User Filter", ["All", "Current LPG users only", "Non-LPG users only", "Known LPG-answer respondents only"])
st.sidebar.markdown("## Chart Controls")
top_n = st.sidebar.slider("Top N in charts", min_value=5, max_value=35, value=15, step=1)
min_sample = st.sidebar.slider("Minimum sample size for rate charts", min_value=1, max_value=50, value=5, step=1)
show_tables = st.sidebar.checkbox("Show supporting tables", value=False)

# Apply country-level filters
df = df_all.copy()
if selected_categories is not None:
    if selected_categories:
        df = df[df["Category"].isin(selected_categories)]
    else:
        st.sidebar.warning("Custom category filter is active, but no category is selected.")
        df = df.iloc[0:0]
if scope == "Consumer / user responses only":
    df = df[~df["Is Supplier"]]
elif scope == "Supplier / distributor responses only":
    df = df[df["Is Supplier"]]
if lpg_filter == "Current LPG users only":
    df = df[df["Current LPG User Flag"].eq(1)]
elif lpg_filter == "Non-LPG users only":
    df = df[df["LPG Adoption Denominator"].eq(1) & df["Current LPG User Flag"].eq(0)]
elif lpg_filter == "Known LPG-answer respondents only":
    df = df[df["LPG Adoption Denominator"].eq(1)]

if df.empty:
    st.warning("No records match the selected filters. Reset the category/scope filter in the sidebar.")
    st.stop()

st.sidebar.download_button(
    "Download Filtered Data CSV",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="filtered_lpg_country_survey_data.csv",
    mime="text/csv",
    use_container_width=True,
)

# KPIs
responses = len(df)
known_lpg = df["LPG Adoption Denominator"].sum()
lpg_users = df["Current LPG User Flag"].sum()
adoption = pct(lpg_users, known_lpg)
valid_usage = df[df["Valid Usage Flag"].eq(1)]
total_usage_kg = valid_usage["Monthly LPG Usage KG"].sum()
total_usage_mt = total_usage_kg / 1000
median_usage = valid_usage["Monthly LPG Usage KG"].median()
valid_price = df[df["Valid Price Flag"].eq(1)]
median_price = valid_price["LPG Price PKR per KG"].median()
safety_den = df["Safety Denominator"].sum()
safety_yes = df["Safety Incident Flag"].sum()
safety = pct(safety_yes, safety_den)
solar_known = non_blank_series(get_col(df, "B4 Solar Installed")).sum()
solar_yes = df["Solar Installed Flag"].sum()
solar_rate = pct(solar_yes, solar_known)
solid_users = df["Uses Solid Fuel"].sum()

kpi_row(
    [
        kpi("Total Responses", fmt_int(responses), "Selected records", BRAND["green"]),
        kpi("Current LPG Users", fmt_int(lpg_users), f"Known LPG answers: {fmt_int(known_lpg)}", BRAND["red"]),
        kpi("LPG Adoption Rate", fmt_pct(adoption), "Current LPG users ÷ known LPG responses", BRAND["green"]),
        kpi("Total Reported Demand", f"{fmt_1(total_usage_mt)} MT/month", "From valid usage records", BRAND["orange"]),
        kpi("Median Usage", f"{fmt_int(median_usage)} KG/month", "Typical user demand", BRAND["blue"]),
        kpi("Median LPG Price", f"{fmt_pkr(median_price)}/KG", "Clean PKR/KG price records", BRAND["purple"]),
        kpi("Safety Incident Rate", fmt_pct(safety), f"{fmt_int(safety_yes)} incidents / {fmt_int(safety_den)} known", BRAND["red"]),
        kpi("Solar Adoption", fmt_pct(solar_rate), f"{fmt_int(solar_yes)} solar users / {fmt_int(solar_known)} known", BRAND["teal"]),
    ],
    columns=4,
)

# Navigation
pages = [
    "1. Executive Country Overview",
    "2. City Snapshot Only",
    "3. Country Sector & Adoption",
    "4. Country Usage & Demand",
    "5. Country Price & Switching",
    "6. Natural Gas & Solar",
    "7. Safety, Quality & Supplier Experience",
    "8. Commercial Users",
    "9. Industrial Users",
    "10. Transport Users",
    "11. Supplier / Distributor Market",
    "12. Data Quality",
    "13. Raw Data",
]
page = st.radio("Dashboard Page", pages, horizontal=True)

# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------
if page == "1. Executive Country Overview":
    section("Executive Country Overview", "Pakistan-level snapshot of LPG adoption, total reported demand, fuel mix, price sensitivity and usage applications.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            "Country-level Respondent Mix by Sector",
            bar_count(response_count(df, "Category").head(top_n), "Category", "Number of Respondents", "Country-level Respondent Mix by Sector", "Respondent Category", "Number of Respondents"),
            "Shows survey sample structure at Pakistan level.",
            "Count of responses by respondent category.",
            "This is sample coverage, not market size.",
            "green",
        )
    with c2:
        chart_card(
            "Country-level LPG Adoption by Sector",
            fig_adoption(df, "Category", "Country-level LPG Adoption by Sector", min_sample, top_n),
            "Compares LPG penetration across respondent sectors at Pakistan level.",
            "LPG Adoption Rate = Current LPG Users ÷ Known LPG Responses × 100.",
            "X-axis is %. Labels show rate and denominator n.",
            "red",
        )
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card(
            "Country-level Fuel Source Mix",
            fig_fuel_sources_country(df),
            "Shows which fuels are currently used across the national survey sample.",
            "Respondent is counted once per fuel if any purpose was selected for that fuel.",
            "X-axis: respondent count; labels: % of total selected responses.",
            "orange",
        )
    with c4:
        chart_card(
            "Country-level LPG Usage by Application",
            fig_application_counts(df),
            "Shows where LPG is being used: cooking, heating, generator, or business/process use.",
            "Count of respondents selecting each LPG application.",
            "Labels show % of current LPG users.",
            "green",
        )
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card(
            "Country-level Preferred Alternative if LPG Becomes Expensive",
            fig_categorical(df, "D4 Alternative If Expensive", "Country-level Preferred Alternative if LPG Becomes Expensive", "Preferred Alternative Fuel", top_n, "Oranges"),
            "Identifies fuel-switching risk if LPG prices rise.",
            "Count of responses by preferred alternative fuel.",
            "This is a country-level substitution-risk view.",
            "orange",
        )
    with c6:
        chart_card(
            "Country-level Future LPG Outlook",
            fig_categorical(df, "C12 LPG Next 12 Months", "Country-level Future LPG Outlook", "Expected LPG Usage Direction", top_n, "RdYlGn"),
            "Shows whether respondents expect LPG usage to increase, decrease or remain stable.",
            "Count by expected LPG usage direction over the next 12 months.",
            "Country-level future demand sentiment.",
            "blue",
        )

elif page == "2. City Snapshot Only":
    section("City Snapshot Only", "City-level analysis is limited to respondent coverage and current LPG user/adoption percentage only.")
    st.markdown(f'<div class="rule-box"><b>City rule:</b> {CITY_ANALYSIS_RULE}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            "Number of Respondents per City",
            bar_count(response_count(df, "City Clean").head(top_n), "City Clean", "Number of Respondents", "Number of Respondents per City", "City", "Number of Respondents"),
            "Shows where the survey responses were collected.",
            "Count of records by standardized city.",
            "This is sample coverage only, not demand size.",
            "green",
        )
    with c2:
        chart_card(
            "City-wise LPG Adoption Rate / Current LPG Users %",
            fig_city_user_pct(df, min_sample, top_n),
            "Shows the percentage of known respondents in each city who already use LPG.",
            "Current LPG Users ÷ Known LPG Responses × 100 by city.",
            "This is the only city-level behaviour metric included by design.",
            "red",
        )
    city_table = adoption_rate(df, "City Clean", min_sample).merge(response_count(df, "City Clean"), on="City Clean", how="left")
    city_table = city_table[["City Clean", "Number of Respondents", "Current LPG Users", "Known LPG Responses", "LPG Adoption Rate (%)", "Sample Strength"]].sort_values("Number of Respondents", ascending=False)
    st.dataframe(city_table, use_container_width=True, hide_index=True)

elif page == "3. Country Sector & Adoption":
    section("Country Sector & Adoption", "Deep sector-level country analysis of adoption, sample strength, demand contribution and LPG application mix.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level Sector Sample Strength", bar_count(response_count(df, "Category").head(top_n), "Category", "Number of Respondents", "Country-level Sector Sample Strength", "Sector", "Number of Respondents"), "Shows the respondent base for each sector before interpreting rates.", "Count of responses by sector.", "Use sample count to judge confidence in sector-level rates.", "green")
    with c2:
        chart_card("Country-level LPG Adoption by Sector", fig_adoption(df, "Category", "Country-level LPG Adoption by Sector", min_sample, top_n), "Identifies sectors where LPG adoption is already high or low.", "Current LPG Users ÷ Known LPG Responses × 100.", "Pakistan-level sector rate, not city/area based.", "red")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Country-level Total LPG Demand by Sector", fig_demand_total(df, "Category", "Country-level Total LPG Demand by Sector", top_n), "Shows which sectors contribute the largest reported LPG demand.", "Sum of valid monthly LPG KG converted to MT/month by sector.", "X-axis: MT/month. Y-axis: sector.", "orange")
    with c4:
        chart_card("Country-level Median LPG Usage by Sector", fig_median_usage(df, "Category", "Country-level Median LPG Usage by Sector", top_n, min_sample), "Compares typical user demand by sector without distortion from large users.", "Median of valid monthly LPG usage KG/month by sector.", "Median is preferred for skewed usage data.", "blue")
    chart_card("Country-level LPG Application Mix by Sector", fig_application_heatmap(df), "Shows how LPG use purpose differs across sectors.", "% of current LPG users in each sector selecting each application.", "Heatmap cell value = % of LPG users in that sector.", "green")

elif page == "4. Country Usage & Demand":
    section("Country Usage & Demand", "Pakistan-level LPG monthly usage, adoption duration, seasonal pattern, demand growth and application mix.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level LPG Usage Distribution", fig_distribution(df, "Monthly LPG Usage KG", "Country-level LPG Usage Distribution", "Monthly LPG Usage (KG/month)", "Number of Respondents", log_x=True), "Shows the spread of reported monthly LPG usage across Pakistan sample.", "Histogram of valid monthly LPG usage in KG/month.", "Usage bands prevent bulk users from hiding household users.", "green")
    with c2:
        chart_card("Country-level LPG Usage by Application", fig_application_counts(df), "Shows main applications of LPG nationally.", "Count of users selecting each application flag.", "Labels show % of current LPG users.", "red")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Country-level LPG Usage Duration", fig_categorical(df, "C7 LPG Usage Duration", "Country-level LPG Usage Duration", "Usage Duration", top_n, "RdYlGn"), "Separates recent LPG adoption from established use.", "Count of respondents by LPG usage duration.", "Country-level adoption maturity view.", "blue")
    with c4:
        chart_card("Country-level LPG Usage Change in Last 3 Years", fig_categorical(df, "C11 LPG Usage Change 3 Years", "Country-level LPG Usage Change in Last 3 Years", "Usage Change", top_n, "RdYlGn"), "Shows whether LPG consumption has been increasing or decreasing.", "Count by 3-year usage change response.", "Country-level historical trend sentiment.", "orange")
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card("Country-level Main Reason for Expected Increase", fig_categorical(df, "C13 Increase Reason", "Country-level Main Reason for Expected Increase", "Increase Reason", top_n, "Greens"), "Explains expected demand growth drivers.", "Count by reason for expected future LPG increase.", "Pakistan-level future demand driver.", "green")
    with c6:
        chart_card("Country-level Seasonal Peak Period", fig_categorical(df, "C16 Highest Usage Period", "Country-level Seasonal Peak Period", "Peak Usage Period", top_n, "Oranges"), "Shows when LPG demand tends to peak.", "Count by highest usage period.", "Country-level seasonality view.", "orange")

elif page == "5. Country Price & Switching":
    section("Country Price & Switching", "Pakistan-level price distribution, price sensitivity, affordability and alternative-fuel switching risk.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level LPG Price Distribution", fig_distribution(df[df["Valid Price Flag"].eq(1)], "LPG Price PKR per KG", "Country-level LPG Price Distribution", "LPG Price (PKR/KG)", "Number of Respondents"), "Shows clean LPG price levels reported across the country sample.", "Histogram of price records converted to PKR/KG and restricted to 100–1,000 PKR/KG.", "X-axis: PKR/KG.", "blue")
    with c2:
        chart_card("Country-level Median LPG Price by Sector", fig_price_by(df, "Category", "Country-level Median LPG Price by Sector", top_n, min_sample), "Compares sector-level reported prices at Pakistan level.", "Median PKR/KG by sector using valid price records.", "Use with valid price count, not city-level comparison.", "purple")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Country-level Price Sensitivity", fig_categorical(df, "D2 Price Sensitivity", "Country-level Price Sensitivity", "Price Sensitivity Level", top_n, "Reds"), "Shows how sensitive respondents are to price movements.", "Count by price sensitivity response.", "Country-level demand-risk indicator.", "red")
    with c4:
        chart_card("Country-level Price Increase Threshold", fig_categorical(df, "D3 Price Shift Threshold", "Country-level Price Increase Threshold", "Price Shift Threshold", top_n, "Oranges"), "Shows the price increase at which users may reduce or switch away from LPG.", "Count by selected price shift threshold.", "Country-level switching threshold.", "orange")
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card("Country-level Preferred Alternative if LPG Expensive", fig_categorical(df, "D4 Alternative If Expensive", "Country-level Preferred Alternative if LPG Expensive", "Alternative Fuel", top_n, "RdYlGn"), "Shows which fuels compete with LPG when price rises.", "Count by preferred alternative fuel.", "Country-level substitution risk.", "green")
    with c6:
        chart_card("Country-level Willingness to Pay More for Availability", fig_categorical(df, "D5 Pay More For Availability", "Country-level Willingness to Pay More for Availability", "Willingness to Pay", top_n, "Greens"), "Shows whether reliability has pricing power.", "Count by willingness to pay for reliable supply.", "Country-level reliability premium indicator.", "blue")

elif page == "6. Natural Gas & Solar":
    section("Natural Gas & Solar", "Country-level relationship between natural gas reliability, LPG adoption and solar usage.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level Natural Gas Connection Status", fig_categorical(df, "B2 Natural Gas Connection", "Country-level Natural Gas Connection Status", "Connection Status", top_n, "RdYlGn"), "Shows whether respondents have piped gas access.", "Count by natural gas connection status.", "Country-level access view.", "green")
    with c2:
        chart_card("Country-level Natural Gas Reliability", fig_categorical(df, "B3 Natural Gas Reliability", "Country-level Natural Gas Reliability", "Reliability Level", top_n, "Reds"), "Shows whether gas supply is reliable, limited or unavailable.", "Count by reliability response.", "Gas unreliability is a key LPG demand driver.", "red")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Natural Gas Reliability vs LPG Adoption", fig_adoption(df[df["B3 Natural Gas Reliability"].apply(normalize_text).ne("Unknown")], "B3 Natural Gas Reliability", "Natural Gas Reliability vs LPG Adoption", min_sample, top_n), "Shows whether unreliable gas is linked with higher LPG adoption.", "Current LPG Users ÷ Known LPG Responses by gas reliability.", "Country-level behavioural comparison by gas reliability level.", "orange")
    with c4:
        chart_card("Country-level Shift if Natural Gas Becomes Reliable", fig_categorical(df, "B7 Shift If Gas Available", "Country-level Shift if Natural Gas Becomes Reliable", "Likely Action", top_n, "Blues"), "Measures long-term demand risk if natural gas becomes reliable again.", "Count by shift-back response.", "Country-level retention risk indicator.", "blue")
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card("Country-level Solar Installed Status", fig_categorical(df, "B4 Solar Installed", "Country-level Solar Installed Status", "Solar Status", top_n, "Greens"), "Shows solar adoption in the sample.", "Count by solar installed/planning status.", "Country-level solar penetration view.", "teal")
    with c6:
        chart_card("Solar Installed vs LPG Adoption", fig_adoption(df[df["B4 Solar Installed"].apply(normalize_text).ne("Unknown")], "B4 Solar Installed", "Solar Installed vs LPG Adoption", min_sample, top_n), "Checks whether solar users still use LPG.", "Current LPG Users ÷ Known LPG Responses by solar installed status.", "Country-level cross-analysis, not city-based.", "green")

elif page == "7. Safety, Quality & Supplier Experience":
    section("Safety, Quality & Supplier Experience", "Country-level LPG safety, cylinder checks, quality issues, supplier ratings and pain severity.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level Safety Incident Rate by Sector", fig_safety_rate(df, "Category", min_sample, top_n), "Shows which sectors report safety incidents more often.", "Safety Incident Rate = Yes safety incident ÷ known safety responses × 100.", "Country-level rate by sector.", "red")
    with c2:
        chart_card("Country-level Cylinder Safety Check Behaviour", fig_categorical(df, "F5 Cylinder Safety Check", "Country-level Cylinder Safety Check Behaviour", "Safety Check Behaviour", top_n, "Oranges"), "Shows whether users check cylinder condition or safety markings.", "Count by cylinder safety-check response.", "Country-level safety awareness indicator.", "orange")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Country-level LPG Safety Feeling", fig_categorical(df, "F6 LPG Safety Feeling", "Country-level LPG Safety Feeling", "Safety Feeling", top_n, "RdYlGn"), "Shows perceived safety of LPG among respondents.", "Count by safety feeling response.", "Country-level perception measure.", "green")
    with c4:
        chart_card("Country-level Quality or Quantity Issue", fig_categorical(df, "F1 Quality Or Quantity Issue", "Country-level Quality or Quantity Issue", "Issue Status", top_n, "Reds"), "Shows product/cylinder quality or quantity concerns.", "Count of yes/no quality or quantity issue responses.", "Country-level issue incidence view.", "red")
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card("Country-level Supplier Experience Rating", fig_supplier_ratings(df), "Summarizes supplier experience across price, availability, delivery, quality and service.", "Average rating by supplier service area.", "X-axis: average rating on 1–5 scale.", "green")
    with c6:
        chart_card("Country-level Pain Severity Score", fig_pain_scores(df), "Ranks operational pain points by combined frequency and seriousness.", "Pain Score = Frequency × Seriousness.", "X-axis: average pain score.", "red")

elif page == "8. Commercial Users":
    section("Commercial Users", "Country-level commercial LPG analysis for restaurant, hotel, catering, tandoor, institutional and other commercial users.")
    commercial = df[df["Is Commercial"]].copy()
    if commercial.empty:
        st.info("No commercial records in the selected scope.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            chart_card("Country-level Commercial Activity Type", fig_categorical(commercial, "I1 Commercial Activity", "Country-level Commercial Activity Type", "Commercial Activity", top_n, "Greens"), "Shows commercial LPG user types captured in the national survey.", "Count by commercial activity type.", "Country-level commercial segmentation.", "green")
        with c2:
            chart_card("Country-level LPG Business Dependency", fig_categorical(commercial, "I4 LPG Business Dependency", "Country-level LPG Business Dependency", "Dependency Level", top_n, "Reds"), "Measures how important LPG is for commercial operations.", "Count by LPG dependency level.", "Country-level commercial dependence indicator.", "red")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            chart_card("Country-level Commercial One-day Unavailability Impact", fig_categorical(commercial, "I5 One Day Unavailability Impact", "Country-level Commercial One-day Unavailability Impact", "Business Impact", top_n, "Oranges"), "Shows business disruption if LPG is unavailable for one day.", "Count by reported impact level.", "Commercial availability risk view.", "orange")
        with c4:
            chart_card("Country-level Profitability Impact", fig_categorical(commercial, "I7 Profitability Impact", "Country-level Profitability Impact", "Profitability Impact", top_n, "Reds"), "Shows effect of LPG price increases on profitability.", "Count by profitability impact level.", "Country-level commercial price risk.", "red")
        c5, c6 = st.columns(2, gap="large")
        with c5:
            chart_card("Country-level Commercial Purchase Channel", fig_categorical(commercial, "I8 Purchase Channel", "Country-level Commercial Purchase Channel", "Purchase Channel", top_n, "Greens"), "Shows where commercial users purchase LPG.", "Count by purchase channel.", "Country-level supply channel view.", "green")
        with c6:
            chart_card("Country-level Commercial Peak Period", fig_categorical(commercial, "I6 Commercial Peak Period", "Country-level Commercial Peak Period", "Peak Period", top_n, "Oranges"), "Shows commercial seasonality, Ramadan, winter, wedding/event peaks etc.", "Count by commercial peak period.", "Country-level commercial seasonality.", "orange")

elif page == "9. Industrial Users":
    section("Industrial Users", "Country-level industrial LPG analysis: sector, gas substitution, supply mode, disruptions, barriers and incremental demand.")
    industrial = df[df["Is Industrial"]].copy()
    if industrial.empty:
        st.info("No industrial records in the selected scope.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            chart_card("Country-level Industry Type", fig_categorical(industrial, "J1 Industry Type", "Country-level Industry Type", "Industry Type", top_n, "Greens"), "Shows industrial respondent sectors.", "Count by industry type.", "Country-level industrial segmentation.", "green")
        with c2:
            chart_card("Gas/RLNG Shortage Impact on LPG Usage", fig_categorical(industrial, "J4 LPG Increase Due To Gas Shortage", "Gas/RLNG Shortage Impact on LPG Usage", "Increase Level", top_n, "Reds"), "Shows whether gas/RLNG shortage is shifting demand to LPG.", "Count by LPG increase due to gas shortage.", "Industrial substitution indicator.", "red")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            chart_card("Country-level Industrial LPG Supply Method", fig_categorical(industrial, "J5 LPG Supply Method", "Country-level Industrial LPG Supply Method", "Supply Method", top_n, "Greens"), "Shows cylinder vs bulk tanker or other LPG supply methods.", "Count by LPG supply method.", "Country-level industrial logistics view.", "green")
        with c4:
            chart_card("Production Disruption due to LPG Unavailability", fig_categorical(industrial, "J8 LPG Unavailability Disruption", "Production Disruption due to LPG Unavailability", "Disruption Frequency", top_n, "Reds"), "Shows how LPG/fuel unavailability affects production operations.", "Count by disruption frequency.", "Industrial reliability risk view.", "red")
        c5, c6 = st.columns(2, gap="large")
        with c5:
            chart_card("Country-level Industrial LPG Shift Barriers", fig_categorical(industrial, "J10 LPG Shift Barriers", "Country-level Industrial LPG Shift Barriers", "Barrier", top_n, "Oranges"), "Shows barriers to increasing LPG use in industry.", "Count by barrier response.", "Country-level adoption barrier view.", "orange")
        with c6:
            if "Industrial Additional LPG MT" in industrial.columns and industrial["Industrial Additional LPG MT"].notna().sum() > 0 and (industrial["Industrial Additional LPG MT"] > 0).sum() > 0:
                chart_card("Potential Additional Industrial LPG Demand", fig_distribution(industrial, "Industrial Additional LPG MT", "Potential Additional Industrial LPG Demand", "Additional LPG Demand (MT/month)", "Number of Industrial Respondents"), "Shows possible incremental LPG demand from industrial respondents.", "Histogram of additional LPG demand entered in MT/month.", "Country-level industrial opportunity estimate.", "green")
            else:
                chart_card("Industrial LPG Opportunity Indicators", fig_categorical(industrial, "J9 Replace Gas RLNG With LPG", "Industrial LPG Opportunity Indicators", "Replace Gas / RLNG with LPG", top_n, "Greens"), "J21 additional demand values were not captured, so the dashboard shows the available industrial conversion indicator instead of a blank chart.", "Count by response to replacing gas/RLNG with LPG.", "Use this as directional evidence only because the industrial sample is small.", "green")

elif page == "10. Transport Users":
    section("Transport Users", "Country-level transport LPG analysis: vehicle type, previous fuel, switching drivers, refill ease, saving and performance.")
    transport = df[df["Is Transport"]].copy()
    if transport.empty:
        st.info("No transport records in the selected scope.")
    else:
        c1, c2 = st.columns(2, gap="large")
        with c1:
            chart_card("Country-level Transport Vehicle Type", fig_categorical(transport, "K1 Vehicle Type", "Country-level Transport Vehicle Type", "Vehicle Type", top_n, "Greens"), "Shows vehicle categories represented.", "Count by vehicle type.", "Country-level transport segmentation.", "green")
        with c2:
            chart_card("Previous Fuel Before LPG", fig_categorical(transport, "K3 Previous Vehicle Fuel", "Previous Fuel Before LPG", "Previous Fuel", top_n, "Reds"), "Shows which fuels LPG is replacing in transport.", "Count by previous fuel.", "Transport fuel-switching view.", "red")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            chart_card("Reason for Switching Vehicle to LPG", fig_categorical(transport, "K5 Reason For LPG Shift", "Reason for Switching Vehicle to LPG", "Switching Reason", top_n, "Oranges"), "Explains why transport users shift to LPG.", "Count by reason for LPG shift.", "Transport adoption-driver view.", "orange")
        with c4:
            chart_card("Monthly Transport LPG Usage", fig_distribution(transport, "Transport LPG KG Month", "Monthly Transport LPG Usage", "Transport LPG Usage (KG/month)", "Number of Transport Respondents"), "Shows transport monthly LPG usage in KG.", "Histogram of converted transport LPG KG/month.", "Country-level transport usage distribution.", "blue")
        c5, c6 = st.columns(2, gap="large")
        with c5:
            chart_card("Transport Expense Change After LPG", fig_categorical(transport, "K10 Monthly Expense Change", "Transport Expense Change After LPG", "Expense Change", top_n, "Greens"), "Shows whether LPG reduced vehicle fuel expense.", "Count by monthly expense change response.", "Transport saving indicator.", "green")
        with c6:
            chart_card("Vehicle Performance on LPG", fig_categorical(transport, "K11 Vehicle Performance", "Vehicle Performance on LPG", "Performance", top_n, "RdYlGn"), "Shows vehicle performance experience on LPG.", "Count by performance response.", "Transport user experience measure.", "red")

elif page == "11. Supplier / Distributor Market":
    section("Supplier / Distributor Market", "Separate supplier-side view covering volume, customer segments, sourcing, reliability, complaints and demand outlook.")
    suppliers = df[df["Is Supplier"]].copy()
    if suppliers.empty:
        st.info("No supplier/distributor records in the selected scope.")
    else:
        total_sold = suppliers["Supplier Monthly Sold MT"].sum(skipna=True)
        med_sold = suppliers["Supplier Monthly Sold MT"].median(skipna=True)
        kpi_row([
            kpi("Supplier Records", fmt_int(len(suppliers)), "Supplier/dealer/refill point responses", BRAND["green"]),
            kpi("Reported Monthly Sold", f"{fmt_1(total_sold)} MT/month", "Sum of clean supplier volume", BRAND["red"]),
            kpi("Median Supplier Volume", f"{fmt_1(med_sold)} MT/month", "Typical supplier scale", BRAND["orange"]),
            kpi("Valid Sold Records", fmt_int(suppliers["Supplier Monthly Sold MT"].notna().sum()), "Records with usable sold volume", BRAND["blue"]),
        ], columns=4)
        c1, c2 = st.columns(2, gap="large")
        with c1:
            chart_card("Supplier Monthly LPG Sold Distribution", fig_distribution(suppliers, "Supplier Monthly Sold MT", "Supplier Monthly LPG Sold Distribution", "Monthly Sold LPG (MT/month)", "Number of Suppliers"), "Shows supplier/dealer distribution volume range.", "Histogram of supplier monthly sold volume in MT/month.", "Supplier-side, not consumer demand.", "green")
        with c2:
            chart_card("Supplier Customer Segments Served", bar_count(count_multiselect(suppliers, "SP3 Customer Segments Supplied", top_n), "Item", "Number of Respondents", "Supplier Customer Segments Served", "Customer Segment", "Number of Suppliers"), "Shows customer segments served by suppliers.", "Multi-select count of supplier segments.", "Supplier-side segment coverage.", "red")
        c3, c4 = st.columns(2, gap="large")
        with c3:
            chart_card("Supplier LPG Source", fig_categorical(suppliers, "SP7 LPG Source", "Supplier LPG Source", "LPG Source", top_n, "Greens"), "Shows where suppliers source LPG.", "Count by LPG source response.", "Supplier sourcing view.", "green")
        with c4:
            chart_card("Supplier Source Reliability", fig_categorical(suppliers, "SP8 Source Reliability", "Supplier Source Reliability", "Reliability", top_n, "Reds"), "Shows reliability of supplier LPG source.", "Count by source reliability response.", "Supplier-side reliability view.", "red")
        c5, c6 = st.columns(2, gap="large")
        with c5:
            chart_card("Fastest Growing Supplier Segment", fig_categorical(suppliers, "SP11 Fastest Growing Segment", "Fastest Growing Supplier Segment", "Growing Segment", top_n, "Oranges"), "Shows where suppliers observe growth.", "Count by fastest growing segment.", "Country-level supplier insight.", "orange")
        with c6:
            chart_card("Supplier Demand Outlook", fig_categorical(suppliers, "SP17 Supplier Demand Outlook", "Supplier Demand Outlook", "Demand Outlook", top_n, "RdYlGn"), "Shows supplier expectations for future LPG demand.", "Count by supplier demand outlook.", "Supplier-side demand sentiment.", "green")

elif page == "12. Data Quality":
    section("Data Quality", "Dashboard data quality, missing fields, valid unit conversion and caution flags.")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Missing Field Analysis", fig_missing_quality(df), "Shows missing values in key survey fields.", "Missing % = Missing records ÷ selected responses × 100.", "Blank values are not always errors because some questions are skipped by routing.", "red")
    with c2:
        chart_card("Record Completeness Distribution", fig_distribution(df, "Data Completeness %", "Record Completeness Distribution", "Data Completeness (%)", "Number of Records"), "Shows completeness across critical common fields.", "Completeness = 100 × (1 − missing critical fields ÷ critical field count).", "Higher is better.", "green")
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Usage Unit Status", fig_categorical(df, "C3 LPG Monthly Quantity Unit", "Monthly LPG Usage Unit Status", "Usage Unit", top_n, "Blues"), "Shows how usage was originally reported before conversion.", "Count by original monthly quantity unit.", "Converted to KG/month for country-level demand charts.", "blue")
    with c4:
        chart_card("Price Unit Status", fig_categorical(df, "C6 LPG Price Unit", "LPG Price Unit Status", "Price Unit", top_n, "Oranges"), "Shows how price was originally reported before conversion.", "Count by original price unit.", "Converted to PKR/KG where possible.", "orange")
    if show_tables:
        st.dataframe(df[["ID", "Category", "City Clean", "Current LPG User Flag", "Monthly LPG Usage KG", "LPG Price PKR per KG", "Missing Critical Fields", "Data Completeness %"]], use_container_width=True, hide_index=True)

elif page == "13. Raw Data":
    section("Raw / Filtered Data", "Inspect and export the filtered country-level survey data used by the dashboard.")
    st.markdown('<div class="note-box">Use the sidebar download button to export the same filtered dataset. The table below keeps raw survey columns plus dashboard-calculated fields.</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, height=650)

# Footer
st.markdown(
    f"""
    <div class="note-box">
        <b>Deployment guidance:</b> For online deployment, place this app file, <b>requirements.txt</b>, and <b>Clean-Data-lpg-survey.csv</b> in the same GitHub repository, then deploy on Streamlit Community Cloud. The app will automatically load the CSV from the repository folder.
    </div>
    """,
    unsafe_allow_html=True,
)
