import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from ui_helpers import insight_toggle
from apple_theme import (T1, T2, T3, T4, CARD, INSET, FILL, HAIR, HAIR2, SHADOW,
                         GREEN, RED, BLUE, AMBER, PURPLE, UP, DOWN, GRID,
                         GREEN_BG, RED_BG, BLUE_BG, AMBER_BG, PURPLE_BG, GREY_BG,
                         rgba, style_fig)

BULL  = GREEN
BEAR  = RED
NEUT  = AMBER
INFO  = BLUE
PURP  = PURPLE
POCC  = AMBER          # Point of Control highlight
BG    = CARD
BG2   = INSET
BDR   = HAIR

_NUM = "letter-spacing:-0.02em;font-variant-numeric:tabular-nums;"


def _sec(title, color=INFO, sub=""):
    return (
        f"<div style='margin:2.2rem 0 0.9rem;'>"
        f"<div style='font-size:1.25rem;font-weight:700;color:{T1};"
        f"letter-spacing:-0.015em;line-height:1.3;'>{title}</div>"
        + (f"<div style='font-size:0.88rem;color:{T3};margin-top:0.2rem;'>{sub}</div>" if sub else "")
        + "</div>"
    )


def _glowbar(pct, color=BULL, height="8px"):
    pct = max(0, min(100, pct))
    return (
        f"<div style='background:{FILL};border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;"
        f"background:{color};border-radius:999px;'></div></div>"
    )


# ══════════════════════════════════════════════════════════════════════════════
#  VOLUME PROFILE COMPUTATION
# ══════════════════════════════════════════════════════════════════════════════

def _df_key(df):
    return (len(df), str(df["Close"].iloc[-1]) if len(df) else "0", str(df.index[-1]) if len(df) else "0")


@st.cache_data(ttl=300, show_spinner=False)
def _compute_volume_profile_cached(df_key, _df, bins=40):
    return _compute_volume_profile_inner(_df, bins)


def _compute_volume_profile(df, bins=40):
    return _compute_volume_profile_cached(_df_key(df), df, bins)


def _compute_volume_profile_inner(df, bins=40):
    hi_all = float(df["High"].max())
    lo_all = float(df["Low"].min())
    if hi_all <= lo_all:
        return None

    price_range = hi_all - lo_all
    bin_size    = price_range / bins
    edges       = [lo_all + i * bin_size for i in range(bins + 1)]
    mids        = [(edges[i] + edges[i + 1]) / 2 for i in range(bins)]
    vols        = [0.0] * bins

    for _, row in df.iterrows():
        bar_lo  = float(row["Low"])
        bar_hi  = float(row["High"])
        bar_vol = float(row.get("Volume", 0) or 0)
        if bar_vol <= 0 or bar_hi <= bar_lo:
            continue
        for b in range(bins):
            overlap_lo = max(bar_lo, edges[b])
            overlap_hi = min(bar_hi, edges[b + 1])
            if overlap_hi > overlap_lo:
                vols[b] += bar_vol * (overlap_hi - overlap_lo) / (bar_hi - bar_lo)

    total_vol = sum(vols)
    if total_vol == 0:
        return None

    poc_idx = int(np.argmax(vols))
    poc     = mids[poc_idx]

    # Value Area — 70% of total volume centred on POC
    va_target = total_vol * 0.70
    va_vol    = vols[poc_idx]
    lo_idx    = poc_idx
    hi_idx    = poc_idx
    while va_vol < va_target:
        expand_up   = vols[hi_idx + 1] if hi_idx + 1 < bins else 0
        expand_down = vols[lo_idx - 1] if lo_idx - 1 >= 0  else 0
        if expand_up >= expand_down and hi_idx + 1 < bins:
            hi_idx += 1
            va_vol += vols[hi_idx]
        elif lo_idx - 1 >= 0:
            lo_idx -= 1
            va_vol += vols[lo_idx]
        else:
            break

    vah = mids[hi_idx]
    val = mids[lo_idx]

    vol_arr    = np.array(vols)
    nonzero    = vol_arr[vol_arr > 0]
    hvn_thresh = float(np.percentile(nonzero, 80)) if len(nonzero) else 0
    lvn_thresh = float(np.percentile(nonzero, 20)) if len(nonzero) else 0
    hvns = [mids[i] for i in range(bins) if vols[i] >= hvn_thresh]
    lvns = [mids[i] for i in range(bins) if 0 < vols[i] <= lvn_thresh]

    vwap = float(
        (df["Close"] * df["Volume"]).sum() / df["Volume"].sum()
    ) if "Volume" in df.columns and df["Volume"].sum() > 0 else float(df["Close"].mean())

    return dict(poc=poc, vah=vah, val=val, hvns=hvns, lvns=lvns,
                vwap=vwap, mids=mids, vols=vols,
                total=total_vol, bin_size=bin_size, hi=hi_all, lo=lo_all)


# ══════════════════════════════════════════════════════════════════════════════
#  SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def _vp_signal(vp, current_price, df):
    poc  = vp["poc"];  vah = vp["vah"];  val = vp["val"];  vwap = vp["vwap"]
    cp   = current_price

    h, l, c = df["High"], df["Low"], df["Close"]
    tr  = pd.concat([(h - l), (h - c.shift(1)).abs(), (l - c.shift(1)).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14, min_periods=1).mean().iloc[-1])
    if not np.isfinite(atr) or atr <= 0:
        atr = float((h - l).mean())

    recent_vol = float(df["Volume"].iloc[-3:].mean()) if "Volume" in df.columns else 1
    avg_vol    = float(df["Volume"].iloc[-20:].mean()) if "Volume" in df.columns else 1
    low_vol    = recent_vol < avg_vol * 0.85
    last_bull  = float(df["Close"].iloc[-1]) > float(df["Open"].iloc[-1]) if "Open" in df.columns else True

    score   = 0
    reasons = []
    zone    = ""

    near_val  = abs(cp - val) / max(val,  0.01) < 0.025
    near_poc  = abs(cp - poc) / max(poc,  0.01) < 0.025
    near_vah  = abs(cp - vah) / max(vah,  0.01) < 0.025
    above_poc = cp > poc
    above_vah = cp > vah
    below_val = cp < val
    in_va     = val <= cp <= vah

    # Zone base score
    if above_vah:
        zone = "Above VAH — Breakout Continuation Zone"
        reasons.append(f"Price ({cp:.2f}) is above VAH ({vah:.2f}) — breakout above value area, momentum is strong")
        score += 30
    elif near_vah:
        zone = "VAH — Testing Upper Boundary"
        reasons.append(f"Price ({cp:.2f}) at VAH ({vah:.2f}) — testing upper boundary, breakout potential if held")
        score += 25
    elif near_poc:
        zone = "POC — Point of Control"
        reasons.append(f"Price ({cp:.2f}) at POC ({poc:.2f}) — max-volume decision level, strong directional edge")
        score += 45
    elif near_val:
        zone = "VAL — Value Area Low (Demand)"
        reasons.append(f"Price ({cp:.2f}) at VAL ({val:.2f}) — historically strong demand zone, buyers defend this level")
        score += 50
    elif below_val:
        zone = "Below VAL — Discounted vs Fair Value"
        reasons.append(f"Price ({cp:.2f}) below VAL ({val:.2f}) — trading below fair value, potential accumulation zone")
        score += 35
    elif above_poc and in_va:
        zone = "Upper Value Area — Bullish Bias"
        reasons.append(f"Price between POC ({poc:.2f}) and VAH ({vah:.2f}) — inside value, buyers in structural control")
        score += 35
    else:
        zone = "Lower Value Area — Near Demand"
        reasons.append(f"Price between VAL ({val:.2f}) and POC ({poc:.2f}) — accumulation zone, demand building")
        score += 40

    # VWAP confirmation
    if cp > vwap:
        score += 10
        reasons.append(f"Price ({cp:.2f}) above VWAP ({vwap:.2f}) — bullish session bias confirmed")
    else:
        reasons.append(f"Price ({cp:.2f}) below VWAP ({vwap:.2f}) — waiting for price to reclaim fair value")

    # Volume context
    if low_vol:
        score += 10
        reasons.append("Recent volume below average — low-vol pullback is a classic high R:R entry condition")

    # Candle direction
    if last_bull:
        score += 10
        reasons.append("Last candle closed bullish — short-term momentum confirms active buyers")
    else:
        reasons.append("Last candle closed neutral — waiting for bullish confirmation candle")

    # LVN context
    lvns_above = [v for v in vp["lvns"] if v > cp]
    if lvns_above and abs(cp - min(lvns_above)) / max(cp, 0.01) < 0.02:
        score += 5
        reasons.append(f"LVN at {min(lvns_above):.2f} just above — thin volume zone, price can accelerate upward quickly")

    # Ensure score stays in 0-100
    score = max(0, min(100, score))

    # Signal determination
    if above_vah and last_bull and cp > vwap:
        signal = "BUY"
    elif score >= 50 and not near_vah:
        signal = "BUY"
    elif score >= 30:
        signal = "WATCH"
    else:
        signal = "NO TRADE"

    # Trade levels — targets ALWAYS above current price
    entry = cp
    stop  = max(val - atr * 0.5, cp - atr * 2.0) if not below_val else cp - atr * 1.5

    # Build targets that are always above entry
    _targets = sorted(set([
        p for p in [poc, vah, vah + (vah - poc), vah + atr * 2, cp + atr * 1.5, cp + atr * 3]
        if p > cp
    ]))
    if len(_targets) >= 2:
        t1 = _targets[0]
        t2 = _targets[1]
    elif len(_targets) == 1:
        t1 = _targets[0]
        t2 = t1 + atr * 1.5
    else:
        t1 = cp + atr * 1.5
        t2 = cp + atr * 3.0

    risk = abs(entry - stop)
    rr1  = round(abs(t1 - entry) / risk, 2) if risk > 0 else 0
    rr2  = round(abs(t2 - entry) / risk, 2) if risk > 0 else 0

    return dict(signal=signal, score=score, zone=zone,
                entry=entry, stop=stop, t1=t1, t2=t2,
                rr1=rr1, rr2=rr2, atr=atr, vwap=vwap, reasons=reasons)


# ══════════════════════════════════════════════════════════════════════════════
#  CHART
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def _build_vp_chart_cached(df_key, _df, _vp, _sig, current_price, tail=90):
    """Cached wrapper around _build_vp_chart (light theme)."""
    return _build_vp_chart(_df, _vp, _sig, current_price, tail)


def _build_vp_chart(df, vp, sig, current_price, tail=90):
    sub = df.tail(tail).copy()
    sub["Date"] = pd.to_datetime(sub["Date"])
    xh = list(sub["Date"])

    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.78, 0.22],
        shared_yaxes=True,
        horizontal_spacing=0.008,
    )

    if all(col in df.columns for col in ["Open", "High", "Low"]):
        fig.add_trace(go.Candlestick(
            x=xh,
            open=sub["Open"].values, high=sub["High"].values,
            low=sub["Low"].values,   close=sub["Close"].values,
            name="OHLC",
            increasing_line_color=UP, decreasing_line_color=DOWN,
            increasing_fillcolor=UP,
            decreasing_fillcolor=DOWN,
            line_width=1,
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=xh, y=list(sub["Close"].values),
            mode="lines", name="Price",
            line=dict(color=INFO, width=1.8),
        ), row=1, col=1)

    if "EMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=xh, y=list(df["EMA_20"].values[-tail:]),
            mode="lines", name="EMA 20",
            line=dict(color=BLUE, width=1.3, dash="dot"),
        ), row=1, col=1)

    poc, vah, val, vwap = vp["poc"], vp["vah"], vp["val"], vp["vwap"]
    # Volume levels labelled on the right, trade levels on the left so close
    # levels (e.g. POC vs VWAP, VAL vs SL) don't print on top of each other.
    _lbl_bg = "rgba(255,255,255,0.85)"
    for level, color, label, dash, pos in [
        (poc,  POCC,      f"POC {poc:.2f}",   "solid", "top right"),
        (vah,  BEAR,      f"VAH {vah:.2f}",   "dash",  "top right"),
        (val,  BULL,      f"VAL {val:.2f}",   "dash",  "top right"),
        (vwap, PURP,      f"VWAP {vwap:.2f}", "dot",   "bottom right"),
    ]:
        fig.add_hline(y=level, line_dash=dash, line_color=color, line_width=1.4,
                      opacity=0.85, annotation_text=label,
                      annotation_position=pos, annotation_bgcolor=_lbl_bg,
                      annotation_font_color=color, annotation_font_size=11,
                      row=1, col=1)

    if sig["signal"] in ("BUY", "WATCH"):
        fig.add_hline(y=sig["stop"], line_dash="dash", line_color=BEAR,
                      line_width=1, opacity=0.7,
                      annotation_text=f"SL {sig['stop']:.2f}",
                      annotation_position="bottom left", annotation_bgcolor=_lbl_bg,
                      annotation_font_color=BEAR, annotation_font_size=11, row=1, col=1)
        fig.add_hline(y=sig["t1"], line_dash="dot", line_color=BULL,
                      line_width=1, opacity=0.7,
                      annotation_text=f"T1 {sig['t1']:.2f}",
                      annotation_position="top left", annotation_bgcolor=_lbl_bg,
                      annotation_font_color=BULL, annotation_font_size=11, row=1, col=1)
        fig.add_hline(y=sig["t2"], line_dash="dashdot", line_color=BULL,
                      line_width=1, opacity=0.7,
                      annotation_text=f"T2 {sig['t2']:.2f}",
                      annotation_position="top left", annotation_bgcolor=_lbl_bg,
                      annotation_font_color=BULL, annotation_font_size=11, row=1, col=1)

    fig.add_hrect(y0=val, y1=vah, fillcolor=rgba(BLUE, 0.06),
                  line_width=0, row=1, col=1)

    mids    = vp["mids"]
    vols_l  = vp["vols"]
    max_v   = max(vols_l) if vols_l else 1
    vol_arr = np.array(vols_l)
    nonzero = vol_arr[vol_arr > 0]
    p80 = float(np.percentile(nonzero, 80)) if len(nonzero) else 0
    p20 = float(np.percentile(nonzero, 20)) if len(nonzero) else 0

    bar_colors = []
    for i, m in enumerate(mids):
        if abs(m - poc) < vp["bin_size"] / 2:
            bar_colors.append(POCC)
        elif val <= m <= vah:
            bar_colors.append(rgba(BLUE, 0.42))
        elif vols_l[i] >= p80:
            bar_colors.append(rgba(GREEN, 0.45))
        elif vols_l[i] <= p20 and vols_l[i] > 0:
            bar_colors.append(rgba(RED, 0.30))
        else:
            bar_colors.append(rgba("#8A8A91", 0.30))

    fig.add_trace(go.Bar(
        x=[v / max_v for v in vols_l], y=mids,
        orientation="h", name="Vol by Price",
        marker_color=bar_colors, showlegend=False,
        hovertemplate="Price: %{y:.2f}<br>Vol: %{customdata:,.0f}<extra></extra>",
        customdata=vols_l,
    ), row=1, col=2)

    fig.update_layout(
        height=520, margin=dict(t=10, b=10, l=8, r=12),
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=dict(color=T2, family="Inter, -apple-system, system-ui, sans-serif", size=12),
        hovermode="y unified",
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor=HAIR, borderwidth=1,
                    font=dict(size=11, color=T2), x=0.01, y=0.99,
                    orientation="h", yanchor="top"),
        xaxis_rangeslider_visible=False,
    )
    for ci in [1, 2]:
        fig.update_xaxes(gridcolor=GRID, showgrid=True, zeroline=False, row=1, col=ci)
        fig.update_yaxes(gridcolor=GRID, showgrid=True, zeroline=False, row=1, col=ci)
    fig.update_xaxes(showticklabels=False, row=1, col=2)
    for ann in (fig.layout.annotations or []):
        if hasattr(ann, "font"):
            ann.font.size = 11
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TAB
# ══════════════════════════════════════════════════════════════════════════════

def volume_profile_tab(df, current_price):
    global BG, BG2, BDR
    theme = st.session_state.get("theme_palette", {})
    BG  = theme.get("panel",     BG)
    BG2 = theme.get("panel_alt", BG2)
    BDR = theme.get("border",    BDR)

    if len(df) < 30:
        st.warning("Need at least 30 bars for Volume Profile.")
        return
    if "Volume" not in df.columns or df["Volume"].sum() == 0:
        st.warning("No volume data available for this symbol.")
        return

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])

    vp = _compute_volume_profile(df, bins=40)
    if vp is None:
        st.error("Volume Profile calculation failed.")
        return

    sig = _vp_signal(vp, current_price, df)
    poc = vp["poc"];  vah = vp["vah"];  val = vp["val"];  vwap = vp["vwap"]

    # ── DECISION BOX ─────────────────────────────────────────────────────────
    _vp_verdict = sig["signal"]  # "BUY", "WATCH", or "NO TRADE"
    _vp_vc      = BULL if _vp_verdict == "BUY" else (NEUT if _vp_verdict == "WATCH" else T3)
    _vp_vbg     = GREEN_BG if _vp_verdict == "BUY" else (AMBER_BG if _vp_verdict == "WATCH" else GREY_BG)
    _vp_conf    = sig.get("score", 0)
    _vp_sub     = sig.get("zone", "")
    _vp_reasons = (sig.get("reasons") or [])[:3]
    _vp_reasons_html = "".join(
        f"<div style='display:flex;align-items:flex-start;gap:0.6rem;padding:0.55rem 0;"
        f"{'border-top:1px solid ' + HAIR + ';' if _i else ''}'>"
        f"<span style='width:6px;height:6px;border-radius:50%;background:{_vp_vc};"
        f"flex-shrink:0;margin-top:0.5rem;'></span>"
        f"<span style='font-size:0.9rem;color:{T2};line-height:1.55;'>{_r}</span></div>"
        for _i, _r in enumerate(_vp_reasons)
    )
    _vp_ladder = ""
    if sig["signal"] in ("BUY", "WATCH"):
        try:
            from _levels import price_ladder_html as _vp_plh
            _vp_stop = sig.get("stop", current_price * 0.97)
            _vp_t1   = sig.get("t1",   current_price * 1.05)
            _vp_t2   = sig.get("t2",   current_price * 1.09)
            _vp_R    = abs(current_price - _vp_stop)
            _vp_t3   = round(current_price + 5.0 * _vp_R, 2)
            _vp_ladder = _vp_plh(current_price, _vp_stop, _vp_t1, _vp_t2, _vp_t3, True)
        except Exception:
            pass

    # ── Tooltip CSS + helper ──────────────────────────────────────────────────
    st.markdown(f"""<style>
    .vp-tip-w{{position:relative;display:inline-flex;align-items:center;cursor:help;margin-left:0.35rem}}
    .vp-tip-w .vp-tt{{visibility:hidden;opacity:0;position:absolute;bottom:135%;left:50%;
        transform:translateX(-50%);background:{CARD};color:{T2};border:1px solid {HAIR};
        border-radius:12px;padding:0.65rem 0.8rem;font-size:0.8rem;font-weight:500;
        line-height:1.5;white-space:normal;width:250px;text-align:left;z-index:200;
        pointer-events:none;transition:opacity .15s;box-shadow:{SHADOW};
        text-transform:none;letter-spacing:0}}
    .vp-tip-w .vp-tt::after{{content:'';position:absolute;top:100%;left:50%;
        transform:translateX(-50%);border:6px solid transparent;border-top-color:{HAIR}}}
    .vp-tip-w:hover .vp-tt{{visibility:visible;opacity:1}}
    </style>""", unsafe_allow_html=True)

    def _vptip(text):
        return (
            f"<span class='vp-tip-w'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:17px;height:17px;border-radius:50%;border:1px solid {HAIR2};"
            f"font-size:0.75rem;line-height:1;color:{T3};font-weight:600;'>?</span>"
            f"<span class='vp-tt'>{text}</span></span>"
        )

    _vp_metric_tooltips = {
        "VAL — Demand Floor":   "Value Area Low — the bottom of the zone where 70% of volume traded. Price at or below VAL is in the 'discount zone' — institutions often step in here to buy.",
        "POC — Max Volume":     "Point of Control — the single price where the most volume traded in the entire session. Acts like a magnet — price gravitates back to POC when it strays far.",
        "VAH — Supply Ceiling": "Value Area High — the top of the 70% volume zone. Price at or above VAH is in the 'premium zone' — sellers tend to show up here.",
        "VWAP — Fair Value":    "Volume-Weighted Average Price — the average price weighted by volume. Big institutions use this as their benchmark. Above VWAP = buyers in control. Below = sellers.",
    }

    _vp_metrics_html = "".join([
        f"<div style='background:{INSET};border:1px solid {HAIR};border-radius:14px;"
        f"padding:0.95rem 1.1rem;min-width:0;'>"
        f"<div style='display:flex;align-items:center;margin-bottom:0.45rem;'>"
        f"<span style='width:8px;height:8px;border-radius:50%;background:{_mc};"
        f"flex-shrink:0;margin-right:0.45rem;'></span>"
        f"<div style='font-size:0.82rem;color:{T3};font-weight:600;'>{_mn}</div>"
        + _vptip(_vp_metric_tooltips.get(_mn, ""))
        + f"</div>"
        f"<div style='font-size:1.45rem;font-weight:700;color:{T1};line-height:1.15;{_NUM}'>{_mv:.2f}</div>"
        f"<div style='font-size:0.82rem;color:{T3};margin-top:0.25rem;{_NUM}'>{_ms}</div>"
        f"</div>"
        for _mn, _mv, _mc, _ms in [
            ("VAL — Demand Floor",   val,  BULL,      f"{(val  / current_price - 1)*100:+.2f}% from price"),
            ("POC — Max Volume",     poc,  POCC,      f"{(poc  / current_price - 1)*100:+.2f}% from price"),
            ("VAH — Supply Ceiling", vah,  BEAR,      f"{(vah  / current_price - 1)*100:+.2f}% from price"),
            ("VWAP — Fair Value",    vwap, PURP,      f"{(vwap / current_price - 1)*100:+.2f}% from price"),
        ]
    ])

    st.markdown(
        f"<div style='background:{CARD};border:1px solid {HAIR};border-radius:18px;"
        f"box-shadow:{SHADOW};margin-bottom:1.4rem;'>"
        f"<div style='padding:1.4rem 1.6rem 1.1rem;'>"
        f"<div style='font-size:0.85rem;color:{T3};font-weight:600;margin-bottom:0.6rem;'>"
        f"Volume profile decision</div>"
        f"<div style='display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap;'>"
        f"<div style='font-size:2.3rem;font-weight:700;color:{_vp_vc};"
        f"line-height:1;letter-spacing:-0.02em;'>{_vp_verdict}</div>"
        f"<div style='flex:1;min-width:200px;'>"
        f"<span style='display:inline-block;font-size:0.88rem;font-weight:600;color:{_vp_vc};"
        f"background:{_vp_vbg};border-radius:980px;padding:0.3rem 0.8rem;line-height:1.4;'>{_vp_sub}</span>"
        f"</div>"
        f"<div style='text-align:center;background:{INSET};border:1px solid {HAIR};"
        f"border-radius:14px;padding:0.7rem 1.2rem;flex-shrink:0;'>"
        f"<div style='font-size:1.6rem;font-weight:700;color:{T1};line-height:1;{_NUM}'>{_vp_conf}"
        f"<span style='font-size:0.85rem;font-weight:600;color:{T3};'>/100</span></div>"
        f"<div style='display:flex;align-items:center;justify-content:center;gap:0.1rem;margin-top:0.3rem;'>"
        f"<div style='font-size:0.8rem;color:{T3};font-weight:600;'>Score</div>"
        + _vptip("Volume Profile confidence score (0–100). Based on how clearly price is positioned relative to VAL, POC, VAH, and VWAP. Above 65 = strong setup. Below 40 = no clear volume edge.")
        + f"</div></div></div>"
        + (f"<div style='margin-top:1rem;'>{_vp_reasons_html}</div>" if _vp_reasons_html else "")
        + f"</div>"
        f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.8rem;"
        f"padding:0 1.6rem 1.4rem;'>"
        + _vp_metrics_html +
        f"</div>"
        + (f"<div style='padding:0 1.6rem 0.75rem;'>{_vp_ladder}</div>" if _vp_ladder else "")
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ── Educational Insight Toggle ──
    insight_toggle(
        "vp_what_is",
        "What is Volume Profile?",
        f"<h4 style='margin:0 0 0.6rem 0;color:{T1};font-size:1rem;font-weight:600;'>Volume Profile — Where the Real Money Trades</h4>"
        "<p>Most charts show you <em>when</em> people traded. Volume Profile flips that — it shows you "
        "<strong>at which price</strong> the most trading happened. Think of it like a heat map on the Y-axis: "
        "the wider the bar, the more money changed hands at that price.</p>"

        "<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:0.7rem;margin:0.8rem 0;'>"

        f"<div style='background:{AMBER_BG};border:1px solid {rgba(AMBER, 0.18)};border-radius:12px;padding:0.8rem 0.95rem;'>"
        f"<div style='font-size:0.9rem;font-weight:600;color:{AMBER};'>POC (Point of Control)</div>"
        f"<div style='font-size:0.85rem;color:{T2};line-height:1.55;margin-top:0.25rem;'>"
        "The single price with the highest traded volume. The market keeps coming back to this price "
        "like a magnet — it's where buyers and sellers agreed the most.</div></div>"

        f"<div style='background:{PURPLE_BG};border:1px solid {rgba(PURPLE, 0.18)};border-radius:12px;padding:0.8rem 0.95rem;'>"
        f"<div style='font-size:0.9rem;font-weight:600;color:{PURPLE};'>VWAP (Volume-Weighted Avg)</div>"
        f"<div style='font-size:0.85rem;color:{T2};line-height:1.55;margin-top:0.25rem;'>"
        "The average price weighted by how much was traded at each level. "
        "Big institutions use VWAP as their benchmark — above VWAP means buyers are winning, below means sellers.</div></div>"

        f"<div style='background:{GREEN_BG};border:1px solid {rgba(GREEN, 0.18)};border-radius:12px;padding:0.8rem 0.95rem;'>"
        f"<div style='font-size:0.9rem;font-weight:600;color:{GREEN};'>VAL (Value Area Low)</div>"
        f"<div style='font-size:0.85rem;color:{T2};line-height:1.55;margin-top:0.25rem;'>"
        "The bottom of the zone where 70% of all trading happened. "
        "When price drops to VAL, smart money often steps in to buy — it's the discount zone.</div></div>"

        f"<div style='background:{RED_BG};border:1px solid {rgba(RED, 0.16)};border-radius:12px;padding:0.8rem 0.95rem;'>"
        f"<div style='font-size:0.9rem;font-weight:600;color:{RED};'>VAH (Value Area High)</div>"
        f"<div style='font-size:0.85rem;color:{T2};line-height:1.55;margin-top:0.25rem;'>"
        "The top of the 70% volume zone. When price rises to VAH, sellers often show up — "
        "it's the premium zone where things get expensive.</div></div>"

        "</div>"

        f"<p style='margin-top:0.5rem;'><strong style='color:{BLUE};'>How to read the signal:</strong></p>"
        "<ul style='margin:0;padding-left:1.2rem;'>"
        "<li>Price <strong>below VAL</strong> with rising volume → potential bounce (BUY zone)</li>"
        "<li>Price <strong>near POC</strong> → market is balanced, expect sideways action</li>"
        "<li>Price <strong>above VAH</strong> → stretched into premium, watch for pullback</li>"
        "<li><strong>HVN</strong> (High Volume Node) = strong support/resistance — price stalls here</li>"
        "<li><strong>LVN</strong> (Low Volume Node) = thin air — price moves fast through these gaps</li>"
        "</ul>"
    )

    # ══ KEY PRICE LEVELS — Volume Based ═════════════════════════════════════
    st.markdown(_sec("Key price levels — volume based", PURP,
                     "Where the most volume traded, relative to the current price"),
                unsafe_allow_html=True)
    insight_toggle(
        "vp_levels",
        "What are POC, VAH, and VAL?",
        "<p><strong>Point of Control (POC)</strong> &mdash; The exact price where the most volume was traded. "
        "This is the market's 'fair value' anchor. Price tends to return here when it drifts away.</p>"
        "<p><strong>Value Area High (VAH)</strong> &mdash; The upper boundary of the price range that contained 70% of all trading volume. "
        "Acting as resistance: price above VAH is trading in 'premium' territory.</p>"
        "<p><strong>Value Area Low (VAL)</strong> &mdash; The lower boundary of the 70% value area. "
        "Acting as support: price below VAL is trading in 'discount' territory and often attracts buyers.</p>"
        "<p>When price is <strong>inside the Value Area</strong>, there is high acceptance &mdash; price may range. "
        "When price breaks <strong>outside</strong>, it often moves fast until it finds a new value area.</p>"
    )
    
    hvns_above = sorted([v for v in vp["hvns"] if v > current_price])
    hvns_below = sorted([v for v in vp["hvns"] if v < current_price], reverse=True)
    lvns_above = sorted([v for v in vp["lvns"] if v > current_price])
    lvns_below = sorted([v for v in vp["lvns"] if v < current_price], reverse=True)

    level_data = [
        ("HVN above",  hvns_above[0] if hvns_above else None, BEAR,      "Strong resistance"),
        ("VAH",        vah,                                    BEAR,      "Supply ceiling"),
        ("POC",        poc,                                    POCC,      "Max volume"),
        ("Current",    current_price,                          INFO,      "—"),
        ("VAL",        val,                                    BULL,      "Demand floor"),
        ("HVN below",  hvns_below[0] if hvns_below else None,  BULL,      "Strong support"),
    ]

    _lvl_card = (f"background:{CARD};border:1px solid {HAIR};border-radius:16px;"
                 f"box-shadow:{SHADOW};padding:1.1rem 0.9rem;text-align:center;min-height:8.9rem;"
                 f"box-sizing:border-box;")
    cols = st.columns(len(level_data), gap="small")
    for col, (label, price, color, desc) in zip(cols, level_data):
        _lbl_html = (
            f"<div style='display:flex;align-items:center;justify-content:center;gap:0.4rem;"
            f"margin-bottom:0.5rem;'>"
            f"<span style='width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;'></span>"
            f"<span style='font-size:0.82rem;color:{T3};font-weight:600;'>{label}</span></div>"
        )
        with col:
            if price is None:
                st.markdown(
                    f"<div style='{_lvl_card}'>"
                    + _lbl_html +
                    f"<div style='font-size:1.4rem;font-weight:700;color:{T4};line-height:1.15;'>—</div>"
                    f"<div style='font-size:0.8rem;color:{T3};margin-top:0.3rem;'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                dist = f"{(price / current_price - 1)*100:+.2f}%"
                st.markdown(
                    f"<div style='{_lvl_card}'>"
                    + _lbl_html +
                    f"<div style='font-size:1.4rem;font-weight:700;color:{T1};line-height:1.15;{_NUM}'>${price:.2f}</div>"
                    f"<div style='font-size:0.85rem;font-weight:600;color:{T2};margin-top:0.3rem;{_NUM}'>{dist}</div>"
                    f"<div style='font-size:0.8rem;color:{T3};margin-top:0.15rem;'>{desc}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if lvns_above and abs(lvns_above[0] - current_price) / max(current_price, 1) < 0.03:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {HAIR};"
            f"border-radius:14px;margin-top:0.8rem;padding:0.85rem 1.1rem;"
            f"font-size:0.88rem;color:{T2};line-height:1.5;'>"
            f"<span style='color:{BULL};font-weight:600;'>LVN just above ({lvns_above[0]:.2f}): </span>"
            f"Thin volume zone — price can accelerate upward quickly through this level.</div>",
            unsafe_allow_html=True,
        )
    if lvns_below and abs(lvns_below[0] - current_price) / max(current_price, 1) < 0.03:
        st.markdown(
            f"<div style='background:{CARD};border:1px solid {HAIR};"
            f"border-radius:14px;margin-top:0.8rem;padding:0.85rem 1.1rem;"
            f"font-size:0.88rem;color:{T2};line-height:1.5;'>"
            f"<span style='color:{INFO};font-weight:600;'>Support zone ({lvns_below[0]:.2f}): </span>"
            f"Low-volume node below — monitor this level as a key support reference.</div>",
            unsafe_allow_html=True,
        )

    # ══ 4. CHART ══════════════════════════════════════════════════════════════
    st.markdown(_sec("Volume profile chart", INFO,
                     "Last 90 bars with volume traded at each price on the right"),
                unsafe_allow_html=True)
    insight_toggle(
        "vp_chart",
        "How to read the Volume Profile chart?",
        "<p>The horizontal bars show how much volume was traded at each price level. "
        "<strong>Tall bars</strong> = high-acceptance zones where buyers and sellers agreed heavily on price.</p>"
        "<p><strong>Short bars</strong> = low-volume nodes (LVNs) where price moved quickly and held briefly. "
        "These are often where price accelerates through in the future.</p>"
        f"<p>The <strong style='color:{POCC}'>orange line</strong> marks the Point of Control (POC). "
        "Price above the POC tends to be bullish; below is bearish. "
        "Breakouts from the Value Area with volume confirmation are the highest-conviction setups.</p>"
    )
    fig = _build_vp_chart_cached(_df_key(df), df, vp, sig, current_price, tail=90)
    style_fig(fig)
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False}, theme=None)

    st.markdown(
        f"<div style='display:flex;gap:0.6rem 1.4rem;flex-wrap:wrap;align-items:center;"
        f"padding:0.8rem 1.1rem;background:{CARD};border:1px solid {HAIR};"
        f"border-radius:14px;margin-bottom:0.5rem;'>"
        + "".join([
            f"<span style='display:inline-flex;align-items:center;gap:0.45rem;"
            f"font-size:0.82rem;color:{T2};font-weight:500;'>"
            f"<span style='width:16px;height:4px;border-radius:2px;background:{lc};flex-shrink:0;'></span>"
            f"{lt}</span>"
            for lc, lt in [
                (POCC,      "POC"),
                (BULL,      "VAL"),
                (BEAR,      "VAH"),
                (PURP,      "VWAP"),
                (rgba(BLUE, 0.55), "Value Area (70% vol)"),
                (rgba(GREEN, 0.55), "HVN — strong support/resistance"),
                (rgba(RED, 0.45),   "LVN — thin air, fast move zone"),
            ]
        ]) +
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='font-size:0.85rem;color:{T3};margin-top:1.5rem;line-height:1.5;"
        f"padding:0.85rem 1.1rem;background:{INSET};border-radius:14px;border:1px solid {HAIR};'>"
        f"Volume Profile is computed from the full selected date range. "
        f"POC, VAH, and VAL shift as new data is added. Not financial advice."
        f"</div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
#  PUBLIC GETTER — called from Decision Tab
# ══════════════════════════════════════════════════════════════════════════════

def get_vp_signal(df, cp):
    """Return a BUY signal dict for the Decision Tab, or None if no trade."""
    if df is None or len(df) < 30:
        return None
    if "Volume" not in df.columns or df["Volume"].sum() == 0:
        return None
    try:
        df = df.copy()
        if "Date" not in df.columns:
            df = df.reset_index()
        df["Date"] = pd.to_datetime(df["Date"])
        vp = _compute_volume_profile(df, bins=40)
        if vp is None:
            return None
        sig = _vp_signal(vp, float(cp), df)
        if sig["signal"] != "BUY":
            return None
        _risk = max(abs(float(cp) - sig["stop"]), 0.001)
        _t3   = round(float(cp) + _risk * 4.236, 2)
        return dict(
            color=BULL,
            verdict_text="▲ BUY",
            sublabel=sig["zone"],
            conf=sig["score"],
            reasons=sig["reasons"][:3],
            entry=float(cp),
            stop=round(sig["stop"], 2),
            t1=round(sig["t1"], 2),
            t2=round(sig["t2"], 2),
            t3=_t3,
        )
    except Exception:
        return None
