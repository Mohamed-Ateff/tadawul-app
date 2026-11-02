"""The home (controls) page's layer of the design.

The home page keeps its own markup and its large CSS block in app.py; this module
is emitted right after that block and re-skins it on top of apple_theme's tokens,
so it looks like the rest of the product: one white card per job on a light canvas,
dark readable text, colour only for meaning.
"""
from __future__ import annotations

import streamlit as st

HOME_CSS = """
<style>
/* ── canvas ─────────────────────────────────────────────────────────────── */
.main .block-container,div.block-container{max-width:1600px!important;
    padding:2rem 3.5rem 5rem!important;margin:0 auto!important;}
/* Script-only components (Arabic translate button, auto-refresh timer) render an
   invisible iframe that still took ~26px plus the block gaps above the cards.
   Take them out of the flow (they keep running) instead of hiding them. */
div.block-container [data-testid="stElementContainer"]:has(iframe[data-testid="stCustomComponentV1"]),
div.block-container [data-testid="stElementContainer"]:has(> iframe){
    position:absolute!important;width:0!important;height:0!important;overflow:hidden!important;
    margin:0!important;padding:0!important;}

/* ── the two cards ──────────────────────────────────────────────────────── */
.st-key-cp_row > div:first-child > [data-testid="stHorizontalBlock"]{gap:1.75rem!important;align-items:flex-start!important;}
/* The keyed containers ARE the cards (their first child can be a style-only
   block, so styling "> div:first-child" missed the left panel). */
.st-key-left_panel,.st-key-right_panel{background:var(--card)!important;border:none!important;
    border-radius:22px!important;box-shadow:var(--shadow)!important;padding:2rem 2.1rem 2.2rem!important;
    height:auto!important;}
.st-key-left_panel > div:first-child,.st-key-right_panel > div:first-child{
    background:transparent!important;border:none!important;border-radius:0!important;box-shadow:none!important;
    padding:0!important;}
.st-key-stock_analysis_panel,.st-key-market_analysis_panel{background:transparent!important;
    border:none!important;padding:0!important;box-shadow:none!important;}
.st-key-cp_row [data-testid="stColumn"]:first-child,.st-key-cp_row [data-testid="column"]:first-child{
    position:sticky!important;top:1.25rem!important;align-self:flex-start!important;}

/* ── section titles ─────────────────────────────────────────────────────── */
.ah-sec{display:flex;align-items:baseline;justify-content:space-between;margin:0 0 0.9rem;}
.ah-sec b{font-size:1.375rem;font-weight:600;color:var(--t1);letter-spacing:-0.022em;}
.ah-sec span{font-size:0.8125rem;font-weight:400;color:var(--t3);}
.ah-sec.gap{margin-top:1.9rem;}
.st-key-left_panel .ah-sec.gap{margin-bottom:0.7rem;}

/* ── period selector (1D … 1Y) as one segmented control ─────────────────── */
.st-key-prd_row [data-testid="stHorizontalBlock"]{background:var(--fill)!important;border-radius:11px!important;
    padding:2px!important;gap:0!important;margin:0!important;}
.st-key-prd_row [data-testid="column"],.st-key-prd_row [data-testid="stColumn"]{padding:0!important;min-width:0!important;}
.st-key-mkt_p_1d .stButton > button,.st-key-mkt_p_1w .stButton > button,.st-key-mkt_p_1m .stButton > button,
.st-key-mkt_p_3m .stButton > button,.st-key-mkt_p_6m .stButton > button,.st-key-mkt_p_1y .stButton > button{
    background:transparent!important;border:none!important;box-shadow:none!important;color:var(--t2)!important;
    font-size:0.8125rem!important;font-weight:500!important;border-radius:9px!important;min-height:1.95rem!important;
    padding:0!important;letter-spacing:0!important;}
.st-key-mkt_p_1d .stButton > button p,.st-key-mkt_p_1w .stButton > button p,.st-key-mkt_p_1m .stButton > button p,
.st-key-mkt_p_3m .stButton > button p,.st-key-mkt_p_6m .stButton > button p,.st-key-mkt_p_1y .stButton > button p{
    color:inherit!important;font-weight:inherit!important;font-size:inherit!important;}
.st-key-mkt_p_1d .stButton > button:hover,.st-key-mkt_p_1w .stButton > button:hover,.st-key-mkt_p_1m .stButton > button:hover,
.st-key-mkt_p_3m .stButton > button:hover,.st-key-mkt_p_6m .stButton > button:hover,.st-key-mkt_p_1y .stButton > button:hover{
    color:var(--t1)!important;background:transparent!important;}

/* ── market pulse: open content, no box inside the box ──────────────────── */
.mpulse-card{background:transparent!important;border:none!important;border-radius:0!important;box-shadow:none!important;
    padding:0!important;margin-top:1.6rem!important;}
.mpulse-card::before{display:none!important;}
.mpulse-top{align-items:flex-start!important;margin-bottom:0!important;}
.mpulse-time{color:var(--t1)!important;font-size:2.75rem!important;font-weight:600!important;letter-spacing:-0.032em!important;
    line-height:1.05!important;white-space:nowrap;font-variant-numeric:tabular-nums;}
.mpulse-sub{color:var(--t3)!important;font-size:0.875rem!important;font-weight:400!important;margin:0.4rem 0 1.2rem!important;}
.mpulse-div{background:var(--hair)!important;margin:0.95rem 0!important;}
.mpulse-row{margin-bottom:0.7rem!important;gap:0.75rem;}
.mpulse-row:last-of-type{margin-bottom:0!important;}
.mpulse-row-label{color:var(--t2)!important;font-size:0.9375rem!important;font-weight:400!important;
    text-transform:none!important;letter-spacing:-0.008em!important;white-space:nowrap;}
.mpulse-tasi-val,.mpulse-perf-val{font-size:1.25rem!important;font-weight:600!important;letter-spacing:-0.02em!important;}
.mpulse-perf-right{gap:0.55rem!important;}
.mpulse-badge-open,.mpulse-badge-closed,.mpulse-sent{font-size:0.75rem!important;font-weight:500!important;
    letter-spacing:0!important;box-shadow:none!important;border:none!important;padding:0.2rem 0.6rem!important;
    border-radius:980px!important;}
.mpulse-badge-open,.mpulse-badge-closed{text-transform:none!important;margin-top:0.55rem;}
.mpulse-sent{display:inline-block;text-transform:lowercase!important;}
.mpulse-sent::first-letter{text-transform:uppercase;}
.mpulse-badge-open{background:var(--green-bg)!important;color:var(--green)!important;}
.mpulse-badge-closed{background:var(--red-bg)!important;color:var(--red)!important;}
.mpulse-badge-open .mpulse-dot{background:#34C759!important;}
.mpulse-badge-closed .mpulse-dot{background:#FF3B30!important;}
.mpulse-bar{height:6px!important;gap:2px!important;border-radius:980px!important;margin-bottom:0.8rem!important;}
.mpulse-bar-up{background:#34C759!important;}
.mpulse-bar-down{background:#FF3B30!important;}
.mpulse-bar-flat{background:var(--hair2)!important;}
.mpulse-pills{gap:1rem!important;}
.mpulse-pill{background:none!important;border:none!important;padding:0!important;font-size:0.875rem!important;
    font-weight:500!important;font-variant-numeric:tabular-nums;}
.mpulse-pill-up{color:var(--green)!important;}
.mpulse-pill-down{color:var(--red)!important;}
.mpulse-pill-flat{color:var(--t3)!important;}
.mpulse-ratio{background:none!important;border:none!important;padding:0!important;color:var(--t3)!important;
    font-size:0.8125rem!important;font-weight:400!important;font-variant-numeric:tabular-nums;}
.mstat-card{background:var(--inset)!important;border:none!important;border-radius:16px!important;}
.mstat-label,.mstat-sub,.mstat-bl{color:var(--t3)!important;}
.mstat-value{color:var(--t1)!important;}
.mstat-bcell{background:var(--card)!important;border:none!important;}

/* ── Tools: the Strategy Scanner button, the page's one big action ──────── */
.st-key-left_panel [data-testid="stHorizontalBlock"]{gap:0.5rem;}
.st-key-btn_champions .stButton > button{
    position:relative!important;background:var(--blue-fill)!important;border:none!important;border-radius:18px!important;
    min-height:5rem!important;padding:1rem 3rem 1rem 1.3rem!important;white-space:normal!important;
    text-transform:none!important;display:flex!important;flex-direction:column!important;align-items:flex-start!important;justify-content:center!important;
    text-align:left!important;box-shadow:none!important;}
.st-key-btn_champions .stButton > button > div{display:flex!important;align-items:center!important;
    justify-content:flex-start!important;width:100%;}
.st-key-btn_champions .stButton > button > div > span{gap:0.7rem!important;align-items:center!important;}
.st-key-btn_champions .stButton > button span:has(> [data-testid="stIconMaterial"]){
    width:1.6rem!important;min-width:1.6rem!important;justify-content:center!important;}
.st-key-btn_champions .stButton > button p{color:#FFFFFF!important;font-size:1.0625rem!important;font-weight:600!important;
    letter-spacing:-0.014em!important;text-transform:none!important;}
.st-key-btn_champions .stButton > button [data-testid="stIconMaterial"]{color:#FFFFFF!important;font-size:1.45rem!important;
    display:inline-flex!important;align-items:center;justify-content:center;flex-shrink:0;}
.st-key-btn_champions .stButton > button::after{
    content:'Best strategy for every stock · live buy signals';
    display:block;margin:0.22rem 0 0 2.3rem;max-width:calc(100% - 2.3rem);font-size:0.8125rem;font-weight:400;
    color:rgba(255,255,255,0.84);line-height:1.35;letter-spacing:-0.006em;text-transform:none;}
.st-key-btn_champions .stButton > button::before{
    content:'';position:absolute;right:1.35rem;top:50%;width:0.5rem;height:0.5rem;
    border-right:1.75px solid rgba(255,255,255,0.8);border-bottom:1.75px solid rgba(255,255,255,0.8);
    transform:translateY(-50%) rotate(-45deg);}
.st-key-btn_champions .stButton > button:hover{background:var(--blue-fill-h)!important;}
.st-key-btn_champions .stButton > button:hover p{color:#FFFFFF!important;}
.st-key-btn_champions .stButton > button:active{transform:scale(.985);}

/* ── user panel ─────────────────────────────────────────────────────────── */
.st-key-user_panel_wrap > div:first-child{background:var(--inset)!important;border:none!important;
    border-radius:16px!important;}
.user-panel-hdr{border-bottom:1px solid var(--hair)!important;}
.user-avatar{background:var(--t1)!important;color:#fff!important;border-radius:50%!important;}
.user-info-name{color:var(--t1)!important;font-weight:600!important;}
.user-info-role,.user-stat-label{color:var(--t3)!important;text-transform:none!important;letter-spacing:0!important;font-size:0.75rem!important;}
.user-stat{background:var(--card)!important;border:none!important;border-radius:12px!important;}
.user-stat-value{color:var(--t1)!important;font-weight:600!important;}

/* ── tabs: Stock Symbol | Scan Market as a segmented control ────────────── */
.st-key-right_panel [role="tablist"]{background:var(--fill)!important;border:none!important;border-radius:11px!important;
    padding:2px!important;gap:0!important;margin:0 0 1.9rem!important;}
.st-key-right_panel [role="tablist"]::after{display:none!important;}
.st-key-right_panel [data-testid="stTab"]{flex:1!important;justify-content:center!important;border-radius:9px!important;
    background:transparent!important;color:var(--t2)!important;padding:0.42rem 1rem!important;border:none!important;
    transition:background-color .22s var(--ease),color .22s var(--ease),box-shadow .22s var(--ease)!important;}
.st-key-right_panel [data-testid="stTab"] p{color:inherit!important;font-size:0.9rem!important;font-weight:500!important;letter-spacing:-0.008em;}
.st-key-right_panel [data-testid="stTab"]:hover{color:var(--t1)!important;}
.st-key-right_panel [data-testid="stTab"][aria-selected="true"]{background:#FFFFFF!important;color:var(--t1)!important;
    box-shadow:var(--seg-on)!important;}
.st-key-right_panel [data-testid="stTab"][aria-selected="true"] p{font-weight:600!important;}
.st-key-right_panel [data-baseweb="tab-highlight"],.st-key-right_panel [data-baseweb="tab-border"],
.st-key-right_panel .react-aria-SelectionIndicator{display:none!important;}
.st-key-right_panel [data-testid="stTabs"] > div:first-child{border-bottom:none!important;box-shadow:none!important;}
.stApp [role="tabpanel"]{color:var(--t1)!important;}

/* ── numbered steps in the right card ───────────────────────────────────── */
.ah-step{display:flex;gap:0.8rem;align-items:flex-start;margin:1.1rem 0 0.1rem;
    border-top:1px solid var(--hair);padding-top:1.7rem;}
.ah-step.first{border-top:none;padding-top:0;margin-top:0;}
.ah-step .n{flex:0 0 24px;height:24px;border-radius:50%;background:var(--fill);color:var(--t2);font-size:0.78rem;
    font-weight:600;display:flex;align-items:center;justify-content:center;margin-top:2px;font-variant-numeric:tabular-nums;}
.ah-step .t{font-size:1.1875rem;font-weight:600;color:var(--t1);letter-spacing:-0.018em;line-height:1.3;}
.ah-step .s{font-size:0.875rem;color:var(--t3);margin-top:0.18rem;line-height:1.45;letter-spacing:-0.006em;}
.ah-run-gap{height:1rem;}
.ah-hr{border-top:1px solid var(--hair);margin:0.6rem 0 0.9rem;}

/* ── labels and inputs ──────────────────────────────────────────────────── */
.cp-input-label,.st-key-right_panel .cp-input-label{color:var(--t2)!important;font-size:0.8125rem!important;font-weight:500!important;
    text-transform:none!important;letter-spacing:-0.004em!important;margin:0.95rem 0 0.38rem!important;}
.stApp .stTextInput input,.stApp .stDateInput input,.stApp .stNumberInput input{font-size:0.9875rem!important;font-weight:400!important;}
.stApp .stSelectbox .react-aria-ComboBox input{font-size:0.9375rem!important;}
.stApp [data-baseweb="popover"] *{color:var(--t1);}
.stApp .stRadio [role="radiogroup"] label,.stApp .stCheckbox label{color:var(--t1)!important;}

/* ── primary action ─────────────────────────────────────────────────────── */
.st-key-right_panel .stButton > button[kind="secondary"]{background:var(--blue-fill)!important;border:none!important;
    color:#FFFFFF!important;border-radius:980px!important;min-height:3rem!important;font-size:1.0625rem!important;
    font-weight:500!important;letter-spacing:-0.012em!important;box-shadow:none!important;}
.st-key-right_panel .stButton > button[kind="secondary"] p{color:#FFFFFF!important;font-weight:500!important;font-size:1.0625rem!important;}
.st-key-right_panel .stButton > button[kind="secondary"]:hover{background:var(--blue-fill-h)!important;color:#FFFFFF!important;}

/* ── indicators: seven quiet groups of tags ─────────────────────────────── */
.st-key-ind_grid{margin-top:0.75rem!important;}
.st-key-ind_grid [data-testid="stHorizontalBlock"]{gap:0.75rem!important;align-items:flex-start!important;}
.st-key-ind_grid [data-testid="stColumn"] > div{gap:0.75rem!important;}
.st-key-right_panel [class*="st-key-indcat_"]{background:var(--inset)!important;border:none!important;
    border-radius:16px!important;padding:1rem 1.05rem 1.1rem!important;gap:0.6rem!important;}
.st-key-right_panel [class*="st-key-indcat_"] [data-testid="stElementContainer"],
.st-key-right_panel [class*="st-key-indcat_"] .stMarkdown,
.st-key-right_panel [class*="st-key-indcat_"] .stMarkdown > div{height:auto!important;min-height:0!important;}
.st-key-right_panel [class*="st-key-indcat_"] [data-testid="stMarkdownContainer"]{margin:0!important;}
.st-key-right_panel [class*="st-key-indcat_"] .ah-cat-h{padding-bottom:0.1rem;}
.ah-cat-h{display:flex;align-items:center;justify-content:space-between;gap:0.5rem;}
.ah-cat-h b{font-size:0.9rem;font-weight:600;color:var(--t1);display:flex;align-items:center;gap:0.35rem;letter-spacing:-0.01em;}
.ah-cat-h .c{font-size:0.78rem;font-weight:400;color:var(--t3);font-variant-numeric:tabular-nums;}
.ah-cat-h .ind-tt{white-space:normal;min-width:280px;max-width:360px;font-size:0.78rem!important;line-height:1.5!important;
    font-weight:400!important;}
.ah-cat-h .ind-tt p{margin:0 0 0.45rem;color:#F5F5F7!important;}
.ah-cat-h .ind-tt b{display:inline;color:#FFFFFF!important;font-size:inherit;}
.ind-tip{background:transparent!important;border:1px solid var(--hair2)!important;color:var(--t3)!important;width:14px!important;height:14px!important;
    font-size:0.58rem!important;font-weight:500!important;transition:color .2s var(--ease),border-color .2s var(--ease);}
.ind-tip:hover{color:var(--blue)!important;border-color:var(--blue)!important;}
.ind-tip .ind-tt{background:rgba(29,29,31,0.94)!important;-webkit-backdrop-filter:blur(20px);backdrop-filter:blur(20px);color:#F5F5F7!important;
    border:none!important;border-radius:12px!important;box-shadow:0 14px 40px rgba(0,0,0,0.25)!important;}
.st-key-right_panel [data-testid="stButtonGroup"]{gap:0.3rem!important;flex-wrap:wrap!important;}
.st-key-right_panel button[data-variant="pills"]{border-radius:980px!important;min-height:0!important;
    padding:0.26rem 0.72rem!important;box-shadow:none!important;background:transparent!important;border:none!important;color:var(--t4)!important;}
.st-key-right_panel button[data-variant="pills"]:hover{background:rgba(0,0,0,0.04)!important;color:var(--t2)!important;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"]{background:#FFFFFF!important;color:var(--t1)!important;
    box-shadow:0 1px 2px rgba(0,0,0,0.06),0 0 0 0.5px rgba(0,0,0,0.04)!important;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"]:hover{background:#FFFFFF!important;color:var(--t1)!important;}
.st-key-right_panel button[data-variant="pills"] p{color:inherit!important;font-size:0.8125rem!important;font-weight:400!important;letter-spacing:-0.006em;}
.st-key-right_panel button[data-variant="pills"][aria-pressed="true"] p{font-weight:500!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"]{background:transparent!important;color:var(--blue)!important;
    box-shadow:none!important;min-height:0!important;padding:0.15rem 0.2rem!important;font-size:0.875rem!important;border-radius:6px!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"] p{color:var(--blue)!important;font-weight:400!important;font-size:0.875rem!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"]:hover{background:transparent!important;}
.st-key-ind_bulk .stButton > button[kind="secondary"]:hover p{text-decoration:underline;text-underline-offset:2px;}
.st-key-ind_bulk [data-testid="stHorizontalBlock"]{gap:0.6rem!important;justify-content:flex-end!important;}
.st-key-ind_bulk [data-testid="stColumn"]{flex:0 0 auto!important;width:auto!important;min-width:0!important;}

/* ── Scan Market: plain-language explainer, strategy card, hints ────────── */
.sm-how{background:var(--inset);border:none;border-radius:18px;padding:1.4rem 1.5rem 1.3rem;margin:0 0 1.9rem;}
.sm-how-h{font-size:1.1875rem;font-weight:600;color:var(--t1);letter-spacing:-0.018em;}
.sm-how-sub{font-size:0.9rem;color:var(--t3);line-height:1.5;margin-top:0.2rem;}
.sm-how-steps{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0.5rem 1.6rem;margin-top:1.1rem;}
@media (max-width:900px){.sm-how-steps{grid-template-columns:1fr;}}
.sm-how-s{display:flex;gap:0.7rem;align-items:flex-start;background:transparent;border:none;
    border-radius:0;padding:0.45rem 0;font-size:0.8438rem;color:var(--t3);line-height:1.45;}
.sm-how-s b{flex:0 0 1.5rem;height:1.5rem;border-radius:50%;background:var(--card);color:var(--t2);font-size:0.75rem;
    display:flex;align-items:center;justify-content:center;font-weight:600;box-shadow:var(--shadow-sm);}
.sm-how-s span{display:block;font-weight:600;color:var(--t1);font-size:0.9rem;margin-bottom:0.08rem;letter-spacing:-0.01em;}
.sm-how-foot{font-size:0.84rem;color:var(--t3);margin-top:0.8rem;line-height:1.5;}
.sm-strat{background:var(--inset);border:none;border-radius:16px;padding:1.1rem 1.3rem 0.5rem;margin:1rem 0 0.8rem;box-shadow:none;}
.sm-strat-top{display:flex;align-items:center;justify-content:space-between;gap:0.8rem;flex-wrap:wrap;margin-bottom:0.65rem;}
.sm-strat-name{font-size:1.0625rem;font-weight:600;color:var(--t1);letter-spacing:-0.014em;}
.sm-pill{font-size:0.75rem;font-weight:500;color:var(--blue);background:var(--blue-bg);padding:0.2rem 0.65rem;border-radius:980px;}
.sm-row{display:grid;grid-template-columns:7rem minmax(0,1fr);gap:0.8rem;padding:0.6rem 0;border-top:1px solid var(--hair);
    font-size:0.9rem;line-height:1.5;}
.sm-row span{font-weight:400;color:var(--t3);font-size:0.875rem;}
.sm-row div{color:var(--t1);}
@media (max-width:700px){.sm-row{grid-template-columns:1fr;gap:0.15rem;}}
.sm-glance{display:grid;gap:0.4rem;margin-bottom:0.4rem;}
.sm-g{display:grid;grid-template-columns:9.5rem minmax(0,1fr) auto;gap:0.8rem;align-items:baseline;padding:0.5rem 0.8rem;
    border-radius:10px;font-size:0.85rem;color:var(--t2);background:transparent;}
.sm-g b{color:var(--t1);font-weight:600;}
.sm-g em{font-style:normal;color:var(--t3);font-size:0.78rem;white-space:nowrap;}
.sm-g.on{background:var(--blue-bg);}
.sm-g.on b{color:var(--blue);}
@media (max-width:900px){.sm-g{grid-template-columns:1fr;gap:0.1rem;}}
.sm-hint{font-size:0.78rem;color:var(--t3);line-height:1.45;margin-top:0.35rem;}

/* ── scan-market strategy card + table ──────────────────────────────────── */
.ah-strat-card{background:var(--inset);border:none;border-radius:16px;padding:1.1rem 1.3rem;margin:0.9rem 0;}
.ah-strat-title{font-size:1rem;font-weight:600;color:var(--t1);margin-bottom:0.35rem;}
.ah-strat-what{font-size:0.9rem;color:var(--t2);line-height:1.55;margin-bottom:0.75rem;}
.ah-strat-meta{display:flex;gap:0.6rem;align-items:baseline;font-size:0.82rem;color:var(--t3);line-height:1.5;margin-top:0.35rem;}
.ah-k{flex:0 0 5.2rem;font-size:0.72rem;font-weight:500;color:var(--t2);}
.ah-strat-tbl{border:none;border-radius:16px;overflow:hidden;overflow-x:auto;background:var(--inset);margin:0 0 0.4rem;}
.ah-strat-tbl table{width:100%;border-collapse:collapse;margin:0!important;border:none!important;}
.ah-strat-tbl th,.ah-strat-tbl td{border:none!important;border-bottom:1px solid var(--hair)!important;}
.ah-strat-tbl th{font-size:0.72rem!important;font-weight:500!important;color:var(--t3)!important;text-align:left;
    padding:0.65rem 1rem!important;background:transparent!important;}
.ah-strat-tbl td{padding:0.75rem 1rem!important;vertical-align:middle;background:transparent;}
.ah-strat-tbl tr:last-child td{border-bottom:none!important;}
.ah-name{font-size:0.88rem;font-weight:600;color:var(--t1)!important;white-space:nowrap;}
.ah-inds{font-size:0.8rem;color:var(--t3)!important;line-height:1.45;}
.ah-mkt{text-align:right;white-space:nowrap;}
.ah-mkt span{font-size:0.74rem;font-weight:500;color:var(--t2)!important;background:var(--fill);padding:0.2rem 0.65rem;border-radius:980px;}
.ah-row.ah-on td{background:var(--blue-bg)!important;}
.ah-row.ah-on .ah-name{color:var(--blue)!important;}

/* ── smaller screens ────────────────────────────────────────────────────── */
@media (max-width:1100px){
  .main .block-container,div.block-container{padding:1.4rem 1.4rem 4rem!important;}
}
@media (max-width:1000px){
  [data-testid="stHorizontalBlock"]:has(.st-key-left_panel){flex-direction:column!important;gap:1rem!important;}
  [data-testid="stHorizontalBlock"]:has(.st-key-left_panel) > [data-testid="stColumn"]{width:100%!important;
      flex:1 1 100%!important;min-width:100%!important;position:static!important;}
}
@media (max-width:640px){
  .main .block-container,div.block-container{max-width:100%!important;padding:0.8rem 0.8rem 4rem!important;}
  .st-key-left_panel,.st-key-right_panel{padding:1.35rem 1.15rem 1.5rem!important;border-radius:20px!important;}
  .st-key-cp_row [data-testid="stColumn"]:first-child,.st-key-cp_row [data-testid="column"]:first-child{position:static!important;}
  .st-key-cp_row > div:first-child > [data-testid="stHorizontalBlock"]{gap:0.8rem!important;}
  .st-key-prd_row [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
  .st-key-prd_row [data-testid="stColumn"]{width:auto!important;flex:1 1 0!important;}
  .mpulse-time{font-size:2.35rem!important;}
  .ah-step .t{font-size:1.09rem;}
  .st-key-btn_champions .stButton > button{padding:0.95rem 2.4rem 0.95rem 1.1rem!important;}
  .st-key-btn_champions .stButton > button::before{right:1.1rem;}
  .st-key-ind_bulk [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;}
}
</style>
"""


def apply_home_apple_theme() -> None:
    """Emit the home page's layer of the design (call after the page's own CSS)."""
    st.markdown(HOME_CSS, unsafe_allow_html=True)


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
