"""Shared Apple-style light design system for the analysis pages.

One palette for the whole app (the same tokens as the Strategy Scanner page in
favorites_tab.py and the home page in apple_home.py), plus:

* RESULTS_CSS / apply_results_apple_theme() - the light canvas and the generic
  Streamlit widgets (tabs, inputs, buttons, expanders, alerts, tables) for the
  stock-analysis results page. Emit it once per run, before the tabs.
* style_fig(fig) - puts any Plotly figure on the light design (white paper,
  quiet grid, dark readable labels). Render it with st.plotly_chart(..., theme=None).
* small CSS classes (ap-card, ap-tile, ap-label, ap-value, ap-pill ...) that
  tab modules may use instead of long inline styles.

Colour rules: one accent (blue) for interactive / neutral highlights, green
and red only for up/down meaning, amber for "wait / caution", greys for
everything else. No glows, no neon, no dark panels.
"""
from __future__ import annotations

import streamlit as st

# ── palette ──────────────────────────────────────────────────────────────────
BG     = "#F2F2F5"   # page canvas
CARD   = "#FFFFFF"   # top-level card
INSET  = "#F7F7FA"   # tile inside a card
FILL   = "#EDEDF1"   # quiet fill (segmented controls, bars' empty track)
HAIR   = "#DEDEE3"   # hairline borders / dividers
HAIR2  = "#C9C9CF"   # stronger hairline (hover)
T1     = "#111114"   # primary text, big numbers
T2     = "#3F3F46"   # body text
T3     = "#5C5C63"   # labels, secondary text
T4     = "#8A8A91"   # faint text (never for essential info)

BLUE   = "#0063D1"
GREEN  = "#1B7A36"
RED    = "#C1121F"
AMBER  = "#A15C00"   # wait / caution / neutral-warning (text-safe on white)
ORANGE = "#C2410C"
PURPLE = "#6E3FD1"
TEAL   = "#0A7C86"
INDIGO = "#4B47C4"

BLUE_BG   = "rgba(0,99,209,0.09)"
GREEN_BG  = "rgba(27,122,54,0.10)"
RED_BG    = "rgba(193,18,31,0.08)"
AMBER_BG  = "rgba(161,92,0,0.10)"
PURPLE_BG = "rgba(110,63,209,0.09)"
TEAL_BG   = "rgba(10,124,134,0.09)"
GREY_BG   = "rgba(17,17,20,0.05)"

SHADOW    = "0 1px 2px rgba(17,17,20,0.05),0 8px 24px rgba(17,17,20,0.06)"
SHADOW_SM = "0 1px 2px rgba(17,17,20,0.06)"

# Chart colours (a touch brighter than the text colours so thin candles read)
UP      = "#1E8E3E"
DOWN    = "#D93025"
GRID    = "#EDEDF1"
SERIES  = [BLUE, PURPLE, AMBER, TEAL, ORANGE, INDIGO, "#8A8A91"]

# Same regime colours as the Strategy Scanner page
REGIME_COLORS = {"TREND": INDIGO, "RANGE": "#086F8C", "VOLATILE": "#8E3FBA"}
REGIME_BG     = {"TREND": "rgba(75,71,196,0.09)", "RANGE": "rgba(8,111,140,0.09)",
                 "VOLATILE": "rgba(142,63,186,0.09)"}

FONT = "Inter, -apple-system, BlinkMacSystemFont, 'SF Pro Text', system-ui, sans-serif"


def tone(value: float, neutral_band: float = 0.0) -> str:
    """Green for > band, red for < -band, grey otherwise."""
    if value > neutral_band:
        return GREEN
    if value < -neutral_band:
        return RED
    return T3


def tone_bg(value: float, neutral_band: float = 0.0) -> str:
    if value > neutral_band:
        return GREEN_BG
    if value < -neutral_band:
        return RED_BG
    return GREY_BG


def rgba(hex_color: str, alpha: float) -> str:
    """'#RRGGBB' -> 'rgba(r,g,b,a)'."""
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


# ── Plotly ───────────────────────────────────────────────────────────────────
def style_fig(fig, *, height: int | None = None, legend: bool | None = None):
    """Put a Plotly figure on the light design. Keeps the figure's own layout
    (margins, legend position, shapes, annotations) and only sets colours,
    fonts and grid. Returns the same figure."""
    upd = dict(
        template="plotly_white",
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(family=FONT, color=T2, size=12),
        hoverlabel=dict(bgcolor=CARD, bordercolor=HAIR, font=dict(family=FONT, color=T1, size=12)),
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor=HAIR, font=dict(color=T2, size=11)),
        title_font=dict(color=T1),
    )
    if height is not None:
        upd["height"] = height
    if legend is not None:
        upd["showlegend"] = legend
    fig.update_layout(**upd)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=HAIR, linecolor=HAIR,
                     tickfont=dict(color=T3), title_font=dict(color=T3))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=HAIR, linecolor=HAIR,
                     tickfont=dict(color=T3), title_font=dict(color=T3))
    # Annotations written for a dark background (white / near-white text) -> dark text
    for ann in fig.layout.annotations or ():
        c = (ann.font.color or "") if ann.font else ""
        if isinstance(c, str) and c.lower() in ("#fff", "#ffffff", "white", "#f0f0f0", "#e0e0e0",
                                                "#e8e8e8", "#eee", "#eeeeee", "#ddd", "#cccccc", "#ccc"):
            ann.font.color = T1
        if getattr(ann, "bgcolor", None) and isinstance(ann.bgcolor, str) and ann.bgcolor.lower() in (
                "#000", "#000000", "#111", "#111111", "#141414", "#181818", "#1b1b1b", "#1c1c1c",
                "#1e1e1e", "#212121", "#222", "#222222", "#2a2a2a", "#303030"):
            ann.bgcolor = CARD
    return fig


# ── CSS ──────────────────────────────────────────────────────────────────────
RESULTS_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{{
  --bg:{BG}; --card:{CARD}; --inset:{INSET}; --fill:{FILL}; --hair:{HAIR}; --hair2:{HAIR2};
  --t1:{T1}; --t2:{T2}; --t3:{T3}; --t4:{T4};
  --blue:{BLUE}; --green:{GREEN}; --red:{RED}; --amber:{AMBER}; --orange:{ORANGE};
  --purple:{PURPLE}; --teal:{TEAL}; --indigo:{INDIGO};
  --blue-bg:{BLUE_BG}; --green-bg:{GREEN_BG}; --red-bg:{RED_BG}; --amber-bg:{AMBER_BG};
  --purple-bg:{PURPLE_BG}; --teal-bg:{TEAL_BG}; --grey-bg:{GREY_BG};
  --shadow:{SHADOW}; --shadow-sm:{SHADOW_SM};
}}

/* canvas */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],section[data-testid="stSidebar"]{{
    background:var(--bg)!important;color:var(--t1)!important;}}
.stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp button,.stApp input{{-webkit-font-smoothing:antialiased;}}
[data-testid="stIconMaterial"],.material-symbols-rounded{{font-family:'Material Symbols Rounded'!important;}}
.main .block-container,div.block-container{{max-width:1600px!important;padding:1.6rem 3.5rem 5rem!important;margin:0 auto!important;}}
[data-testid="stElementContainer"]:has(> .stMarkdown [data-testid="stMarkdownContainer"] > style:only-child){{display:none!important;}}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{{color:var(--t1)!important;letter-spacing:-0.01em;}}
.stApp [data-testid="stMarkdownContainer"]{{color:var(--t2);}}
.stApp [data-testid="stCaptionContainer"],.stApp .stCaption{{color:var(--t3)!important;}}
.stApp hr{{border-color:var(--hair)!important;}}

/* tabs -> segmented control (top-level and nested) */
.stApp [data-testid="stTabs"] [role="tablist"]{{background:var(--fill)!important;border:none!important;border-radius:12px!important;
    padding:3px!important;gap:2px!important;box-shadow:none!important;overflow-x:auto;scrollbar-width:none;margin-bottom:1.2rem!important;}}
.stApp [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar{{display:none;}}
.stApp [data-testid="stTab"]{{background:transparent!important;color:var(--t2)!important;border:none!important;border-radius:9px!important;
    padding:0.5rem 1rem!important;white-space:nowrap;flex:1 0 auto!important;justify-content:center!important;}}
.stApp [data-testid="stTab"] p{{color:inherit!important;font-size:0.92rem!important;font-weight:500!important;}}
.stApp [data-testid="stTab"]:hover{{color:var(--t1)!important;background:rgba(255,255,255,0.55)!important;}}
.stApp [data-testid="stTab"][aria-selected="true"]{{background:#FFFFFF!important;color:var(--t1)!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.14),0 0 0 0.5px rgba(0,0,0,0.06)!important;}}
.stApp [data-testid="stTab"][aria-selected="true"] p{{font-weight:600!important;}}
.stApp [data-testid="stTabs"] .react-aria-SelectionIndicator,.stApp [data-baseweb="tab-highlight"],
.stApp [data-baseweb="tab-border"]{{display:none!important;}}
.stApp [data-testid="stTabPanel"]{{color:var(--t1);}}

/* inputs */
.stApp [data-testid="stWidgetLabel"] p,.stApp .stRadio label p,.stApp .stCheckbox label p,.stApp .stSlider label p,
.stApp .stToggle label p{{color:var(--t2)!important;}}
.stApp [data-testid="stTextInputRootElement"],.stApp .stDateInput [data-baseweb="input"],.stApp .stTextInput [data-baseweb="input"],
.stApp .stSelectbox [data-baseweb="select"] > div,.stApp .stMultiSelect [data-baseweb="select"] > div,
.stApp .stNumberInput [data-baseweb="input"],.stApp .stTextArea textarea{{
    background:#E8E8ED!important;border:none!important;border-radius:12px!important;box-shadow:none!important;color:var(--t1)!important;}}
.stApp .stSelectbox [data-baseweb="select"],.stApp .stMultiSelect [data-baseweb="select"]{{background:transparent!important;border:none!important;}}
.stApp .stTextInput input,.stApp .stDateInput input,.stApp .stNumberInput input{{background:transparent!important;color:var(--t1)!important;
    -webkit-text-fill-color:var(--t1)!important;border:none!important;}}
.stApp [data-baseweb="select"] *{{color:var(--t1)!important;}}
/* Streamlit >= 1.5x selectboxes are react-aria ComboBoxes, not baseweb selects */
.stApp .stSelectbox .react-aria-ComboBox [role="group"]{{background:#E8E8ED!important;border:none!important;
    border-radius:12px!important;box-shadow:none!important;}}
.stApp .stSelectbox .react-aria-ComboBox input{{background:transparent!important;color:var(--t1)!important;
    -webkit-text-fill-color:var(--t1)!important;}}
.stApp .stSelectbox .react-aria-ComboBox [role="group"]:focus-within{{box-shadow:0 0 0 3px rgba(0,99,209,0.22)!important;}}
.stApp .stSelectbox svg,.stApp .stMultiSelect svg,.stApp .stDateInput svg{{color:var(--t3)!important;fill:var(--t3)!important;}}
.stApp .stNumberInput button{{background:#E8E8ED!important;color:var(--t2)!important;border:none!important;}}
.stApp .stNumberInput button:hover{{background:var(--hair)!important;}}
.stApp .stMultiSelect [data-baseweb="tag"]{{background:var(--blue-bg)!important;color:var(--blue)!important;border:none!important;}}
.stApp .stMultiSelect [data-baseweb="tag"] *{{color:var(--blue)!important;}}
body div[data-baseweb="popover"],body div[data-baseweb="popover"] > div,body div[data-baseweb="menu"],
body ul[role="listbox"],body li[role="option"]{{background:#FFFFFF!important;color:var(--t1)!important;border-color:var(--hair)!important;}}
body li[role="option"]:hover,body li[role="option"][aria-selected="true"]{{background:var(--fill)!important;}}
body div[data-baseweb="popover"] *{{color:var(--t1);}}
.stApp [data-testid="stRadioOption"]:has(input:checked) > div > div:first-child{{background:var(--blue)!important;border-color:var(--blue)!important;}}
.stApp .stCheckbox label:has(input:checked) > span + div{{background:var(--blue)!important;border-color:var(--blue)!important;}}
.stApp [data-testid="stSlider"] [role="slider"]{{background:var(--blue)!important;box-shadow:none!important;}}
.stApp [data-testid="stSliderThumbValue"]{{color:var(--blue)!important;}}

/* buttons */
.stApp .stButton > button,.stApp .stDownloadButton > button,.stApp .stFormSubmitButton > button{{background:#FFFFFF!important;
    color:var(--t1)!important;border:1px solid var(--hair)!important;border-radius:12px!important;box-shadow:var(--shadow-sm)!important;
    font-weight:600!important;}}
.stApp .stButton > button p,.stApp .stDownloadButton > button p{{color:inherit!important;}}
.stApp .stButton > button:hover,.stApp .stDownloadButton > button:hover{{background:var(--fill)!important;border-color:var(--hair2)!important;}}
.stApp .stButton > button[kind="primary"]{{background:var(--blue)!important;border-color:var(--blue)!important;color:#FFFFFF!important;}}
.stApp .stButton > button[kind="primary"]:hover{{background:#0052AD!important;}}
.stApp button[data-variant="pills"]{{background:#FFFFFF!important;border:1px solid var(--hair)!important;color:var(--t3)!important;
    border-radius:980px!important;box-shadow:none!important;}}
.stApp button[data-variant="pills"][aria-pressed="true"]{{background:var(--blue-bg)!important;border-color:rgba(0,99,209,0.22)!important;
    color:var(--blue)!important;}}
.stApp button[data-variant="pills"] p{{color:inherit!important;}}

/* expanders, alerts, metrics, tables, code */
.stApp [data-testid="stExpander"],.stApp .stExpander{{background:transparent!important;border:none!important;}}
.stApp [data-testid="stExpander"] details{{background:#FFFFFF!important;border:1px solid var(--hair)!important;border-radius:16px!important;}}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{{color:var(--t1)!important;}}
.stApp [data-testid="stExpander"] summary:hover{{background:var(--inset)!important;}}
.stApp [data-testid="stAlert"]{{background:var(--inset)!important;border:1px solid var(--hair)!important;border-radius:14px!important;color:var(--t2)!important;}}
.stApp [data-testid="stAlert"] *{{color:var(--t2)!important;}}
.stApp [data-testid="stMetric"]{{background:#FFFFFF!important;border:1px solid var(--hair)!important;border-radius:14px!important;padding:0.9rem 1rem!important;}}
.stApp [data-testid="stMetric"] > div{{background:transparent!important;}}
.stApp [data-testid="stMetricLabel"],.stApp [data-testid="stMetricLabel"] *{{color:var(--t3)!important;}}
.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricValue"] *{{color:var(--t1)!important;}}
.stApp div[data-testid="stDataFrame"],.stApp div[data-testid="stTable"],.stApp div[data-testid="stDataEditor"]{{background:#FFFFFF!important;
    border:1px solid var(--hair)!important;border-radius:14px!important;overflow:hidden;}}
.stApp .stTable table,.stApp .stTable th,.stApp .stTable td,.stApp div[data-testid="stTable"] th,.stApp div[data-testid="stTable"] td{{
    background:#FFFFFF!important;color:var(--t1)!important;border-color:var(--hair)!important;}}
.stApp .stTable th,.stApp div[data-testid="stTable"] th{{background:var(--inset)!important;color:var(--t3)!important;}}
.stApp [data-testid="stMarkdownContainer"] table th{{background:var(--inset);color:var(--t3);border-color:var(--hair);}}
.stApp [data-testid="stMarkdownContainer"] table td{{color:var(--t2);border-color:var(--hair);}}
.stApp code{{background:var(--fill)!important;color:var(--t1)!important;}}
.stApp [data-testid="stSpinner"] *,.stApp [data-testid="stProgress"] *{{color:var(--t2)!important;}}
.stApp .js-plotly-plot .modebar{{background:transparent!important;}}
.stApp .js-plotly-plot .modebar-btn path{{fill:var(--t4)!important;}}

/* shared building blocks for tab modules */
.ap-card{{background:var(--card);border:1px solid var(--hair);border-radius:18px;box-shadow:var(--shadow);padding:1.3rem 1.4rem;}}
.ap-tile{{background:var(--inset);border:1px solid var(--hair);border-radius:14px;padding:0.9rem 1rem;}}
.ap-section{{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin:1.8rem 0 0.8rem;}}
.ap-section-title{{font-size:1.25rem;font-weight:700;color:var(--t1);letter-spacing:-0.015em;}}
.ap-section-sub{{font-size:0.88rem;color:var(--t3);margin-top:0.15rem;}}
.ap-label{{font-size:0.78rem;font-weight:600;color:var(--t3);}}
.ap-value{{font-size:1.5rem;font-weight:700;color:var(--t1);letter-spacing:-0.02em;line-height:1.15;font-variant-numeric:tabular-nums;}}
.ap-sub{{font-size:0.82rem;color:var(--t3);}}
.ap-pill{{display:inline-flex;align-items:center;gap:0.3rem;font-size:0.76rem;font-weight:600;padding:0.2rem 0.65rem;border-radius:980px;
    background:var(--grey-bg);color:var(--t2);white-space:nowrap;}}
.ap-pill.green{{background:var(--green-bg);color:var(--green);}}
.ap-pill.red{{background:var(--red-bg);color:var(--red);}}
.ap-pill.blue{{background:var(--blue-bg);color:var(--blue);}}
.ap-pill.amber{{background:var(--amber-bg);color:var(--amber);}}
.ap-pill.purple{{background:var(--purple-bg);color:var(--purple);}}
.ap-pill.teal{{background:var(--teal-bg);color:var(--teal);}}
.ap-grid{{display:grid;gap:0.8rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));}}
.ap-divider{{border-top:1px solid var(--hair);margin:1rem 0;}}
</style>
"""


def apply_results_apple_theme() -> None:
    """Emit the light design layer for the stock-analysis results page."""
    st.markdown(RESULTS_CSS, unsafe_allow_html=True)
