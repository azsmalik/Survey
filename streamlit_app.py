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

INCOME_BAND_CANDIDATES = [
    "G8 Income Band",
    "Income Band",
    "Monthly Income",
    "Average Monthly Income",
    "Avg Monthly Income",
    "Household Income",
    "Monthly Household Income",
    "Household Income PKR",
]

INCOME_CLASS_ORDER = [
    "Low Income",
    "Lower-Middle Income",
    "Middle / Upper-Middle Income",
    "Upper Income",
    "Undisclosed Income",
]

INCOME_CLASS_THRESHOLDS = [
    {
        "Survey Income Band": "Below PKR 50,000",
        "Dashboard Income Class": "Low Income",
        "Threshold Logic": "< PKR 50,000 per month",
        "Use in Analysis": "Household/residential affordability and LPG adoption",
    },
    {
        "Survey Income Band": "PKR 50,001-100,000",
        "Dashboard Income Class": "Lower-Middle Income",
        "Threshold Logic": "PKR 50,001 to 100,000 per month",
        "Use in Analysis": "Household/residential affordability and LPG adoption",
    },
    {
        "Survey Income Band": "PKR 100,001-250,000",
        "Dashboard Income Class": "Middle / Upper-Middle Income",
        "Threshold Logic": "PKR 100,001 to 250,000 per month",
        "Use in Analysis": "Household/residential affordability and LPG adoption",
    },
    {
        "Survey Income Band": "Above PKR 250,000",
        "Dashboard Income Class": "Upper Income",
        "Threshold Logic": "> PKR 250,000 per month",
        "Use in Analysis": "Household/residential affordability and LPG adoption",
    },
    {
        "Survey Income Band": "Prefer not to say",
        "Dashboard Income Class": "Undisclosed Income",
        "Threshold Logic": "Income band intentionally not disclosed",
        "Use in Analysis": "Shown separately and not mixed with income tiers",
    },
]

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
            max-width: 1760px;
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
            margin: 0 0 24px 0;
        }}
        .hero-title {{
            color: var(--navy);
            font-size: 34px;
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
            min-height: 118px;
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
            font-size: 25px;
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
            padding: 14px 16px 16px 16px;
            margin: 0 0 24px 0;
        }}
        .analysis-box {{
            margin-top: 7px;
            background: #F8FAFC;
            border: 1px solid #E5E7EB;
            border-left: 5px solid var(--accent);
            border-radius: 14px;
            padding: 10px 12px;
            color: #334155;
            font-size: 12.5px;
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
            font-size: 12.5px;
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
            overflow-wrap: anywhere;
        }}
        div[data-testid="stDataFrame"] {{
            border-radius: 14px;
            overflow: hidden;
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

        div[data-baseweb="tab-list"] {{
            gap: 8px;
            flex-wrap: wrap;
        }}
        button[data-baseweb="tab"] {{
            height: auto;
            min-height: 42px;
            white-space: normal;
            line-height: 1.2;
            padding: 8px 12px;
        }}
        .stPlotlyChart {{
            overflow: visible;
        }}
        div[data-testid="stMetricValue"] {{
            white-space: normal;
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


def normalize_income_class(x) -> str:
    """Convert the survey income bands into fixed management analysis classes.

    The survey captures income as a band, not as a numeric income value.
    Therefore, dashboard analysis must classify income using the exact survey
    threshold bands instead of creating artificial numeric cut-offs.
    """
    raw = normalize_text(x)
    low = raw.lower().replace("–", "-").replace("—", "-")

    if raw == "Unknown" or low in {"not captured", "not applicable", "n/a", "na", "blank", "missing"}:
        return "Not Captured / Not Applicable"

    if "prefer" in low or "not to say" in low or "undisclosed" in low:
        return "Undisclosed Income"

    # Survey threshold 1: Below PKR 50,000 per month
    if "below" in low and "50" in low:
        return "Low Income"

    # Survey threshold 2: PKR 50,001-100,000 per month
    if ("50,001" in raw or "50001" in low or "50k" in low or "50,000" in raw) and ("100" in raw or "100" in low):
        return "Lower-Middle Income"

    # Survey threshold 3: PKR 100,001-250,000 per month
    if ("100,001" in raw or "100001" in low or "100,000" in raw) and ("250" in raw or "250" in low):
        return "Middle / Upper-Middle Income"

    # Survey threshold 4: Above PKR 250,000 per month
    if "above" in low and "250" in low:
        return "Upper Income"

    return raw


def income_sort_key(value: str) -> int:
    try:
        return INCOME_CLASS_ORDER.index(value)
    except ValueError:
        return len(INCOME_CLASS_ORDER) + 1


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


def wrap_chart_title(title: str, width: int = 78) -> str:
    """Wrap long Plotly titles using HTML line breaks so they do not overlap legends."""
    title = str(title)
    if len(title) <= width:
        return title
    words = title.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return "<br>".join(lines[:3])


def shorten_axis_labels(fig: go.Figure, max_len: int = 28) -> go.Figure:
    """Shorten very long categorical tick labels while preserving full labels in hover."""
    for axis_name in ["xaxis", "yaxis"]:
        axis = getattr(fig.layout, axis_name, None)
        if axis is None:
            continue
        try:
            values = axis.categoryarray
            if values:
                tickvals = list(values)
                ticktext = [str(v) if len(str(v)) <= max_len else str(v)[: max_len - 3] + "..." for v in tickvals]
                fig.update_layout({axis_name: dict(tickmode="array", tickvals=tickvals, ticktext=ticktext)})
        except Exception:
            pass
    return fig


def polish_trace_readability(fig: go.Figure) -> go.Figure:
    """Apply conservative defaults that prevent label and number overlap."""
    bar_traces = [t for t in fig.data if getattr(t, "type", "") == "bar"]
    vertical_bar_count = sum(1 for t in bar_traces if getattr(t, "orientation", None) != "h")
    grouped_or_stacked_vertical = vertical_bar_count > 1

    for trace in fig.data:
        trace_type = getattr(trace, "type", "")

        if trace_type == "bar":
            try:
                trace.textfont = dict(color=BRAND["ink"], size=10)
                trace.insidetextfont = dict(color="white", size=10)
                trace.outsidetextfont = dict(color=BRAND["ink"], size=10)
            except Exception:
                pass
            try:
                trace.cliponaxis = False
                trace.constraintext = "both"
            except Exception:
                pass

            # Dense grouped/stacked vertical bars are the main source of overlap.
            # Keep numbers in hover and supporting tables instead of forcing labels on every bar.
            if grouped_or_stacked_vertical and getattr(trace, "orientation", None) != "h":
                try:
                    trace.textposition = "none"
                except Exception:
                    pass
            else:
                try:
                    if getattr(trace, "textposition", None) in ["outside", "inside"]:
                        trace.textposition = "auto"
                except Exception:
                    pass

        elif trace_type in {"scatter", "pie", "treemap", "sunburst"}:
            try:
                trace.textfont = dict(color=BRAND["ink"], size=10)
            except Exception:
                pass

        elif trace_type == "heatmap":
            try:
                trace.textfont = dict(size=9)
            except Exception:
                pass

    return fig


def style_fig(fig: go.Figure, title: str, height: int = 520) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        title=dict(text=wrap_chart_title(title), x=0.02, xanchor="left", y=0.98, font=dict(size=18, color=BRAND["navy"])),
        height=max(height, 560),
        margin=dict(l=185, r=120, t=120, b=130),
        font=dict(size=12, color=BRAND["ink"]),
        paper_bgcolor="white",
        plot_bgcolor="#F8FAFC",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.04,
            xanchor="right",
            x=1,
            font=dict(size=10),
            itemwidth=30,
        ),
        uniformtext=dict(minsize=9, mode="hide"),
        bargap=0.24,
        bargroupgap=0.18,
    )
    fig.update_xaxes(
        showgrid=False,
        automargin=True,
        title_standoff=18,
        title_font=dict(color=BRAND["ink"], size=12),
        tickfont=dict(color=BRAND["ink"], size=10),
        linecolor="#CBD5E1",
        tickcolor="#CBD5E1",
    )
    fig.update_yaxes(
        gridcolor="rgba(16,42,67,0.12)",
        automargin=True,
        title_standoff=18,
        title_font=dict(color=BRAND["ink"], size=12),
        tickfont=dict(color=BRAND["ink"], size=10),
        separatethousands=True,
        linecolor="#CBD5E1",
        tickcolor="#CBD5E1",
    )
    fig = polish_trace_readability(fig)
    fig = shorten_axis_labels(fig)
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
    color = BRAND.get(accent, BRAND["green"])
    st.markdown(f'<div class="chart-card" style="--accent:{color};">', unsafe_allow_html=True)

    # Streamlit can raise DuplicateElementId when the same Plotly chart structure
    # appears in multiple sector tabs. A controlled unique key prevents this.
    st.session_state["_plotly_chart_counter"] = st.session_state.get("_plotly_chart_counter", 0) + 1
    chart_key = f"plotly_chart_{st.session_state['_plotly_chart_counter']}"

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

    # Some survey exports keep area type under A9 Area Type. Use it as a fallback.
    if "A9 Area Type" in df.columns:
        area_fallback = df["A9 Area Type"].apply(normalize_text)
        df["Area Type"] = np.where(df["Area Type"].isin(["Unknown", "", "nan", "None"]), area_fallback, df["Area Type"])

    df["Category"] = df["Respondent Category"].map(CATEGORY_MAP).fillna(df["Respondent Category"])
    df["Category"] = df["Category"].apply(normalize_text)
    df["City Clean"] = df["City"].replace({"Unknown": "Not Captured", "": "Not Captured"})
    df["Province Clean"] = df["Province"].replace({"Unknown": "Not Captured", "": "Not Captured"})
    df["Area Type Clean"] = df["Area Type"].replace({"Unknown": "Not Captured", "": "Not Captured"})
    # Canonical area-type labels for clean Urban / Rural / Peri-Urban comparison.
    df["Area Type Clean"] = df["Area Type Clean"].apply(lambda x: (
        "Peri-Urban" if "peri" in normalize_text(x).lower() else
        "Urban" if normalize_text(x).lower() == "urban" else
        "Rural" if normalize_text(x).lower() == "rural" else
        "Not Captured" if normalize_text(x).lower() in {"unknown", "", "nan", "none", "null"} else
        normalize_text(x)
    ))

    # Income band is captured mainly for household respondents in this survey.
    # The dashboard keeps it as a band/class rather than treating it as numeric income.
    income_source = pd.Series("Unknown", index=df.index)
    income_source_column = "Not Found"
    for candidate in INCOME_BAND_CANDIDATES:
        if candidate in df.columns:
            values = df[candidate].apply(normalize_text)
            income_source = income_source.mask(income_source.eq("Unknown"), values)
            if income_source_column == "Not Found":
                income_source_column = candidate
    df["Income Band Raw"] = income_source.apply(normalize_text)
    df["Income Class"] = df["Income Band Raw"].apply(normalize_income_class)
    df["Income Captured Flag"] = (~df["Income Class"].isin(["Not Captured / Not Applicable", "Unknown"])).astype(int)
    df["Income Source Column"] = income_source_column

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
    df["Natural Gas Denominator"] = non_blank_series(get_col(df, "B2 Natural Gas Connection")).astype(int)
    df["Solar Installed Flag"] = get_col(df, "B4 Solar Installed").apply(yes_flag)
    df["Solar Denominator"] = non_blank_series(get_col(df, "B4 Solar Installed")).astype(int)
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

    # Household size is captured under different possible column names depending on the survey export.
    # The dashboard will use the first available valid numeric field.
    household_size_candidates = [
        "G1 Household Size",
        "C1 Household Members",
        "Household Members",
        "Number of Household Members",
        "Household Size",
        "No Of People In Household",
        "No. of People in Household",
        "People In Household",
    ]
    household_size = pd.Series(np.nan, index=df.index)
    for candidate in household_size_candidates:
        if candidate in df.columns:
            candidate_values = pd.to_numeric(df[candidate], errors="coerce")
            household_size = household_size.fillna(candidate_values)
    df["Household Size"] = household_size
    df["Valid Household Size Flag"] = df["Household Size"].between(1, 50, inclusive="both").astype(int)
    df["Household LPG KG per Person"] = np.where(
        (df["Valid Household Size Flag"].eq(1)) & (df["Monthly LPG Usage KG"].notna()) & (df["Monthly LPG Usage KG"] > 0),
        df["Monthly LPG Usage KG"] / df["Household Size"],
        np.nan,
    )

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
    g["Label"] = g.apply(lambda r: f"{r['LPG Adoption Rate (%)']:.1f}%" if pd.notna(r["LPG Adoption Rate (%)"]) else "n/a", axis=1)
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
    g["Label"] = g.apply(lambda r: f"{r[rate_name]:.1f}%" if pd.notna(r[rate_name]) else "n/a", axis=1)
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
        fig.update_xaxes(tickangle=-18, tickfont=dict(size=10), automargin=True)
        fig.update_layout(xaxis_title=x_title, yaxis_title=y_title, coloraxis_showscale=False)
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="auto", cliponaxis=False)
    return style_fig(fig, title, height=max(480, min(790, 380 + len(d) * 28)))


def fig_adoption(df: pd.DataFrame, by: str, title: str, min_n: int, top_n: int) -> go.Figure:
    d = adoption_rate(df, by, min_n).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    fig = px.bar(d, x="LPG Adoption Rate (%)", y=by, orientation="h", text="Label", color="Known LPG Responses", color_continuous_scale="RdYlGn", hover_data=["Current LPG Users", "Known LPG Responses", "Total Responses", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="LPG Adoption Rate (% of Known Responses)", yaxis_title=by, coloraxis_colorbar_title="Known n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_city_user_pct(df: pd.DataFrame, min_n: int, top_n: int) -> go.Figure:
    d = adoption_rate(df, "City Clean", min_n).head(top_n)
    if d.empty:
        return empty_fig("City-wise Current LPG User %")
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    fig = px.bar(d, x="LPG Adoption Rate (%)", y="City Clean", orientation="h", text="Label", color="Current LPG Users", color_continuous_scale="Greens", hover_data=["Current LPG Users", "Known LPG Responses", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="Current LPG Users (% of Known Responses)", yaxis_title="City", coloraxis_colorbar_title="LPG Users")
    return style_fig(fig, "City-wise LPG Adoption Rate / Current LPG Users %", height=max(520, min(850, 380 + len(d) * 30)))


def fig_demand_total(df: pd.DataFrame, by: str, title: str, top_n: int) -> go.Figure:
    d = demand_summary(df, by).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Total LPG Usage MT/month", ascending=True)
    fig = px.bar(d, x="Total LPG Usage MT/month", y=by, orientation="h", text="Total LPG Usage MT/month", color="Median LPG Usage KG/month", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Total LPG Usage (MT/month)", yaxis_title=by, coloraxis_colorbar_title="Median KG/month")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_median_usage(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    d = demand_summary(df, by)
    d = d[d["Valid Usage Records"] >= min_n].sort_values("Median LPG Usage KG/month", ascending=False).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Median LPG Usage KG/month", ascending=True)
    fig = px.bar(d, x="Median LPG Usage KG/month", y=by, orientation="h", text="Median LPG Usage KG/month", color="Valid Usage Records", color_continuous_scale="RdYlGn")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Median LPG Usage (KG/month)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_price_by(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    d = median_price_summary(df, by)
    d = d[d["Valid Price Records"] >= min_n].head(top_n)
    if d.empty:
        return empty_fig(title, "No valid price records after sample filter")
    d = d.sort_values("Median LPG Price PKR/KG", ascending=True)
    fig = px.bar(d, x="Median LPG Price PKR/KG", y=by, orientation="h", text="Median LPG Price PKR/KG", color="Valid Price Records", color_continuous_scale="RdYlGn_r")
    fig.update_traces(texttemplate="PKR %{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Median LPG Price (PKR/KG)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_distribution(df: pd.DataFrame, column: str, title: str, x_title: str, y_title: str, log_x: bool = False) -> go.Figure:
    if column not in df.columns:
        return empty_fig(title)
    d = df[df[column].notna() & (df[column] > 0)].copy()
    if d.empty:
        return empty_fig(title)

    # Use a plain histogram instead of Plotly's marginal box plot.
    # The previous marginal='box' created Box traces; combined with global textfont styling,
    # it generated the ValueError shown in the screenshots.
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=d[column],
            nbinsx=35,
            marker=dict(color=BRAND["green"], line=dict(color="white", width=1)),
            hovertemplate=f"{x_title}: %{{x}}<br>{y_title}: %{{y}}<extra></extra>",
            name=title,
        )
    )
    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title, bargap=0.07, showlegend=False)
    if log_x:
        fig.update_xaxes(type="log")
    return style_fig(fig, title, height=575)



def fig_usage_bucket_distribution(df: pd.DataFrame, title: str = "LPG Usage Distribution") -> go.Figure:
    """Bucketed usage chart used instead of log-scale histograms.

    This prevents empty-looking charts when small household records and very large
    commercial/industrial records exist in the same selected dataset.
    """
    if "Monthly LPG Usage KG" not in df.columns:
        return empty_fig(title)

    d = df[df["Monthly LPG Usage KG"].notna() & (df["Monthly LPG Usage KG"] > 0)].copy()
    if d.empty:
        return empty_fig(title, "No valid monthly LPG usage records for the selected filters")

    bins = [0, 25, 50, 100, 250, 500, 1000, 5000, 10000, 50000, float("inf")]
    labels = [
        "0-25 KG",
        "25-50 KG",
        "50-100 KG",
        "100-250 KG",
        "250-500 KG",
        "500-1,000 KG",
        "1,000-5,000 KG",
        "5,000-10,000 KG",
        "10,000-50,000 KG",
        ">50,000 KG",
    ]
    d["Usage Bucket"] = pd.cut(d["Monthly LPG Usage KG"], bins=bins, labels=labels, include_lowest=True)
    bucket_df = d.groupby("Usage Bucket", observed=True).size().reset_index(name="Number of Respondents")
    bucket_df["Usage Bucket"] = bucket_df["Usage Bucket"].astype(str)

    fig = px.bar(
        bucket_df,
        x="Usage Bucket",
        y="Number of Respondents",
        text="Number of Respondents",
        color="Number of Respondents",
        color_continuous_scale="RdYlGn",
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_layout(
        xaxis_title="Monthly LPG Usage Bucket",
        yaxis_title="Number of Respondents",
        coloraxis_showscale=False,
    )
    fig.update_xaxes(tickangle=-18, tickfont=dict(size=10), automargin=True)
    return style_fig(fig, title, height=560)


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
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
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
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Number of Respondents", yaxis_title="Fuel Source", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Fuel Source Mix", 560)


def fig_safety_rate(df: pd.DataFrame, by: str, min_n: int, top_n: int) -> go.Figure:
    d = rate_summary(df, by, "Safety Incident Flag", "Safety Denominator", "Safety Incident Rate (%)", min_n).head(top_n)
    if d.empty:
        return empty_fig("Country-level Safety Incident Rate")
    d = d.sort_values("Safety Incident Rate (%)", ascending=True)
    fig = px.bar(d, x="Safety Incident Rate (%)", y=by, orientation="h", text="Label", color="denominator", color_continuous_scale="RdYlGn_r", hover_data=["numerator", "denominator", "Sample Strength"])
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
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
    fig.update_traces(texttemplate="%{text:.2f}", textposition="auto", cliponaxis=False)
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
    fig.update_traces(texttemplate="%{text:.2f}", textposition="auto", cliponaxis=False)
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
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%")
    fig.update_layout(xaxis_title="Missing Responses (%)", yaxis_title="Survey Field", coloraxis_showscale=False)
    return style_fig(fig, "Country-level Data Completeness / Missing Field Analysis", 620)


# ------------------------------------------------------------
# Amended sector-wise analysis helpers
# ------------------------------------------------------------
def metric_summary(dff: pd.DataFrame) -> Dict[str, float]:
    valid_usage_local = dff[dff["Valid Usage Flag"].eq(1)].copy() if "Valid Usage Flag" in dff.columns else pd.DataFrame()
    valid_price_local = dff[dff["Valid Price Flag"].eq(1)].copy() if "Valid Price Flag" in dff.columns else pd.DataFrame()
    known_lpg_local = float(dff["LPG Adoption Denominator"].sum()) if "LPG Adoption Denominator" in dff.columns else 0
    lpg_users_local = float(dff["Current LPG User Flag"].sum()) if "Current LPG User Flag" in dff.columns else 0
    total_usage_kg_local = float(valid_usage_local["Monthly LPG Usage KG"].sum()) if not valid_usage_local.empty else np.nan
    total_usage_mt_local = total_usage_kg_local / 1000 if pd.notna(total_usage_kg_local) else np.nan
    return {
        "responses": len(dff),
        "known_lpg": known_lpg_local,
        "lpg_users": lpg_users_local,
        "adoption_pct": pct(lpg_users_local, known_lpg_local),
        "total_usage_mt": total_usage_mt_local,
        "avg_usage_kg": valid_usage_local["Monthly LPG Usage KG"].mean() if not valid_usage_local.empty else np.nan,
        "valid_usage_records": len(valid_usage_local),
        "avg_price": valid_price_local["LPG Price PKR per KG"].mean() if not valid_price_local.empty else np.nan,
        "valid_price_records": len(valid_price_local),
        "natural_gas_yes": float(dff["Natural Gas Connection Flag"].sum()) if "Natural Gas Connection Flag" in dff.columns else 0,
        "natural_gas_den": float(dff["Natural Gas Denominator"].sum()) if "Natural Gas Denominator" in dff.columns else 0,
        "solar_yes": float(dff["Solar Installed Flag"].sum()) if "Solar Installed Flag" in dff.columns else 0,
        "solar_den": float(dff["Solar Denominator"].sum()) if "Solar Denominator" in dff.columns else 0,
        "safety_yes": float(dff["Safety Incident Flag"].sum()) if "Safety Incident Flag" in dff.columns else 0,
        "safety_den": float(dff["Safety Denominator"].sum()) if "Safety Denominator" in dff.columns else 0,
        "solid_users": float(dff["Uses Solid Fuel"].sum()) if "Uses Solid Fuel" in dff.columns else 0,
    }


def demand_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    d = df[df["Valid Usage Flag"].eq(1)].copy()
    if d.empty or by not in d.columns:
        return pd.DataFrame()
    g = d.groupby(by, dropna=False).agg(
        **{
            "Valid Usage Records": ("Monthly LPG Usage KG", "count"),
            "Total LPG Usage KG/month": ("Monthly LPG Usage KG", "sum"),
            "Total LPG Usage MT/month": ("Monthly LPG Usage MT", "sum"),
            "Average LPG Usage KG/month": ("Monthly LPG Usage KG", "mean"),
            "Median LPG Usage KG/month": ("Monthly LPG Usage KG", "median"),
        }
    ).reset_index()
    return g.sort_values("Total LPG Usage MT/month", ascending=False)


def median_price_summary(df: pd.DataFrame, by: str) -> pd.DataFrame:
    # Kept function name for compatibility with the existing code, but primary analysis is now average/mean.
    d = df[df["Valid Price Flag"].eq(1)].copy()
    if d.empty or by not in d.columns:
        return pd.DataFrame()
    g = d.groupby(by, dropna=False).agg(
        **{
            "Valid Price Records": ("LPG Price PKR per KG", "count"),
            "Average LPG Price PKR/KG": ("LPG Price PKR per KG", "mean"),
            "Median LPG Price PKR/KG": ("LPG Price PKR per KG", "median"),
        }
    ).reset_index()
    return g.sort_values("Average LPG Price PKR/KG", ascending=False)


def fig_demand_total(df: pd.DataFrame, by: str, title: str, top_n: int) -> go.Figure:
    d = demand_summary(df, by).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Total LPG Usage MT/month", ascending=True)
    fig = px.bar(
        d,
        x="Total LPG Usage MT/month",
        y=by,
        orientation="h",
        text="Total LPG Usage MT/month",
        color="Average LPG Usage KG/month",
        color_continuous_scale="RdYlGn",
        hover_data=["Valid Usage Records", "Average LPG Usage KG/month"],
    )
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Total Reported Demand (MT/month)", yaxis_title=by, coloraxis_colorbar_title="Avg KG/month")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(d) * 28)))


def fig_median_usage(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    # Kept function name for compatibility; chart now shows Average LPG Usage.
    d = demand_summary(df, by)
    d = d[d["Valid Usage Records"] >= min_n].sort_values("Average LPG Usage KG/month", ascending=False).head(top_n)
    if d.empty:
        return empty_fig(title)
    d = d.sort_values("Average LPG Usage KG/month", ascending=True)
    fig = px.bar(
        d,
        x="Average LPG Usage KG/month",
        y=by,
        orientation="h",
        text="Average LPG Usage KG/month",
        color="Valid Usage Records",
        color_continuous_scale="RdYlGn",
        hover_data=["Valid Usage Records", "Total LPG Usage MT/month"],
    )
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Average LPG Usage (KG/month)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title.replace("Median", "Average"), height=max(500, min(820, 380 + len(d) * 28)))


def fig_price_by(df: pd.DataFrame, by: str, title: str, top_n: int, min_n: int) -> go.Figure:
    d = median_price_summary(df, by)
    d = d[d["Valid Price Records"] >= min_n].head(top_n)
    if d.empty:
        return empty_fig(title, "No valid price records after sample filter")
    d = d.sort_values("Average LPG Price PKR/KG", ascending=True)
    fig = px.bar(
        d,
        x="Average LPG Price PKR/KG",
        y=by,
        orientation="h",
        text="Average LPG Price PKR/KG",
        color="Valid Price Records",
        color_continuous_scale="RdYlGn_r",
        hover_data=["Valid Price Records", "Median LPG Price PKR/KG"],
    )
    fig.update_traces(texttemplate="PKR %{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title="Average LPG Price (PKR/KG)", yaxis_title=by, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title.replace("Median", "Average"), height=max(500, min(820, 380 + len(d) * 28)))


def fig_rate_by_sector(df: pd.DataFrame, numerator: str, denominator: str, rate_title: str, min_n: int, top_n: int, color_scale: str = "RdYlGn") -> go.Figure:
    d = rate_summary(df, "Category", numerator, denominator, rate_title, min_n).head(top_n)
    if d.empty:
        return empty_fig(rate_title)
    d = d.sort_values(rate_title, ascending=True)
    fig = px.bar(
        d,
        x=rate_title,
        y="Category",
        orientation="h",
        text="Label",
        color="denominator",
        color_continuous_scale=color_scale,
        hover_data=["numerator", "denominator", "Sample Strength"],
    )
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title=rate_title, yaxis_title="Sector", coloraxis_colorbar_title="Known n")
    return style_fig(fig, rate_title + " by Sector", height=max(500, min(820, 380 + len(d) * 30)))


def fig_area_split_by_sector(df: pd.DataFrame, title: str = "Urban / Rural Split by Sector") -> go.Figure:
    if "Area Type Clean" not in df.columns or "Category" not in df.columns:
        return empty_fig(title)
    d = df.copy()
    d = d[d["Area Type Clean"].apply(normalize_text).ne("Unknown")]
    if d.empty:
        return empty_fig(title, "Urban / rural field is not available in the selected records")
    g = d.groupby(["Category", "Area Type Clean"], dropna=False).size().reset_index(name="Respondents")
    totals = g.groupby("Category")["Respondents"].transform("sum")
    g["Share %"] = np.where(totals > 0, g["Respondents"] / totals * 100, np.nan)
    fig = px.bar(
        g,
        x="Category",
        y="Share %",
        color="Area Type Clean",
        text="Share %",
        barmode="stack",
        color_discrete_sequence=[BRAND["green"], BRAND["orange"], BRAND["blue"], BRAND["gray"]],
        hover_data=["Respondents"],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_yaxes(ticksuffix="%", range=[0, 105])
    fig.update_xaxes(tickangle=-18, tickfont=dict(size=10), automargin=True)
    fig.update_layout(xaxis_title="Sector", yaxis_title="Share of respondents", legend_title_text="Area Type")
    return style_fig(fig, title, height=600)


def fig_fuel_mix_by_sector(df: pd.DataFrame, title: str = "Fuel Source Mix by Sector") -> go.Figure:
    rows = []
    for cat, sub in df.groupby("Category"):
        base = len(sub)
        if base == 0:
            continue
        for fuel in FUEL_PREFIXES:
            col = f"Uses {fuel}"
            if col in sub.columns:
                users = sub[col].sum()
                rows.append({"Sector": cat, "Fuel Source": fuel, "% of Sector Responses": pct(users, base), "Respondents": users})
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig(title)
    pivot = d.pivot(index="Sector", columns="Fuel Source", values="% of Sector Responses").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="% of Sector"))
    fig.update_layout(xaxis_title="Fuel Source", yaxis_title="Sector")
    return style_fig(fig, title, height=max(530, 310 + len(pivot) * 34))


def fig_numeric_mean_by_sector(df: pd.DataFrame, column: str, title: str, x_title: str, min_n: int, top_n: int, color_scale: str = "RdYlGn") -> go.Figure:
    if column not in df.columns:
        return empty_fig(title)
    d = df[pd.to_numeric(df[column], errors="coerce").notna()].copy()
    d[column] = pd.to_numeric(d[column], errors="coerce")
    d = d[d[column] > 0]
    if d.empty:
        return empty_fig(title)
    g = d.groupby("Category", dropna=False).agg(**{"Valid Records": (column, "count"), "Average Value": (column, "mean")}).reset_index()
    g = g[g["Valid Records"] >= min_n].sort_values("Average Value", ascending=False).head(top_n)
    if g.empty:
        return empty_fig(title, "No sector has enough valid records after sample filter")
    g = g.sort_values("Average Value", ascending=True)
    fig = px.bar(g, x="Average Value", y="Category", orientation="h", text="Average Value", color="Valid Records", color_continuous_scale=color_scale)
    fig.update_traces(texttemplate="%{text:,.1f}", textposition="auto", cliponaxis=False)
    fig.update_layout(xaxis_title=x_title, yaxis_title="Sector", coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=max(500, min(820, 380 + len(g) * 30)))


def fig_categorical_by_sector_heatmap(df: pd.DataFrame, column: str, title: str, top_n_categories: int = 8) -> go.Figure:
    if column not in df.columns:
        return empty_fig(title)
    d = df[non_blank_series(df[column])].copy()
    if d.empty:
        return empty_fig(title)
    top_values = d[column].apply(normalize_text).value_counts().head(top_n_categories).index.tolist()
    d[column] = d[column].apply(normalize_text)
    d = d[d[column].isin(top_values)]
    g = d.groupby(["Category", column], dropna=False).size().reset_index(name="Responses")
    totals = g.groupby("Category")["Responses"].transform("sum")
    g["Share %"] = np.where(totals > 0, g["Responses"] / totals * 100, 0)
    pivot = g.pivot(index="Category", columns=column, values="Share %").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="% within sector"))
    fig.update_layout(xaxis_title=column, yaxis_title="Sector")
    return style_fig(fig, title, height=max(530, 310 + len(pivot) * 34))


def fig_data_completeness_by_sector(df: pd.DataFrame) -> go.Figure:
    if "Data Completeness %" not in df.columns:
        return empty_fig("Average Data Completeness by Sector")
    g = df.groupby("Category", dropna=False).agg(**{"Records": ("Category", "count"), "Average Completeness %": ("Data Completeness %", "mean")}).reset_index()
    g = g.sort_values("Average Completeness %", ascending=True)
    fig = px.bar(g, x="Average Completeness %", y="Category", orientation="h", text="Average Completeness %", color="Records", color_continuous_scale="Greens")
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="Average Data Completeness", yaxis_title="Sector", coloraxis_colorbar_title="Records")
    return style_fig(fig, "Average Data Completeness by Sector", height=max(520, min(820, 380 + len(g) * 30)))


def sector_kpi_cards(dff: pd.DataFrame) -> List[str]:
    m = metric_summary(dff)
    return [
        kpi("Total Responses", fmt_int(m["responses"]), "Selected sector records", BRAND["green"]),
        kpi("Current LPG Users", fmt_int(m["lpg_users"]), f"Known LPG answers: {fmt_int(m['known_lpg'])}", BRAND["red"]),
        kpi("LPG Adoption Rate", fmt_pct(m["adoption_pct"]), "LPG users ÷ known LPG responses", BRAND["green"]),
        kpi("Natural Gas Connections", fmt_int(m["natural_gas_yes"]), f"{fmt_pct(pct(m['natural_gas_yes'], m['natural_gas_den']))} of {fmt_int(m['natural_gas_den'])} known", BRAND["blue"]),
        kpi("Total Reported Demand", f"{fmt_1(m['total_usage_mt'])} MT/month", "Sum of valid monthly usage records", BRAND["orange"]),
        kpi("Average LPG Usage", f"{fmt_int(m['avg_usage_kg'])} KG/month", "Mean of valid usage records", BRAND["blue"]),
        kpi("Average LPG Price", f"{fmt_pkr(m['avg_price'])}/KG", "Mean of clean PKR/KG records", BRAND["purple"]),
        kpi("Safety Incident Rate", fmt_pct(pct(m["safety_yes"], m["safety_den"])), f"{fmt_int(m['safety_yes'])} incidents / {fmt_int(m['safety_den'])} known", BRAND["red"]),
        kpi("Solar Adoption", fmt_pct(pct(m["solar_yes"], m["solar_den"])), f"{fmt_int(m['solar_yes'])} solar users / {fmt_int(m['solar_den'])} known", BRAND["teal"]),
        kpi("Valid Usage Records", fmt_int(m["valid_usage_records"]), "Used for demand and average usage", BRAND["green"]),
        kpi("Valid Price Records", fmt_int(m["valid_price_records"]), "Used for average LPG price", BRAND["purple"]),
        kpi("Solid Fuel Users", fmt_int(m["solid_users"]), "Respondents using solid fuel", BRAND["orange"]),
    ]



def fig_area_lpg_users(df: pd.DataFrame, min_n: int, top_n: int) -> go.Figure:
    title = "LPG Adoption Share by Area Type"
    if "Area Type Clean" not in df.columns:
        return empty_fig(title)
    d = adoption_rate(df, "Area Type Clean", min_n).head(top_n)
    if d.empty:
        return empty_fig(title, "No area type has enough known LPG responses after the selected filter")
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    d["Display Label"] = d.apply(
        lambda r: f"{r['LPG Adoption Rate (%)']:.1f}%" if pd.notna(r["LPG Adoption Rate (%)"]) else "n/a",
        axis=1,
    )
    fig = px.bar(
        d,
        x="LPG Adoption Rate (%)",
        y="Area Type Clean",
        orientation="h",
        text="Display Label",
        color="Known LPG Responses",
        color_continuous_scale="RdYlGn",
        hover_data=["Current LPG Users", "Known LPG Responses", "Total Responses", "Sample Strength"],
    )
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(
        xaxis_title="LPG Adoption Share (% of known LPG responses)",
        yaxis_title="Area Type",
        coloraxis_colorbar_title="Known n",
    )
    return style_fig(fig, title, height=max(500, min(760, 380 + len(d) * 55)))

def fig_area_adoption_rate(df: pd.DataFrame, min_n: int, top_n: int) -> go.Figure:
    title = "LPG Adoption Rate by Area Type"
    if "Area Type Clean" not in df.columns:
        return empty_fig(title)
    d = adoption_rate(df, "Area Type Clean", min_n).head(top_n)
    if d.empty:
        return empty_fig(title, "No area type has enough known LPG responses after the selected filter")
    d = d.sort_values("LPG Adoption Rate (%)", ascending=True)
    fig = px.bar(
        d,
        x="LPG Adoption Rate (%)",
        y="Area Type Clean",
        orientation="h",
        text="Label",
        color="Known LPG Responses",
        color_continuous_scale="Greens",
        hover_data=["Current LPG Users", "Known LPG Responses", "Sample Strength"],
    )
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="LPG Adoption Rate (% of known responses)", yaxis_title="Area Type", coloraxis_colorbar_title="Known n")
    return style_fig(fig, title, height=max(500, min(760, 380 + len(d) * 55)))


def fig_fuel_mix_by_area(df: pd.DataFrame, title: str = "Fuel Source Usage Share by Area Type") -> go.Figure:
    if "Area Type Clean" not in df.columns:
        return empty_fig(title)
    rows = []
    for area, sub in df.groupby("Area Type Clean", dropna=False):
        area = normalize_text(area)
        if area in {"Unknown", "", "Not Captured"}:
            continue
        base = len(sub)
        if base == 0:
            continue
        for fuel in FUEL_PREFIXES:
            col = f"Uses {fuel}"
            if col in sub.columns:
                users = float(sub[col].sum())
                rows.append({
                    "Area Type": area,
                    "Fuel Source": fuel,
                    "% of Area Responses": pct(users, base),
                    "Respondents": users,
                    "Area Base": base,
                })
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig(title)
    fig = px.bar(
        d,
        x="Area Type",
        y="% of Area Responses",
        color="Fuel Source",
        text="% of Area Responses",
        barmode="group",
        hover_data=["Respondents", "Area Base"],
        color_discrete_sequence=[BRAND["green"], BRAND["blue"], BRAND["orange"], BRAND["teal"], BRAND["red"], BRAND["purple"], BRAND["gray"], BRAND["green_dark"]],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_yaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="Area Type", yaxis_title="Share of respondents within area type", legend_title_text="Fuel Source")
    return style_fig(fig, title, height=640)

def fig_fuel_share_heatmap_by_area(df: pd.DataFrame, title: str = "Fuel Source Share by Area Type") -> go.Figure:
    if "Area Type Clean" not in df.columns:
        return empty_fig(title)
    rows = []
    for area, sub in df.groupby("Area Type Clean", dropna=False):
        area = normalize_text(area)
        if area in {"Unknown", ""}:
            continue
        base = len(sub)
        if base == 0:
            continue
        for fuel in FUEL_PREFIXES:
            col = f"Uses {fuel}"
            if col in sub.columns:
                rows.append({"Area Type": area, "Fuel Source": fuel, "% of Area Responses": pct(sub[col].sum(), base)})
    d = pd.DataFrame(rows)
    if d.empty:
        return empty_fig(title)
    pivot = d.pivot(index="Area Type", columns="Fuel Source", values="% of Area Responses").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="% of area"))
    fig.update_layout(xaxis_title="Fuel Source", yaxis_title="Area Type")
    return style_fig(fig, title, height=max(520, 330 + len(pivot) * 55))


def fig_sector_area_adoption_heatmap(df: pd.DataFrame, min_n: int) -> go.Figure:
    title = "Sector-wise LPG Adoption by Area Type"
    if "Area Type Clean" not in df.columns or "Category" not in df.columns:
        return empty_fig(title)
    g = df.groupby(["Category", "Area Type Clean"], dropna=False).agg(
        **{
            "Current LPG Users": ("Current LPG User Flag", "sum"),
            "Known LPG Responses": ("LPG Adoption Denominator", "sum"),
        }
    ).reset_index()
    g = g[g["Known LPG Responses"] >= min_n]
    if g.empty:
        return empty_fig(title, "No sector-area combination has enough known LPG responses after the selected sample filter")
    g["LPG Adoption Rate (%)"] = np.where(g["Known LPG Responses"] > 0, g["Current LPG Users"] / g["Known LPG Responses"] * 100, np.nan)
    pivot = g.pivot(index="Category", columns="Area Type Clean", values="LPG Adoption Rate (%)").fillna(0)
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="Adoption %"))
    fig.update_layout(xaxis_title="Area Type", yaxis_title="Sector")
    return style_fig(fig, title, height=max(560, 320 + len(pivot) * 36))


def fig_area_demand_total(df: pd.DataFrame, top_n: int) -> go.Figure:
    return fig_demand_total(df, "Area Type Clean", "Total Reported LPG Demand by Area Type", top_n)


def fig_area_average_usage(df: pd.DataFrame, top_n: int, min_n: int) -> go.Figure:
    return fig_median_usage(df, "Area Type Clean", "Average LPG Usage by Area Type", top_n, min_n)


def render_area_wise_analysis(dff: pd.DataFrame, top_n: int, min_sample: int, show_tables: bool) -> None:
    if "Area Type Clean" not in dff.columns:
        st.info("Area Type field is not available in the selected dataset.")
        return
    area_df = dff[dff["Area Type Clean"].apply(normalize_text).ne("Unknown")].copy()
    if area_df.empty:
        st.info("No area-wise records are available after the selected filters.")
        return

    area_types = area_df["Area Type Clean"].nunique()
    known_lpg = area_df["LPG Adoption Denominator"].sum()
    lpg_users = area_df["Current LPG User Flag"].sum()
    valid_usage = area_df[area_df["Valid Usage Flag"].eq(1)]
    total_demand = valid_usage["Monthly LPG Usage MT"].sum() if not valid_usage.empty else np.nan
    avg_usage = valid_usage["Monthly LPG Usage KG"].mean() if not valid_usage.empty else np.nan
    natural_gas = area_df["Natural Gas Connection Flag"].sum() if "Natural Gas Connection Flag" in area_df.columns else np.nan
    solar_users = area_df["Solar Installed Flag"].sum() if "Solar Installed Flag" in area_df.columns else np.nan

    kpi_row([
        kpi("Area Types Captured", fmt_int(area_types), "Urban / Rural / Peri-Urban etc.", BRAND["green"]),
        kpi("LPG Users", fmt_int(lpg_users), f"Known LPG responses: {fmt_int(known_lpg)}", BRAND["red"]),
        kpi("Area-wise LPG Adoption", fmt_pct(pct(lpg_users, known_lpg)), "LPG users ÷ known LPG responses", BRAND["green"]),
        kpi("Total Reported Demand", f"{fmt_1(total_demand)} MT/month", "Sum of valid usage records", BRAND["orange"]),
        kpi("Average LPG Usage", f"{fmt_int(avg_usage)} KG/month", "Mean of valid usage records", BRAND["blue"]),
        kpi("Natural Gas Connections", fmt_int(natural_gas), "Respondents with natural gas", BRAND["blue"]),
        kpi("Solar Users", fmt_int(solar_users), "Respondents with solar installed", BRAND["teal"]),
        kpi("Solid Fuel Users", fmt_int(area_df["Uses Solid Fuel"].sum() if "Uses Solid Fuel" in area_df.columns else np.nan), "Respondents using solid fuel", BRAND["orange"]),
    ], columns=4)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            "LPG Adoption Share by Area Type",
            fig_area_lpg_users(area_df, min_sample, top_n),
            "Shows LPG user share in Urban, Rural, Peri-Urban or other area types, with counts retained only as denominator evidence.",
            "Adoption Share = LPG users ÷ known LPG responses within area type × 100.",
            "X-axis: percentage; labels show user count and known response base.",
            "green",
        )
    with c2:
        chart_card(
            "LPG Adoption Rate by Area Type",
            fig_area_adoption_rate(area_df, min_sample, top_n),
            "Compares LPG adoption across area types.",
            "Adoption Rate = Current LPG Users ÷ Known LPG Responses × 100.",
            "X-axis: percentage adoption rate.",
            "red",
        )

    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card(
            "Fuel Source Usage Share by Area Type",
            fig_fuel_mix_by_area(area_df),
            "Shows LPG and other fuel usage shares across Urban, Rural and Peri-Urban respondents.",
            "Share = respondents using fuel ÷ total respondents in area type × 100.",
            "Grouped bars show percentages; raw counts are retained in hover.",
            "orange",
        )
    with c4:
        chart_card(
            "Fuel Source Share by Area Type",
            fig_fuel_share_heatmap_by_area(area_df),
            "Shows fuel preference mix within each area type.",
            "Share = respondents using fuel ÷ total respondents in area type × 100.",
            "Heatmap values are % of area type responses.",
            "blue",
        )

    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card(
            "Sector-wise LPG Adoption by Area Type",
            fig_sector_area_adoption_heatmap(area_df, min_sample),
            "Shows how LPG adoption changes when sector and area type are viewed together.",
            "For each sector-area cell: LPG users ÷ known LPG responses × 100.",
            "Heatmap values are adoption percentages.",
            "green",
        )
    with c6:
        chart_card(
            "Total Reported Demand by Area Type",
            fig_area_demand_total(area_df, top_n),
            "Shows which area type contributes more reported LPG demand.",
            "Total demand = sum of valid monthly LPG KG converted to MT/month by area type.",
            "X-axis: MT/month.",
            "orange",
        )

    chart_card(
        "Average LPG Usage by Area Type",
        fig_area_average_usage(area_df, top_n, min_sample),
        "Compares mean monthly LPG usage across Urban, Rural and Peri-Urban respondents.",
        "Average = mean of valid monthly LPG KG records by area type.",
        "X-axis: KG/month.",
        "blue",
    )

    if show_tables:
        table = adoption_rate(area_df, "Area Type Clean", min_sample).merge(response_count(area_df, "Area Type Clean"), on="Area Type Clean", how="left")
        table = table.merge(demand_summary(area_df, "Area Type Clean"), on="Area Type Clean", how="left")
        st.dataframe(table, use_container_width=True, hide_index=True)


def income_analysis_base(df: pd.DataFrame) -> pd.DataFrame:
    """Use captured household income bands only.

    Income in this survey is captured as G8 Income Band and is primarily a
    residential/household question. To avoid misleading cross-sector analysis,
    income-class visuals are restricted to residential records with known LPG
    adoption responses.
    """
    if "Income Class" not in df.columns:
        return pd.DataFrame()
    d = df.copy()
    if "Is Residential" in d.columns:
        d = d[d["Is Residential"].eq(True)]
    d = d[~d["Income Class"].isin(["Not Captured / Not Applicable", "Unknown", "Not Captured"])]
    d = d[d["LPG Adoption Denominator"].eq(1)]
    return d



def income_threshold_dataframe() -> pd.DataFrame:
    """Return the fixed income thresholds used in the dashboard."""
    return pd.DataFrame(INCOME_CLASS_THRESHOLDS)


def income_threshold_note_html() -> str:
    return (
        '<div class="note-box">'
        '<b>Income threshold definition:</b> Income class is based on the self-reported '
        'monthly household income band captured in <b>G8 Income Band</b>. The dashboard '
        'does not convert income bands into artificial numeric values. Analysis uses the '
        'survey thresholds directly. This section is restricted to household/residential respondents only. '
        'Percentages are used as the main comparison method because sample sizes differ by income class; counts are shown only as n-size evidence.'
        '</div>'
    )


def income_lpg_summary(df: pd.DataFrame) -> pd.DataFrame:
    d = income_analysis_base(df)
    if d.empty:
        return pd.DataFrame()
    g = d.groupby("Income Class", dropna=False).agg(
        **{
            "Known LPG Responses": ("LPG Adoption Denominator", "sum"),
            "Current LPG Users": ("Current LPG User Flag", "sum"),
            "Total Responses": ("Income Class", "count"),
            "Average LPG Usage KG/month": ("Monthly LPG Usage KG", "mean"),
            "Average LPG Price PKR/KG": ("LPG Price PKR per KG", "mean"),
            "Average Monthly LPG Spend PKR": ("Monthly LPG Spend PKR", "mean"),
        }
    ).reset_index()
    g["Non-LPG Users"] = g["Known LPG Responses"] - g["Current LPG Users"]
    g["LPG Adoption Rate (%)"] = np.where(g["Known LPG Responses"] > 0, g["Current LPG Users"] / g["Known LPG Responses"] * 100, np.nan)
    g["Non-LPG Share (%)"] = np.where(g["Known LPG Responses"] > 0, g["Non-LPG Users"] / g["Known LPG Responses"] * 100, np.nan)
    g["Sort Key"] = g["Income Class"].apply(income_sort_key)
    return g.sort_values("Sort Key")


def fig_income_lpg_vs_non_lpg(df: pd.DataFrame, min_n: int) -> go.Figure:
    title = "LPG Users vs Non-LPG Users by Income Class"
    g = income_lpg_summary(df)
    if g.empty:
        return empty_fig(title, "Income band was not captured for the selected records")
    g = g[g["Known LPG Responses"] >= min_n]
    if g.empty:
        return empty_fig(title, "No income class has enough known LPG responses after the sample filter")
    rows = []
    for _, r in g.iterrows():
        rows.append({
            "Income Class": r["Income Class"],
            "LPG Status": "Current LPG Users",
            "Share %": r["LPG Adoption Rate (%)"],
            "Respondents": r["Current LPG Users"],
            "Known Base": r["Known LPG Responses"],
            "Sort Key": r["Sort Key"],
        })
        rows.append({
            "Income Class": r["Income Class"],
            "LPG Status": "Non-LPG Users",
            "Share %": r["Non-LPG Share (%)"],
            "Respondents": r["Non-LPG Users"],
            "Known Base": r["Known LPG Responses"],
            "Sort Key": r["Sort Key"],
        })
    d = pd.DataFrame(rows).sort_values("Sort Key")
    fig = px.bar(
        d,
        x="Income Class",
        y="Share %",
        color="LPG Status",
        text="Share %",
        barmode="stack",
        hover_data=["Respondents", "Known Base"],
        color_discrete_sequence=[BRAND["green"], BRAND["red"]],
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="auto", cliponaxis=False)
    fig.update_yaxes(ticksuffix="%", range=[0, 105])
    fig.update_xaxes(tickangle=-18, tickfont=dict(size=10), automargin=True)
    fig.update_layout(xaxis_title="Income Class", yaxis_title="Share of known LPG responses", legend_title_text="LPG Status")
    return style_fig(fig, title, height=600)


def fig_income_adoption_rate(df: pd.DataFrame, min_n: int) -> go.Figure:
    title = "LPG Adoption Rate by Income Class"
    g = income_lpg_summary(df)
    if g.empty:
        return empty_fig(title, "Income band was not captured for the selected records")
    g = g[g["Known LPG Responses"] >= min_n]
    if g.empty:
        return empty_fig(title, "No income class has enough known LPG responses after the sample filter")
    g["Label"] = g.apply(lambda r: f"{r['LPG Adoption Rate (%)']:.1f}%", axis=1)
    fig = px.bar(
        g.sort_values("LPG Adoption Rate (%)", ascending=True),
        x="LPG Adoption Rate (%)",
        y="Income Class",
        orientation="h",
        text="Label",
        color="Known LPG Responses",
        color_continuous_scale="RdYlGn",
        hover_data=["Current LPG Users", "Non-LPG Users", "Known LPG Responses"],
    )
    fig.update_traces(texttemplate="%{text}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(ticksuffix="%", range=[0, 105])
    fig.update_layout(xaxis_title="LPG Adoption Rate", yaxis_title="Income Class", coloraxis_colorbar_title="Known n")
    return style_fig(fig, title, height=max(520, min(760, 380 + len(g) * 55)))


def fig_income_price_sensitivity(df: pd.DataFrame) -> go.Figure:
    title = "Price Sensitivity Mix by Income Class"
    d = income_analysis_base(df)
    if d.empty or "D2 Price Sensitivity" not in d.columns:
        return empty_fig(title)
    d = d[non_blank_series(d["D2 Price Sensitivity"])].copy()
    if d.empty:
        return empty_fig(title, "No price sensitivity responses are available for captured income classes")
    g = d.groupby(["Income Class", "D2 Price Sensitivity"], dropna=False).size().reset_index(name="Responses")
    totals = g.groupby("Income Class")["Responses"].transform("sum")
    g["Share %"] = np.where(totals > 0, g["Responses"] / totals * 100, np.nan)
    pivot = g.pivot(index="Income Class", columns="D2 Price Sensitivity", values="Share %").fillna(0)
    pivot = pivot.reindex([x for x in INCOME_CLASS_ORDER if x in pivot.index])
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="Reds", labels=dict(color="% within income"))
    fig.update_layout(xaxis_title="Price Sensitivity", yaxis_title="Income Class")
    return style_fig(fig, title, height=max(520, 320 + len(pivot) * 55))


def fig_income_fuel_mix(df: pd.DataFrame) -> go.Figure:
    title = "Fuel Source Share by Income Class"
    d = income_analysis_base(df)
    if d.empty:
        return empty_fig(title)
    rows = []
    for inc, sub in d.groupby("Income Class", dropna=False):
        base = len(sub)
        if base == 0:
            continue
        for fuel in FUEL_PREFIXES:
            col = f"Uses {fuel}"
            if col in sub.columns:
                rows.append({"Income Class": inc, "Fuel Source": fuel, "% of Income Class": pct(sub[col].sum(), base), "Respondents": sub[col].sum(), "Base": base})
    g = pd.DataFrame(rows)
    if g.empty:
        return empty_fig(title)
    pivot = g.pivot(index="Income Class", columns="Fuel Source", values="% of Income Class").fillna(0)
    pivot = pivot.reindex([x for x in INCOME_CLASS_ORDER if x in pivot.index])
    fig = px.imshow(pivot, text_auto=".1f", color_continuous_scale="RdYlGn", labels=dict(color="% within income"))
    fig.update_layout(xaxis_title="Fuel Source", yaxis_title="Income Class")
    return style_fig(fig, title, height=max(520, 320 + len(pivot) * 55))


def fig_income_average_metric(df: pd.DataFrame, metric_col: str, title: str, x_title: str, min_n: int, color_scale: str = "RdYlGn") -> go.Figure:
    d = income_analysis_base(df)
    if d.empty or metric_col not in d.columns:
        return empty_fig(title)
    d = d[pd.to_numeric(d[metric_col], errors="coerce").notna()].copy()
    d[metric_col] = pd.to_numeric(d[metric_col], errors="coerce")
    d = d[d[metric_col] > 0]
    if d.empty:
        return empty_fig(title)
    g = d.groupby("Income Class", dropna=False).agg(**{"Valid Records": (metric_col, "count"), "Average Value": (metric_col, "mean")}).reset_index()
    g = g[g["Valid Records"] >= min_n]
    if g.empty:
        return empty_fig(title, "No income class has enough valid records after the sample filter")
    g["Sort Key"] = g["Income Class"].apply(income_sort_key)
    g = g.sort_values("Sort Key")
    fig = px.bar(g, x="Income Class", y="Average Value", text="Average Value", color="Valid Records", color_continuous_scale=color_scale, hover_data=["Valid Records"])
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="auto", cliponaxis=False)
    fig.update_xaxes(tickangle=-18, tickfont=dict(size=10), automargin=True)
    fig.update_layout(xaxis_title="Income Class", yaxis_title=x_title, coloraxis_colorbar_title="Valid n")
    return style_fig(fig, title, height=560)


def render_income_analysis(dff: pd.DataFrame, top_n: int, min_sample: int, show_tables: bool) -> None:
    income_df = income_analysis_base(dff)
    if income_df.empty:
        st.info("Income band is not available for the selected filters. Income analysis is restricted to household/residential respondents because G8 Income Band is a household-income field, not a commercial/industrial income field.")
        return
    known = income_df["LPG Adoption Denominator"].sum()
    users = income_df["Current LPG User Flag"].sum()
    non_users = known - users
    residential_share = pct(income_df["Is Residential"].sum(), len(income_df)) if "Is Residential" in income_df.columns else np.nan
    kpi_row([
        kpi("Income Responses", fmt_int(len(income_df)), "Captured income-class records", BRAND["green"]),
        kpi("LPG Adoption", fmt_pct(pct(users, known)), f"{fmt_int(users)} users / {fmt_int(known)} known", BRAND["red"]),
        kpi("Non-LPG Share", fmt_pct(pct(non_users, known)), f"{fmt_int(non_users)} non-users / {fmt_int(known)} known", BRAND["orange"]),
        kpi("Residential Share", fmt_pct(residential_share), "Income is mainly household data", BRAND["blue"]),
    ], columns=4)
    st.markdown(income_threshold_note_html(), unsafe_allow_html=True)
    with st.expander("Income class thresholds used in this analysis", expanded=True):
        st.dataframe(income_threshold_dataframe(), use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            "LPG Users vs Non-LPG Users by Income Class",
            fig_income_lpg_vs_non_lpg(income_df, min_sample),
            "Compares LPG and non-LPG shares inside each income class.",
            "Share = LPG/non-LPG respondents ÷ known LPG responses within income class × 100.",
            "Main axis is percentage; counts are shown as evidence in hover and labels.",
            "green",
        )
    with c2:
        chart_card(
            "LPG Adoption Rate by Income Class",
            fig_income_adoption_rate(income_df, min_sample),
            "Shows whether LPG adoption changes between lower and upper income bands.",
            "Adoption Rate = Current LPG Users ÷ Known LPG Responses × 100.",
            "X-axis is percentage to avoid skew from unequal respondent counts.",
            "red",
        )
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card(
            "Price Sensitivity Mix by Income Class",
            fig_income_price_sensitivity(income_df),
            "Shows affordability pressure across income bands.",
            "Cell value = response share within income class × 100.",
            "Heatmap uses percentages, not raw counts.",
            "orange",
        )
    with c4:
        chart_card(
            "Fuel Source Share by Income Class",
            fig_income_fuel_mix(income_df),
            "Shows LPG and alternative-fuel usage across income classes.",
            "Share = respondents using fuel ÷ total respondents in income class × 100.",
            "Heatmap values are percentage shares within income class.",
            "blue",
        )
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card(
            "Average LPG Usage by Income Class",
            fig_income_average_metric(income_df, "Monthly LPG Usage KG", "Average LPG Usage by Income Class", "Average LPG Usage (KG/month)", 1, "RdYlGn"),
            "Shows mean monthly LPG usage for captured income classes.",
            "Average = mean of valid monthly LPG usage KG records within income class.",
            "Use with valid record count in hover to judge reliability.",
            "green",
        )
    with c6:
        chart_card(
            "Average Monthly LPG Spend by Income Class",
            fig_income_average_metric(income_df, "Monthly LPG Spend PKR", "Average Monthly LPG Spend by Income Class", "Average Monthly LPG Spend (PKR)", 1, "Oranges"),
            "Shows monthly affordability burden by income band.",
            "Average spend = mean of valid monthly LPG spend records within income class.",
            "Spend is shown as average amount, while adoption/fuel mix are percentage-based.",
            "orange",
        )
    if show_tables:
        st.dataframe(income_lpg_summary(income_df), use_container_width=True, hide_index=True)

def render_executive_sector_tab(dff: pd.DataFrame, tab_name: str, top_n: int, min_sample: int, show_tables: bool) -> None:
    kpi_row(sector_kpi_cards(dff), columns=4)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            f"{tab_name} - LPG Adoption by Sector" if tab_name == "All Sectors" else f"{tab_name} - Fuel Source Mix",
            fig_adoption(dff, "Category", "Country-level LPG Adoption by Sector", min_sample, top_n) if tab_name == "All Sectors" else fig_fuel_sources_country(dff),
            "Shows LPG adoption and fuel behaviour for the selected executive sector view.",
            "Adoption = Current LPG Users ÷ Known LPG Responses × 100; fuel count = respondent using fuel at least once.",
            "All metrics are calculated only for the selected sector tab.",
            "green",
        )
    with c2:
        chart_card(
            f"{tab_name} - Total Reported Demand",
            fig_demand_total(dff, "Category", "Total Reported LPG Demand by Sector", top_n) if tab_name == "All Sectors" else fig_usage_bucket_distribution(dff, f"{tab_name} LPG Usage Distribution"),
            "Shows reported monthly LPG demand and usage spread.",
            "Total demand = sum of valid monthly LPG KG converted to MT/month; average usage uses mean.",
            "KG/month and MT/month are used consistently.",
            "orange",
        )
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card(
            f"{tab_name} - Average LPG Usage",
            fig_median_usage(dff, "Category", "Average LPG Usage by Sector", top_n, min_sample) if tab_name == "All Sectors" else fig_application_counts(dff),
            "Shows average LPG usage or usage applications within the selected view.",
            "Average usage = mean of valid monthly LPG KG records.",
            "Application labels show share of current LPG users.",
            "blue",
        )
    with c4:
        chart_card(
            f"{tab_name} - Average LPG Price",
            fig_price_by(dff, "Category", "Average LPG Price by Sector", top_n, min_sample) if tab_name == "All Sectors" else fig_distribution(dff[dff["Valid Price Flag"].eq(1)], "LPG Price PKR per KG", f"{tab_name} LPG Price Distribution", "LPG Price (PKR/KG)", "Number of Respondents"),
            "Shows average LPG price for the selected sector view.",
            "Average LPG price = mean of valid PKR/KG price records.",
            "Price records are restricted to clean PKR/KG values.",
            "purple",
        )
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card(
            f"{tab_name} - Urban / Rural Split",
            fig_area_split_by_sector(dff, f"{tab_name} Urban / Rural Split by Sector"),
            "Shows urban/rural sample split for the selected executive view.",
            "Share = respondents in area type ÷ total respondents in sector × 100.",
            "Shown as stacked percentage by sector.",
            "red",
        )
    with c6:
        chart_card(
            f"{tab_name} - Natural Gas and Solar View",
            fig_rate_by_sector(dff, "Natural Gas Connection Flag", "Natural Gas Denominator", "Natural Gas Connection Rate (%)", min_sample, top_n, "Blues") if tab_name == "All Sectors" else fig_rate_by_sector(dff, "Solar Installed Flag", "Solar Denominator", "Solar Adoption Rate (%)", 1, top_n, "Greens"),
            "Shows natural gas or solar status within the selected sector view.",
            "Rate = yes responses ÷ known responses × 100.",
            "Labels show rate and denominator n.",
            "teal",
        )
    if show_tables:
        st.dataframe(demand_summary(dff, "Category"), use_container_width=True, hide_index=True)


def render_household_analysis(dff: pd.DataFrame, top_n: int, min_sample: int, show_tables: bool) -> None:
    household = dff[dff["Is Residential"]].copy() if "Is Residential" in dff.columns else pd.DataFrame()
    if household.empty:
        st.info("No household / residential records are available in the selected filters.")
        return
    valid_household_size = household[household["Valid Household Size Flag"].eq(1)] if "Valid Household Size Flag" in household.columns else pd.DataFrame()
    avg_people = valid_household_size["Household Size"].mean() if not valid_household_size.empty else np.nan
    avg_house_usage = household.loc[household["Valid Usage Flag"].eq(1), "Monthly LPG Usage KG"].mean()
    avg_per_person = household["Household LPG KG per Person"].mean() if "Household LPG KG per Person" in household.columns else np.nan
    total_house_demand = household.loc[household["Valid Usage Flag"].eq(1), "Monthly LPG Usage MT"].sum()
    kpi_row([
        kpi("Household Responses", fmt_int(len(household)), "Residential + society records", BRAND["green"]),
        kpi("Avg People per Household", fmt_1(avg_people), "Mean household size", BRAND["blue"]),
        kpi("Avg LPG Consumption per Household", f"{fmt_int(avg_house_usage)} KG/month", "Mean household LPG usage", BRAND["orange"]),
        kpi("Avg LPG Consumption per Person", f"{fmt_1(avg_per_person)} KG/month", "Household usage ÷ people", BRAND["purple"]),
        kpi("Total Household Demand", f"{fmt_1(total_house_demand)} MT/month", "Sum of valid household usage", BRAND["red"]),
        kpi("Household LPG Users", fmt_int(household["Current LPG User Flag"].sum()), f"Known: {fmt_int(household['LPG Adoption Denominator'].sum())}", BRAND["green"]),
        kpi("Natural Gas Connections", fmt_int(household["Natural Gas Connection Flag"].sum()), f"{fmt_pct(pct(household['Natural Gas Connection Flag'].sum(), household['Natural Gas Denominator'].sum()))} of known", BRAND["blue"]),
        kpi("Solar Adoption", fmt_pct(pct(household["Solar Installed Flag"].sum(), household["Solar Denominator"].sum())), f"{fmt_int(household['Solar Installed Flag'].sum())} solar users", BRAND["teal"]),
    ], columns=4)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card(
            "Household Size vs Average LPG Consumption",
            fig_numeric_mean_by_sector(household.assign(**{"Household Size Band": household["Household Size"].round().astype("Int64").astype(str)}), "Monthly LPG Usage KG", "Average LPG Usage by Household Segment", "Average LPG Usage (KG/month)", 1, top_n),
            "Shows average LPG consumption for residential records. Use this with household-size KPI to interpret per-family demand.",
            "Average = mean of valid monthly LPG KG records.",
            "KG/month per household.",
            "green",
        )
    with c2:
        if "Household Size" in household.columns:
            hh = household[household["Household Size"].notna() & household["Monthly LPG Usage KG"].notna() & (household["Household Size"] > 0) & (household["Monthly LPG Usage KG"] > 0)].copy()
            if hh.empty:
                fig = empty_fig("Household Size vs LPG Consumption", "No valid household size and LPG usage records")
            else:
                fig = px.scatter(hh, x="Household Size", y="Monthly LPG Usage KG", color="Area Type Clean", size="Monthly LPG Usage KG", hover_data=["Category", "City Clean"], color_discrete_sequence=[BRAND["green"], BRAND["red"], BRAND["orange"], BRAND["blue"]])
                fig.update_layout(xaxis_title="People per Household", yaxis_title="LPG Usage (KG/month)")
                fig = style_fig(fig, "Household Size vs LPG Consumption", height=560)
            chart_card(
                "Household Size vs LPG Consumption",
                fig,
                "Shows whether larger households report higher monthly LPG consumption.",
                "Scatter of people per household against monthly LPG KG.",
                "Each dot is one household record where both fields are valid.",
                "red",
            )
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Household Fuel Source Mix", fig_fuel_sources_country(household), "Shows which fuels residential respondents use.", "Respondent counted once per fuel if any relevant use is selected.", "Count and share of household records.", "orange")
    with c4:
        chart_card("Household LPG Application Mix", fig_application_counts(household), "Shows household use cases such as cooking, heating, water heating, and generator use.", "Count of selected LPG application flags.", "Labels show % of current LPG household users.", "green")
    c5, c6 = st.columns(2, gap="large")
    with c5:
        chart_card("Household Natural Gas Reliability", fig_categorical(household, "B3 Natural Gas Reliability", "Household Natural Gas Reliability", "Reliability Level", top_n, "Reds"), "Shows gas reliability for household respondents.", "Count by natural gas reliability response.", "Household-level gas reliability view.", "red")
    with c6:
        chart_card("Household Alternative if LPG Expensive", fig_categorical(household, "D4 Alternative If Expensive", "Household Alternative if LPG Expensive", "Alternative Fuel", top_n, "Oranges"), "Shows switching risk for residential LPG use.", "Count by preferred alternative fuel if LPG becomes expensive.", "Household-level substitution view.", "orange")
    if show_tables:
        cols = [c for c in ["ID", "Category", "City Clean", "Area Type Clean", "Household Size", "Monthly LPG Usage KG", "Household LPG KG per Person", "LPG Price PKR per KG", "Current LPG User Flag", "Natural Gas Connection Flag", "Solar Installed Flag"] if c in household.columns]
        st.dataframe(household[cols], use_container_width=True, hide_index=True)

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
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar filters are kept simple and business-friendly.
st.sidebar.markdown("## Dashboard Navigation")

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
    "13. Household / Residential Analysis",
    "14. Area-wise Fuel Usage Analysis",
    "15. Income Class Analysis",
    "16. Raw Data",
]
page = st.sidebar.selectbox("Dashboard Page", pages, index=0)

st.sidebar.markdown("## Easy Filters")
category_options = sorted([x for x in df_all["Category"].dropna().unique().tolist() if x != "Unknown"])
selected_categories = st.sidebar.multiselect("Sector", category_options, default=category_options)

area_options = sorted([x for x in df_all["Area Type Clean"].dropna().unique().tolist() if x != "Unknown"])
selected_area_types = st.sidebar.multiselect("Urban / Rural", area_options, default=area_options)

income_options = [x for x in INCOME_CLASS_ORDER if x in df_all["Income Class"].unique().tolist()]
if income_options:
    selected_income_classes = st.sidebar.multiselect("Income Class", income_options, default=income_options)
else:
    selected_income_classes = []

scope = st.sidebar.selectbox("Analysis Scope", ["All responses", "Consumer / user responses only", "Supplier / distributor responses only"])
lpg_filter = st.sidebar.selectbox("LPG User Filter", ["All", "Current LPG users only", "Non-LPG users only", "Known LPG-answer respondents only"])

st.sidebar.markdown("## Chart Controls")
top_n = st.sidebar.slider("Top N in charts", min_value=5, max_value=35, value=15, step=1)
min_sample = st.sidebar.slider("Minimum sample size for rate charts", min_value=1, max_value=50, value=5, step=1)
show_tables = st.sidebar.checkbox("Show supporting tables", value=False)

# Apply country-level filters
df = df_all.copy()
if selected_categories:
    df = df[df["Category"].isin(selected_categories)]
else:
    st.sidebar.warning("No sector is selected.")
    df = df.iloc[0:0]

if selected_area_types:
    df = df[df["Area Type Clean"].isin(selected_area_types)]
else:
    st.sidebar.warning("No urban/rural area type is selected.")
    df = df.iloc[0:0]

# Income class is an optional filter because it is mainly applicable to household records.
# It is applied only when the Income Class Analysis page is selected; otherwise it would
# unintentionally remove commercial/industrial/supplier records where income is not applicable.
if page == "15. Income Class Analysis" and selected_income_classes:
    df = df[df["Income Class"].isin(selected_income_classes)]

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

# The large KPI summary has been moved inside the Executive page and made sector-wise.
# Page navigation is now controlled from the sidebar to avoid top-page overlap.

# ------------------------------------------------------------
# Pages
# ------------------------------------------------------------
if page == "1. Executive Country Overview":
    section("Executive Country Overview", "Sector-wise executive summary of LPG adoption, demand, average usage, average price, natural gas, solar, safety and urban/rural split.")
    sector_names = ["All Sectors"] + sorted([x for x in df["Category"].dropna().unique().tolist() if x != "Unknown"])
    tabs = st.tabs(sector_names)
    for sector_name, tab in zip(sector_names, tabs):
        with tab:
            sector_df = df.copy() if sector_name == "All Sectors" else df[df["Category"].eq(sector_name)].copy()
            render_executive_sector_tab(sector_df, sector_name, top_n, min_sample, show_tables)

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
    chart_card(
        "City Sample Coverage by Sector",
        fig_categorical_by_sector_heatmap(df, "City Clean", "City Sample Coverage by Sector", top_n_categories=min(top_n, 10)),
        "Shows city coverage across sectors without doing deep city-level behaviour analysis.",
        "Cell value = share of city responses within each sector among displayed cities.",
        "This remains a sample-coverage chart, not a city demand estimate.",
        "blue",
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
        chart_card("Country-level Average LPG Usage by Sector", fig_median_usage(df, "Category", "Country-level Average LPG Usage by Sector", top_n, min_sample), "Compares average reported user demand by sector using mean values.", "Average / mean of valid monthly LPG usage KG/month by sector.", "Average is used throughout the dashboard as requested for management analysis.", "blue")
    chart_card("Country-level LPG Application Mix by Sector", fig_application_heatmap(df), "Shows how LPG use purpose differs across sectors.", "% of current LPG users in each sector selecting each application.", "Heatmap cell value = % of LPG users in that sector.", "green")

elif page == "4. Country Usage & Demand":
    section("Country Usage & Demand", "Pakistan-level LPG monthly usage, adoption duration, seasonal pattern, demand growth and application mix.")
    st.markdown('<div class="note-box"><b>Average / outlier note:</b> Usage metrics use mean values as requested. Because commercial and industrial respondents can report very large LPG volumes, average usage should always be read together with valid-record count and the usage-bucket distribution.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        chart_card("Country-level LPG Usage Distribution", fig_usage_bucket_distribution(df, "Country-level LPG Usage Distribution"), "Shows the spread of reported monthly LPG usage across Pakistan sample.", "Histogram of valid monthly LPG usage in KG/month.", "Log scale avoids bulk users hiding household users.", "green")
    with c2:
        chart_card("Country-level LPG Usage by Application", fig_application_counts(df), "Shows main applications of LPG nationally.", "Count of users selecting each application flag.", "Labels show % of current LPG users.", "red")
    c_sector1, c_sector2 = st.columns(2, gap="large")
    with c_sector1:
        chart_card("Sector-wise Total Reported LPG Demand", fig_demand_total(df, "Category", "Sector-wise Total Reported LPG Demand", top_n), "Shows which sectors drive total reported LPG demand.", "Sum of valid monthly LPG usage KG converted to MT/month by sector.", "X-axis: MT/month; color: average KG/month.", "orange")
    with c_sector2:
        chart_card("Sector-wise Average LPG Usage", fig_median_usage(df, "Category", "Sector-wise Average LPG Usage", top_n, min_sample), "Shows mean monthly LPG usage by sector.", "Average usage = mean of valid monthly LPG KG records by sector.", "X-axis: KG/month; color: valid record count.", "blue")
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
        chart_card("Country-level Average LPG Price by Sector", fig_price_by(df, "Category", "Country-level Average LPG Price by Sector", top_n, min_sample), "Compares sector-level average reported prices at Pakistan level.", "Average PKR/KG by sector using valid price records.", "Use with valid price count, not city-level comparison.", "purple")
    chart_card(
        "Sector-wise Price Sensitivity Mix",
        fig_categorical_by_sector_heatmap(df, "D2 Price Sensitivity", "Sector-wise Price Sensitivity Mix", top_n_categories=8),
        "Compares price sensitivity across sectors.",
        "Cell value = share of each price sensitivity response within sector.",
        "Useful for comparing lower/upper operational pressure by sector.",
        "red",
    )
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
    c_sector1, c_sector2 = st.columns(2, gap="large")
    with c_sector1:
        chart_card("Sector-wise Natural Gas Connection Rate", fig_rate_by_sector(df, "Natural Gas Connection Flag", "Natural Gas Denominator", "Natural Gas Connection Rate (%)", min_sample, top_n, "Blues"), "Shows natural gas connection rate by sector.", "Natural Gas Connection Rate = yes ÷ known natural gas responses × 100.", "X-axis: %; labels show denominator.", "blue")
    with c_sector2:
        chart_card("Sector-wise Solar Adoption Rate", fig_rate_by_sector(df, "Solar Installed Flag", "Solar Denominator", "Solar Adoption Rate (%)", min_sample, top_n, "Greens"), "Shows solar adoption rate by sector.", "Solar Adoption Rate = solar yes ÷ known solar responses × 100.", "X-axis: %; labels show denominator.", "green")
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
    chart_card(
        "Sector-wise Quality / Quantity Issue Mix",
        fig_categorical_by_sector_heatmap(df, "F1 Quality Or Quantity Issue", "Sector-wise Quality / Quantity Issue Mix", top_n_categories=6),
        "Shows product/cylinder quality or quantity issue responses by sector.",
        "Cell value = share of each response within sector.",
        "Helps identify sectors with stronger quality concern concentration.",
        "red",
    )
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
        avg_sold = suppliers["Supplier Monthly Sold MT"].mean(skipna=True)
        kpi_row([
            kpi("Supplier Records", fmt_int(len(suppliers)), "Supplier/dealer/refill point responses", BRAND["green"]),
            kpi("Reported Monthly Sold", f"{fmt_1(total_sold)} MT/month", "Sum of clean supplier volume", BRAND["red"]),
            kpi("Average Supplier Volume", f"{fmt_1(avg_sold)} MT/month", "Mean supplier scale", BRAND["orange"]),
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
    chart_card(
        "Data Completeness by Sector",
        fig_data_completeness_by_sector(df),
        "Shows average critical-field completeness for each sector.",
        "Average completeness = mean of record completeness percentage by sector.",
        "Higher percentage means stronger data quality for that sector.",
        "green",
    )
    c3, c4 = st.columns(2, gap="large")
    with c3:
        chart_card("Usage Unit Status", fig_categorical(df, "C3 LPG Monthly Quantity Unit", "Monthly LPG Usage Unit Status", "Usage Unit", top_n, "Blues"), "Shows how usage was originally reported before conversion.", "Count by original monthly quantity unit.", "Converted to KG/month for country-level demand charts.", "blue")
    with c4:
        chart_card("Price Unit Status", fig_categorical(df, "C6 LPG Price Unit", "LPG Price Unit Status", "Price Unit", top_n, "Oranges"), "Shows how price was originally reported before conversion.", "Count by original price unit.", "Converted to PKR/KG where possible.", "orange")
    if show_tables:
        st.dataframe(df[["ID", "Category", "City Clean", "Current LPG User Flag", "Monthly LPG Usage KG", "LPG Price PKR per KG", "Missing Critical Fields", "Data Completeness %"]], use_container_width=True, hide_index=True)

elif page == "13. Household / Residential Analysis":
    section("Household / Residential Analysis", "Detailed household-sector analysis covering average household size, LPG consumption per household, per-person consumption, natural gas, solar, fuel mix and switching risk.")
    render_household_analysis(df, top_n, min_sample, show_tables)

elif page == "14. Area-wise Fuel Usage Analysis":
    section("Area-wise Fuel Usage Analysis", "Detailed Urban / Rural / Peri-Urban analysis covering LPG users, adoption rate, other fuel usage, sector-area adoption, total reported demand and average LPG usage.")
    st.markdown('<div class="note-box"><b>Percentage-first rule:</b> Area-wise comparisons use percentages as the primary view because Urban, Rural and Peri-Urban sample sizes are not equal. Counts are retained as n-size evidence in labels, hover data and tables.</div>', unsafe_allow_html=True)
    render_area_wise_analysis(df, top_n, min_sample, show_tables)

elif page == "15. Income Class Analysis":
    section("Income Class Analysis", "Household/residential income-band analysis using defined income thresholds. LPG and non-LPG comparisons use percentages first, with n-size shown for evidence.")
    render_income_analysis(df, top_n, min_sample, show_tables)

elif page == "16. Raw Data":
    section("Raw / Filtered Data", "Inspect and export the filtered country-level survey data used by the dashboard.")
    st.markdown('<div class="note-box">Use the sidebar download button to export the same filtered dataset. The table below keeps raw survey columns plus dashboard-calculated fields.</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True, height=650)

# Footer
st.markdown(
    f"""
    <div class="note-box">
        <b>Run command:</b> <code>python -m streamlit run DashLPG.py --server.address 0.0.0.0 --server.port 8501</code>
    </div>
    """,
    unsafe_allow_html=True,
)
