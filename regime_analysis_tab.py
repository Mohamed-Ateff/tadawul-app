import streamlit as st
import plotly.graph_objects as go
from ui_helpers import insight_toggle
from apple_theme import (
    T1, T2, T3, T4, CARD, INSET, FILL, HAIR, SHADOW,
    GREEN, RED, BLUE, AMBER, ORANGE, PURPLE,
    REGIME_COLORS, REGIME_BG, style_fig,
)

BULL = GREEN
BEAR = RED
NEUT = AMBER
INFO = BLUE
PURP = PURPLE
BG   = CARD
BG2  = INSET
BDR  = HAIR


def _sec(title, sub="", color=INFO):
    return (
        f"<div class='ap-section' style='display:block;margin:2.2rem 0 0.9rem;'>"
        f"<div class='ap-section-title' style='font-size:1.25rem;font-weight:700;color:{T1};"
        f"letter-spacing:-0.015em;'>{title}</div>"
        + (f"<div class='ap-section-sub' style='font-size:0.88rem;color:{T3};margin-top:0.15rem;'>{sub}</div>"
           if sub else "")
        + "</div>"
    )


def _glowbar(pct, color=BULL, height="6px"):
    pct = max(0, min(100, float(pct)))
    return (
        f"<div style='background:{FILL};border-radius:999px;height:{height};overflow:hidden;'>"
        f"<div style='width:{pct}%;height:100%;background:{color};border-radius:999px;'></div></div>"
    )

REGIME_COLOR = dict(REGIME_COLORS)

REGIME_DESC = {
    "TREND":    "Market is making clear directional moves — momentum and trend-following strategies work best. Ride the direction.",
    "RANGE":    "Price is bouncing between a support floor and resistance ceiling — buy the dips, take profit at the top.",
    "VOLATILE": "Price is moving fast and unpredictably — high ATR with no clear direction. Reduce size, widen stops, wait for a clearer setup.",
}

REGIME_STRATEGY = {
    "TREND": [
        ("✅ Follow the trend",       "Enter in the trend direction. Use trailing stops to lock in profits."),
        ("✅ Buy pullbacks to EMA",   "Don’t chase the top. Wait for a dip to the 20 or 50 EMA then buy."),
        ("⚠️ Avoid counter-trades",  "Going against a strong trend has low odds. Wait for reversal confirmation first."),
    ],
    "RANGE": [
        ("✅ Buy at support",          "Enter near the lower bound where price has bounced before."),
        ("✅ Take profit at resistance", "Don’t be greedy — the upper bound is where sellers show up."),
        ("⚠️ Watch out for breakouts", "If price closes strongly above resistance, the range may be ending — that’s a new opportunity."),
    ],
    "VOLATILE": [
        ("⚠️ Cut your position size",  "In volatile markets, losses can be bigger than expected. Trade smaller."),
        ("✅ Widen your stop loss",    "Tight stops will get hit by noise. Give the trade more room, or skip it."),
        ("✅ Wait for a clear setup",  "Volatile regimes often transition to TREND or RANGE. Patience pays."),
        ("⚠️ Avoid breakout entries",  "Breakouts in volatile markets fail often. Wait for a confirmed close above/below the level."),
    ],
}


def _normalize_regime_df(df):
    clean = df.copy()
    regimes = clean["REGIME"].astype("string").str.strip().str.upper()
    regimes = regimes.replace({
        "TRENDING": "TREND",
        "SIDEWAYS": "RANGE",
        "VOLATILITY": "VOLATILE",
    })
    regimes = regimes.where(regimes.isin(REGIME_COLOR.keys()))
    regimes = regimes.ffill().bfill().fillna("RANGE")
    clean["REGIME"] = regimes
    return clean


def _streak(df):
    regime = df["REGIME"].iloc[-1]
    count = 0
    for r in reversed(df["REGIME"].tolist()):
        if r == regime:
            count += 1
        else:
            break
    return count


def _stability(df, window=20):
    regime = df["REGIME"].iloc[-1]
    tail = df["REGIME"].tail(window)
    return round((tail == regime).sum() / len(tail) * 100, 1)


def _momentum(df, days=5):
    if len(df) < days + 1:
        return 0.0
    return (df["Close"].iloc[-1] / df["Close"].iloc[-(days + 1)] - 1) * 100


def _stat_tile(label, value, sub, val_color, bg, border, muted, bar_pct=None, bar_color=None):
    bar_html = ""
    if bar_pct is not None:
        bar_html = (
            f"<div style='margin-top:0.6rem;height:5px;background:{FILL};"
            f"border-radius:999px;overflow:hidden;'>"
            f"<div style='width:{bar_pct:.0f}%;height:100%;background:{bar_color or val_color};"
            f"border-radius:999px;'></div></div>"
        )
    return (
        f"<div style='background:{INSET};border:1px solid {HAIR};"
        f"border-radius:14px;padding:1rem 1.2rem;'>"
        f"<div style='font-size:0.8rem;color:{T3};"
        f"margin-bottom:0.45rem;font-weight:600;'>{label}</div>"
        f"<div style='font-size:1.4rem;font-weight:700;color:{val_color};line-height:1.15;"
        f"letter-spacing:-0.02em;font-variant-numeric:tabular-nums;'>{value}</div>"
        f"<div style='font-size:0.8rem;color:{T3};margin-top:0.3rem;'>{sub}</div>"
        f"{bar_html}"
        f"</div>"
    )


def get_regime_signal(df, cp):
    """Return a signal dict for the Decision Tab aggregator, or None if no trade."""
    if df is None or len(df) < 20:
        return None
    try:
        df = _normalize_regime_df(df)
        latest = df.iloc[-1]
        current_regime = str(latest["REGIME"])
        mom_5d  = _momentum(df, 5)
        mom_20d = _momentum(df, 20)
        adx_val = float(latest.get("ADX_14", 0) or 0)
        ema20   = float(latest.get("EMA_20", float(cp)) or float(cp))
        ema50   = float(latest.get("EMA_50", float(cp)) or float(cp))
        atr_val = float(latest.get("ATR_14", float(cp) * 0.02) or float(cp) * 0.02)
        stability = _stability(df, 20)
        streak    = _streak(df)

        # Score regime favorability for a long trade
        score = 50
        if current_regime == "TREND":
            score += 20 if mom_5d >= 0 else -10
            score += 10 if float(cp) > ema20 else -8
            score += 8  if adx_val >= 25 else (-5 if adx_val < 18 else 0)
        elif current_regime == "RANGE":
            score += 5 if float(cp) > ema20 else -5
            score -= 5 if float(cp) < ema50 else 0
        elif current_regime == "VOLATILE":
            score -= 20

        score += 5 if stability >= 60 else (-5 if stability < 35 else 0)
        score = max(0, min(100, score))

        # Only surface bullish regime setups
        if score < 52:
            return None

        is_buy  = current_regime == "TREND" and mom_5d >= 0 and float(cp) > ema20
        verdict = "▲ BUY" if is_buy else "▶ HOLD"
        reasons = [
            f"Regime: {current_regime} ({streak}d streak, {stability:.0f}% stability)",
            f"5D momentum {'+' if mom_5d >= 0 else ''}{mom_5d:.1f}%, ADX {adx_val:.0f}",
        ]

        _stop = round(float(cp) - 2 * atr_val, 2)
        _risk = max(float(cp) - _stop, 0.001)
        return dict(
            color=GREEN,
            verdict_text=verdict,
            sublabel=f"Regime Analysis — {current_regime}",
            conf=score,
            reasons=reasons,
            entry=float(cp),
            stop=_stop,
            t1=round(float(cp) + _risk * 2.0, 2),
            t2=round(float(cp) + _risk * 3.5, 2),
            t3=round(float(cp) + _risk * 5.5, 2),
        )
    except Exception:
        return None


def render_regime_analysis_tab(df, info_icon, create_regime_distribution_chart):
    df = _normalize_regime_df(df)

    theme_palette  = st.session_state.get('theme_palette', {})
    bg_card = theme_palette.get('panel_alt', BG2)
    bg_plot = theme_palette.get('panel', BG)
    border  = theme_palette.get('border', BDR)
    text    = theme_palette.get('text', T1)
    muted   = theme_palette.get('muted', T3)

    latest         = df.iloc[-1]
    current_price  = latest["Close"]
    current_regime = latest["REGIME"]
    rc             = REGIME_COLOR.get(current_regime, T3)
    rc_bg          = REGIME_BG.get(current_regime, INSET)
    desc           = REGIME_DESC.get(current_regime, "")

    # ── computed metrics ──────────────────────────────────────────────────────
    streak       = _streak(df)
    stability    = _stability(df, 20)
    mom_5d       = _momentum(df, 5)
    mom_20d      = _momentum(df, 20)
    adx_val      = float(latest.get("ADX_14", 0) or 0)
    avg_vol_20   = df.tail(20)["Volume"].mean()
    vol_ratio    = (latest.get("Volume", 0) / avg_vol_20) if avg_vol_20 > 0 else 1.0
    vol_label    = "High" if vol_ratio >= 1.5 else "Low" if vol_ratio < 0.7 else "Normal"
    vol_col      = BULL if vol_ratio >= 1.5 else T3 if vol_ratio < 0.7 else NEUT
    adx_label    = "Strong" if adx_val >= 30 else "Weak" if adx_val < 20 else "Moderate"
    adx_col      = BULL if adx_val >= 30 else BEAR if adx_val < 20 else NEUT
    stability_col= BULL if stability >= 70 else NEUT if stability >= 45 else BEAR
    mom_col_5    = BULL if mom_5d  >= 0 else BEAR
    mom_col_20   = BULL if mom_20d >= 0 else BEAR
    mom_sign_5   = "+" if mom_5d  >= 0 else ""
    mom_sign_20  = "+" if mom_20d >= 0 else ""

    regime_counts = df["REGIME"].value_counts()
    total_days    = len(df)
    trend_days    = regime_counts.get("TREND",    0)
    range_days    = regime_counts.get("RANGE",    0)
    vol_days      = regime_counts.get("VOLATILE", 0)
    trend_pct     = round(trend_days / total_days * 100, 1) if total_days else 0
    range_pct     = round(range_days / total_days * 100, 1) if total_days else 0
    volatile_pct  = round(vol_days   / total_days * 100, 1) if total_days else 0

    # ── DECISION BOX ─────────────────────────────────────────────────────────
    _atr_val = float(latest.get("ATR_14", current_price * 0.02) or current_price * 0.02)
    _ema20   = float(latest.get("EMA_20", current_price) or current_price)
    _ema50   = float(latest.get("EMA_50", current_price) or current_price)

    if current_regime == "TREND" and mom_5d >= 0 and current_price > _ema20:
        _dec_v    = "BUY"
        _dec_col  = BULL
        _dec_sub  = f"Regime is trending up — momentum and structure are aligned. Enter on dips to EMA20."
        _dec_entry = current_price
        _dec_stop  = round(current_price - 2 * _atr_val, 2)
        _dec_t1    = round(current_price + 2 * _atr_val, 2)
        _dec_t2    = round(current_price + 3.5 * _atr_val, 2)
        _dec_t3    = round(current_price + 5.5 * _atr_val, 2)
    elif current_regime == "VOLATILE" or (current_regime == "TREND" and mom_5d < 0):
        _dec_v    = "WAIT"
        _dec_col  = NEUT
        _dec_sub  = f"Volatile or trend reversing — risk is elevated. No new entries until regime stabilises."
        _dec_entry = _dec_stop = _dec_t1 = _dec_t2 = _dec_t3 = None
    else:
        _dec_v    = "HOLD"
        _dec_col  = BLUE
        _dec_sub  = f"Range-bound regime with {stability:.0f}% stability. Wait for a breakout before entering."
        _dec_entry = _dec_stop = _dec_t1 = _dec_t2 = _dec_t3 = None

    _dec_rgb = {"BUY": "27,122,54", "WAIT": "161,92,0", "HOLD": "0,99,209"}.get(_dec_v, "0,99,209")

    _ladder_html = ""
    if _dec_v == "BUY" and _dec_entry:
        try:
            from _levels import price_ladder_html as _reg_plh
            _ladder_html = _reg_plh(_dec_entry, _dec_stop, _dec_t1, _dec_t2, _dec_t3, True)
        except Exception:
            pass

    # ── Tooltip CSS + helper ──────────────────────────────────────────────────
    st.markdown(f"""<style>
    .reg-tip-wrap{{position:relative;display:inline-flex;align-items:center;cursor:help;margin-left:0.35rem}}
    .reg-tip-wrap .reg-tt{{
        visibility:hidden;opacity:0;position:absolute;bottom:135%;left:50%;
        transform:translateX(-50%);background:{CARD};color:{T2};border:1px solid {HAIR};
        border-radius:12px;padding:0.6rem 0.75rem;font-size:0.8rem;font-weight:500;
        line-height:1.5;white-space:normal;width:250px;text-align:left;z-index:200;
        pointer-events:none;transition:opacity .15s;box-shadow:0 8px 24px rgba(17,17,20,0.12);
        text-transform:none;letter-spacing:0}}
    .reg-tip-wrap .reg-tt::after{{content:'';position:absolute;top:100%;left:50%;
        transform:translateX(-50%);border:6px solid transparent;border-top-color:{CARD}}}
    .reg-tip-wrap:hover .reg-tt{{visibility:visible;opacity:1}}
    .reg-metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:0.8rem;
        padding:0 1.75rem 1.5rem;}}
    .reg-metric{{background:{INSET};border:1px solid {HAIR};border-radius:14px;padding:0.95rem 1.1rem;}}
    </style>""", unsafe_allow_html=True)

    def _rtip(text):
        return (
            f"<span class='reg-tip-wrap'>"
            f"<span style='display:inline-flex;align-items:center;justify-content:center;"
            f"width:16px;height:16px;border-radius:50%;border:1px solid {HAIR};background:{CARD};"
            f"font-size:0.7rem;color:{T3};font-weight:600;line-height:1;'>?</span>"
            f"<span class='reg-tt'>{text}</span></span>"
        )

    def _rlbl(text, tooltip=""):
        return (
            f"<div style='display:flex;align-items:center;margin-bottom:0.35rem;'>"
            f"<div style='font-size:0.82rem;color:{T3};font-weight:600;'>{text}</div>"
            + (_rtip(tooltip) if tooltip else "")
            + f"</div>"
        )

    _num = "font-size:1.45rem;font-weight:700;letter-spacing:-0.02em;line-height:1.15;font-variant-numeric:tabular-nums;"
    _msub = f"font-size:0.82rem;color:{T3};margin-top:0.2rem;"

    st.markdown(
        f"<div style='background:{CARD};border:1px solid {HAIR};box-shadow:{SHADOW};"
        f"border-radius:18px;margin-bottom:1.4rem;'>"
        f"<div style='padding:1.5rem 1.75rem 1.4rem;"
        f"display:flex;flex-wrap:wrap;align-items:flex-start;justify-content:space-between;gap:1.5rem;'>"
        f"<div style='min-width:0;flex:1 1 320px;'>"
        f"<div style='font-size:0.85rem;color:{T3};font-weight:600;margin-bottom:0.4rem;'>Decision</div>"
        f"<div style='font-size:2.8rem;font-weight:700;color:{_dec_col};"
        f"letter-spacing:-0.03em;line-height:1;'>{_dec_v}</div>"
        f"<div style='font-size:0.92rem;color:{T2};margin-top:0.6rem;"
        f"font-weight:500;line-height:1.6;max-width:460px;'>{_dec_sub}</div>"
        f"</div>"
        f"<div style='text-align:right;flex:0 1 300px;'>"
        f"<div style='display:flex;align-items:center;justify-content:flex-end;gap:0.3rem;margin-bottom:0.4rem;'>"
        f"<div style='font-size:0.85rem;color:{T3};font-weight:600;'>Regime</div>"
        + _rtip("Market condition detected by combining ADX, EMA direction, and ATR volatility. "
                "TREND = price moving strongly in one direction (ADX above 20, EMA sloping). "
                "RANGE = price bouncing between support and resistance. "
                "VOLATILE = large unpredictable swings — reduce size, wait for clarity.")
        + f"</div>"
        f"<div style='display:inline-block;background:{rc_bg};color:{rc};border-radius:12px;"
        f"padding:0.35rem 0.85rem;font-size:1.6rem;font-weight:700;line-height:1.1;"
        f"letter-spacing:-0.01em;'>{current_regime}</div>"
        f"<div style='font-size:0.85rem;color:{T2};font-weight:600;margin-top:0.45rem;'>{streak}d streak</div>"
        f"<div style='font-size:0.85rem;color:{T3};line-height:1.55;margin-top:0.35rem;"
        f"max-width:300px;margin-left:auto;text-align:right;'>{desc}</div>"
        f"</div>"
        f"</div>"
        f"<div class='reg-metrics'>"
        f"<div class='reg-metric'>"
        + _rlbl("5D momentum",
            "Price change over the last 5 trading days. "
            "Positive = short-term upward momentum. Negative = price is falling. "
            "20D momentum is shown as a secondary reference for the medium-term trend.")
        + f"<div style='{_num}color:{mom_col_5};'>"
        f"{'+' if mom_5d >= 0 else ''}{mom_5d:.1f}%</div>"
        f"<div style='{_msub}'>20D: <span style='color:{mom_col_20};font-weight:600;'>{'+' if mom_20d >= 0 else ''}{mom_20d:.1f}%</span></div>"
        f"</div>"
        f"<div class='reg-metric'>"
        + _rlbl("ADX",
            "Average Directional Index — measures trend strength, not direction. "
            "Above 30 = strong trend in whichever direction. "
            "20–30 = moderate trend. Below 20 = weak or no trend (choppy). "
            "High ADX in TREND regime = strong tailwind for momentum trades.")
        + f"<div style='{_num}color:{adx_col};'>{adx_val:.0f}</div>"
        f"<div style='{_msub}'>{adx_label}</div>"
        f"</div>"
        f"<div class='reg-metric'>"
        + _rlbl("Volume",
            "Today's volume compared to the 20-day average. "
            "High (1.5×+) = strong market participation — confirms the move. "
            "Low (below 0.7×) = thin trading — moves are less reliable and easier to fake. "
            "Normal = average interest.")
        + f"<div style='{_num}color:{vol_col};'>{vol_label}</div>"
        f"<div style='{_msub}'>{vol_ratio:.1f}x avg</div>"
        f"</div>"
        f"<div class='reg-metric'>"
        + _rlbl("Stability",
            "How consistently the stock has been in its current regime over the last 20 sessions. "
            "70%+ = very stable — the regime is well-established. "
            "Below 35% = regime is flickering — mixed signals, be cautious. "
            "A stable TREND regime with high ADX is the ideal setup for momentum trades.")
        + f"<div style='{_num}color:{stability_col};'>{stability:.0f}%</div>"
        f"<div style='{_msub}'>last 20 sessions</div>"
        f"</div>"
        f"</div>"
        + (f"<div style='border-top:1px solid {HAIR};'>{_ladder_html}</div>" if _ladder_html else "")
        + f"</div>",
        unsafe_allow_html=True,
    )

    # ── DISTRIBUTION ──────────────────────────────────────────────────────────
    st.markdown(_sec("Regime distribution", f"How the last {total_days} days split across the three regimes"),
                unsafe_allow_html=True)
    insight_toggle(
        "regime_dist",
        "What are TREND, RANGE, and VOLATILE regimes?",
        "<p><strong>TREND</strong> &mdash; The market is moving strongly in one direction. "
        "Price is above (bullish) or below (bearish) its moving averages, and ADX is above 25. "
        "Trend-following indicators (EMA, MACD) are most reliable in this regime.</p>"
        "<p><strong>RANGE</strong> &mdash; The market is moving sideways between support and resistance. "
        "ADX is below 20, price oscillates without a clear direction. "
        "Mean-reversion indicators (RSI, Stochastic, Bollinger Bands) perform best here.</p>"
        "<p><strong>VOLATILE</strong> &mdash; The market is making large, unpredictable swings in both directions. "
        "High ATR relative to recent history. All trade signals carry higher risk "
        "and tighter risk management (smaller positions, wider stops) is recommended.</p>"
        "<p>The <strong>Regime Distribution</strong> bar shows how the stock spent time in each state over the past period. "
        "A stock that was in TREND 70% of the time is a reliable trend-follower.</p>"
    )
    _dist_rows = ""
    for _i, (label, key, days, pct) in enumerate([
        ("Trend",    "TREND",    trend_days, trend_pct),
        ("Range",    "RANGE",    range_days, range_pct),
        ("Volatile", "VOLATILE", vol_days,   volatile_pct),
    ]):
        color = REGIME_COLOR[key]
        _is_cur = key == current_regime
        _dist_rows += (
            f"<div style='padding:1rem 0;{'border-top:1px solid ' + HAIR + ';' if _i else ''}'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;"
            f"gap:1rem;margin-bottom:0.6rem;'>"
            f"<div style='display:flex;align-items:center;gap:0.55rem;'>"
            f"<span style='width:10px;height:10px;border-radius:50%;background:{color};"
            f"display:inline-block;'></span>"
            f"<span style='font-size:0.98rem;font-weight:600;color:{T1};'>{label}</span>"
            + (f"<span style='font-size:0.76rem;font-weight:600;padding:0.15rem 0.6rem;"
               f"border-radius:980px;background:{REGIME_BG[key]};color:{color};'>Current</span>"
               if _is_cur else "")
            + f"</div>"
            f"<div style='display:flex;align-items:baseline;gap:0.7rem;'>"
            f"<span style='font-size:0.85rem;color:{T3};font-variant-numeric:tabular-nums;'>{days} days</span>"
            f"<span style='font-size:1.25rem;font-weight:700;color:{color};letter-spacing:-0.02em;"
            f"font-variant-numeric:tabular-nums;min-width:4.2rem;text-align:right;'>{pct}%</span>"
            f"</div>"
            f"</div>"
            + _glowbar(pct, color, "8px")
            + f"</div>"
        )
    st.markdown(
        f"<div style='background:{CARD};border:1px solid {HAIR};border-radius:18px;"
        f"box-shadow:{SHADOW};padding:0.35rem 1.5rem;margin-bottom:0.6rem;'>"
        f"{_dist_rows}</div>",
        unsafe_allow_html=True,
    )

    # ── TIMELINE ─────────────────────────────────────────────────────────────
    st.markdown(_sec("Regime timeline", "Last 120 days, one bar per session coloured by regime"),
                unsafe_allow_html=True)
    insight_toggle(
        "regime_timeline",
        "How to read the Regime Timeline?",
        "<p>Each colored block on the timeline represents consecutive days the stock spent in the same regime. "
        f"<strong style='color:{REGIME_COLOR['TREND']}'>Indigo = TREND</strong>, "
        f"<strong style='color:{REGIME_COLOR['RANGE']}'>Teal = RANGE</strong>, "
        f"<strong style='color:{REGIME_COLOR['VOLATILE']}'>Purple = VOLATILE</strong>. "
        "The colour shows the regime only, not the direction — check the price chart for that.</p>"
        "<p>Look for transitions: a shift from RANGE to TREND is often the start of a breakout. "
        "A shift from TREND to VOLATILE may signal exhaustion. "
        "Long runs of a single color indicate a persistent, reliable market condition.</p>"
    )
    timeline_df = df.tail(120).copy()
    fig = go.Figure()
    for regime, color in REGIME_COLOR.items():
        mask = timeline_df["REGIME"] == regime
        fig.add_trace(go.Bar(
            x=timeline_df.loc[mask, "Date"],
            y=[1] * mask.sum(),
            name=regime,
            marker_color=color,
            marker_line_width=0,
            width=86400000,
            hovertemplate=f"<b>{regime}</b><br>%{{x|%b %d %Y}}<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        height=140,
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        font=dict(color=T3, family="Inter, Arial, sans-serif", size=12),
        xaxis=dict(showgrid=False, showline=False, zeroline=False,
                   tickfont=dict(color=T3), tickformat="%b %y"),
        yaxis=dict(visible=False),
        margin=dict(t=36, b=30, l=12, r=12),
        showlegend=True,
        bargap=0,
    )
    style_fig(fig)
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.04,
                    xanchor="right", x=1, font=dict(color=T2, size=12),
                    bgcolor="rgba(0,0,0,0)", borderwidth=0),
    )
    fig.update_xaxes(showgrid=False)
    # Hide non-trading days so the timeline reads as one continuous strip
    try:
        import pandas as _pd
        _dts = _pd.to_datetime(timeline_df["Date"]).dt.normalize()
        if len(_dts) > 1:
            _missing = _pd.date_range(_dts.min(), _dts.max(), freq="D").difference(_dts)
            if len(_missing):
                fig.update_xaxes(rangebreaks=[dict(values=[d.strftime("%Y-%m-%d") for d in _missing])])
    except Exception:
        pass
    st.plotly_chart(fig, width="stretch", theme=None,
                    config={"displayModeBar": False})
