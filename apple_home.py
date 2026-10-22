"""Light, Apple-style skin for the home (controls) page.

The home page keeps its own markup and its large dark CSS block in app.py;
this module is emitted right after that block and re-skins it with the same
design tokens the Strategy Scanner page uses (favorites_tab.py), so the two
pages look like one product: light canvas, white cards, dark readable text,
quiet colour used only for meaning.
"""
from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

import streamlit as st

HOME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{
  --bg:#F2F2F5; --card:#FFFFFF; --inset:#F7F7FA; --fill:#EDEDF1;
  --hair:#DEDEE3; --hair2:#C9C9CF;
  --t1:#111114; --t2:#3F3F46; --t3:#5C5C63; --t4:#8A8A91;
  --blue:#0063D1; --blue-bg:rgba(0,99,209,0.09);
  --green:#1B7A36; --green-bg:rgba(27,122,54,0.10);
  --red:#C1121F; --red-bg:rgba(193,18,31,0.08);
  --orange:#A34800; --orange-bg:rgba(163,72,0,0.10);
  --shadow:0 1px 2px rgba(17,17,20,0.05),0 8px 24px rgba(17,17,20,0.06);
  --shadow-sm:0 1px 2px rgba(17,17,20,0.06);
}

/* ── canvas ─────────────────────────────────────────────────────────────── */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
section[data-testid="stSidebar"]{background:var(--bg)!important;color:var(--t1)!important;}
.stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp button,.stApp input{-webkit-font-smoothing:antialiased;}
[data-testid="stIconMaterial"],.material-symbols-rounded{font-family:'Material Symbols Rounded'!important;}
.main .block-container,div.block-container{max-width:1600px!important;
    padding:2.4rem 3.5rem 5rem!important;margin:0 auto!important;}
[data-testid="stElementContainer"]:has(> .stMarkdown [data-testid="stMarkdownContainer"] > style:only-child){
    display:none!important;}

/* ── the two cards ──────────────────────────────────────────────────────── */
.st-key-cp_row > div:first-child > [data-testid="stHorizontalBlock"]{gap:1.6rem!important;align-items:flex-start!important;}
/* The keyed containers ARE the cards (their first child can be a style-only
   block, so styling "> div:first-child" missed the left panel). */
.st-key-left_panel,.st-key-right_panel{background:var(--card)!important;border:1px solid var(--hair)!important;
    border-radius:22px!important;box-shadow:var(--shadow)!important;padding:1.6rem 1.7rem 1.8rem!important;
    height:auto!important;}
.st-key-left_panel > div:first-child,.st-key-right_panel > div:first-child{
    background:transparent!important;border:none!important;border-radius:0!important;box-shadow:none!important;
    padding:0!important;}
.st-key-stock_analysis_panel,.st-key-market_analysis_panel{background:transparent!important;
    border:none!important;padding:0!important;box-shadow:none!important;}

/* ── period selector (1D … 1Y) as one segmented control ─────────────────── */
.st-key-prd_row [data-testid="stHorizontalBlock"]{background:var(--fill)!important;border-radius:12px!important;
    padding:3px!important;gap:2px!important;margin:0 0 0.4rem!important;}
.st-key-prd_row [data-testid="column"],.st-key-prd_row [data-testid="stColumn"]{padding:0!important;min-width:0!important;}
.st-key-mkt_p_1d .stButton > button,.st-key-mkt_p_1w .stButton > button,.st-key-mkt_p_1m .stButton > button,
.st-key-mkt_p_3m .stButton > button,.st-key-mkt_p_6m .stButton > button,.st-key-mkt_p_1y .stButton > button{
    background:transparent!important;border:none!important;box-shadow:none!important;color:var(--t2)!important;
    font-size:0.85rem!important;font-weight:500!important;border-radius:9px!important;min-height:2.1rem!important;
    padding:0!important;letter-spacing:0!important;}
.st-key-mkt_p_1d .stButton > button p,.st-key-mkt_p_1w .stButton > button p,.st-key-mkt_p_1m .stButton > button p,
.st-key-mkt_p_3m .stButton > button p,.st-key-mkt_p_6m .stButton > button p,.st-key-mkt_p_1y .stButton > button p{
    color:inherit!important;font-weight:inherit!important;}
.st-key-mkt_p_1d .stButton > button:hover,.st-key-mkt_p_1w .stButton > button:hover,.st-key-mkt_p_1m .stButton > button:hover,
.st-key-mkt_p_3m .stButton > button:hover,.st-key-mkt_p_6m .stButton > button:hover,.st-key-mkt_p_1y .stButton > button:hover{
    color:var(--t1)!important;background:rgba(255,255,255,0.6)!important;}

/* ── user / scanner / journal buttons ───────────────────────────────────── */
.st-key-left_panel [data-testid="stHorizontalBlock"]{gap:0.5rem!important;}
.st-key-btn_user .stButton > button,.st-key-btn_champions .stButton > button,.st-key-btn_journal .stButton > button,
.st-key-btn_user_active .stButton > button,.st-key-btn_champions_active .stButton > button,
.st-key-btn_journal_active .stButton > button,.st-key-btn_saved .stButton > button{
    background:var(--card)!important;border:1px solid var(--hair)!important;border-radius:12px!important;
    color:var(--t1)!important;font-size:0.9rem!important;font-weight:600!important;text-transform:none!important;
    letter-spacing:0!important;min-height:2.6rem!important;box-shadow:var(--shadow-sm)!important;}
.st-key-btn_user .stButton > button p,.st-key-btn_champions .stButton > button p,.st-key-btn_journal .stButton > button p,
.st-key-btn_user_active .stButton > button p,.st-key-btn_champions_active .stButton > button p,
.st-key-btn_journal_active .stButton > button p{color:inherit!important;font-weight:inherit!important;text-transform:none!important;}
.st-key-btn_user .stButton > button:hover,.st-key-btn_champions .stButton > button:hover,
.st-key-btn_journal .stButton > button:hover{background:var(--fill)!important;border-color:var(--hair2)!important;}
.st-key-btn_user_active .stButton > button,.st-key-btn_champions_active .stButton > button,
.st-key-btn_journal_active .stButton > button{background:var(--t1)!important;border-color:var(--t1)!important;color:#FFFFFF!important;}

/* ── user panel ─────────────────────────────────────────────────────────── */
.st-key-user_panel_wrap > div:first-child{background:var(--inset)!important;border:1px solid var(--hair)!important;
    border-radius:16px!important;}
.user-panel-hdr{border-bottom:1px solid var(--hair)!important;}
.user-avatar{background:var(--t1)!important;color:#fff!important;border-radius:50%!important;}
.user-info-name{color:var(--t1)!important;font-weight:600!important;}
.user-info-role,.user-stat-label{color:var(--t3)!important;text-transform:none!important;letter-spacing:0!important;font-size:0.75rem!important;}
.user-stat{background:var(--card)!important;border:1px solid var(--hair)!important;border-radius:12px!important;}
.user-stat-value{color:var(--t1)!important;font-weight:600!important;}
.st-key-logout_btn .stButton > button{background:var(--red-bg)!important;border:none!important;color:var(--red)!important;
    text-transform:none!important;border-radius:12px!important;}
.st-key-disconnect_btn .stButton > button{background:var(--card)!important;border:1px solid var(--hair)!important;
    color:var(--t2)!important;text-transform:none!important;border-radius:12px!important;}

/* ── market pulse card ──────────────────────────────────────────────────── */
.mpulse-card{background:var(--inset)!important;border:1px solid var(--hair)!important;border-radius:18px!important;
    padding:1.2rem 1.25rem 1.05rem!important;margin-top:1rem!important;}
.mpulse-card::before{display:none!important;}
.mpulse-time{color:var(--t1)!important;font-size:2rem!important;font-weight:600!important;letter-spacing:-0.03em!important;}
.mpulse-sub{color:var(--t3)!important;font-size:0.82rem!important;}
.mpulse-div{background:var(--hair)!important;}
.mpulse-row-label{color:var(--t2)!important;font-size:0.85rem!important;font-weight:500!important;
    text-transform:none!important;letter-spacing:0!important;}
.mpulse-tasi-val,.mpulse-perf-val{font-size:1.35rem!important;font-weight:600!important;letter-spacing:-0.02em!important;}
.mpulse-badge-open,.mpulse-badge-closed,.mpulse-sent{font-size:0.75rem!important;font-weight:600!important;
    text-transform:none!important;letter-spacing:0!important;box-shadow:none!important;border:none!important;padding:0.22rem 0.65rem!important;}
.mpulse-badge-open{background:var(--green-bg)!important;color:var(--green)!important;}
.mpulse-badge-closed{background:var(--red-bg)!important;color:var(--red)!important;}
.mpulse-badge-open .mpulse-dot{background:var(--green)!important;}
.mpulse-badge-closed .mpulse-dot{background:var(--red)!important;}
.mpulse-bar{height:8px!important;}
.mpulse-bar-up{background:#34A853!important;}
.mpulse-bar-down{background:#E5484D!important;}
.mpulse-bar-flat{background:var(--hair2)!important;}
.mpulse-pill{font-size:0.82rem!important;font-weight:600!important;border:none!important;}
.mpulse-pill-up{background:var(--green-bg)!important;color:var(--green)!important;}
.mpulse-pill-down{background:var(--red-bg)!important;color:var(--red)!important;}
.mpulse-pill-flat{background:var(--fill)!important;color:var(--t2)!important;}
.mpulse-ratio{background:var(--card)!important;border:1px solid var(--hair)!important;color:var(--t2)!important;
    font-size:0.78rem!important;font-weight:500!important;}
.mstat-card{background:var(--inset)!important;border:1px solid var(--hair)!important;border-radius:18px!important;}
.mstat-label,.mstat-sub,.mstat-bl{color:var(--t3)!important;}
.mstat-value{color:var(--t1)!important;}
.mstat-bcell{background:var(--card)!important;border:1px solid var(--hair)!important;}

/* ── tabs: Stock Symbol | Scan Market as a segmented control ────────────── */
.st-key-right_panel [role="tablist"]{background:var(--fill)!important;border:none!important;border-radius:12px!important;
    padding:3px!important;gap:2px!important;margin-bottom:1.4rem!important;}
.st-key-right_panel [data-testid="stTab"]{flex:1!important;justify-content:center!important;border-radius:9px!important;
    background:transparent!important;color:var(--t2)!important;padding:0.5rem 1rem!important;border:none!important;}
.st-key-right_panel [data-testid="stTab"] p{color:inherit!important;font-size:0.95rem!important;font-weight:500!important;}
.st-key-right_panel [data-testid="stTab"][aria-selected="true"]{background:#FFFFFF!important;color:var(--t1)!important;
    box-shadow:0 1px 4px rgba(0,0,0,0.14),0 0 0 0.5px rgba(0,0,0,0.06)!important;}
.st-key-right_panel [data-testid="stTab"][aria-selected="true"] p{font-weight:600!important;}
.st-key-right_panel [data-baseweb="tab-highlight"],.st-key-right_panel [data-baseweb="tab-border"],
.st-key-right_panel .react-aria-SelectionIndicator{display:none!important;}
.stApp [role="tabpanel"]{color:var(--t1)!important;}

/* ── labels and inputs ──────────────────────────────────────────────────── */
.cp-input-label{color:var(--t2)!important;font-size:0.85rem!important;font-weight:600!important;
    text-transform:none!important;letter-spacing:0!important;margin:1rem 0 0.4rem!important;}
.stApp [data-testid="stTextInputRootElement"],.stApp [data-testid="stDateInputField"],
.stApp .stDateInput [data-baseweb="input"],.stApp .stTextInput [data-baseweb="input"],
.stApp [data-baseweb="select"] > div,.stApp .stNumberInput [data-baseweb="input"]{
    background:#E8E8ED!important;border:none!important;border-radius:12px!important;box-shadow:none!important;}
.stApp [data-testid="stTextInputRootElement"] *,.stApp .stDateInput [data-baseweb="input"] *{border:none!important;}
.stApp .stTextInput input,.stApp .stDateInput input,.stApp .stNumberInput input{
    background:transparent!important;color:var(--t1)!important;-webkit-text-fill-color:var(--t1)!important;
    font-size:1rem!important;font-weight:500!important;border:none!important;}
.stApp .stTextInput input::placeholder{color:var(--t4)!important;}
.stApp [data-baseweb="select"] *{color:var(--t1)!important;}
/* Streamlit >= 1.5x selectboxes are react-aria ComboBoxes, not baseweb selects */
.stApp .stSelectbox .react-aria-ComboBox [role="group"]{background:#E8E8ED!important;border:none!important;
    border-radius:12px!important;box-shadow:none!important;}
.stApp .stSelectbox .react-aria-ComboBox input{background:transparent!important;color:var(--t1)!important;
    -webkit-text-fill-color:var(--t1)!important;font-size:0.95rem!important;}
.stApp .stSelectbox .react-aria-ComboBox [role="group"]:focus-within{box-shadow:0 0 0 3px rgba(0,99,209,0.22)!important;}
.stApp [data-testid="stTextInputRootElement"]:focus-within,.stApp .stDateInput [data-baseweb="input"]:focus-within{
    box-shadow:0 0 0 3px rgba(0,99,209,0.22)!important;}
.stApp .stDateInput svg,.stApp [data-baseweb="select"] svg{color:var(--t3)!important;fill:var(--t3)!important;}
.stApp [data-baseweb="popover"] *{color:var(--t1);}
.stApp [data-testid="stWidgetLabel"] p,.stApp .stRadio label p,.stApp .stCheckbox label p,
.stApp .stSlider label p{color:var(--t2)!important;}

/* ── indicator chips ────────────────────────────────────────────────────── */
.cp-ind-hdr{color:var(--t1)!important;font-size:1.05rem!important;font-weight:600!important;text-transform:none!important;
    letter-spacing:0!important;border-top:1px solid var(--hair)!important;padding-top:1.3rem!important;margin-top:1.6rem!important;}
.cp-ind-hdr::after{display:none!important;}
.cp-cat{font-size:0.88rem!important;margin:1rem 0 0.5rem!important;}
.cp-cat span:last-child{color:var(--t1)!important;font-weight:600!important;text-transform:none!important;letter-spacing:0!important;}
.ind-row{gap:0.45rem!important;}
.ind-chip{background:var(--card)!important;border:1px solid var(--hair)!important;border-radius:980px!important;
    padding:0.42rem 0.8rem!important;box-shadow:none!important;}
.ind-chip:hover{background:var(--fill)!important;border-color:var(--hair2)!important;}
.ind-chip span.ic-lbl{color:var(--t1)!important;font-size:0.85rem!important;font-weight:500!important;}
.ind-chip.active{background:var(--blue-bg)!important;border-color:rgba(0,99,209,0.35)!important;}
.ind-chip.active span.ic-lbl{color:var(--blue)!important;font-weight:600!important;}
.ind-chip span.ic-new{background:var(--green-bg)!important;border:none!important;color:var(--green)!important;
    font-size:0.62rem!important;font-weight:600!important;text-transform:none!important;letter-spacing:0!important;}
.ind-tip{background:var(--fill)!important;border:none!important;color:var(--t3)!important;width:16px!important;height:16px!important;}
.ind-tip:hover{color:var(--blue)!important;background:var(--blue-bg)!important;}
.ind-tip .ind-tt{background:#1C1C1E!important;color:#F2F2F7!important;border:none!important;border-radius:12px!important;
    box-shadow:0 8px 28px rgba(0,0,0,0.22)!important;}

/* ── primary action ─────────────────────────────────────────────────────── */
.st-key-right_panel .stButton > button[kind="secondary"]{background:var(--blue)!important;border:none!important;
    color:#FFFFFF!important;border-radius:14px!important;min-height:3rem!important;font-size:1rem!important;
    font-weight:600!important;letter-spacing:0!important;box-shadow:0 4px 14px rgba(0,99,209,0.25)!important;}
.st-key-right_panel .stButton > button[kind="secondary"] p{color:#FFFFFF!important;font-weight:600!important;}
.st-key-right_panel .stButton > button[kind="secondary"]:hover{background:#0052AD!important;}

/* ── generic streamlit bits on this page ────────────────────────────────── */
.stApp .stRadio [role="radiogroup"] label,.stApp .stCheckbox label{color:var(--t1)!important;}
.stApp [data-testid="stExpander"]{background:transparent!important;border:none!important;}
.stApp [data-testid="stExpander"] details{background:var(--card)!important;border:1px solid var(--hair)!important;border-radius:16px!important;}
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{color:var(--t1)!important;}
.stApp [data-testid="stAlert"]{border-radius:14px!important;}
.stApp [data-testid="stRadioOption"]:has(input:checked) > div > div:first-child{
    background:var(--blue)!important;border-color:var(--blue)!important;}
.stApp .stCheckbox label:has(input:checked) > span + div{background:var(--blue)!important;border-color:var(--blue)!important;}

/* ── page top ───────────────────────────────────────────────────────────── */
.main .block-container,div.block-container{padding-top:1.5rem!important;}
/* Script-only components (Arabic translate button, auto-refresh timer) render an
   invisible iframe that still took ~26px plus the block gaps above the cards.
   Take them out of the flow (they keep running) instead of hiding them. */
div.block-container [data-testid="stElementContainer"]:has(iframe[data-testid="stCustomComponentV1"]),
div.block-container [data-testid="stElementContainer"]:has(> iframe){
    position:absolute!important;width:0!important;height:0!important;overflow:hidden!important;
    margin:0!important;padding:0!important;}
.ah-hero{margin:0 0 1.7rem;padding:0 0.25rem;}
.ah-eyebrow{font-size:0.8rem;font-weight:600;color:var(--t3);letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.3rem;}
.ah-title{font-size:2.45rem;font-weight:700;letter-spacing:-0.035em;color:var(--t1);line-height:1.12;}
.ah-sub{font-size:1.02rem;color:var(--t3);margin-top:0.4rem;}

/* ── left column: sticky, titled sections ───────────────────────────────── */
.st-key-cp_row [data-testid="stColumn"]:first-child,.st-key-cp_row [data-testid="column"]:first-child{
    position:sticky!important;top:1.2rem!important;align-self:flex-start!important;}
.ah-sec{display:flex;align-items:baseline;justify-content:space-between;margin:0 0 0.75rem;}
.ah-sec b{font-size:1.2rem;font-weight:700;color:var(--t1);letter-spacing:-0.015em;}
.ah-sec span{font-size:0.82rem;font-weight:500;color:var(--t3);}
.ah-sec.gap{margin-top:1.6rem;}
.st-key-left_panel .mpulse-card{margin-top:0.6rem!important;}
.st-key-btn_user .stButton > button,.st-key-btn_champions .stButton > button,.st-key-btn_journal .stButton > button,
.st-key-btn_user_active .stButton > button,.st-key-btn_champions_active .stButton > button,
.st-key-btn_journal_active .stButton > button{min-height:3.1rem!important;font-size:0.88rem!important;}
.st-key-left_panel .stButton [data-testid="stIconMaterial"]{color:var(--blue)!important;font-size:1.15rem!important;}
.st-key-btn_user_active [data-testid="stIconMaterial"],.st-key-btn_champions_active [data-testid="stIconMaterial"],
.st-key-btn_journal_active [data-testid="stIconMaterial"]{color:#FFFFFF!important;}

/* ── numbered steps in the right card ───────────────────────────────────── */
.ah-step{display:flex;gap:0.85rem;align-items:flex-start;margin:0.6rem 0 0.2rem;
    border-top:1px solid var(--hair);padding-top:1.5rem;}
.ah-step.first{border-top:none;padding-top:0;margin-top:0.1rem;}
.ah-step .n{flex:0 0 28px;height:28px;border-radius:50%;background:var(--t1);color:#FFFFFF;font-size:0.84rem;
    font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:1px;}
.ah-step .t{font-size:1.12rem;font-weight:600;color:var(--t1);letter-spacing:-0.01em;line-height:1.35;}
.ah-step .s{font-size:0.88rem;color:var(--t3);margin-top:0.12rem;line-height:1.5;}
.st-key-right_panel .cp-input-label{font-size:0.8rem!important;font-weight:500!important;color:var(--t3)!important;
    margin:0.9rem 0 0.35rem!important;}
.ah-run-gap{height:0.9rem;}
.ah-hr{border-top:1px solid var(--hair);margin:0.6rem 0 0.9rem;}

/* ── indicator groups ───────────────────────────────────────────────────── */
.st-key-right_panel [class*="st-key-indcat_"]{background:var(--inset)!important;border:1px solid var(--hair)!important;
    border-radius:16px!important;padding:0.95rem 1rem 1.05rem!important;gap:0.55rem!important;}
.st-key-ind_grid [data-testid="stHorizontalBlock"]{gap:0.9rem!important;align-items:flex-start!important;}
.st-key-ind_grid [data-testid="stColumn"] > div{gap:0.9rem!important;}
.ah-cat-h{display:flex;align-items:center;justify-content:space-between;gap:0.5rem;}
.ah-cat-h b{font-size:0.92rem;font-weight:600;color:var(--t1);display:flex;align-items:center;gap:0.4rem;}
.ah-cat-h .c{font-size:0.78rem;font-weight:500;color:var(--t3);font-variant-numeric:tabular-nums;}
.ah-cat-h .ind-tt{white-space:normal;min-width:280px;max-width:360px;font-size:0.78rem!important;line-height:1.5!important;
    font-weight:400!important;}
.ah-cat-h .ind-tt p{margin:0 0 0.45rem;color:#F2F2F7!important;}
.ah-cat-h .ind-tt b{display:inline;color:#FFFFFF!important;font-size:inherit;}
.st-key-right_panel [data-testid="stButtonGroup"]{gap:0.4rem!important;flex-wrap:wrap!important;}
.st-key-right_panel button[data-variant="pills"]{border-radius:980px!important;min-height:0!important;
    padding:0.32rem 0.8rem!important;box-shadow:none!important;transition:background .15s,border-color .15s;
    background:var(--card)!important;border:1px solid var(--hair)!important;color:var(--t3)!important;}
.st-key-right_panel button[data-variant="pills"]:hover{border-color:var(--hair2)!important;color:var(--t1)!important;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"]{background:rgba(0,99,209,0.10)!important;
    border-color:rgba(0,99,209,0.22)!important;color:var(--blue)!important;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"]:hover{background:rgba(0,99,209,0.16)!important;}
.st-key-right_panel button[data-variant="pills"] p{color:inherit!important;font-size:0.84rem!important;font-weight:500!important;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"] p{font-weight:600!important;}
.st-key-right_panel [class*="st-key-indcat_"] [data-testid="stMarkdownContainer"]{margin:0!important;}
.st-key-left_panel .ah-sec.gap{margin-bottom:0.45rem;}

/* ── Tools: the Strategy Scanner button as a prominent blue card ─────────── */
.st-key-btn_champions .stButton > button{
    position:relative!important;background:var(--blue)!important;border:none!important;border-radius:16px!important;
    min-height:4.9rem!important;padding:0.95rem 3rem 0.95rem 1.1rem!important;
    display:flex!important;flex-direction:column!important;align-items:flex-start!important;justify-content:center!important;
    text-align:left!important;box-shadow:0 6px 18px rgba(0,99,209,0.28)!important;
    transition:background .15s ease,transform .15s ease,box-shadow .15s ease!important;}
.st-key-btn_champions .stButton > button > div{display:flex!important;align-items:center!important;
    justify-content:flex-start!important;width:100%;}
.st-key-btn_champions .stButton > button > div > span{gap:0.75rem!important;align-items:center!important;}
/* the icon's own wrapper is only 16px wide: let it hold the full 2.3rem circle */
.st-key-btn_champions .stButton > button span:has(> [data-testid="stIconMaterial"]){
    width:2.3rem!important;min-width:2.3rem!important;justify-content:center!important;}
.st-key-btn_champions .stButton > button p{color:#FFFFFF!important;font-size:1.08rem!important;font-weight:600!important;
    letter-spacing:-0.01em!important;}
.st-key-btn_champions .stButton > button [data-testid="stIconMaterial"]{color:#FFFFFF!important;font-size:1.25rem!important;
    background:rgba(255,255,255,0.18);border-radius:50%;width:2.3rem;height:2.3rem;display:inline-flex!important;
    align-items:center;justify-content:center;flex-shrink:0;}
.st-key-btn_champions .stButton > button::after{
    content:'Best strategy for every stock · live buy signals';
    display:block;margin:0.3rem 0 0 3.05rem;font-size:0.82rem;font-weight:500;color:rgba(255,255,255,0.86);
    line-height:1.35;}
.st-key-btn_champions .stButton > button::before{
    content:'›';position:absolute;right:1.15rem;top:50%;transform:translateY(-52%);
    font-size:1.9rem;font-weight:400;color:rgba(255,255,255,0.9);line-height:1;}
.st-key-btn_champions .stButton > button:hover{background:#0052AD!important;transform:translateY(-1px);
    box-shadow:0 10px 24px rgba(0,99,209,0.34)!important;}
.st-key-btn_champions .stButton > button:hover p{color:#FFFFFF!important;}
.st-key-btn_champions .stButton > button:active{transform:translateY(0);}
.st-key-ind_grid{margin-top:0.5rem!important;}
.st-key-right_panel [role="tablist"]{border-bottom:none!important;}
.st-key-right_panel [data-testid="stTabs"] > div:first-child{border-bottom:none!important;box-shadow:none!important;}
.st-key-right_panel [class*="st-key-indcat_"] [data-testid="stElementContainer"],
.st-key-right_panel [class*="st-key-indcat_"] .stMarkdown,
.st-key-right_panel [class*="st-key-indcat_"] .stMarkdown > div{height:auto!important;min-height:0!important;}
.st-key-right_panel [class*="st-key-indcat_"] .ah-cat-h{padding-bottom:0.15rem;}
.st-key-ind_bulk .stButton > button[kind="secondary"]{background:transparent!important;color:var(--blue)!important;
    box-shadow:none!important;min-height:0!important;padding:0.15rem 0.2rem!important;font-size:0.88rem!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"] p{color:var(--blue)!important;font-weight:500!important;font-size:0.88rem!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"]:hover{background:transparent!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"]:hover p{text-decoration:underline;}
.st-key-ind_bulk [data-testid="stHorizontalBlock"]{gap:0.6rem!important;justify-content:flex-end!important;}
.st-key-ind_bulk [data-testid="stColumn"]{flex:0 0 auto!important;width:auto!important;min-width:0!important;}

/* ── Scan Market: plain-language explainer, strategy card, hints ────────── */
.sm-how{background:var(--inset);border:1px solid var(--hair);border-radius:16px;padding:1.15rem 1.25rem 1.05rem;margin:0.2rem 0 1.2rem;}
.sm-how-h{font-size:1.08rem;font-weight:700;color:var(--t1);letter-spacing:-0.01em;}
.sm-how-sub{font-size:0.9rem;color:var(--t2);line-height:1.55;margin-top:0.25rem;}
.sm-how-steps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0.6rem;margin-top:0.9rem;}
@media (max-width:900px){.sm-how-steps{grid-template-columns:1fr;}}
.sm-how-s{display:flex;gap:0.7rem;align-items:flex-start;background:var(--card);border:1px solid var(--hair);
    border-radius:12px;padding:0.75rem 0.85rem;font-size:0.86rem;color:var(--t2);line-height:1.5;}
.sm-how-s b{flex:0 0 1.6rem;height:1.6rem;border-radius:50%;background:var(--blue);color:#FFFFFF;font-size:0.8rem;
    display:flex;align-items:center;justify-content:center;font-weight:600;}
.sm-how-s span{display:block;font-weight:600;color:var(--t1);font-size:0.9rem;margin-bottom:0.1rem;}
.sm-how-foot{font-size:0.84rem;color:var(--t3);margin-top:0.8rem;line-height:1.5;}
.sm-strat{background:var(--card);border:1px solid var(--hair);border-radius:16px;padding:1.05rem 1.2rem;margin:0.9rem 0 0.8rem;
    box-shadow:var(--shadow-sm);}
.sm-strat-top{display:flex;align-items:center;justify-content:space-between;gap:0.8rem;flex-wrap:wrap;margin-bottom:0.5rem;}
.sm-strat-name{font-size:1.1rem;font-weight:700;color:var(--t1);letter-spacing:-0.01em;}
.sm-pill{font-size:0.78rem;font-weight:600;color:var(--blue);background:var(--blue-bg);padding:0.2rem 0.7rem;border-radius:980px;}
.sm-row{display:grid;grid-template-columns:7.5rem minmax(0,1fr);gap:0.8rem;padding:0.55rem 0;border-top:1px solid var(--hair);
    font-size:0.9rem;line-height:1.55;}
.sm-row span{font-weight:600;color:var(--t3);font-size:0.84rem;padding-top:0.05rem;}
.sm-row div{color:var(--t2);}
@media (max-width:700px){.sm-row{grid-template-columns:1fr;gap:0.15rem;}}
.sm-glance{display:grid;gap:0.4rem;margin-bottom:0.4rem;}
.sm-g{display:grid;grid-template-columns:9.5rem minmax(0,1fr) auto;gap:0.8rem;align-items:baseline;padding:0.5rem 0.8rem;
    border-radius:10px;font-size:0.85rem;color:var(--t2);background:transparent;}
.sm-g b{color:var(--t1);font-weight:600;}
.sm-g em{font-style:normal;color:var(--t3);font-size:0.78rem;white-space:nowrap;}
.sm-g.on{background:var(--blue-bg);}
.sm-g.on b{color:var(--blue);}
@media (max-width:900px){.sm-g{grid-template-columns:1fr;gap:0.1rem;}}
.sm-hint{font-size:0.8rem;color:var(--t3);line-height:1.5;margin-top:0.35rem;}

/* ── scan-market strategy card + table ──────────────────────────────────── */
.ah-strat-card{background:var(--inset);border:1px solid var(--hair);border-radius:16px;padding:1.05rem 1.2rem;margin:0.9rem 0;}
.ah-strat-title{font-size:1rem;font-weight:600;color:var(--t1);margin-bottom:0.35rem;}
.ah-strat-what{font-size:0.9rem;color:var(--t2);line-height:1.55;margin-bottom:0.75rem;}
.ah-strat-meta{display:flex;gap:0.6rem;align-items:baseline;font-size:0.82rem;color:var(--t3);line-height:1.5;margin-top:0.35rem;}
.ah-k{flex:0 0 5.2rem;font-size:0.72rem;font-weight:600;color:var(--t2);}
.ah-strat-tbl{border:1px solid var(--hair);border-radius:16px;overflow:hidden;overflow-x:auto;background:var(--card);margin:0 0 0.4rem;}
.ah-strat-tbl table{width:100%;border-collapse:collapse;margin:0!important;border:none!important;}
.ah-strat-tbl th,.ah-strat-tbl td{border:none!important;border-bottom:1px solid var(--hair)!important;}
.ah-strat-tbl th{font-size:0.72rem!important;font-weight:600!important;color:var(--t3)!important;text-align:left;
    padding:0.65rem 1rem!important;background:var(--inset)!important;}
.ah-strat-tbl td{padding:0.75rem 1rem!important;vertical-align:middle;background:var(--card);}
.ah-strat-tbl tr:last-child td{border-bottom:none!important;}
.ah-name{font-size:0.88rem;font-weight:600;color:var(--t1)!important;white-space:nowrap;}
.ah-inds{font-size:0.8rem;color:var(--t3)!important;line-height:1.45;}
.ah-mkt{text-align:right;white-space:nowrap;}
.ah-mkt span{font-size:0.74rem;font-weight:600;color:var(--t2)!important;background:var(--fill);padding:0.2rem 0.65rem;border-radius:980px;}
.ah-row.ah-on td{background:var(--blue-bg)!important;}
.ah-row.ah-on .ah-name{color:var(--blue)!important;}
</style>
"""


def apply_home_apple_theme() -> None:
    """Emit the home page's Apple-style layer (call after the page's own CSS)."""
    st.markdown(HOME_CSS, unsafe_allow_html=True)


def hero_html(name: str) -> str:
    """Large page title: date eyebrow, greeting, one-line purpose."""
    now = datetime.now(timezone(timedelta(hours=3)))          # Riyadh
    h = now.hour
    greet = ("Good morning" if 5 <= h < 12 else
             "Good afternoon" if 12 <= h < 17 else "Good evening")
    first = (name or "").strip().split(" ")[0].title()
    who = f", {html.escape(first)}" if first else ""
    return (f"<div class='ah-hero'>"
            f"<div class='ah-eyebrow'>{now.strftime('%A, %d %B')} · Tadawul</div>"
            f"<div class='ah-title'>{greet}{who}</div>"
            f"<div class='ah-sub'>Analyze one stock in depth, or scan the whole Saudi market for setups.</div>"
            f"</div>")


def sec_html(title: str, aside: str = "", gap: bool = False) -> str:
    """Section title for the left column."""
    return (f"<div class='ah-sec{' gap' if gap else ''}'><b>{title}</b>"
            f"<span>{aside}</span></div>")


def step_html(n: int, title: str, sub: str = "", rule: bool = True) -> str:
    """Numbered step header used in the right card's forms. rule=False drops the
    hairline above it (when the caller draws a full-width one itself)."""
    cls = ' first' if (n == 1 or not rule) else ''
    return (f"<div class='ah-step{cls}'><span class='n'>{n}</span>"
            f"<div><div class='t'>{title}</div>"
            f"{f'<div class=s>{sub}</div>' if sub else ''}</div></div>")
