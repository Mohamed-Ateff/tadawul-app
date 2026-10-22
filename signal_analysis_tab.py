import streamlit as st
import pandas as pd
import numpy as np
from math import sqrt as _sqrt
from ui_helpers import insight_toggle
from apple_theme import (
    T1, T2, T3, CARD, INSET, HAIR, FILL, SHADOW, GREY_BG,
    GREEN, RED, BLUE, AMBER, PURPLE, TEAL,
    REGIME_COLORS, REGIME_BG,
)


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS (light Apple design — see apple_theme.py)
# ─────────────────────────────────────────────────────────────────────────────
BULL = GREEN
BEAR = RED
NEUT = AMBER
INFO = BLUE
PURP = PURPLE
GOLD = AMBER
BG   = CARD
BG2  = INSET
BDR  = HAIR

# shared inline-style fragments
_LBL = f"font-size:0.8rem;font-weight:600;color:{T3};"
_NUM = "letter-spacing:-0.02em;font-variant-numeric:tabular-nums;"


def _wr_tone(wr):
    """Green / amber / red for a win-rate style percentage."""
    return GREEN if wr >= 55 else (AMBER if wr >= 45 else RED)


def _pill(text, color, bg):
    return (
        f"<span style='display:inline-flex;align-items:center;font-size:0.78rem;font-weight:600;"
        f"color:{color};background:{bg};border-radius:980px;padding:0.2rem 0.65rem;"
        f"white-space:nowrap;'>{text}</span>"
    )


def _hex_rgba(hex_color, alpha=0.12):
    hc = str(hex_color).strip().lstrip("#")
    if len(hc) != 6:
        return f"rgba(127,127,127,{alpha})"
    r, g, b = int(hc[:2], 16), int(hc[2:4], 16), int(hc[4:], 16)
    return f"rgba({r},{g},{b},{alpha})"


def signal_analysis_tab(df, info_icon):
    # flush any pending save/remove toast from last on_click
    _pending_toast = st.session_state.pop('_rc_toast', None)
    if _pending_toast:
        st.toast(_pending_toast[0], icon=_pending_toast[1])

    from signal_engine import (
        detect_signals, evaluate_signal_success,
        find_consensus_signals, analyze_indicator_combinations,
        calculate_monthly_performance,
    )
    from charts import (
        create_ema_chart, create_adx_chart, create_rsi_chart,
        create_macd_chart, create_bollinger_bands_chart,
        create_stochastic_chart,
    )

    # Light design: the old dark theme_palette is no longer used for these cards.
    panel     = CARD
    panel_alt = INSET
    border    = HAIR
    text_col  = T1
    muted     = T3

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <style>
        .sa-kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.9rem;
            margin-bottom: 1.4rem;
        }}
        .sa-kpi-card {{
            background: {CARD};
            border: 1px solid {HAIR};
            border-radius: 16px;
            box-shadow: {SHADOW};
            padding: 1.1rem 1.25rem;
        }}
        .sa-kpi-label {{
            font-size: 0.82rem;
            color: {T3};
            font-weight: 600;
            margin-bottom: 0.45rem;
        }}
        .sa-kpi-value {{
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: -0.02em;
            font-variant-numeric: tabular-nums;
        }}
        .sa-kpi-sub {{
            font-size: 0.8rem;
            color: {T3};
            margin-top: 0.35rem;
            font-weight: 500;
        }}
        .sa-input-label {{
            font-size: 0.82rem;
            color: {T3};
            font-weight: 600;
            margin-bottom: 0.35rem;
        }}
        .sa-tip {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 15px;
            height: 15px;
            border-radius: 50%;
            border: 1px solid {HAIR};
            background: {CARD};
            font-size: 0.66rem;
            color: {T3};
            font-weight: 600;
            margin-left: 0.3rem;
            cursor: help;
            vertical-align: middle;
            line-height: 1;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='ap-section' style='margin-top:0.4rem;'><div>"
        f"<div class='ap-section-title' style='font-size:1.25rem;font-weight:700;color:{T1};'>Signal analysis</div>"
        f"<div class='ap-section-sub' style='font-size:0.88rem;color:{T3};'>"
        f"How every indicator's buy signals played out, with your risk/reward and holding period.</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    with c1:
        st.markdown(
            "<div class='sa-input-label'>Risk</div>",
            unsafe_allow_html=True,
        )
        risk_val = st.number_input(
            "Risk",
            min_value=1,
            max_value=100,
            value=1,
            step=1,
            label_visibility="collapsed",
            key="sa_risk_val",
        )
    with c2:
        st.markdown(
            "<div class='sa-input-label'>Reward</div>",
            unsafe_allow_html=True,
        )
        reward_val = st.number_input(
            "Reward",
            min_value=1,
            max_value=100,
            value=2,
            step=1,
            label_visibility="collapsed",
            key="sa_reward_val",
        )
    with c3:
        st.markdown(
            "<div class='sa-input-label'>Holding period</div>",
            unsafe_allow_html=True,
        )
        _period_map = {"Short (5d)": 5, "Medium (63d)": 63, "Long (252d)": 252}
        _period_label = st.selectbox(
            "Period",
            list(_period_map.keys()),
            index=1,
            label_visibility="collapsed",
            key="sa_period_val",
        )
        holding_period = _period_map[_period_label]
    with c4:
        st.markdown(
            "<div class='sa-input-label'>Combo depth</div>",
            unsafe_allow_html=True,
        )
        _depth_opts = {
            "Pairs only (2)": 2,
            "Up to Triples (3)": 3,
            "Up to Quads (4)": 4,
            "Up to 5-Way (5)": 5,
            "Up to 6-Way (6)": 6,
        }
        _depth_label = st.selectbox(
            "Depth",
            list(_depth_opts.keys()),
            index=2,
            label_visibility="collapsed",
            key="sa_combo_depth",
        )
        max_combo_depth = _depth_opts[_depth_label]
    combo_signal_window = 3

    stop_loss     = 0.02
    rr_ratio      = reward_val / risk_val
    profit_target = stop_loss * rr_ratio

    # ── Run engines (cached in session_state — reruns like Save clicks are instant) ──
    _sym      = st.session_state.get('analyzed_symbol', '')
    _last_bar = str(df.index[-1]) if len(df) > 0 else ''
    _sa_key   = (_sym, _last_bar, holding_period, max_combo_depth, risk_val, reward_val)

    if st.session_state.get('_sa_cache_key') == _sa_key:
        (signals_df, results, successful_signals, all_signal_details,
         consensus_signals, combo_results, monthly_performance) = st.session_state['_sa_cache']
    else:
        with st.spinner("Running signal analysis…"):
            signals_df = detect_signals(df)
            results, successful_signals, all_signal_details = evaluate_signal_success(
                df, signals_df, profit_target, holding_period, stop_loss
            )
            consensus_signals   = find_consensus_signals(signals_df)
            combo_results       = analyze_indicator_combinations(
                signals_df, df, profit_target, holding_period, stop_loss, max_combo_depth,
                combo_signal_window,
            )
            monthly_performance = calculate_monthly_performance(all_signal_details)
        st.session_state['_sa_cache'] = (
            signals_df, results, successful_signals, all_signal_details,
            consensus_signals, combo_results, monthly_performance,
        )
        st.session_state['_sa_cache_key'] = _sa_key

    # ── Aggregate stats ───────────────────────────────────────────────────────
    total_signals    = sum(d["total_signals"] for d in results.values())
    total_successful = len(successful_signals)
    overall_success  = (total_successful / total_signals * 100) if total_signals > 0 else 0.0
    total_failed     = total_signals - total_successful

    all_gains  = [s["gain"] for s in all_signal_details if s["gain"] > 0]
    all_losses = [abs(s["gain"]) for s in all_signal_details if s["gain"] < 0]
    actual_avg_gain = float(np.mean(all_gains))  if all_gains  else 0.0
    actual_avg_loss = float(np.mean(all_losses)) if all_losses else 0.0
    actual_rr       = round(actual_avg_gain / actual_avg_loss, 2) if actual_avg_loss > 0 else 0.0
    pf_overall      = round(sum(all_gains) / sum(all_losses), 2) \
                      if all_losses and sum(all_losses) > 0 else 0.0
    expectancy_all  = round(
        (overall_success / 100) * actual_avg_gain -
        (1 - overall_success / 100) * actual_avg_loss, 2
    )
    insight_toggle(
        "kpi_metrics",
        "What do these numbers mean? (tap to read)",
        "<p><strong>Win Rate</strong> — Out of all the signals, how many actually made money? Above 50% means it's right more often than wrong.</p>"
        "<p><strong>Total Signals</strong> — How many times this indicator said 'buy' during the time period you're testing.</p>"
        "<p><strong>Successful</strong> — Trades that hit your profit target before getting stopped out.</p>"
        "<p><strong>Failed</strong> — Trades that hit the stop loss or ran out of time.</p>"
        "<p><strong>Profit Factor</strong> — Total money made ÷ total money lost. Above 1.0 = making money. Above 2.0 = very good.</p>"
        "<p><strong>Expectancy</strong> — On average, how much do you make (or lose) per trade? Positive = you're making money over time.</p>"
    )
    
    # ── Wilson lower-bound helper ─────────────────────────────────────────────
    def _wilson(n, pct):
        if n == 0:
            return 0.0
        p = pct / 100
        z = 1.645
        denom  = 1 + z * z / n
        centre = p + z * z / (2 * n)
        spread = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
        return (centre - spread) / denom * 100

    # ── Per-indicator 70/30 train/test split (bar-based, framework §11) ──────
    # Training = first 70% of the price history; Testing = last 30% (out-of-sample).
    # Returns (train_wr_pct, test_wr_pct) — either may be None if no signals fall in that window.
    _bar_dates = [str(d) for d in df["Date"].tolist()] if "Date" in df.columns else [str(i) for i in range(len(df))]
    if _bar_dates:
        _split_i = max(1, int(len(_bar_dates) * 0.70))
        _split_i = min(_split_i, len(_bar_dates) - 1)
        _split_date = _bar_dates[_split_i]
    else:
        _split_date = None

    def _ind_train_test_wr(ind_signals):
        if not ind_signals or _split_date is None:
            return (None, None)
        train_w = train_n = 0
        test_w  = test_n  = 0
        for s in ind_signals:
            d = str(s["date"])
            if d < _split_date:
                train_n += 1
                if s["gain"] > 0: train_w += 1
            else:
                test_n += 1
                if s["gain"] > 0: test_w += 1
        train_pct = (train_w / train_n * 100) if train_n > 0 else None
        test_pct  = (test_w  / test_n  * 100) if test_n  > 0 else None
        return (train_pct, test_pct)

    # Backwards-compat shim — older callers expect a single test-WR value.
    def _ind_test_wr(ind_signals):
        return _ind_train_test_wr(ind_signals)[1]

    # ── Per-indicator rank score (framework §16: Test 50 / Stab 20 / Trades 15 / Div 10 / Bal 5)
    def _ind_rank_score(train_w, test_w, total, wins, losses):
        eff_test = test_w if test_w is not None else (train_w if train_w is not None else 0.0)
        eff_train = train_w if train_w is not None else eff_test
        gap         = abs(eff_train - eff_test)
        bal         = 1 - abs(wins - losses) / max(wins + losses, 1)
        test_score  = min(max(eff_test, 0), 100) / 100 * 50
        stab_score  = max(0, 1 - gap / 50) * 20
        trade_score = min(total / 20, 1) * 15
        div_score   = 10                          # single indicator always gets full diversity credit
        bal_score   = bal * 5
        return round(test_score + stab_score + trade_score + div_score + bal_score, 1)

    # ── Spec §3 + §4: category → role label.
    _LOGIC_TYPE = {
        "Trend":         "Trend Filter",
        "Momentum":      "Entry Timing",
        "Volume":        "Confirmation",
        "Volatility":    "Risk Filter",
        "Mean Reversion":"Mean Reversion",
        "Support":       "S/R Level",
        "Regime":        "Regime Filter",
        "Pattern":       "Price Action",
    }

    # ══════════════════════════════════════════════════════════════════════════
    # 1. KPI ROW  (6 tiles)
    # ══════════════════════════════════════════════════════════════════════════
    sc      = BULL if overall_success >= 50 else BEAR
    pf_col  = BULL if pf_overall >= 1.5 else NEUT if pf_overall >= 1.0 else BEAR
    exp_col = BULL if expectancy_all > 0 else BEAR

    st.markdown(f"""
    <div class='sa-kpi-grid'>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Total signals</div>
            <div class='sa-kpi-value' style='color:{T1};'>{total_signals}</div>
            <div class='sa-kpi-sub'>All indicators</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Successful</div>
            <div class='sa-kpi-value' style='color:{BULL};'>{total_successful}</div>
            <div class='sa-kpi-sub'>Hit {risk_val}:{reward_val} target</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Failures</div>
            <div class='sa-kpi-value' style='color:{BEAR};'>{total_failed}</div>
            <div class='sa-kpi-sub'>Missed target</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Win rate</div>
            <div class='sa-kpi-value' style='color:{sc};'>{overall_success:.1f}%</div>
            <div class='sa-kpi-sub'>Overall hit rate</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Profit factor</div>
            <div class='sa-kpi-value' style='color:{pf_col};'>{pf_overall:.2f}</div>
            <div class='sa-kpi-sub'>Gross W / Gross L</div>
        </div>
        <div class='sa-kpi-card'>
            <div class='sa-kpi-label'>Expectancy</div>
            <div class='sa-kpi-value' style='color:{exp_col};'>{expectancy_all:+.2f}%</div>
            <div class='sa-kpi-sub'>Per-trade edge</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SIGNALS SUB-TABS
    # ══════════════════════════════════════════════════════════════════════════
    _sig_main_tabs = st.tabs(["Single Indicator", "Indicator Combinations"])

    with _sig_main_tabs[0]:
        # ── indicator map: key → (name, category, role, params, chart_fn) ──────────
        # Spec §3: 8 categories. Volatility = filter-only by default (§3.4).
        # Volume VWAP doubles as a Support/Resistance level.
        indicator_map = {
            "EMA":   ("EMA (20/50/200)",       "Trend",      "Trend Filter + Entry Timing",  "20/50/200",   create_ema_chart),
            "SMA":   ("SMA (50/200)",           "Trend",      "Trend Filter",                 "50/200",      None),
            "PSAR":  ("Parabolic SAR",          "Trend",      "Trailing Stop + Reversal",     "0.02/0.2",    None),
            "ICHI":  ("Ichimoku Cloud",         "Trend",      "Trend Filter + S/R Levels",    "9/26/52",     None),
            "WMA":   ("WMA (20)",               "Trend",      "Trend Filter",                 "20",          None),
            "MACD":  ("MACD (12/26/9)",         "Trend",      "Trend Filter + Entry Signal",  "12/26/9",     create_macd_chart),
            "RSI":   ("RSI (14)",               "Momentum",   "Entry Timing + Overbought",    "14",          None),
            "STOCH": ("Stochastic (14,3,3)",    "Momentum",   "Entry Timing + Mean Reversion","14/3/3",      create_stochastic_chart),
            "ROC":   ("ROC (12)",               "Momentum",   "Momentum Confirmation",        "12",          None),
            "CCI":   ("CCI (20)",               "Momentum",   "Extreme Deviation Filter",     "20",          None),
            "WILLR": ("Williams %R (14)",       "Momentum",   "Overbought/Oversold Timing",   "14",          None),
            "BB":    ("Bollinger Bands (20,2)", "Volatility", "Volatility Filter / Risk",     "20/2",        create_bollinger_bands_chart),
            "KC":    ("Keltner Channel",        "Volatility", "Volatility Filter / Risk",     "20/1.5",      None),
            "DC":    ("Donchian (20)",          "Volatility", "Volatility Filter / Risk",     "20",          None),
            "MFI":   ("MFI (14)",               "Volume",     "Volume Momentum Confirmation", "14",          None),
            "CMF":   ("CMF (20)",               "Volume",     "Volume Flow Confirmation",     "20",          None),
            "VWAP":  ("VWAP",                   "Volume",     "Institutional Anchor / Filter","daily",       None),
            "OBV":   ("OBV",                    "Volume",     "Volume Trend Confirmation",    "cumulative",  None),
            "ADX":   ("ADX (14) +DI/-DI",       "Regime",     "Trend Strength Filter",        "14",          create_adx_chart),
        }

        # Volatility = filter-only per spec §3.4 — excluded from "primary signal" leaderboard.
        # They still appear in combinations as Risk Filter slots.
        _FILTER_ONLY = {"BB", "KC", "DC"}

        _CAT_COLOR = {
            "Trend": INFO, "Momentum": BULL, "Volume": PURP, "Volatility": NEUT,
            "Regime": GOLD, "Mean Reversion": PURP, "Support": INFO, "Pattern": PURPLE,
        }

        # ── build per-indicator stats ─────────────────────────────────────────────
        succ_by_ind = {}
        for s in successful_signals:
            succ_by_ind.setdefault(s["indicator"], []).append(s["gain"])

        indicator_performance = []
        regime_color_map = dict(REGIME_COLORS)

        for key, (name, category, role, params, chart_fn) in indicator_map.items():
            if key not in results:
                continue
            data  = results[key]
            total = data.get("total_signals", 0)
            if total <= 0:
                continue
            succ_gains  = succ_by_ind.get(key, [])
            win_count   = len(succ_gains)
            win_rate    = win_count / total * 100
            avg_gain    = float(np.mean(succ_gains)) if succ_gains else 0.0
            loss_gains  = [abs(s["gain"]) for s in all_signal_details
                           if s["indicator"] == key and s["gain"] < 0]
            avg_loss    = -float(np.mean(loss_gains)) if loss_gains else 0.0
            pf          = round(sum(succ_gains) / sum(loss_gains), 2) \
                          if loss_gains and sum(loss_gains) > 0 else 0.0
            exp         = (win_rate / 100) * avg_gain + (1 - win_rate / 100) * avg_loss
            ind_sigs    = sorted(
                [s for s in all_signal_details if s["indicator"] == key],
                key=lambda x: pd.to_datetime(x["date"]),
            )
            regime_perf = data.get("regime_performance", {})
            best_regime = max(regime_perf, key=regime_perf.get) if regime_perf else ""
            _train_wr, _test_wr = _ind_train_test_wr(ind_sigs)
            _gap = round(abs((_train_wr or 0) - (_test_wr or 0)), 1) if (_train_wr is not None and _test_wr is not None) else None
            indicator_performance.append({
                "key": key, "name": name, "category": category,
                "role": role, "params": params,
                "total": total, "win_count": win_count,
                "win_rate": win_rate, "avg_gain": round(avg_gain, 2),
                "avg_loss": round(avg_loss, 2), "profit_factor": pf,
                "expectancy": round(exp, 2),
                "best_regime": best_regime, "regime_performance": regime_perf,
                "chart_fn": chart_fn, "signals": ind_sigs,
                "max_gain": data.get("max_gain", 0),
                "max_loss": data.get("max_loss", 0),
                "wilson": _wilson(total, win_rate),
                "train_wr":      round(_train_wr, 1) if _train_wr is not None else None,
                "test_wr":       round(_test_wr, 1)  if _test_wr  is not None else None,
                "stability_gap": _gap,
                "rank_score":    _ind_rank_score(_train_wr, _test_wr, total, win_count, total - win_count),
                "logic_type":    _LOGIC_TYPE.get(category, "Signal"),
                "filter_only":   key in _FILTER_ONLY,
            })

        # Spec §3.4: volatility indicators are filter-only — not graded as primary signals.
        indicator_performance = [x for x in indicator_performance if not x["filter_only"]]
        indicator_performance = [x for x in indicator_performance if x["win_rate"] < 100]
        indicator_performance.sort(key=lambda x: x["rank_score"], reverse=True)
        card_accents = [T2]  # rank badges are neutral in the light design

        # ══════════════════════════════════════════════════════════════════════════
        # INDICATOR LEADERBOARD
        # ══════════════════════════════════════════════════════════════════════════
        if not indicator_performance:
            st.info("No indicator data available for the selected period.")
        else:
            _ind_tips = {
                "Signals":       "Total number of times this indicator triggered a signal",
                "Wins":          "Number of signals that ended in a profitable trade",
                "Losses":        "Number of signals that resulted in a loss",
                "Avg Gain":      "Average profit on winning trades — higher means bigger wins",
                "Avg Loss":      "Average loss on losing trades — closer to 0 means better risk control",
                "Best Regime":   "Market condition where this indicator performed best (Trend/Range/Volatile)",
                "Profit Factor": "Total gains ÷ total losses — above 1.0 means profitable",
                "Expectancy":    "Average profit per trade across all signals",
            }

            def _sb(label, value, color, bg=None, sub=None, sub_color=None):
                # Light tile: INSET background regardless of the old tint (bg kept for signature).
                _sh = (
                    f"<div style='font-size:0.8rem;font-weight:600;color:{sub_color or color};"
                    f"margin-top:0.3rem;'>{sub}</div>"
                ) if sub else ""
                _tip = _ind_tips.get(label, "")
                _tip_html = (
                    f"<span class='sa-tip' title='{_tip}'>?</span>"
                ) if _tip else ""
                _disp = label[:1] + label[1:].lower()
                return (
                    f"<div style='background:{INSET};border:1px solid {HAIR};"
                    f"border-radius:12px;padding:0.9rem 0.8rem;text-align:center;'>"
                    f"<div style='{_LBL}margin-bottom:0.4rem;'>{_disp}{_tip_html}</div>"
                    f"<div style='font-size:1.3rem;font-weight:700;color:{color};line-height:1.1;{_NUM}'>{value}</div>"
                    f"{_sh}</div>"
                )

            for idx, ind in enumerate(indicator_performance):
                accent   = card_accents[idx % len(card_accents)]
                br_color = regime_color_map.get(ind["best_regime"], accent)
                win_pct  = ind["win_rate"]
                loss_pct = 100 - win_pct
                total    = ind["total"]
                wins     = ind["win_count"]
                losses   = total - wins
                gain_col = BULL if ind["avg_gain"] >= 1 else NEUT if ind["avg_gain"] > 0 else BEAR
                loss_col = BEAR if ind["avg_loss"] < -1 else NEUT
                logic    = ind["logic_type"]

                _trw = ind.get("train_wr")
                _twr = ind["test_wr"]
                _gap = ind["stability_gap"]
                _rs  = ind["rank_score"]
                _trw_str = f"{_trw:.1f}%" if _trw is not None else "—"
                _twr_str = f"{_twr:.1f}%" if _twr is not None else "—"
                _gap_str = f"{_gap:.0f}pts" if _gap is not None else "—"
                _trw_c = T3 if _trw is None else (BULL if _trw >= 55 else (NEUT if _trw >= 45 else BEAR))
                _tw_c  = T3 if _twr is None else (BULL if _twr >= 55 else (NEUT if _twr >= 45 else BEAR))
                _gap_c = T3 if _gap is None else (BULL if _gap < 10 else (NEUT if _gap < 20 else BEAR))
                _rs_c  = BULL if _rs >= 70 else (NEUT if _rs >= 50 else BEAR)
                _wp_c  = _wr_tone(win_pct)

                def _tt_cell(lbl, val, col, sub, first=False):
                    _bl = "" if first else f"border-left:1px solid {HAIR};"
                    return (
                        f"<div style='text-align:center;padding:0.15rem 0.4rem;{_bl}'>"
                        f"<div style='{_LBL}margin-bottom:0.3rem;'>{lbl}</div>"
                        f"<div style='font-size:1.2rem;font-weight:700;color:{col};line-height:1.1;{_NUM}'>{val}</div>"
                        f"<div style='font-size:0.78rem;color:{T3};margin-top:0.25rem;'>{sub}</div></div>"
                    )

                _train_test_html = (
                    f"<div style='background:{INSET};border:1px solid {HAIR};border-radius:12px;"
                    f"padding:0.85rem 1rem;margin-bottom:0.9rem;'>"
                    f"<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;'>"
                    + _tt_cell("Train WR", _trw_str, _trw_c, "first 70% bars", first=True)
                    + _tt_cell("Test WR", _twr_str, _tw_c, "last 30% (OOS)")
                    + _tt_cell("Stability", _gap_str, _gap_c, "train − test")
                    + _tt_cell("Rank score", f"{_rs:.0f}", _rs_c, "out of 100")
                    + f"</div></div>"
                )

                st.markdown((
                    f"<div style='background:{CARD};border:1px solid {HAIR};box-shadow:{SHADOW};"
                    f"border-radius:18px;overflow:hidden;margin-bottom:1.1rem;'>"
                    f"<div style='padding:1.4rem 1.5rem;'>"
                    f"<div style='display:flex;align-items:center;gap:1.1rem;margin-bottom:1.1rem;flex-wrap:wrap;'>"
                    f"<div style='width:2.75rem;height:2.75rem;border-radius:50%;"
                    f"background:{FILL};border:1px solid {HAIR};"
                    f"display:flex;align-items:center;justify-content:center;flex-shrink:0;'>"
                    f"<span style='font-size:1rem;font-weight:700;color:{T1};{_NUM}'>#{idx+1}</span></div>"
                    f"<div style='flex:1;min-width:220px;'>"
                    f"<div style='font-size:1.2rem;font-weight:700;color:{T1};letter-spacing:-0.01em;'>{ind['name']}</div>"
                    f"<div style='display:flex;align-items:center;gap:0.45rem;margin-top:0.4rem;flex-wrap:wrap;'>"
                    + _pill(ind['category'], BLUE, "rgba(0,99,209,0.09)")
                    + _pill(logic, T2, GREY_BG)
                    + f"<span style='font-size:0.82rem;color:{T3};font-weight:500;'>{ind['role']}</span>"
                    f"<span style='font-size:0.78rem;color:{T3};border:1px solid {HAIR};border-radius:6px;"
                    f"padding:0.08rem 0.45rem;font-weight:500;background:{CARD};'>params: {ind['params']}</span>"
                    f"</div></div>"
                    f"<div style='text-align:right;flex-shrink:0;'>"
                    f"<div style='font-size:2.5rem;font-weight:700;color:{_wp_c};line-height:1;{_NUM}'>{win_pct:.0f}%</div>"
                    f"<div style='{_LBL}margin-top:0.3rem;'>Win rate</div>"
                    f"</div></div>"
                    f"<div style='margin-bottom:1rem;'>"
                    f"<div style='display:flex;border-radius:980px;overflow:hidden;"
                    f"height:8px;background:{FILL};margin-bottom:0.45rem;'>"
                    f"<div style='width:{win_pct:.1f}%;background:{GREEN};'></div>"
                    f"<div style='width:{loss_pct:.1f}%;background:{_hex_rgba(BEAR,.30)};'></div>"
                    f"</div>"
                    f"<div style='display:flex;justify-content:space-between;gap:0.5rem;flex-wrap:wrap;'>"
                    f"<span style='font-size:0.82rem;color:{T2};font-weight:600;'>"
                    f"<span style='color:{GREEN};'>&#10003;</span> {total} signals &middot; "
                    f"<span style='color:{GREEN};'>{win_pct:.0f}% winners</span></span>"
                    f"<span style='font-size:0.82rem;color:{BEAR};font-weight:600;'>{loss_pct:.0f}% losers</span>"
                    f"</div></div>"
                    + _train_test_html
                    + f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:0.6rem;'>"
                    + _sb("Signals",       str(total),                    T1)
                    + _sb("Wins",          str(wins),                     T1, None, f"{win_pct:.0f}%", BULL)
                    + _sb("Losses",        str(losses),                   T1, None, f"{loss_pct:.0f}%", BEAR)
                    + _sb("Best Regime",   ind["best_regime"] or "—", br_color if ind["best_regime"] else T3)
                    + _sb("Avg Gain",      f"+{ind['avg_gain']:.2f}%",    gain_col)
                    + _sb("Avg Loss",      f"{ind['avg_loss']:.2f}%",     loss_col)
                    + _sb("Profit Factor", f"{ind['profit_factor']:.2f}", BULL if ind['profit_factor'] >= 1.5 else (NEUT if ind['profit_factor'] >= 1 else BEAR))
                    + _sb("Expectancy",    f"{ind['expectancy']:+.2f}%",  BULL if ind['expectancy'] > 0 else BEAR)
                    + "</div></div></div>"
                ), unsafe_allow_html=True)



    with _sig_main_tabs[1]:
        # ══════════════════════════════════════════════════════════════════════════
        # REGIME CHAMPIONS
        # ══════════════════════════════════════════════════════════════════════════
        _all_names = {p["key"]: p["name"] for p in indicator_performance}
        combo_accent_cycle = [BULL, INFO, NEUT, PURP, TEAL, GOLD]

        def _wr_color(wr):
            # (background tint, text colour) on the light design
            if wr >= 65: return ("rgba(27,122,54,0.12)", GREEN)
            if wr >= 55: return ("rgba(27,122,54,0.08)", GREEN)
            if wr >= 45: return ("rgba(0,99,209,0.09)", BLUE)
            if wr >= 35: return ("rgba(193,18,31,0.08)", RED)
            return (GREY_BG, T3)

        _regime_meta = {
            "TREND":    {"accent": REGIME_COLORS["TREND"],    "bg": REGIME_BG["TREND"],    "label": "Trend",    "summary": "Use when price is moving cleanly in one direction."},
            "RANGE":    {"accent": REGIME_COLORS["RANGE"],    "bg": REGIME_BG["RANGE"],    "label": "Range",    "summary": "Use when price rotates between support and resistance."},
            "VOLATILE": {"accent": REGIME_COLORS["VOLATILE"], "bg": REGIME_BG["VOLATILE"], "label": "Volatile", "summary": "Use when price expands quickly and needs fast confirmation."},
        }

        _broad_cat = {
            "Trend":          "Trend",
            "Momentum":       "Momentum",
            "Volume":         "Volume",
            "Volatility":     "Volatility",
            "Regime":         "Regime",
            "Mean Reversion": "Mean Reversion",
            "Support":        "Support",
            "Pattern":        "Pattern",
        }

        # Spec §3.4: volatility = filter-only. Disqualify combos that are *only* volatility.
        _COMBO_FILTER_ONLY_KEYS = {"BB", "KC", "DC"}

        def _ind_cat(key):
            raw = indicator_map.get(key, ("", "", "", "", None))[1]
            return _broad_cat.get(raw, "Other")

        # Spec §11: 70/30 split. monthly_win_rates is keyed by YYYY-MM; first 70% = train.
        def _train_test_wr_combo(cd):
            mwr = cd.get("monthly_win_rates", {})
            base = cd["success_rate"]
            if not mwr:
                return (base, base)
            months = sorted(mwr.keys())
            split  = max(1, int(len(months) * 0.70))
            split  = min(split, len(months) - 1) if len(months) >= 2 else split
            train_vals = [mwr[m] for m in months[:split] if mwr[m] is not None]
            test_vals  = [mwr[m] for m in months[split:] if mwr[m] is not None]
            train_w = float(np.mean(train_vals)) if train_vals else base
            test_w  = float(np.mean(test_vals))  if test_vals  else train_w
            return (train_w, test_w)

        # Spec §8 enforcement: penalise combos that violate category-diversity rules.
        # 1 indicator: ok. 2: should be cross-category. 3: ≥2 cats. 4+: ≥3 cats.
        # Same-category overload (>2 from one cat) is also penalised.
        def _diversity_score(parts):
            cats = [_ind_cat(p) for p in parts]
            n = len(parts)
            n_cats = len(set(cats))
            if n == 1:
                return 1.0
            ccount = {}
            for c in cats:
                ccount[c] = ccount.get(c, 0) + 1
            overload = max(0, max(ccount.values()) - 2)  # 0 if max-per-cat ≤ 2
            if   n == 2: target = 2
            elif n == 3: target = 2
            else:        target = 3
            return max(0.0, min(1.0, n_cats / target)) * (1.0 - 0.25 * overload)

        def _rank_score_combo(cd, parts, train_w, test_w):
            gap    = abs(train_w - test_w)
            n      = cd["total"]
            wins   = cd["successful"]
            losses = cd["failed"]
            bal    = 1 - abs(wins - losses) / max(wins + losses, 1)
            div    = _diversity_score(parts)
            return round(
                min(test_w, 100) / 100 * 50    # §16 Testing 50%
                + max(0, 1 - gap / 50) * 20    # §16 Stability 20%
                + min(n / 30, 1) * 15          # §16 Trades 15%
                + div * 10                     # §16 Diversity 10%
                + bal * 5,                     # §16 Balance 5%
                2,
            )

        all_combo_data = []
        if combo_results:
            for combo_key, cd in combo_results.items():
                parts = [p.strip() for p in combo_key.split(" + ")]
                n_c   = cd["total"]
                wr    = cd["success_rate"]
                if wr >= 100:
                    continue
                # Spec §3.4: skip combos that are 100% volatility-filter (no primary signals).
                if all(p in _COMBO_FILTER_ONLY_KEYS for p in parts):
                    continue
                # Spec §8: drop strategies that pile >2 indicators into the same category.
                _cats   = [_ind_cat(p) for p in parts]
                _ccount = {}
                for c in _cats:
                    _ccount[c] = _ccount.get(c, 0) + 1
                if max(_ccount.values()) > 2:
                    continue
                regime_perf_raw = cd.get("regime_performance", {})
                regime_totals   = cd.get("regime_totals", {})
                rp      = {r: regime_perf_raw.get(r, 0) for r in regime_perf_raw if regime_totals.get(r, 0) > 0}
                best_r  = max(rp, key=rp.get) if rp else ""
                _trw, _tw = _train_test_wr_combo(cd)
                _gap    = round(abs(_trw - _tw), 1)
                all_combo_data.append({
                    "key":           combo_key,
                    "indicators":    parts,
                    "size":          len(parts),
                    "label":         " + ".join(_all_names.get(p, p) for p in parts),
                    "total":         n_c,
                    "active_bars":   cd.get("active_bars", n_c),
                    "regime_totals": regime_totals,
                    "wins":          cd["successful"],
                    "losses":        cd["failed"],
                    "win_rate":      wr,
                    "train_wr":      round(_trw, 1),
                    "test_wr":       round(_tw, 1),
                    "stability_gap": _gap,
                    "avg_gain":      cd["avg_gain"],
                    "avg_loss":      cd["avg_loss"],
                    "profit_factor": cd["profit_factor"],
                    "expectancy":    cd["expectancy"],
                    "avg_hold":      cd.get("avg_hold", 0),
                    "regime_perf":   rp,
                    "best_regime":   best_r,
                    "rank_score":    _rank_score_combo(cd, parts, _trw, _tw),
                    "overloaded_cats": [c for c, n in _ccount.items() if n > 2],
                    "cat_counts":    _ccount,
                    "signal_freq":   cd.get("signal_frequency", 0),
                    "signal_window": cd.get("signal_window", combo_signal_window),
                    "consistency":   cd.get("monthly_consistency", 0),
                    "monthly_win_rates": cd.get("monthly_win_rates", {}),
                })
            all_combo_data.sort(key=lambda x: x["rank_score"], reverse=True)

        if all_combo_data:

            def _tip_icon(text):
                _safe = str(text).replace("'", "&#39;").replace('"', '&quot;')
                return f"<span class='sa-tip' title='{_safe}'>?</span>"

            def _focus_metric(label, value, color, sub="", tip=""):
                _tip_html = _tip_icon(tip) if tip else ""
                _sub_html = (
                    f"<div style='font-size:0.78rem;color:{muted};margin-top:0.3rem;font-weight:500;'>{sub}</div>"
                    if sub else ""
                )
                return (
                    f"<div style='background:{panel_alt};border:1px solid {border};"
                    f"border-radius:12px;padding:0.85rem 0.8rem;text-align:center;'>"
                    f"<div style='{_LBL}margin-bottom:0.4rem;'>{label}{_tip_html}</div>"
                    f"<div style='font-size:1.25rem;font-weight:700;color:{color};line-height:1.1;{_NUM}'>{value}</div>"
                    f"{_sub_html}</div>"
                )

            def _sample_band(row):
                _total = row["total"]
                if _total >= 25: return ("Deep sample",   INFO)
                if _total >= 15: return ("Strong sample", BULL)
                if _total >= 8:  return ("Usable sample", NEUT)
                return ("Thin sample", BEAR)

            def _render_focus_card(row, rank, focus_regime, hero=False):
                _meta         = _regime_meta[focus_regime]
                _accent       = _meta["accent"]
                _label        = _meta["label"]
                _sample_label, _sample_color = _sample_band(row)
                _wr_col  = BULL if row["win_rate"] >= 55 else NEUT if row["win_rate"] >= 45 else BEAR
                _pf_col  = BULL if row["profit_factor"] >= 1.3 else NEUT if row["profit_factor"] >= 1 else BEAR
                _exp_col = BULL if row["expectancy"] > 0 else BEAR
                _title   = f"Top {_label} setup" if hero else f"#{rank}"
                _card_pad = "1.25rem 1.35rem" if hero else "0.95rem 1.1rem"
                _card_rad = "16px" if hero else "14px"
                _accent_bg = _meta.get("bg", GREY_BG)
                _sample_bg = (
                    "rgba(27,122,54,0.10)" if _sample_color == BULL else
                    "rgba(193,18,31,0.08)" if _sample_color == BEAR else
                    "rgba(161,92,0,0.10)" if _sample_color == NEUT else
                    "rgba(0,99,209,0.09)"
                )
                _title_pill = (
                    _pill(_title, _accent, _accent_bg) if hero else
                    _pill(_title, T1, FILL)
                )
                st.markdown(
                    (
                        f"<div style='background:{panel};border:1px solid {border};border-radius:{'18px' if hero else '16px'};"
                        f"box-shadow:{SHADOW};overflow:hidden;margin-bottom:0.6rem;'>"
                        f"<div style='padding:{'1.4rem 1.5rem' if hero else '1.15rem 1.3rem'};'>"
                        f"<div style='display:flex;justify-content:space-between;gap:1rem;align-items:flex-start;flex-wrap:wrap;margin-bottom:1rem;'>"
                        f"<div style='flex:1;min-width:260px;'>"
                        f"<div style='display:flex;flex-wrap:wrap;align-items:center;gap:0.4rem;margin-bottom:0.6rem;'>"
                        + _title_pill
                        + _pill(_sample_label, _sample_color, _sample_bg)
                        + _pill(f"{row['size']}-way", T2, GREY_BG)
                        + _pill(f"Best in {_label}", _accent, _accent_bg)
                        + f"</div>"
                        f"<div style='font-size:{'1.25rem' if hero else '1.08rem'};font-weight:700;color:{text_col};"
                        f"letter-spacing:-0.01em;line-height:1.35;'>"
                        f"{row['label']}</div>"
                        f"</div>"
                        f"<div style='text-align:right;min-width:150px;'>"
                        f"<div style='{_LBL}'>"
                        f"Overall win{_tip_icon('Win rate across the full test period.')}</div>"
                        f"<div style='font-size:{'2.7rem' if hero else '2.1rem'};font-weight:700;color:{_wr_col};line-height:1.05;"
                        f"margin-top:0.2rem;{_NUM}'>{row['win_rate']:.1f}%</div>"
                        f"<div style='font-size:0.82rem;color:{muted};margin-top:0.3rem;font-weight:500;'>"
                        f"{row['wins']} winners · {row['losses']} losers</div>"
                        f"</div></div>"
                        # Spec §11+§16: train/test/stability/score row.
                        + (
                            f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.6rem;margin-bottom:0.6rem;'>"
                            + _focus_metric('Train WR',  f"{row.get('train_wr', row['win_rate']):.1f}%",
                                            BULL if row.get('train_wr', row['win_rate']) >= 55 else (NEUT if row.get('train_wr', row['win_rate']) >= 45 else BEAR),
                                            'first 70%', 'Win rate on the first 70% of months (training).')
                            + _focus_metric('Test WR',   f"{row['test_wr']:.1f}%",
                                            BULL if row['test_wr'] >= 55 else (NEUT if row['test_wr'] >= 45 else BEAR),
                                            'last 30% OOS', 'Out-of-sample win rate on the last 30% of months.')
                            + _focus_metric('Stability', f"{row['stability_gap']:.0f}pts",
                                            BULL if row['stability_gap'] < 10 else (NEUT if row['stability_gap'] < 20 else BEAR),
                                            'train − test', 'Gap between train and test win rate. Lower = more stable.')
                            + _focus_metric('Rank score', f"{row.get('rank_score', 0):.0f}",
                                            BULL if row.get('rank_score', 0) >= 70 else (NEUT if row.get('rank_score', 0) >= 50 else BEAR),
                                            '/100', 'Test 50% + Stability 20% + Trades 15% + Diversity 10% + Balance 5%.')
                            + "</div>"
                        )
                        + f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.6rem;margin-bottom:0.6rem;'>"
                        + _focus_metric('Entries', str(row['total']), T1, f"{row['signal_freq']:.1f}/100 bars", 'Distinct trade entries in the full test.')
                        + _focus_metric('Winners', str(row['wins']), BULL, tip='Entries that finished positive.')
                        + _focus_metric('Losers',  str(row['losses']), BEAR, tip='Entries that finished negative.')
                        + _focus_metric('Profit factor', f"{row['profit_factor']:.2f}", _pf_col, tip='Total gains divided by total losses.')
                        + _focus_metric('Expectancy', f"{row['expectancy']:+.2f}%", _exp_col, tip='Average edge per trade.')
                        + "</div>"
                        + f"<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:0.6rem;'>"
                        + _focus_metric('Avg hold', f"{row['avg_hold']:.0f}d", T1, tip='Average days held per trade.')
                        + _focus_metric('Avg gain', f"+{row['avg_gain']:.2f}%", BULL, tip='Average size of winning trades.')
                        + _focus_metric('Avg loss', f"{row['avg_loss']:.2f}%",  BEAR, tip='Average size of losing trades.')
                        + "</div></div></div>"
                    ),
                    unsafe_allow_html=True,
                )

            def _render_regime_champion_section(_section_name, _regime_key, _save_offset):
                _section_meta    = _regime_meta[_regime_key]
                _regime_combos_all = [row for row in all_combo_data if row["best_regime"] == _regime_key]
                if not _regime_combos_all:
                    _regime_combos_all = [
                        row for row in all_combo_data
                        if row.get("regime_totals", {}).get(_regime_key, 0) > 0
                    ]
                # Spec §16: rank by rank_score (test-weighted), then break ties on test_wr / trades.
                _regime_combos = sorted(
                    _regime_combos_all,
                    key=lambda row: (row.get("rank_score", 0), row["test_wr"], row["total"], row["profit_factor"]),
                    reverse=True,
                )[:10]

                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;"
                    f"margin:0.4rem 0 0.9rem 0;flex-wrap:wrap;'>"
                    f"<div>"
                    f"<div style='font-size:1.25rem;color:{T1};font-weight:700;letter-spacing:-0.015em;'>"
                    f"{_section_name} champions</div>"
                    f"<div style='font-size:0.88rem;color:{T3};margin-top:0.2rem;'>"
                    f"Best 10 setups in {_section_name.lower()} conditions</div>"
                    f"</div>"
                    + _pill(f"Showing {min(10, len(_regime_combos_all))} of {len(_regime_combos_all)}", T2, GREY_BG)
                    + f"</div>",
                    unsafe_allow_html=True,
                )

                if not _regime_combos:
                    st.markdown(
                        f"<div style='background:{panel};border:1px solid {border};border-radius:16px;"
                        f"box-shadow:{SHADOW};padding:1.1rem 1.25rem;color:{T2};font-size:0.9rem;'>"
                        f"No {_section_name.lower()} combinations found.</div>",
                        unsafe_allow_html=True,
                    )
                    return

                _champion = _regime_combos[0]
                _render_focus_card(_champion, 1, _regime_key, hero=True)
                from favorites_tab import render_save_regime_champion_button
                render_save_regime_champion_button(_champion, _regime_key, _period_label, _save_offset + 1)

                if len(_regime_combos) > 1:
                    st.markdown(
                        f"<div style='display:flex;align-items:baseline;gap:0.6rem;margin:1.6rem 0 0.8rem 0;flex-wrap:wrap;'>"
                        f"<span style='font-size:1.1rem;font-weight:700;color:{T1};letter-spacing:-0.01em;'>"
                        f"More {_section_name.lower()} setups</span>"
                        f"<span style='font-size:0.85rem;color:{T3};'>Top {len(_regime_combos)} only</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption(f"Only one {_section_name.lower()} setup matched.")

                for _rank, _row in enumerate(_regime_combos[1:], start=2):
                    _render_focus_card(_row, _rank, _regime_key, hero=False)
                    render_save_regime_champion_button(_row, _regime_key, _period_label, _save_offset + _rank)

        _regime_sections = [
            ("Trend",    "TREND",    0),
            ("Range",    "RANGE",    100),
            ("Volatile", "VOLATILE", 200),
        ]
        _champion_tabs = st.tabs([f"{_name} Champions" for _name, _, _ in _regime_sections])
        for _tab, (_section_name, _regime_key, _save_offset) in zip(_champion_tabs, _regime_sections):
            with _tab:
                if all_combo_data:
                    _render_regime_champion_section(_section_name, _regime_key, _save_offset)
                else:
                    st.info(f"No {_section_name.lower()} combinations available yet — run more signals to populate this tab.")
