"""The app's one design system: Apple's light look, used by every page.

* GLOBAL_CSS / apply_global_design() - tokens, type, canvas, motion and the generic
  Streamlit widgets. Emitted once per run, first thing in main(), so every page
  starts from the same base and nothing flashes dark while a page loads.
* RESULTS_CSS / apply_results_apple_theme() - the extra layer for the stock-analysis
  and market-scan results pages (tabs, tiles, shared building blocks).
* style_fig(fig) - puts any Plotly figure on the design (white paper, quiet grid,
  dark readable labels). Render it with st.plotly_chart(..., theme=None).
* small CSS classes (ap-card, ap-tile, ap-label, ap-value, ap-pill ...) that tab
  modules may use instead of long inline styles.

Colour rules: one accent (blue) for interactive things, green and red only for
up/down meaning, amber for "wait / caution", greys for everything else. Depth comes
from white on light grey and a whisper of shadow: no glows, no gradients, no neon.
"""
from __future__ import annotations

import streamlit as st

# ── palette ──────────────────────────────────────────────────────────────────
BG     = "#F5F5F7"   # page canvas
CARD   = "#FFFFFF"   # top-level card
INSET  = "#F5F5F7"   # tile inside a card
FILL   = "#EFEFF1"   # quiet fill (segmented controls, bars' empty track)
HAIR   = "#E8E8ED"   # hairline borders / dividers
HAIR2  = "#D2D2D7"   # stronger hairline (hover)
T1     = "#1D1D1F"   # primary text, big numbers
T2     = "#424245"   # body text
T3     = "#636366"   # labels, secondary text
T4     = "#86868B"   # faint text (never for essential info)

BLUE      = "#0066CC"   # text and links
BLUE_FILL = "#0071E3"   # buttons and solid fills
GREEN  = "#1B7A36"
RED    = "#D70015"
AMBER  = "#B25000"   # wait / caution / neutral-warning (text-safe on white)
ORANGE = "#C93400"
PURPLE = "#8944AB"
TEAL   = "#0071A4"
INDIGO = "#3634A3"

BLUE_BG   = "rgba(0,113,227,0.08)"
GREEN_BG  = "rgba(52,199,89,0.14)"
RED_BG    = "rgba(255,59,48,0.10)"
AMBER_BG  = "rgba(255,149,0,0.13)"
PURPLE_BG = "rgba(175,82,222,0.10)"
TEAL_BG   = "rgba(48,176,199,0.12)"
GREY_BG   = "rgba(118,118,128,0.12)"

SHADOW    = "0 1px 2px rgba(0,0,0,0.03),0 6px 20px rgba(0,0,0,0.045)"
SHADOW_SM = "0 1px 2px rgba(0,0,0,0.04)"

# Chart colours (a touch brighter than the text colours so thin candles read)
UP      = "#2AA84A"
DOWN    = "#E8362B"
GRID    = "#F2F2F4"
SERIES  = ["#007AFF", "#AF52DE", "#FF9500", "#30B0C7", "#FF6B35", "#5856D6", "#8E8E93"]

# Same regime colours as the Strategy Scanner page
REGIME_COLORS = {"TREND": INDIGO, "RANGE": TEAL, "VOLATILE": PURPLE}
REGIME_BG     = {"TREND": "rgba(88,86,214,0.10)", "RANGE": "rgba(48,176,199,0.12)",
                 "VOLATILE": "rgba(175,82,222,0.10)"}
REGIME_FILLS  = {"TREND": "#5856D6", "RANGE": "#30B0C7", "VOLATILE": "#AF52DE"}   # bars and dots

# San Francisco on Apple devices; everywhere else Inter, whose optical sizes are its
# closest match (the display cut tightens by itself at large sizes).
FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', Inter, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"


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
        legend=dict(bgcolor="rgba(255,255,255,0.7)", bordercolor="rgba(255,255,255,0)", font=dict(color=T2, size=11)),
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


# ── CSS: every page ──────────────────────────────────────────────────────────
_TOKENS = (
    ":root{"
    f"--bg:{BG};--card:{CARD};--inset:{INSET};--fill:{GREY_BG};--hair:{HAIR};--hair2:{HAIR2};"
    f"--t1:{T1};--t2:{T2};--t3:{T3};--t4:{T4};"
    f"--blue:{BLUE};--blue-fill:{BLUE_FILL};--blue-fill-h:#0077ED;--green:{GREEN};--red:{RED};"
    f"--amber:{AMBER};--orange:{ORANGE};--purple:{PURPLE};--teal:{TEAL};--indigo:{INDIGO};"
    f"--blue-bg:{BLUE_BG};--green-bg:{GREEN_BG};--red-bg:{RED_BG};--amber-bg:{AMBER_BG};"
    f"--orange-bg:{AMBER_BG};--purple-bg:{PURPLE_BG};--teal-bg:{TEAL_BG};--grey-bg:{GREY_BG};"
    "--indigo-bg:rgba(88,86,214,0.10);"
    f"--shadow:{SHADOW};--shadow-sm:{SHADOW_SM};"
    "--shadow-lift:0 2px 4px rgba(0,0,0,0.04),0 12px 32px rgba(0,0,0,0.08);"
    "--seg-on:0 1px 3px rgba(0,0,0,0.10),0 0 0 0.5px rgba(0,0,0,0.04);"
    "--btn:rgba(0,0,0,0.05);--btn-h:rgba(0,0,0,0.08);"
    "--r-lg:20px;--r-md:14px;--r-sm:10px;"
    f"--font:{FONT};"
    "--ease:cubic-bezier(.25,.1,.25,1);--ease-out:cubic-bezier(.22,.61,.36,1);"
    "}"
)

GLOBAL_CSS = (
    "<style>\n"
    "@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300..700&display=swap');\n"
    + _TOKENS + r"""

/* type */
.stApp,.stApp *{font-family:var(--font)!important;}
[data-testid="stIconMaterial"],.material-symbols-rounded{font-family:'Material Symbols Rounded'!important;}
.stApp{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility;
    font-optical-sizing:auto;letter-spacing:-0.006em;color:var(--t1);}
.stApp ::selection{background:rgba(0,113,227,0.18);}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{color:var(--t1)!important;font-weight:600!important;letter-spacing:-0.018em;}
.stApp .stMarkdown > [data-testid="stMarkdownContainer"]{color:var(--t2);}
.stApp [data-testid="stCaptionContainer"],.stApp .stCaption{color:var(--t3)!important;}
.stApp b{font-weight:600;}
.stApp hr{border-color:var(--hair)!important;}
.stApp code{background:var(--fill)!important;color:var(--t1)!important;border-radius:6px;}

/* canvas: light from the very first paint */
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],section[data-testid="stSidebar"]{
    background:var(--bg)!important;}
.stApp [data-testid="stMain"]{overflow-x:hidden!important;}
[data-testid="stElementContainer"]:has(> .stMarkdown [data-testid="stMarkdownContainer"] > style:only-child){display:none!important;}

/* scrollbars: thin, floating, out of the way */
*::-webkit-scrollbar{width:11px;height:11px;}
*::-webkit-scrollbar-track{background:transparent;}
*::-webkit-scrollbar-thumb{background:rgba(0,0,0,0.20);border-radius:980px;border:3px solid transparent;background-clip:content-box;}
*::-webkit-scrollbar-thumb:hover{background:rgba(0,0,0,0.36);border:3px solid transparent;background-clip:content-box;}
*::-webkit-scrollbar-corner{background:transparent;}

/* while a script runs: nothing dims. A hairline slides along the top instead, and only
   if the wait is long enough to notice. */
.stApp [data-stale="true"]{opacity:1!important;transition:none!important;}
.stApp::before{content:'';position:fixed;top:0;left:0;right:0;height:2px;z-index:1000000;pointer-events:none;
    background:linear-gradient(90deg,rgba(0,113,227,0),#0071E3 50%,rgba(0,113,227,0)) no-repeat;
    background-size:38% 100%;background-position:-60% 0;opacity:0;transition:opacity .3s ease;}
.stApp[data-test-script-state="running"]::before{opacity:1;transition-delay:.2s;
    animation:apLoad 1.3s cubic-bezier(.45,.05,.55,.95) infinite;}
@keyframes apLoad{from{background-position:-60% 0;}to{background-position:160% 0;}}

/* content arrives softly */
@keyframes apRise{from{opacity:0;transform:translateY(7px);}to{opacity:1;transform:none;}}
@keyframes apFade{from{opacity:0;}to{opacity:1;}}
.st-key-left_panel,.st-key-right_panel,.st-key-hero_box,.sc-tb,.mr-head,.mr-kpis{animation:apRise .5s var(--ease-out) both;}
.st-key-right_panel{animation-delay:.04s;}
[class*="st-key-lsc_panel_"]{animation:apRise .38s var(--ease-out) both;}
[data-testid="stTabPanel"]{animation:apFade .32s ease both;}
details.sc-more,details.sc-det,details.sc-alts,details.insight-toggle,details.mr-more{interpolate-size:allow-keywords;}
details.sc-more::details-content,details.sc-det::details-content,details.sc-alts::details-content,
details.insight-toggle::details-content,details.mr-more::details-content{height:0;overflow:clip;opacity:0;
    transition:height .34s var(--ease-out),opacity .26s ease,content-visibility .34s allow-discrete;}
details.sc-more[open]::details-content,details.sc-det[open]::details-content,details.sc-alts[open]::details-content,
details.insight-toggle[open]::details-content,details.mr-more[open]::details-content{height:auto;opacity:1;}
@media (prefers-reduced-motion:reduce){
  .stApp *,.stApp::before{animation:none!important;transition:none!important;}
}

/* buttons */
.stApp .stButton button,.stApp .stDownloadButton button,.stApp .stFormSubmitButton button{
    background:var(--btn)!important;color:var(--t1)!important;border:none!important;border-radius:980px!important;
    box-shadow:none!important;font-weight:500!important;letter-spacing:-0.01em;
    transition:background-color .2s var(--ease),color .2s var(--ease),transform .14s var(--ease),box-shadow .2s var(--ease)!important;}
.stApp .stButton button p,.stApp .stDownloadButton button p,.stApp .stFormSubmitButton button p{
    color:inherit!important;font-weight:inherit!important;}
.stApp .stButton button:hover,.stApp .stDownloadButton button:hover,.stApp .stFormSubmitButton button:hover{
    background:var(--btn-h)!important;color:var(--t1)!important;}
.stApp .stButton button:active,.stApp .stDownloadButton button:active,.stApp .stFormSubmitButton button:active{transform:scale(.975);}
.stApp .stButton button:focus-visible,.stApp .stDownloadButton button:focus-visible{outline:none!important;
    box-shadow:0 0 0 3px rgba(0,113,227,0.30)!important;}
.stApp .stButton button[kind="primary"],.stApp .stFormSubmitButton button[kind="primary"]{
    background:var(--blue-fill)!important;color:#FFFFFF!important;}
.stApp .stButton button[kind="primary"]:hover{background:var(--blue-fill-h)!important;color:#FFFFFF!important;}
.stApp button[data-variant="pills"]{background:var(--btn)!important;border:none!important;color:var(--t2)!important;
    border-radius:980px!important;box-shadow:none!important;transition:background-color .2s var(--ease),color .2s var(--ease)!important;}
.stApp button[data-variant="pills"]:hover{background:var(--btn-h)!important;color:var(--t1)!important;}
.stApp button[data-variant="pills"][aria-pressed="true"]{background:var(--blue-bg)!important;color:var(--blue)!important;}
.stApp button[data-variant="pills"] p{color:inherit!important;}

/* inputs: a soft fill, no outline until focused */
.stApp [data-testid="stWidgetLabel"] p,.stApp .stRadio label p,.stApp .stCheckbox label p,.stApp .stSlider label p,
.stApp .stToggle label p{color:var(--t2)!important;}
.stApp [data-testid="stTextInputRootElement"],.stApp .stDateInput [data-baseweb="input"],.stApp .stTextInput [data-baseweb="input"],
.stApp .stSelectbox [data-baseweb="select"] > div,.stApp .stMultiSelect [data-baseweb="select"] > div,
.stApp .stNumberInput [data-baseweb="input"],.stApp .stTextArea textarea,
.stApp .stSelectbox .react-aria-ComboBox [role="group"],.stApp [data-testid="stDateInputField"]{
    background:var(--fill)!important;border:none!important;border-radius:12px!important;box-shadow:none!important;
    color:var(--t1)!important;transition:box-shadow .2s var(--ease),background-color .2s var(--ease)!important;}
.stApp [data-testid="stTextInputRootElement"] *,.stApp .stDateInput [data-baseweb="input"] *{border:none!important;}
.stApp [data-testid="stTextInputRootElement"]:focus-within,.stApp .stDateInput [data-baseweb="input"]:focus-within,
.stApp .stNumberInput [data-baseweb="input"]:focus-within,.stApp .stSelectbox .react-aria-ComboBox [role="group"]:focus-within,
.stApp [data-testid="stDateInputField"]:focus-within{
    box-shadow:0 0 0 3.5px rgba(0,113,227,0.20)!important;}
.stApp .stSelectbox [data-baseweb="select"],.stApp .stMultiSelect [data-baseweb="select"]{background:transparent!important;border:none!important;}
.stApp .stTextInput input,.stApp .stDateInput input,.stApp .stNumberInput input,.stApp .stSelectbox .react-aria-ComboBox input{
    background:transparent!important;color:var(--t1)!important;-webkit-text-fill-color:var(--t1)!important;border:none!important;}
.stApp .stTextInput input::placeholder,.stApp .stNumberInput input::placeholder{color:var(--t3)!important;-webkit-text-fill-color:var(--t3)!important;opacity:1;}
.stApp [data-baseweb="select"] *{color:var(--t1)!important;}
.stApp .stSelectbox svg,.stApp .stMultiSelect svg,.stApp .stDateInput svg{color:var(--t3)!important;fill:var(--t3)!important;}
.stApp .stNumberInput button{background:transparent!important;color:var(--t2)!important;border:none!important;box-shadow:none!important;}
.stApp .stNumberInput button:hover{background:var(--btn)!important;}
.stApp .stMultiSelect [data-baseweb="tag"]{background:var(--blue-bg)!important;color:var(--blue)!important;border:none!important;}
.stApp .stMultiSelect [data-baseweb="tag"] *{color:var(--blue)!important;}
.stApp [data-testid="stRadioOption"]:has(input:checked) > div > div:first-child{background:var(--blue-fill)!important;border-color:var(--blue-fill)!important;}
.stApp .stCheckbox label:has(input:checked) > span + div{background:var(--blue-fill)!important;border-color:var(--blue-fill)!important;}
.stApp [data-testid="stSlider"] [role="slider"]{background:#FFFFFF!important;box-shadow:0 1px 4px rgba(0,0,0,0.25)!important;}
.stApp [data-testid="stSliderThumbValue"]{color:var(--blue)!important;}

/* floating things: frosted glass */
body div[data-baseweb="popover"],body div[data-baseweb="popover"] > div,body div[data-baseweb="menu"],body ul[role="listbox"]{
    background:rgba(255,255,255,0.88)!important;-webkit-backdrop-filter:saturate(180%) blur(24px);backdrop-filter:saturate(180%) blur(24px);
    color:var(--t1)!important;border:none!important;border-radius:14px!important;}
body div[data-baseweb="popover"]{box-shadow:0 0 0 0.5px rgba(0,0,0,0.08),0 14px 40px rgba(0,0,0,0.14)!important;}
body li[role="option"]{background:transparent!important;color:var(--t1)!important;border-radius:8px!important;}
body li[role="option"]:hover,body li[role="option"][aria-selected="true"]{background:var(--fill)!important;}
body div[data-baseweb="popover"] *{color:var(--t1);}
body [data-testid="stTooltipContent"]{background:rgba(255,255,255,0.90)!important;
    -webkit-backdrop-filter:saturate(180%) blur(24px);backdrop-filter:saturate(180%) blur(24px);color:var(--t1)!important;
    border:none!important;border-radius:12px!important;box-shadow:0 0 0 0.5px rgba(0,0,0,0.08),0 14px 40px rgba(0,0,0,0.14)!important;}
body [data-testid="stTooltipContent"] *{color:var(--t1)!important;font-family:var(--font)!important;}
#translate-fab-btn{height:34px!important;border-radius:980px!important;padding:0 14px!important;
    background:rgba(255,255,255,0.72)!important;-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);
    border:none!important;box-shadow:0 0 0 0.5px rgba(0,0,0,0.08),0 2px 12px rgba(0,0,0,0.08)!important;color:var(--t2)!important;
    font-family:var(--font)!important;transition:box-shadow .25s var(--ease),transform .14s var(--ease)!important;}
#translate-fab-btn:hover{background:rgba(255,255,255,0.92)!important;color:var(--t1)!important;
    box-shadow:0 0 0 0.5px rgba(0,0,0,0.08),0 4px 18px rgba(0,0,0,0.12)!important;}
#translate-fab-btn:active{transform:scale(.97);}
#translate-fab-btn.active{background:rgba(255,255,255,0.92)!important;color:var(--blue)!important;}
#translate-fab-btn .fab-dot{background:var(--hair2)!important;box-shadow:none!important;}
#translate-fab-btn.active .fab-dot{background:var(--blue-fill)!important;box-shadow:none!important;}

/* expanders, alerts, metrics, tables */
.stApp [data-testid="stExpander"],.stApp .stExpander{background:transparent!important;border:none!important;}
.stApp [data-testid="stExpander"] details{background:var(--card)!important;border:none!important;border-radius:16px!important;
    box-shadow:var(--shadow-sm)!important;overflow:hidden;}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{color:var(--t1)!important;}
.stApp [data-testid="stExpander"] summary{transition:background-color .2s var(--ease);}
.stApp [data-testid="stExpander"] summary:hover{background:rgba(0,0,0,0.02)!important;}
.stApp [data-testid="stExpander"] svg,.stApp [data-testid="stExpander"] [data-testid="stIconMaterial"]{color:var(--t3)!important;fill:var(--t3)!important;}
.stApp [data-testid="stAlert"]{background:var(--inset)!important;border:none!important;border-radius:14px!important;color:var(--t2)!important;}
.stApp [data-testid="stAlert"] *{color:var(--t2)!important;}
.stApp [data-testid="stMetric"]{background:var(--card)!important;border:none!important;border-radius:14px!important;padding:0.95rem 1.05rem!important;}
.stApp [data-testid="stMetric"] > div{background:transparent!important;}
.stApp [data-testid="stMetricLabel"],.stApp [data-testid="stMetricLabel"] *{color:var(--t3)!important;}
.stApp [data-testid="stMetricValue"],.stApp [data-testid="stMetricValue"] *{color:var(--t1)!important;font-weight:600!important;}
.stApp div[data-testid="stDataFrame"],.stApp div[data-testid="stTable"],.stApp div[data-testid="stDataEditor"]{background:var(--card)!important;
    border:1px solid var(--hair)!important;border-radius:14px!important;overflow:hidden;}
.stApp .stTable table,.stApp .stTable th,.stApp .stTable td,.stApp div[data-testid="stTable"] th,.stApp div[data-testid="stTable"] td{
    background:var(--card)!important;color:var(--t1)!important;border-color:var(--hair)!important;}
.stApp .stTable th,.stApp div[data-testid="stTable"] th{background:var(--card)!important;color:var(--t3)!important;font-weight:500!important;}
.stApp [data-testid="stMarkdownContainer"] table th{background:transparent;color:var(--t3);border-color:var(--hair);font-weight:500;}
.stApp [data-testid="stMarkdownContainer"] table td{color:var(--t2);border-color:var(--hair);}
.stApp [data-testid="stProgress"] p,.stApp [data-testid="stSpinner"] p,.stApp [data-testid="stSpinner"] div{color:var(--t3)!important;}
.stApp [data-testid="stProgress"] > div > div > div{background:var(--fill)!important;height:4px!important;border-radius:980px!important;}
.stApp [data-testid="stProgress"] > div > div > div > div{background:var(--blue-fill)!important;height:4px!important;border-radius:980px!important;
    transition:width .3s var(--ease);}
.stApp [style*="border:1px solid #E8E8ED"]{border-color:transparent!important;}
.stApp [data-testid="stPlotlyChart"]{border-radius:16px;overflow:hidden;}
.stApp .js-plotly-plot .modebar{background:transparent!important;}
.stApp .js-plotly-plot .modebar-btn path{fill:var(--t4)!important;}
@media (max-width:640px){.stApp .js-plotly-plot .modebar-container{display:none!important;}}
</style>
""")


def apply_global_design() -> None:
    """Emit the design base for this run. Call once, before any page renders."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── CSS: results pages ───────────────────────────────────────────────────────
RESULTS_CSS = r"""
<style>
.main .block-container,div.block-container{max-width:1600px!important;padding:2rem 3.5rem 5rem!important;margin:0 auto!important;}
@media (max-width:1100px){.main .block-container,div.block-container{padding:1.4rem 1.4rem 4rem!important;}}
@media (max-width:640px){
  .main .block-container,div.block-container{padding:0.9rem 0.8rem 3.5rem!important;}
  /* stacked columns keep a little air, and a side divider has nothing left to divide */
  .stApp [data-testid="stTabPanel"] [data-testid="stHorizontalBlock"]{row-gap:0.6rem!important;}
  .stApp [style*="border-right:1px solid #E8E8ED"]{border-right:none!important;padding-right:0!important;}
}

/* tabs -> segmented control (top-level and nested) */
.stApp [data-testid="stTabs"] [role="tablist"]{background:var(--fill)!important;border:none!important;border-radius:11px!important;
    padding:2px!important;gap:0!important;box-shadow:none!important;overflow-x:auto;scrollbar-width:none;margin:0 0 1.4rem!important;}
.stApp [data-testid="stTabs"] [role="tablist"]::-webkit-scrollbar{display:none;}
.stApp [data-testid="stTabs"] [role="tablist"]::after{display:none!important;}
.stApp [data-testid="stTab"]{background:transparent!important;color:var(--t2)!important;border:none!important;border-radius:9px!important;
    padding:0.42rem 0.95rem!important;white-space:nowrap;flex:1 0 auto!important;justify-content:center!important;
    transition:background-color .22s var(--ease),color .22s var(--ease),box-shadow .22s var(--ease)!important;}
.stApp [data-testid="stTab"] p{color:inherit!important;font-size:0.875rem!important;font-weight:500!important;letter-spacing:-0.008em;}
.stApp [data-testid="stTab"]:hover{color:var(--t1)!important;}
.stApp [data-testid="stTab"][aria-selected="true"]{background:#FFFFFF!important;color:var(--t1)!important;box-shadow:var(--seg-on)!important;}
.stApp [data-testid="stTab"][aria-selected="true"] p{font-weight:600!important;}
.stApp [data-testid="stTabs"] .react-aria-SelectionIndicator,.stApp [data-baseweb="tab-highlight"],
.stApp [data-baseweb="tab-border"]{display:none!important;}
.stApp [data-testid="stTabPanel"]{color:var(--t1);}

/* back buttons hug their text */
.stApp .st-key-ma_back_btn .stButton button{width:auto!important;padding:0.4rem 0.9rem!important;min-height:auto!important;white-space:nowrap!important;}

/* inputs here sit straight on the canvas: white, like the cards around them */
.stApp [data-testid="stTabPanel"] .stSelectbox .react-aria-ComboBox [role="group"],
.stApp [data-testid="stTabPanel"] [data-testid="stNumberInputContainer"],
.stApp [data-testid="stTabPanel"] [data-testid="stTextInputRootElement"]{background:#FFFFFF!important;
    border:none!important;border-radius:12px!important;box-shadow:var(--shadow-sm)!important;}
.stApp [data-testid="stTabPanel"] [data-testid="stNumberInputContainer"] *{background:transparent!important;}
.stApp [data-testid="stTabPanel"] .stSelectbox .react-aria-ComboBox [role="group"]:focus-within,
.stApp [data-testid="stTabPanel"] [data-testid="stNumberInputContainer"]:focus-within{box-shadow:0 0 0 3.5px rgba(0,113,227,0.20)!important;}

/* shared building blocks for tab modules */
.ap-card{background:var(--card);border:none;border-radius:20px;box-shadow:var(--shadow);padding:1.5rem 1.6rem;}
.ap-tile{background:var(--inset);border:none;border-radius:14px;padding:0.95rem 1.05rem;}
.ap-section{display:flex;align-items:baseline;justify-content:space-between;gap:1rem;margin:2.2rem 0 0.9rem;}
.ap-section-title{font-size:1.35rem;font-weight:600;color:var(--t1);letter-spacing:-0.02em;}
.ap-section-sub{font-size:0.875rem;color:var(--t3);margin-top:0.2rem;}
.ap-label{font-size:0.78rem;font-weight:500;color:var(--t3);}
.ap-value{font-size:1.5rem;font-weight:600;color:var(--t1);letter-spacing:-0.022em;line-height:1.15;}
.ap-sub{font-size:0.82rem;color:var(--t3);}
.ap-pill{display:inline-flex;align-items:center;gap:0.3rem;font-size:0.75rem;font-weight:500;padding:0.2rem 0.62rem;border-radius:980px;
    background:var(--grey-bg);color:var(--t2);white-space:nowrap;}
.ap-pill.green{background:var(--green-bg);color:var(--green);}
.ap-pill.red{background:var(--red-bg);color:var(--red);}
.ap-pill.blue{background:var(--blue-bg);color:var(--blue);}
.ap-pill.amber{background:var(--amber-bg);color:var(--amber);}
.ap-pill.purple{background:var(--purple-bg);color:var(--purple);}
.ap-pill.teal{background:var(--teal-bg);color:var(--teal);}
.ap-grid{display:grid;gap:0.8rem;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));}
.ap-divider{border-top:1px solid var(--hair);margin:1.1rem 0;}
</style>
"""


def apply_results_apple_theme() -> None:
    """Emit the extra design layer for the results pages."""
    st.markdown(RESULTS_CSS, unsafe_allow_html=True)
