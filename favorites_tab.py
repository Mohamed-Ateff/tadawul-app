"""
favorites_tab.py
────────────────
All favorites feature logic in one place:
  - favorites_css(palette)      → CSS string (injected via app.py style block)
  - render_favorites_panel(palette) → renders the full saved-strategies panel
  - render_save_button(i, ka, kb, row, top_names) → ☆/★ button on combo cards
"""

from __future__ import annotations
import streamlit as st
import time as _time
from datetime import date as _today_date
from auth import upsert_favorite, delete_favorite


# ── CSS ───────────────────────────────────────────────────────────────────────

def favorites_css(palette: dict) -> str:
    """
    Returns the CSS block for the favorites panel.
    `palette` must contain: cp_bg, cp_border, cp_shadow, c_text, c_muted
    """
    cp_bg     = palette["cp_bg"]
    cp_border = palette["cp_border"]
    cp_shadow = palette["cp_shadow"]
    c_text    = palette["c_text"]
    c_muted   = palette["c_muted"]

    return f"""
        /* ── Favorites panel wrapper ── */
        .st-key-fav_panel_wrap {{
            background: {cp_bg} !important;
            border: 1px solid {cp_border} !important;
            border-radius: 24px !important;
            box-shadow: {cp_shadow} !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            padding: 1.1rem 1.4rem 1.3rem 1.4rem !important;
            box-sizing: border-box !important;
            margin-bottom: 0.7rem !important;
        }}
        .st-key-fav_panel_wrap > div,
        .st-key-fav_panel_wrap [data-testid="stVerticalBlockBorderWrapper"],
        .st-key-fav_panel_wrap [data-testid="stVerticalBlock"] {{
            background: transparent !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
        }}
        /* close button */
        .st-key-fav_close_panel .stButton > button {{
            background: rgba(239,83,80,0.07) !important;
            border: 1px solid rgba(239,83,80,0.30) !important;
            border-radius: 20px !important;
            color: rgba(239,83,80,0.75) !important;
            height: 2rem !important;
            min-height: 2rem !important;
            font-size: 0.72rem !important;
            font-weight: 800 !important;
            padding: 0 1rem !important;
            letter-spacing: 0.3px !important;
            transition: all 0.15s ease !important;
        }}
        .st-key-fav_close_panel .stButton > button:hover {{
            background: rgba(239,83,80,0.16) !important;
            border-color: rgba(239,83,80,0.65) !important;
            color: #ef5350 !important;
            box-shadow: 0 0 10px rgba(239,83,80,0.20) !important;
        }}
        /* delete buttons */
        [class*="st-key-fav_del_"] .stButton > button {{
            background: rgba(239,83,80,0.05) !important;
            border: 1px solid rgba(239,83,80,0.20) !important;
            border-radius: 10px !important;
            color: rgba(239,83,80,0.55) !important;
            min-height: 6rem !important;
            height: 100% !important;
            font-size: 1rem !important;
            padding: 0 !important;
            transition: all 0.15s ease !important;
        }}
        [class*="st-key-fav_del_"] .stButton > button:hover {{
            background: rgba(239,83,80,0.14) !important;
            border-color: rgba(239,83,80,0.60) !important;
            color: #ef5350 !important;
            box-shadow: 0 0 12px rgba(239,83,80,0.20) !important;
        }}
        /* save strategy button (combo cards) */
        [class*="st-key-fav_save_"] .stButton > button {{
            background: rgba(244,114,182,0.06) !important;
            border: 1px solid rgba(244,114,182,0.22) !important;
            border-radius: 20px !important;
            color: rgba(244,114,182,0.80) !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            min-height: 1.9rem !important;
            padding: 0 1rem !important;
            transition: all 0.15s ease !important;
        }}
        [class*="st-key-fav_save_"] .stButton > button:hover {{
            background: rgba(244,114,182,0.15) !important;
            border-color: rgba(244,114,182,0.55) !important;
            color: #f472b6 !important;
            box-shadow: 0 0 10px rgba(244,114,182,0.25) !important;
        }}
        /* panel inner elements */
        .fav-hdr {{ display:flex; align-items:center; gap:0.55rem;
                    padding-bottom:0.75rem; margin-bottom:0.75rem;
                    border-bottom:1px solid {cp_border}; }}
        .fav-hdr-icon {{ font-size:1rem; }}
        .fav-hdr-title {{ font-size:0.84rem; font-weight:800; color:{c_text};
                          flex:1; letter-spacing:0.2px; }}
        .fav-hdr-count {{ background:rgba(244,114,182,0.12);
                          border:1px solid rgba(244,114,182,0.28);
                          color:#f472b6; font-size:0.65rem; font-weight:800;
                          border-radius:20px; padding:0.12rem 0.55rem; }}
        .fav-empty {{ display:flex; flex-direction:column; align-items:center;
                      padding:1.8rem 1rem; gap:0.5rem; }}
        .fav-empty-icon {{ font-size:2rem; opacity:0.2; }}
        .fav-empty-txt {{ font-size:0.75rem; color:{c_muted}; text-align:center;
                          font-weight:600; max-width:320px; line-height:1.6;
                          opacity:0.75; }}
        .fav-card {{
            background: rgba(255,255,255,0.022);
            border: 1px solid {cp_border};
            border-radius: 16px;
            overflow: hidden;
            margin-bottom: 0.1rem;
        }}
        .fav-card-top {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.75rem 1rem 0.6rem 1rem;
            border-bottom: 1px solid {cp_border};
            background: rgba(244,114,182,0.035);
            flex-wrap: wrap;
        }}
        .fav-sym {{
            background: rgba(244,114,182,0.12);
            border: 1px solid rgba(244,114,182,0.30);
            border-radius: 8px;
            padding: 0.22rem 0.65rem;
            font-size: 0.78rem; font-weight: 900;
            color: #f472b6; letter-spacing: 0.5px;
        }}
        .fav-sep {{ color:{c_muted}; opacity:0.35; font-weight:300; font-size:1rem; }}
        .fav-pill {{
            background: rgba(38,166,154,0.10);
            border: 1px solid rgba(38,166,154,0.25);
            border-radius: 6px; padding: 0.15rem 0.55rem;
            font-size: 0.69rem; font-weight: 800; color: #26A69A;
        }}
        .fav-plus {{ font-size:0.65rem; color:{c_muted}; font-weight:700; }}
        .fav-regime {{
            margin-left: auto;
            font-size: 0.6rem; font-weight: 800;
            text-transform: uppercase; letter-spacing: 0.6px;
            border-radius: 20px; padding: 0.15rem 0.6rem;
            border: 1px solid currentColor; opacity: 0.85;
        }}
        .fav-date {{
            font-size: 0.58rem; color: {c_muted}; opacity: 0.55;
            margin-left: 0.2rem; align-self: center;
        }}
        .fav-card-bot {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            padding: 0.65rem 1rem 0.7rem 1rem;
            gap: 0;
        }}
        .fav-si {{
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            padding: 0.15rem 0;
        }}
        .fav-si:not(:last-child) {{
            border-right: 1px solid {cp_border};
        }}
        .fsl {{
            font-size: 0.51rem; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.6px;
            color: {c_muted}; margin-bottom: 0.18rem; opacity: 0.75;
        }}
        .fsv {{
            font-size: 0.92rem; font-weight: 900;
            color: {c_text}; line-height: 1;
        }}
    """


# ── Panel renderer ────────────────────────────────────────────────────────────

def render_favorites_panel() -> None:
    """Renders the full Saved Strategies panel when toggled open."""
    if not st.session_state.get('show_favorites_panel', False):
        return

    favs      = st.session_state.get('favorites', [])
    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

    # split by type
    _ind_favs   = [f for f in favs if f.get('save_type') == 'indicator']
    _combo_favs = [f for f in favs if f.get('save_type') == 'combo']
    _strat_favs = [f for f in favs if f.get('save_type') not in ('indicator', 'combo')]

    with st.container(key="fav_panel_wrap"):
        # ── header row ────────────────────────────────────────────────
        hc1, hc2 = st.columns([9, 1])
        with hc1:
            count_badge = f"<span class='fav-hdr-count'>{len(favs)}</span>" if favs else ""
            st.markdown(
                f"<div class='fav-hdr'><span class='fav-hdr-icon'>★</span>"
                f"<span class='fav-hdr-title'>Saved Analysis</span>{count_badge}</div>",
                unsafe_allow_html=True)
        with hc2:
            with st.container(key="fav_close_panel"):
                if st.button("✕  Close", key="fav_close_btn", width="stretch"):
                    st.session_state.show_favorites_panel = False
                    st.rerun()

        # ── empty state ───────────────────────────────────────────────
        if not favs:
            st.markdown(
                "<div class='fav-empty'><div class='fav-empty-icon'>☆</div>"
                "<div class='fav-empty-txt'>Nothing saved yet.<br>"
                "Run a <b>Signal Analysis</b> and tap <b>☆ Save</b> on any indicator "
                "or combination card. Also works on <b>Tadawul AI</b> result pages.</div></div>",
                unsafe_allow_html=True)
            return

        # ── helper: render one fav card + delete button ───────────────
        def _fav_card(f_idx: int, fav: dict, label: str, accent: str,
                      extra_pills: list = None):
            _regime = fav.get('best_regime') or ''
            _bc     = _r_colors.get(_regime, '#9e9e9e')
            _wr     = fav.get('win_rate', 0)
            _wr_c   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
            _ag     = fav.get('avg_gain', 0)
            _al     = fav.get('avg_loss', 0)
            _ag_c   = '#26A69A' if _ag >= 1 else ('#FFC107' if _ag > 0 else '#ef5350')
            _sym    = fav.get('symbol', '').replace('.SR', '')
            _disp   = fav.get('pair_display', fav.get('pair', ''))
            _sn     = fav.get('stock_name', '')
            _exp_c  = '#26A69A' if fav.get('expectancy', 0) > 0 else '#ef5350'

            # pills row from pair_display (split by +)
            _parts = [p.strip() for p in _disp.split('+')]
            _pills_html = ''
            for pi, pn in enumerate(_parts):
                _pills_html += f"<span class='fav-pill'>{pn}</span>"
                if pi < len(_parts) - 1:
                    _pills_html += "<span class='fav-plus'>+</span>"

            # settings row (risk/reward + period) for indicators & combos
            _settings_html = ''
            _rv = fav.get('risk_val'); _rw = fav.get('reward_val')
            _pl = fav.get('period_label', '')
            if _rv and _rw:
                _settings_html = (
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;'>"
                    f"R:R {_rv}:{_rw}</span>"
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;margin-left:0.2rem;'>"
                    f"{_pl.split('(')[0].strip() if _pl else ''}</span>"
                )
            _sw = fav.get('signal_window')
            if fav.get('save_type') == 'combo' and _sw:
                _sw_i = int(_sw)
                _sw_lbl = 'Same bar' if _sw_i <= 1 else f'Sync {_sw_i} bars'
                _settings_html += (
                    f"<span style='font-size:0.58rem;color:#9e9e9e;border:1px solid #404040;"
                    f"border-radius:4px;padding:0.1rem 0.4rem;margin-left:0.2rem;'>"
                    f"{_sw_lbl}</span>"
                )

            _card = (
                "<div class='fav-card' style='border-left:3px solid "
                + accent + ";'>"
                "<div class='fav-card-top'>"
                f"<span class='fav-sym'>{_sym}</span>"
                f"<span style='font-size:0.58rem;font-weight:700;color:{accent};"
                f"background:{accent}18;border:1px solid {accent}44;border-radius:4px;"
                f"padding:0.1rem 0.45rem;'>{label}</span>"
                "<span class='fav-sep'>|</span>"
                + _pills_html
                + (_settings_html)
                + (f"<span class='fav-regime' style='color:{_bc};border-color:{_bc};'>{_regime}</span>" if _regime else '')
                + f"<span class='fav-date'>{fav.get('saved_at', '')}</span>"
                "</div>"
                "<div class='fav-card-bot'>"
                f"<div class='fav-si'><span class='fsl'>Win Rate</span><span class='fsv' style='color:{_wr_c}'>{_wr:.1f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Avg Gain</span><span class='fsv' style='color:{_ag_c}'>+{_ag:.2f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Expectancy</span><span class='fsv' style='color:{_exp_c}'>{fav.get('expectancy',0):+.2f}%</span></div>"
                f"<div class='fav-si'><span class='fsl'>Signals</span><span class='fsv'>{fav.get('signals', 0)}</span></div>"
                "</div>"
                "</div>"
            )
            _ec1, _ec2 = st.columns([12, 1])
            with _ec1:
                st.markdown(_card, unsafe_allow_html=True)
            with _ec2:
                if st.button("✕", key=f"fav_del_{f_idx}", width="stretch"):
                    _user = st.session_state.get('auth_username', '')
                    delete_favorite(_user, fav.get('id', ''))
                    st.session_state.favorites = [x for x in favs if x.get('id') != fav.get('id')]
                    st.rerun()

        _global_idx = 0

        # ── Section: Saved Indicators ─────────────────────────────────
        if _ind_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.6rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#4caf50;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#4caf50;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Indicators</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_ind_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _ind_favs:
                _fav_card(_global_idx, _fav, "Indicator", "#4caf50")
                _global_idx += 1

        # ── Section: Saved Combinations ───────────────────────────────
        if _combo_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.9rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#FFD700;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#FFD700;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Combinations</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_combo_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _combo_favs:
                _fav_card(_global_idx, _fav, "Combo", "#FFD700")
                _global_idx += 1

        # ── Section: Saved Strategies (Tadawul AI) ────────────────────
        if _strat_favs:
            st.markdown(
                "<div style='display:flex;align-items:center;gap:0.5rem;"
                "margin:0.9rem 0 0.5rem 0;'>"
                "<span style='width:3px;height:0.9rem;background:#f472b6;border-radius:2px;"
                "flex-shrink:0;display:inline-block;'></span>"
                "<span style='font-size:0.72rem;font-weight:800;color:#f472b6;"
                "text-transform:uppercase;letter-spacing:0.5px;'>Saved Strategies</span>"
                f"<span style='font-size:0.58rem;color:#757575;'>({len(_strat_favs)})</span>"
                "</div>",
                unsafe_allow_html=True)
            for _fav in _strat_favs:
                _parts  = _fav.get('pair', '').split(' + ')
                _pill_a = _parts[0] if _parts else ''
                _pill_b = _parts[1] if len(_parts) > 1 else ''
                _regime = _fav.get('best_regime') or ''
                _bc     = _r_colors.get(_regime, '#9e9e9e')
                _wr     = _fav.get('win_rate', 0)
                _wr_c   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
                _ag     = _fav.get('avg_gain', 0)
                _al     = _fav.get('avg_loss', 0)
                _ag_c   = '#26A69A' if _ag >= 1 else ('#FFC107' if _ag > 0 else '#ef5350')
                _sym    = _fav.get('symbol', '').replace('.SR', '')

                _card = (
                    "<div class='fav-card' style='border-left:3px solid #f472b6;'>"
                    "<div class='fav-card-top'>"
                    f"<span class='fav-sym'>{_sym}</span>"
                    "<span class='fav-sep'>|</span>"
                    f"<span class='fav-pill'>{_pill_a}</span>"
                    "<span class='fav-plus'>+</span>"
                    f"<span class='fav-pill'>{_pill_b}</span>"
                    + (f"<span class='fav-regime' style='color:{_bc};border-color:{_bc};'>{_regime}</span>" if _regime else '')
                    + f"<span class='fav-date'>{_fav.get('saved_at', '')}</span>"
                    "</div>"
                    "<div class='fav-card-bot'>"
                    f"<div class='fav-si'><span class='fsl'>Win Rate</span><span class='fsv' style='color:{_wr_c}'>{_wr:.1f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Avg Gain</span><span class='fsv' style='color:{_ag_c}'>+{_ag:.2f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Avg Loss</span><span class='fsv' style='color:#ef5350'>{_al:.2f}%</span></div>"
                    f"<div class='fav-si'><span class='fsl'>Signals</span><span class='fsv'>{_fav.get('signals', 0)}</span></div>"
                    "</div>"
                    "</div>"
                )
                _ec1, _ec2 = st.columns([12, 1])
                with _ec1:
                    st.markdown(_card, unsafe_allow_html=True)
                with _ec2:
                    if st.button("✕", key=f"fav_del_{_global_idx}", width="stretch"):
                        _user = st.session_state.get('auth_username', '')
                        delete_favorite(_user, _fav.get('id', ''))
                        st.session_state.favorites = [x for x in favs if x.get('id') != _fav.get('id')]
                        st.rerun()
                _global_idx += 1


# ── Internal helper: toggle a favorite in session_state + DB ─────────────────

def _toggle_favorite(fav_id: str, new_fav: dict | None) -> None:
    """
    Save or remove a favorite.
    If new_fav is None  → remove.
    If new_fav is dict  → add.
    Raises on error so callers can show a toast.
    """
    _user = st.session_state.get('auth_username', '')
    if not _user:
        raise RuntimeError("Not logged in")
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    _cur  = st.session_state.favorites
    _exists = any(f.get('id') == fav_id for f in _cur)

    if _exists:
        delete_favorite(_user, fav_id)
        st.session_state.favorites = [f for f in _cur if f.get('id') != fav_id]
    elif new_fav is not None:
        upsert_favorite(_user, new_fav)
        st.session_state.favorites = _cur + [new_fav]


# ── Save button (combo cards) ─────────────────────────────────────────────────

def render_save_button(i: int, ka: str, kb: str, row: dict, top_names: dict) -> None:
    """
    Renders the ☆/★ Save Strategy toggle button below a combination card.
    Call this right after st.markdown(card, ...) inside the pair_data loop.
    """
    _sym      = st.session_state.get('analyzed_symbol', '')
    _fav_id   = f"{_sym}__{ka}__{kb}"
    _cur_favs = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl  = "★  Saved — click to remove" if _is_saved else "☆  Save Strategy"

    _entry_price = None
    _df = st.session_state.get('df')
    if _df is not None:
        try:
            _entry_price = float(_df['Close'].iloc[-1])
        except Exception:
            pass

    _new_fav = {
        'id':            _fav_id,
        'symbol':        _sym,
        'stock_name':    st.session_state.get('analyzed_stock_name', ''),
        'pair':          f"{ka} + {kb}",
        'pair_display':  f"{top_names.get(ka, ka)} + {top_names.get(kb, kb)}",
        'win_rate':      row['win_rate'],
        'profit_factor': row['profit_factor'],
        'expectancy':    row['expectancy'],
        'avg_gain':      row['avg_gain'],
        'avg_loss':      row['avg_loss'],
        'signals':       row['total'],
        'best_regime':   row['best_regime'],
        'saved_at':      _today_date.today().strftime('%b %d, %Y'),
        'entry_price':   _entry_price,
        'save_type':     'strategy',
    }

    _sv_col, _ = st.columns([2, 8])
    with _sv_col:
        st.button(
            _btn_lbl,
            key=f"fav_save_{i}_{ka}_{kb}",
            width="stretch",
            on_click=_toggle_favorite,
            args=(_fav_id, None if _is_saved else _new_fav),
        )


# ── Save button: single indicator ─────────────────────────────────────────────

def render_save_indicator_button(idx: int, ind: dict, risk_val: int,
                                  reward_val: int, period_label: str) -> None:
    """☆/★ save button for a single indicator card."""
    _sym         = st.session_state.get('analyzed_symbol', '')
    _period_key  = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _fav_id      = f"ind__{_sym}__{ind['key']}__r{risk_val}x{reward_val}__{_period_key}"
    _cur_favs    = st.session_state.get('favorites', [])
    _is_saved    = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl     = "★  Saved — click to remove" if _is_saved else f"☆  Save  {ind['name']}"

    _new_fav = {
        'id':            _fav_id,
        'symbol':        _sym,
        'stock_name':    st.session_state.get('analyzed_stock_name', ''),
        'pair':          ind['key'],
        'pair_display':  ind['name'],
        'win_rate':      ind['win_rate'],
        'profit_factor': ind['profit_factor'],
        'expectancy':    ind['expectancy'],
        'avg_gain':      ind['avg_gain'],
        'avg_loss':      ind['avg_loss'],
        'signals':       ind['total'],
        'best_regime':   ind.get('best_regime', ''),
        'saved_at':      _today_date.today().strftime('%b %d, %Y'),
        'entry_price':   None,
        'save_type':     'indicator',
        'risk_val':      risk_val,
        'reward_val':    reward_val,
        'period_label':  period_label,
        'combo_indicators': ind['name'],
    }

    st.button(
        _btn_lbl,
        key=f"fav_save_ind_{idx}_{ind['key']}",
        width="stretch",
        on_click=_toggle_favorite,
        args=(_fav_id, None if _is_saved else _new_fav),
    )


# ── Save button: N-way combo ─────────────────────────────────────────────────

def render_save_combo_button(idx: int, row: dict, all_names: dict,
                              risk_val: int, reward_val: int, period_label: str,
                              signal_window: int = 1,
                              regime_tag: str | None = None,
                              button_label: str | None = None) -> None:
    """☆/★ save button for a combination card in the Signal Analysis tab."""
    _sym         = st.session_state.get('analyzed_symbol', '')
    _key_str     = '__'.join(sorted(row['indicators']))
    _period_key  = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _regime_tag  = (regime_tag or '').strip().upper()
    _regime_key  = f"__reg{_regime_tag}" if _regime_tag else ""
    _window_key  = f"__w{int(signal_window)}"
    _fav_id      = f"combo__{_sym}__{_key_str}__r{risk_val}x{reward_val}__{_period_key}{_window_key}{_regime_key}"
    _cur_favs    = st.session_state.get('favorites', [])
    _is_saved    = any(f.get('id') == _fav_id for f in _cur_favs)
    _ind_names   = [all_names.get(k, k) for k in row['indicators']]
    _display     = ' + '.join(_ind_names)
    _btn_lbl     = "★  Saved — click to remove" if _is_saved else (button_label or f"☆  Save  {row['size']}-Way Combo")

    _new_fav = {
        'id':               _fav_id,
        'symbol':           _sym,
        'stock_name':       st.session_state.get('analyzed_stock_name', ''),
        'pair':             ' + '.join(row['indicators']),
        'pair_display':     _display,
        'win_rate':         row['win_rate'],
        'profit_factor':    row['profit_factor'],
        'expectancy':       row['expectancy'],
        'avg_gain':         row['avg_gain'],
        'avg_loss':         row['avg_loss'],
        'signals':          row['total'],
        'best_regime':      _regime_tag or row.get('best_regime', ''),
        'saved_at':         _today_date.today().strftime('%b %d, %Y'),
        'entry_price':      None,
        'save_type':        'combo',
        'risk_val':         risk_val,
        'reward_val':       reward_val,
        'period_label':     period_label,
        'combo_indicators': _display,
        'signal_window':    int(signal_window),
    }

    st.button(
        _btn_lbl,
        key=f"fav_save_combo_{idx}_{_key_str[:30]}",
        width="stretch",
        on_click=_toggle_favorite,
        args=(_fav_id, None if _is_saved else _new_fav),
    )


# ── Full-page Saved Analysis view ─────────────────────────────────────────────

def render_saved_page() -> None:
    """Renders the full Saved Analysis page (replaces main content)."""
    favs      = st.session_state.get('favorites', [])
    _r_colors = {'TREND': '#4A9EFF', 'RANGE': '#FFC107', 'VOLATILE': '#FF6B6B'}

    # Three categories: Indicators, Combinations, Regime Champions
    _ind_favs   = [f for f in favs if f.get('save_type') == 'indicator']
    _rc_favs    = [f for f in favs if f.get('save_type') == 'regime_champion']
    _combo_favs = [f for f in favs if f.get('save_type') not in ('indicator', 'regime_champion')]

    # ── page CSS ─────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── page wrapper ─────────────────────────────────────────────── */
    .sv-page { max-width: 960px; margin: 0 auto; }

    /* ── back button ──────────────────────────────────────────────── */
    .st-key-sv_back .stButton > button {
        background: transparent !important;
        border: 1px solid #272727 !important;
        border-radius: 10px !important; color: #606060 !important;
        font-size: 0.76rem !important; font-weight: 700 !important;
        min-height: 2.1rem !important; padding: 0 1rem !important;
        transition: all .15s ease !important;
    }
    .st-key-sv_back .stButton > button:hover {
        background: rgba(255,255,255,0.04) !important;
        border-color: #404040 !important; color: #e0e0e0 !important;
    }

    /* ── sort select ──────────────────────────────────────────────── */
    .st-key-sv_sort [data-baseweb="select"] {
        background: #161616 !important; border: 1px solid #272727 !important;
        border-radius: 10px !important; min-height: 2.1rem !important;
    }
    .st-key-sv_sort [data-baseweb="select"] * {
        color: #9e9e9e !important; font-size: 0.72rem !important;
        font-weight: 600 !important;
    }

    /* ── filter pills ─────────────────────────────────────────────── */
    .st-key-sv_filters .stButton > button {
        background: #161616 !important;
        border: 1px solid #272727 !important; border-radius: 20px !important;
        color: #606060 !important; font-size: 0.7rem !important;
        font-weight: 700 !important; min-height: 1.9rem !important;
        padding: 0 1rem !important; white-space: nowrap !important;
        transition: all .15s ease !important;
    }
    .st-key-sv_filters .stButton > button:hover {
        background: rgba(38,166,154,0.06) !important;
        border-color: rgba(38,166,154,0.25) !important; color: #26A69A !important;
    }
    [class*="st-key-svf_on"] .stButton > button {
        background: rgba(38,166,154,0.10) !important;
        border: 1px solid rgba(38,166,154,0.35) !important;
        color: #26A69A !important; font-weight: 800 !important;
        box-shadow: 0 0 12px rgba(38,166,154,0.08) !important;
    }

    /* ── delete buttons ───────────────────────────────────────────── */
    [class*="st-key-sv_del_"] .stButton > button {
        background: transparent !important;
        border: 1px solid rgba(239,83,80,0.12) !important;
        border-radius: 10px !important; color: rgba(239,83,80,0.30) !important;
        height: 100% !important; min-height: 100% !important;
        font-size: 0.85rem !important; padding: 0 !important;
        transition: all .15s ease !important;
    }
    [class*="st-key-sv_del_"] .stButton > button:hover {
        background: rgba(239,83,80,0.08) !important;
        border-color: rgba(239,83,80,0.50) !important; color: #ef5350 !important;
        box-shadow: 0 0 15px rgba(239,83,80,0.12) !important;
    }

    /* ── hero stat cards ──────────────────────────────────────────── */
    .sv-hero { display: grid; grid-template-columns: repeat(3, 1fr);
               gap: 0.7rem; margin-bottom: 1.4rem; }
    .sv-hc { background: #1b1b1b; border: 1px solid #272727;
             border-radius: 14px; padding: 1rem 1.2rem;
             position: relative; overflow: hidden; }
    .sv-hc::before { content: ''; position: absolute; top: 0; left: 0; right: 0;
                     height: 3px; border-radius: 14px 14px 0 0; }
    .sv-hc-val { font-size: 1.8rem; font-weight: 900; line-height: 1;
                 letter-spacing: -1px; }
    .sv-hc-lbl { font-size: 0.6rem; color: #606060; font-weight: 700;
                 text-transform: uppercase; letter-spacing: 0.6px; margin-top: 0.3rem; }

    /* ── section header ───────────────────────────────────────────── */
    .sv-sec { display: flex; align-items: center; gap: 0.55rem;
              margin: 1.6rem 0 0.7rem 0; }
    .sv-sec-bar { width: 3px; height: 1.1rem; border-radius: 2px; flex-shrink: 0; }
    .sv-sec-t { font-size: 0.76rem; font-weight: 800;
                text-transform: uppercase; letter-spacing: 0.6px; }
    .sv-sec-n { font-size: 0.6rem; color: #606060; font-weight: 600; }

    /* ── card ──────────────────────────────────────────────────────── */
    .sv-card { background: #1b1b1b; border: 1px solid #272727;
               border-radius: 14px; overflow: hidden; margin-bottom: 0.55rem;
               transition: border-color .15s ease, box-shadow .15s ease; }
    .sv-card:hover { border-color: #363636;
                     box-shadow: 0 4px 20px rgba(0,0,0,0.3); }

    /* card header */
    .sv-ch { display: flex; align-items: center; gap: 0.6rem;
             padding: 0.85rem 1.1rem; flex-wrap: wrap; }
    .sv-sym { font-size: 0.88rem; font-weight: 900; color: #26A69A;
              background: rgba(38,166,154,0.08); border: 1px solid rgba(38,166,154,0.20);
              border-radius: 8px; padding: 0.2rem 0.6rem; letter-spacing: 0.5px; }
    .sv-sname { font-size: 0.62rem; color: #505050; font-weight: 600; }
    .sv-type { font-size: 0.55rem; font-weight: 800; text-transform: uppercase;
               letter-spacing: 0.5px; border-radius: 20px; padding: 0.15rem 0.65rem;
               border: 1px solid; }
    .sv-pills { display: flex; flex-wrap: wrap; align-items: center; gap: 0.25rem;
                flex: 1; min-width: 0; }
    .sv-pill { font-size: 0.68rem; font-weight: 800; border-radius: 6px;
               padding: 0.15rem 0.5rem; border: 1px solid; }
    .sv-plus { font-size: 0.62rem; color: #404040; font-weight: 700; }
    .sv-tag { font-size: 0.55rem; font-weight: 700; border-radius: 5px;
              padding: 0.12rem 0.45rem; border: 1px solid; white-space: nowrap; }
    .sv-date { font-size: 0.55rem; color: #505050; font-weight: 600; margin-left: auto; }

    /* card stats grid */
    .sv-sg { display: grid; grid-template-columns: repeat(6, 1fr);
             background: #161616; }
    .sv-si { padding: 0.65rem 0.4rem; text-align: center;
             border-right: 1px solid #222222; position: relative; }
    .sv-si:last-child { border-right: none; }
    .sv-si::before { content: ''; position: absolute; top: 0; left: 0; right: 0;
                     height: 2px; }
    .sv-sl { font-size: 0.48rem; font-weight: 700; text-transform: uppercase;
             letter-spacing: 0.7px; color: #505050; margin-bottom: 0.2rem; }
    .sv-sv { font-size: 0.88rem; font-weight: 900; line-height: 1; }

    /* ── empty state ──────────────────────────────────────────────── */
    .sv-empty { display: flex; flex-direction: column; align-items: center;
                gap: 0.8rem; padding: 5rem 2rem; text-align: center; }
    .sv-empty-ring { width: 64px; height: 64px; border-radius: 50%;
                     border: 2px solid #272727; display: flex;
                     align-items: center; justify-content: center;
                     font-size: 1.6rem; color: #363636; }
    .sv-empty-t { font-size: 0.95rem; font-weight: 800; color: #606060; }
    .sv-empty-s { font-size: 0.72rem; color: #404040; max-width: 340px;
                  line-height: 1.7; }
    </style>
    """, unsafe_allow_html=True)

    _total = len(favs)

    # ── header row ────────────────────────────────────────────────────────
    _hc = st.columns([1.2, 6, 2.5])
    with _hc[0]:
        with st.container(key="sv_back"):
            if st.button("←  Back", key="sv_back_btn", width="stretch"):
                st.session_state.show_saved_page = False
                st.rerun()
    with _hc[1]:
        st.markdown(
            f"<div style='display:flex;align-items:baseline;gap:0.6rem;padding-top:0.15rem;'>"
            f"<span style='font-size:1.15rem;font-weight:900;color:#e0e0e0;"
            f"letter-spacing:-0.3px;'>Saved Analysis</span>"
            f"<span style='font-size:0.65rem;font-weight:700;color:#505050;'>"
            f"{_total} item{'s' if _total != 1 else ''}</span></div>",
            unsafe_allow_html=True)
    with _hc[2]:
        with st.container(key="sv_sort"):
            _sort_by = st.selectbox(
                "Sort", ["Win Rate ↓", "Signals ↓", "Date Saved ↓"],
                index=0, key="sv_sort_sel", label_visibility="collapsed")

    # ── hero stats ─────────────────────────────────────────────────────────
    # compute best win rate across all
    _all_wr = [f.get('win_rate', 0) for f in favs]
    _best_wr = max(_all_wr) if _all_wr else 0
    _best_wr_c = '#26A69A' if _best_wr >= 55 else ('#FFC107' if _best_wr >= 45 else '#ef5350')

    st.markdown(
        f"<div class='sv-hero'>"
        f"<div class='sv-hc' style='--c:#26A69A;'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#26A69A,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#26A69A;'>{_total}</div>"
        f"<div class='sv-hc-lbl'>Total Saved</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#4caf50,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#4caf50;'>{len(_ind_favs)}</div>"
        f"<div class='sv-hc-lbl'>Indicators</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#FFD700,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#FFD700;'>{len(_combo_favs)}</div>"
        f"<div class='sv-hc-lbl'>Combinations</div></div>"
        f"<div class='sv-hc'>"
        f"<div style='position:absolute;top:0;left:0;right:0;height:3px;"
        f"background:linear-gradient(90deg,#a78bfa,transparent);border-radius:14px 14px 0 0;'></div>"
        f"<div class='sv-hc-val' style='color:#a78bfa;'>{len(_rc_favs)}</div>"
        f"<div class='sv-hc-lbl'>Champions</div></div>"
        f"</div>",
        unsafe_allow_html=True)

    # ── filter tabs ────────────────────────────────────────────────────────
    if 'sp_filter' not in st.session_state:
        st.session_state.sp_filter = 'all'
    _cur = st.session_state.sp_filter
    _fopts = [
        ('all',       f'All  ({_total})'),
        ('indicator', f'Indicators  ({len(_ind_favs)})'),
        ('combo',     f'Combinations  ({len(_combo_favs)})'),
        ('champions', f'Champions  ({len(_rc_favs)})'),
    ]
    with st.container(key="sv_filters"):
        _fc = st.columns(len(_fopts))
        for _i, (_k, _l) in enumerate(_fopts):
            _ak = 'svf_on' if _cur == _k else 'svf_off'
            with st.container(key=f"{_ak}_{_i}"):
                with _fc[_i]:
                    if st.button(_l, key=f"svf_{_k}", width="stretch"):
                        st.session_state.sp_filter = _k
                        st.rerun()

    # ── empty state ────────────────────────────────────────────────────────
    if not favs:
        st.markdown(
            "<div class='sv-empty'>"
            "<div class='sv-empty-ring'>☆</div>"
            "<div class='sv-empty-t'>No saved analysis yet</div>"
            "<div class='sv-empty-s'>Run a <b>Signal Analysis</b> and tap "
            "<b>☆ Save</b> on any indicator or combination card to start "
            "building your collection.</div></div>",
            unsafe_allow_html=True)
        return

    # ── sort helper ────────────────────────────────────────────────────────
    def _sort(lst):
        if _sort_by.startswith('Win Rate'):
            return sorted(lst, key=lambda x: x.get('win_rate', 0), reverse=True)
        if _sort_by.startswith('Signals'):
            return sorted(lst, key=lambda x: x.get('signals', 0), reverse=True)
        return list(reversed(lst))  # Date Saved ↓  (newest first)

    # ── card renderer ──────────────────────────────────────────────────────
    def _card(idx: int, fav: dict, accent: str, type_lbl: str):
        _sym  = fav.get('symbol', '').replace('.SR', '')
        _sn   = fav.get('stock_name', '')
        _disp = fav.get('pair_display', fav.get('pair', ''))
        _reg  = fav.get('best_regime') or ''
        _rc   = _r_colors.get(_reg, '#606060')
        _wr   = fav.get('win_rate', 0)
        _wc   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
        _pf   = fav.get('profit_factor', 0)
        _pc   = '#26A69A' if _pf >= 1.5 else ('#FFC107' if _pf >= 1 else '#ef5350')
        _ea   = fav.get('expectancy', 0)
        _ec   = '#26A69A' if _ea > 0 else '#ef5350'
        _ag   = fav.get('avg_gain', 0)
        _ac   = '#26A69A' if _ag > 0 else '#ef5350'
        _al   = fav.get('avg_loss', 0)
        _sig  = fav.get('signals', 0)
        _rv   = fav.get('risk_val')
        _rw   = fav.get('reward_val')
        _pl   = (fav.get('period_label', '') or '').split('(')[0].strip()
        _sw   = fav.get('signal_window')
        _dt   = fav.get('saved_at', '')

        # pills
        _parts = [p.strip() for p in _disp.split('+')]
        _pills = ''
        for _pi, _pn in enumerate(_parts):
            _pills += (
                f"<span class='sv-pill' style='color:{accent};"
                f"border-color:{accent}33;background:{accent}0A;'>{_pn}</span>"
            )
            if _pi < len(_parts) - 1:
                _pills += "<span class='sv-plus'>+</span>"

        _tags = ''
        if _rv and _rw:
            _tags += (f"<span class='sv-tag' style='color:#64b5f6;"
                      f"border-color:rgba(100,181,246,0.25);background:rgba(100,181,246,0.06);'>"
                      f"R:R {_rv}:{_rw}</span>")
        if _pl:
            _tags += (f"<span class='sv-tag' style='color:#ce93d8;"
                      f"border-color:rgba(206,147,216,0.25);background:rgba(206,147,216,0.06);'>"
                      f"{_pl}</span>")
        if fav.get('save_type') == 'combo' and _sw:
            _sw_i = int(_sw)
            _sw_lbl = 'Same bar' if _sw_i <= 1 else f'Sync {_sw_i} bars'
            _tags += (f"<span class='sv-tag' style='color:#90caf9;'"
                      f"border-color:rgba(144,202,249,0.25);background:rgba(144,202,249,0.06);'>"
                      f"{_sw_lbl}</span>")
        if _reg:
            _tags += (f"<span class='sv-tag' style='color:{_rc};"
                      f"border-color:{_rc}33;background:{_rc}0A;'>{_reg}</span>")

        _h = (
            f"<div class='sv-card'>"
            # header
            f"<div class='sv-ch'>"
            f"<span class='sv-sym'>{_sym}</span>"
            + (f"<span class='sv-sname'>{_sn}</span>" if _sn else '')
            + f"<span class='sv-type' style='color:{accent};"
            f"border-color:{accent}33;background:{accent}0A;'>{type_lbl}</span>"
            f"<div class='sv-pills'>{_pills}</div>"
            + _tags
            + f"<span class='sv-date'>{_dt}</span>"
            f"</div>"
            # stats grid
            f"<div class='sv-sg'>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_wc};'></div>"
            f"<div class='sv-sl'>Win Rate</div>"
            f"<div class='sv-sv' style='color:{_wc};'>{_wr:.1f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_pc};'></div>"
            f"<div class='sv-sl'>Profit Factor</div>"
            f"<div class='sv-sv' style='color:{_pc};'>{_pf:.2f}</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_ec};'></div>"
            f"<div class='sv-sl'>Expectancy</div>"
            f"<div class='sv-sv' style='color:{_ec};'>{_ea:+.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:{_ac};'></div>"
            f"<div class='sv-sl'>Avg Gain</div>"
            f"<div class='sv-sv' style='color:{_ac};'>+{_ag:.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:#ef5350;'></div>"
            f"<div class='sv-sl'>Avg Loss</div>"
            f"<div class='sv-sv' style='color:#ef5350;'>{_al:.2f}%</div></div>"
            f"<div class='sv-si'>"
            f"<div style='position:absolute;top:0;left:0;right:0;height:2px;background:#505050;'></div>"
            f"<div class='sv-sl'>Signals</div>"
            f"<div class='sv-sv' style='color:#9e9e9e;'>{_sig}</div></div>"
            f"</div></div>"
        )
        _c1, _c2 = st.columns([14, 1])
        with _c1:
            st.markdown(_h, unsafe_allow_html=True)
        with _c2:
            with st.container(key=f"sv_del_{idx}"):
                if st.button("✕", key=f"sv_rm_{idx}", width="stretch"):
                    _user = st.session_state.get('auth_username', '')
                    delete_favorite(_user, fav.get('id', ''))
                    st.session_state.favorites = [x for x in favs if x.get('id') != fav.get('id')]
                    st.rerun()

    # ── render sections ───────────────────────────────────────────────────
    _gidx = 0
    _active = st.session_state.get('sp_filter', 'all')

    def _section(title, color, flist, tlbl):
        nonlocal _gidx
        if not flist:
            return
        st.markdown(
            f"<div class='sv-sec'>"
            f"<div class='sv-sec-bar' style='background:{color};'></div>"
            f"<span class='sv-sec-t' style='color:{color};'>{title}</span>"
            f"<span class='sv-sec-n'>({len(flist)})</span></div>",
            unsafe_allow_html=True)
        for _f in _sort(flist):
            _card(_gidx, _f, color, tlbl)
            _gidx += 1

    if _active in ('all', 'indicator'):
        _section("Indicators", "#4caf50", _ind_favs, "Indicator")
    if _active in ('all', 'combo'):
        _section("Combinations", "#FFD700", _combo_favs, "Combination")
    if _active in ('all', 'champions'):
        _section("Regime Champions", "#a78bfa", _rc_favs, "Champion")


# ── Save Strategy button ──────────────────────────────────────────────────────
# Uses on_click callback — NO @st.fragment in loops (causes identity bugs).
# The callback fires synchronously before the rerun, so the button label
# updates on the very next render with zero lag.

def _rc_toggle(fav_id: str, new_fav: dict) -> None:
    """on_click callback: toggle a regime-champion strategy save/remove."""
    _user = st.session_state.get('auth_username', '')
    if not _user:
        st.session_state['_rc_toast'] = ("Not logged in", "❌")
        return
    _cur = st.session_state.get('favorites', [])
    _exists = any(f.get('id') == fav_id for f in _cur)
    try:
        if _exists:
            delete_favorite(_user, fav_id)
            st.session_state.favorites = [f for f in _cur if f.get('id') != fav_id]
            st.session_state['_rc_toast'] = ("Strategy removed", "🗑️")
        elif new_fav is not None:
            upsert_favorite(_user, new_fav)
            st.session_state.favorites = _cur + [new_fav]
            st.session_state['_rc_toast'] = ("Strategy saved!", "⭐")
    except Exception as _e:
        st.session_state['_rc_toast'] = (f"Save failed: {_e}", "❌")


def render_save_regime_champion_button(row, regime_key, period_label, save_idx):
    _sym    = st.session_state.get('analyzed_symbol', '')
    _pk     = period_label.replace(' ', '').replace('(', '_').replace(')', '').replace('/', '')
    _combo  = row.get('label', '')
    _fav_id = f"rc__{_sym}__{regime_key}__{_pk}__r{save_idx}"

    _new_fav = {
        'id':               _fav_id,
        'symbol':           _sym,
        'stock_name':       st.session_state.get('analyzed_stock_name', ''),
        'pair':             _combo,
        'pair_display':     _combo,
        'win_rate':         row.get('win_rate', 0),
        'profit_factor':    row.get('profit_factor', 0),
        'expectancy':       row.get('expectancy', 0),
        'avg_gain':         row.get('avg_gain', 0),
        'avg_loss':         row.get('avg_loss', 0),
        'signals':          row.get('total', 0),
        'best_regime':      regime_key,
        'saved_at':         _today_date.today().strftime('%b %d, %Y'),
        'save_type':        'regime_champion',
        'period_label':     period_label,
        'combo_indicators': _combo,
        'signal_window':    row.get('signal_window', 1),
        'risk_val':         st.session_state.get('sa_risk_val', 1),
        'reward_val':       st.session_state.get('sa_reward_val', 2),
    }

    _cur_favs = st.session_state.get('favorites', [])
    _is_saved = any(f.get('id') == _fav_id for f in _cur_favs)
    _btn_lbl  = "★  Strategy Saved  ·  Click to Remove" if _is_saved else "☆  Save Strategy"

    st.button(
        _btn_lbl,
        key=f"sb_{save_idx}_{regime_key}",
        use_container_width=True,
        on_click=_rc_toggle,
        args=(_fav_id, _new_fav),
    )


# ── Saved Strategies full-page view ───────────────────────────────────────────

def render_champions_vault_page():
    favs    = st.session_state.get('favorites', [])
    rc_favs = [f for f in favs if f.get('save_type') == 'regime_champion']
    _user   = st.session_state.get('auth_username', '')

    _REGIME_META = {
        'TREND':    ('#26A69A', '↗', 'Trend'),
        'RANGE':    ('#4A9EFF', '↔', 'Range'),
        'VOLATILE': ('#FF6B6B', '⚡', 'Volatile'),
    }
    _PERIODS = ['Short (5d)', 'Medium (63d)', 'Long (252d)']
    _PERIOD_SHORT = {'Short (5d)': ('Short', '5D'), 'Medium (63d)': ('Medium', '63D'), 'Long (252d)': ('Long', '252D')}

    st.markdown("""
    <style>
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] { display:none !important; }

    .main .block-container, div.block-container {
        max-width: 96% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        padding-top: 1.6rem !important;
        padding-bottom: 5rem !important;
    }

    /* ════════════════════════════════════════
       TOP BAR  (title + KPIs inline)
    ════════════════════════════════════════ */
    .ss-topbar {
        display:flex; align-items:center; gap:1.2rem;
        margin-bottom:1.6rem; flex-wrap:wrap;
    }
    .ss-topbar-title {
        font-size:1.55rem; font-weight:900; color:#e8e8e8;
        letter-spacing:-0.5px; white-space:nowrap;
    }
    .ss-topbar-sub {
        font-size:0.74rem; color:#3a3a3a; font-weight:600;
        white-space:nowrap;
    }
    .ss-topbar-divider {
        width:1px; height:2rem; background:#222; flex-shrink:0;
    }
    .ss-kpi-inline {
        display:flex; align-items:center; gap:0.3rem;
    }
    .ss-kpi-inline-val {
        font-size:1.15rem; font-weight:900; line-height:1;
    }
    .ss-kpi-inline-lbl {
        font-size:0.63rem; font-weight:700; color:#3a3a3a;
        text-transform:uppercase; letter-spacing:0.8px;
        margin-top:0.15rem;
    }
    .ss-kpi-dot {
        width:6px; height:6px; border-radius:50%; flex-shrink:0;
        margin-right:0.2rem; margin-bottom:0.05rem;
    }

    /* ── back button ── */
    .st-key-cv_back_wrap .stButton > button {
        background:transparent !important;
        border:1px solid #252525 !important;
        border-radius:8px !important; color:#404040 !important;
        font-size:0.72rem !important; font-weight:700 !important;
        padding:0.45rem 0.9rem !important;
        height:auto !important; min-height:auto !important;
        transition:all 0.12s ease !important; letter-spacing:0.2px !important;
    }
    .st-key-cv_back_wrap .stButton > button:hover {
        border-color:#404040 !important; color:#c0c0c0 !important;
    }

    /* ════════════════════════════════════════
       STOCK ROW  (full-width horizontal band)
    ════════════════════════════════════════ */
    .ss-stock-row {
        border:1px solid #b8860b55;
        border-radius:12px;
        margin-bottom:0.7rem;
        overflow:hidden;
        background:#141414;
        box-shadow:0 0 0 1px #b8860b18;
    }
    .ss-stock-row:hover {
        border-color:#DAA52088;
        box-shadow:0 0 0 1px #DAA52033;
    }

    /* stock label strip */
    .ss-stock-label {
        display:flex; align-items:center; gap:0.65rem;
        padding:0.6rem 1rem 0.55rem;
        background:#191919;
        border-bottom:1px solid #b8860b33;
    }
    .ss-stock-sym {
        font-size:0.95rem; font-weight:900; color:#d0d0d0;
        letter-spacing:0.2px;
    }
    .ss-stock-name {
        font-size:0.7rem; color:#383838; font-weight:600;
    }
    .ss-stock-count {
        margin-left:auto;
        font-size:0.62rem; font-weight:800; letter-spacing:0.6px;
        color:#383838; text-transform:uppercase;
    }

    /* inner 3-col grid */
    .ss-period-grid {
        display:grid; grid-template-columns:repeat(3,1fr);
    }
    .ss-period-col {
        border-right:1px solid #1a1a1a; padding:0.5rem 0.65rem 0.55rem;
    }
    .ss-period-col:last-child { border-right:none; }

    .ss-period-title {
        font-size:0.65rem; font-weight:800; color:#5a5a5a;
        text-transform:uppercase; letter-spacing:1px;
        margin-bottom:0.4rem; display:flex; align-items:center; gap:0.3rem;
    }
    .ss-period-title-dot {
        width:5px; height:5px; border-radius:50%; background:#a78bfa; flex-shrink:0;
    }

    /* ════════════════════════════════════════
       STRATEGY CHIP  (single row, minimal)
    ════════════════════════════════════════ */
    .ss-chip {
        display:flex; align-items:center; gap:0;
        background:#0f0f0f; border:1px solid #1d1d1d;
        border-radius:6px; overflow:hidden;
        margin-bottom:0.3rem;
        transition:border-color 0.1s;
    }
    .ss-chip:hover { border-color:#2a2a2a; }
    .ss-chip-bar { width:2px; flex-shrink:0; align-self:stretch; }
    .ss-chip-body {
        flex:1; min-width:0; padding:0.32rem 0.5rem;
        display:flex; align-items:center; gap:0.4rem;
    }
    .ss-chip-regime {
        font-size:0.6rem; font-weight:800; padding:0.18rem 0.52rem;
        border-radius:20px; text-transform:uppercase; letter-spacing:0.3px;
        white-space:nowrap; flex-shrink:0; line-height:1.4;
        border:none;
    }
    .ss-chip-name {
        font-size:0.72rem; font-weight:700; color:#888;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
        flex:1; min-width:0; line-height:1.3;
    }
    .ss-chip-wr {
        font-size:0.72rem; font-weight:800;
        white-space:nowrap; flex-shrink:0; padding-right:0.1rem;
    }
    .ss-chip-sigs {
        font-size:0.58rem; font-weight:700; color:#363636;
        white-space:nowrap; flex-shrink:0;
    }

    /* ── empty column placeholder ── */
    .ss-col-empty {
        font-size:0.68rem; color:#1e1e1e; font-weight:600;
        padding:0.25rem 0; letter-spacing:0.3px;
    }

    /* ── remove button ── */
    [class*="st-key-ssrm_"] .stButton > button {
        background:transparent !important; border:none !important;
        color:#242424 !important;
        font-size:0.62rem !important; font-weight:700 !important;
        padding:0.25rem 0.35rem !important;
        height:auto !important; min-height:auto !important;
        transition:color 0.1s ease !important; line-height:1 !important;
    }
    [class*="st-key-ssrm_"] .stButton > button:hover {
        color:#ef5350 !important;
    }

    /* ════════════════════════════════════════
       SECTION DIVIDER
    ════════════════════════════════════════ */
    .ss-section-divider {
        display:flex; align-items:center; gap:0.8rem;
        margin:2.2rem 0 1.1rem;
    }
    .ss-section-line { flex:1; height:1px; background:#1a1a1a; }
    .ss-section-lbl {
        font-size:0.82rem; font-weight:800; color:#383838;
        text-transform:uppercase; letter-spacing:1.2px; white-space:nowrap;
        display:flex; align-items:center; gap:0.45rem;
    }
    .ss-section-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }

    /* ════════════════════════════════════════
       LIVE SIGNAL CARDS
    ════════════════════════════════════════ */
    .ls-card {
        background:#111; border:1px solid #1e1e1e;
        border-radius:12px; overflow:hidden;
        margin-bottom:0.6rem;
        transition:border-color 0.15s;
    }
    .ls-card:hover { border-color:#2a2a2a; }
    .ls-card-fire { border-color:#26A69A22 !important; }
    .ls-card-fire:hover { border-color:#26A69A55 !important; }

    .ls-top {
        display:flex; align-items:center; gap:0.65rem;
        padding:0.65rem 1rem; border-bottom:1px solid #181818;
        flex-wrap:wrap;
    }
    .ls-sym {
        font-size:0.9rem; font-weight:900; color:#c8c8c8;
        letter-spacing:0.2px; white-space:nowrap;
    }
    .ls-tag {
        font-size:0.6rem; font-weight:800; padding:0.14rem 0.48rem;
        border-radius:20px; border:none; text-transform:uppercase;
        letter-spacing:0.4px; white-space:nowrap;
    }
    .ls-combo-name {
        font-size:0.76rem; font-weight:600; color:#3a3a3a;
        flex:1; min-width:0; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis;
    }
    .ls-badge-fire {
        font-size:0.62rem; font-weight:800; padding:0.18rem 0.6rem;
        border-radius:4px; white-space:nowrap; flex-shrink:0;
        background:rgba(38,166,154,0.1); border:1px solid rgba(38,166,154,0.3);
        color:#26A69A; letter-spacing:0.4px; text-transform:uppercase;
    }

    /* indicator pills row */
    .ls-pills { display:flex; flex-wrap:wrap; gap:0.28rem; padding:0.45rem 1rem; }
    .ls-pill {
        font-size:0.7rem; font-weight:700; padding:0.16rem 0.5rem;
        border-radius:4px; border:1px solid; line-height:1.4;
    }

    /* price ladder — 4 cells */
    .ls-ladder {
        display:grid; grid-template-columns:repeat(4,1fr);
        border-top:1px solid #181818;
    }
    .ls-cell {
        padding:0.65rem 0.9rem; border-right:1px solid #181818;
        position:relative;
    }
    .ls-cell:last-child { border-right:none; }
    .ls-cell-top { position:absolute; top:0; left:0; right:0; height:1px; }
    .ls-cell-lbl {
        font-size:0.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.8px; color:#363636; margin-bottom:0.28rem;
    }
    .ls-cell-val {
        font-size:1.2rem; font-weight:900; line-height:1; letter-spacing:-0.2px;
    }
    .ls-cell-sub {
        font-size:0.72rem; font-weight:600; margin-top:0.18rem; color:#363636;
    }

    /* quiet/watching row */
    .ls-quiet {
        display:flex; align-items:center; gap:0.55rem;
        background:#0d0d0d; border:1px solid #181818;
        border-radius:8px; padding:0.45rem 0.8rem;
        margin-bottom:0.3rem; flex-wrap:wrap;
    }
    .ls-quiet-sym { font-size:0.82rem; font-weight:800; color:#545454; white-space:nowrap; }
    .ls-quiet-combo { font-size:0.72rem; color:#3a3a3a; flex:1; min-width:0;
                      white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .ls-quiet-prog { font-size:0.62rem; color:#444; font-weight:700;
                     white-space:nowrap; text-transform:uppercase; letter-spacing:0.5px; }

    /* ════════════════════════════════════════
       EMPTY STATE
    ════════════════════════════════════════ */
    .ss-empty {
        background:#111; border:1px solid #1e1e1e; border-radius:14px;
        padding:5rem 2rem; text-align:center;
    }
    .ss-empty-icon { font-size:2rem; color:#252525; margin-bottom:1rem; }
    .ss-empty-title { font-size:1.2rem; font-weight:800; color:#383838; margin-bottom:0.5rem; }
    .ss-empty-body  { font-size:0.9rem; color:#2a2a2a; max-width:480px; margin:0 auto; line-height:1.8; }
    </style>
    """, unsafe_allow_html=True)

    # ── counts ────────────────────────────────────────────────────────────────
    _n       = len(rc_favs)
    _stocks  = len(set(f.get('symbol', '') for f in rc_favs))
    _trend_n = sum(1 for f in rc_favs if f.get('best_regime') == 'TREND')
    _range_n = sum(1 for f in rc_favs if f.get('best_regime') == 'RANGE')
    _vol_n   = sum(1 for f in rc_favs if f.get('best_regime') == 'VOLATILE')

    # ── top bar ───────────────────────────────────────────────────────────────
    _tl, _tr = st.columns([1, 0.13])
    with _tl:
        st.markdown(
            "<div class='ss-topbar'>"
            "<div>"
            "<div class='ss-topbar-title'>Saved Strategies</div>"
            "<div class='ss-topbar-sub'>Regime champions · grouped by stock &amp; period</div>"
            "</div>"
            "<div class='ss-topbar-divider'></div>"
            # stocks
            f"<div class='ss-kpi-inline'>"
            f"<div><div class='ss-kpi-inline-val' style='color:#707070'>{_stocks}</div>"
            f"<div class='ss-kpi-inline-lbl'>Stocks</div></div></div>"
            "<div class='ss-topbar-divider'></div>"
            # saved
            f"<div class='ss-kpi-inline'>"
            f"<div><div class='ss-kpi-inline-val' style='color:#a78bfa'>{_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Saved</div></div></div>"
            "<div class='ss-topbar-divider'></div>"
            # trend
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#26A69A'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#26A69A'>{_trend_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Trend</div></div></div>"
            # range
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#4A9EFF'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#4A9EFF'>{_range_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Range</div></div></div>"
            # volatile
            f"<div class='ss-kpi-inline'>"
            f"<div class='ss-kpi-dot' style='background:#FF6B6B'></div>"
            f"<div><div class='ss-kpi-inline-val' style='color:#FF6B6B'>{_vol_n}</div>"
            f"<div class='ss-kpi-inline-lbl'>Volatile</div></div></div>"
            "</div>",
            unsafe_allow_html=True)
    with _tr:
        with st.container(key="cv_back_wrap"):
            if st.button("← Back", key="cv_back_btn", use_container_width=True):
                st.session_state.show_champions_vault = False
                st.rerun()

    # ── empty state ───────────────────────────────────────────────────────────
    if not rc_favs:
        st.markdown(
            "<div class='ss-empty'>"
            "<div class='ss-empty-icon'>★</div>"
            "<div class='ss-empty-title'>No saved strategies yet</div>"
            "<div class='ss-empty-body'>Run analysis on any stock, go to "
            "<b style='color:#555'>Signal Analysis → Indicator Combinations → Regime Champions</b>, "
            "then tap <b style='color:#a78bfa'>☆ Save Strategy</b>.</div>"
            "</div>",
            unsafe_allow_html=True)
        return

    # ── build per-stock, per-period lookup ────────────────────────────────────
    _by_stock: dict = {}
    for _f in rc_favs:
        _s  = _f.get('symbol', '—')
        _sn = _f.get('stock_name', '')
        _pl = _f.get('period_label', 'Medium (63d)')
        if _s not in _by_stock:
            _by_stock[_s] = {'sname': _sn, 'periods': {p: [] for p in _PERIODS}}
        _matched = next((p for p in _PERIODS if p.lower().startswith(_pl.split()[0].lower())), _pl)
        _by_stock[_s]['periods'].setdefault(_matched, []).append(_f)

    for _sd in _by_stock.values():
        for _pl2 in _sd['periods']:
            _sd['periods'][_pl2].sort(key=lambda f: -float(f.get('win_rate', 0) or 0))

    # ── filter bar ───────────────────────────────────────────────────────────
    _fcol1, _fcol2, _fcol3 = st.columns([2, 1, 1], gap="small")
    with _fcol1:
        _search = st.text_input(" ", placeholder="Search symbol or indicator…",
                                key="cv_search", label_visibility="collapsed")
    with _fcol2:
        _regime_filter = st.selectbox(" ", ["All Regimes", "Trend", "Range", "Volatile"],
                                      key="cv_regime_filter", label_visibility="collapsed")
    with _fcol3:
        _period_filter = st.selectbox(" ", ["All Periods", "Short", "Medium", "Long"],
                                      key="cv_period_filter", label_visibility="collapsed")

    _sq = _search.strip().lower() if _search else ""
    _rf = _regime_filter if _regime_filter != "All Regimes" else ""
    _pf_sel = _period_filter if _period_filter != "All Periods" else ""

    # ── render one row per stock ──────────────────────────────────────────────
    _gidx = 0
    for _sym, _sdata in sorted(_by_stock.items()):
        _sname   = _sdata['sname']
        _periods = _sdata['periods']
        _sym_disp = _sym.replace('.SR', '')

        # apply filters
        if _sq and _sq not in _sym_disp.lower() and _sq not in _sname.lower() and \
           not any(_sq in f.get('combo_indicators','').lower()
                   for v in _periods.values() for f in v):
            continue
        if _rf:
            if not any(f.get('best_regime','').title() == _rf
                       for v in _periods.values() for f in v):
                continue
        if _pf_sel:
            if not any(_pf_sel in p for p in _periods if _periods[p]):
                continue

        _strat_n = sum(len(v) for v in _periods.values())

        # ── stock card header ────────────────────────────────────────────────
        st.markdown(
            f"<div class='ss-stock-row'>"
            f"<div class='ss-stock-label'>"
            f"<span class='ss-stock-sym'>{_sym_disp}</span>"
            + (f"<span class='ss-stock-name'>{_sname}</span>" if _sname else "")
            + f"<span class='ss-stock-count'>{_strat_n} saved</span>"
            f"</div>",
            unsafe_allow_html=True)

        # ── 3 columns: Short | Medium | Long — always side by side ──────────
        _PERIOD_ORDER = [('Short (5d)', 'Short', '5D'), ('Medium (63d)', 'Medium', '63D'), ('Long (252d)', 'Long', '252D')]
        _col_s, _col_m, _col_l = st.columns(3, gap="small")
        _period_cols = [_col_s, _col_m, _col_l]

        for (_pl3, _lbl3, _days3), _pcol in zip(_PERIOD_ORDER, _period_cols):
            _strats_p = _periods.get(_pl3, [])
            with _pcol:
                # period header
                st.markdown(
                    f"<div class='ss-period-title' style='padding:0.4rem 0 0.3rem;'>"
                    f"<div class='ss-period-title-dot'></div>{_lbl3}"
                    f"<span style='color:#3a3a3a;margin-left:0.25rem;font-size:0.58rem;font-weight:700;'>{_days3}</span>"
                    f"<span style='color:#2a2a2a;margin-left:auto;font-size:0.58rem;'>({len(_strats_p)})</span>"
                    f"</div>",
                    unsafe_allow_html=True)

                if not _strats_p:
                    st.markdown("<div class='ss-col-empty'>—</div>", unsafe_allow_html=True)
                    continue

                for _f in _strats_p:
                    _wr    = float(_f.get('win_rate', 0) or 0)
                    _sig   = int(_f.get('signals', 0) or 0)
                    _combo = _f.get('combo_indicators', '—')
                    _rk    = _f.get('best_regime', 'TREND')
                    _fid   = _f.get('id', '')

                    _rc, _ri, _rlbl = _REGIME_META.get(_rk, ('#a78bfa', '★', _rk.title()))
                    _wc = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
                    _rmkey = f"ssrm_{_fid.replace('.','_').replace(' ','_').replace('(','_').replace(')','_').replace('/','_')}"[:72]

                    _c_chip, _c_del = st.columns([14, 1])
                    with _c_chip:
                        st.markdown(
                            f"<div class='ss-chip'>"
                            f"<div class='ss-chip-bar' style='background:{_rc}'></div>"
                            f"<div class='ss-chip-body'>"
                            f"<span class='ss-chip-regime' style='background:{_rc};color:#0a0a0a;'>"
                            f"{_ri}&nbsp;{_rlbl}</span>"
                            f"<span class='ss-chip-name' title='{_combo}'>{_combo}</span>"
                            f"<span class='ss-chip-sigs'>{_sig}×</span>"
                            f"<span class='ss-chip-wr' style='color:{_wc}'>{_wr:.0f}%</span>"
                            f"</div></div>",
                            unsafe_allow_html=True)
                    with _c_del:
                        with st.container(key=_rmkey):
                            st.button("✕", key=f"btn_{_rmkey}",
                                      use_container_width=True,
                                      on_click=_rc_toggle, args=(_fid, None))
                    _gidx += 1

        # close stock card
        st.markdown("</div>", unsafe_allow_html=True)

    # ── LIVE SIGNALS SECTION ─────────────────────────────────────────────────
    _render_live_signals(rc_favs)


# ── Live signal checker ───────────────────────────────────────────────────────

# Maps display name fragments → signal column key in signals_df
_IND_KEY_MAP = {
    'EMA':        'EMA',
    'SMA':        'SMA',
    'Parabolic':  'PSAR',
    'Ichimoku':   'ICHI',
    'WMA':        'WMA',
    'RSI':        'RSI',
    'MACD':       'MACD',
    'Stochastic': 'STOCH',
    'ROC':        'ROC',
    'CCI':        'CCI',
    'Williams':   'WILLR',
    'Bollinger':  'BB',
    'Keltner':    'KC',
    'Donchian':   'DC',
    'MFI':        'MFI',
    'CMF':        'CMF',
    'VWAP':       'VWAP',
    'OBV':        'OBV',
    'ADX':        'ADX',
}

_PERIOD_DAYS = {'Short (5d)': '3mo', 'Medium (63d)': '6mo', 'Long (252d)': '2y'}

_REGIME_COLORS = {'TREND': '#26A69A', 'RANGE': '#4A9EFF', 'VOLATILE': '#FF6B6B'}
_REGIME_ICONS  = {'TREND': '↗', 'RANGE': '↔', 'VOLATILE': '⚡'}


def _combo_display_to_keys(combo_str: str) -> list[str]:
    """Convert 'EMA (20/50/200) + RSI (14)' → ['EMA', 'RSI']"""
    keys = []
    for part in combo_str.split('+'):
        part = part.strip()
        for fragment, key in _IND_KEY_MAP.items():
            if fragment.lower() in part.lower():
                keys.append(key)
                break
    return list(dict.fromkeys(keys))  # dedupe, preserve order


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_df_cached(symbol: str, yf_period: str):
    """Fetch OHLCV + compute all indicators. Returns (df, price) or (None, None)."""
    try:
        import yfinance as yf
        import pandas as pd
        import pandas_ta as ta

        _df = yf.download(symbol, period=yf_period, interval='1d', progress=False, auto_adjust=True)
        if _df is None or len(_df) < 20:
            return None, None
        _df.columns = [c[0] if isinstance(c, tuple) else c for c in _df.columns]
        _df = _df.reset_index()
        if 'Date' not in _df.columns and 'Datetime' in _df.columns:
            _df = _df.rename(columns={'Datetime': 'Date'})
        _df['Date'] = pd.to_datetime(_df['Date'])

        _c = _df['Close']
        _df['EMA_20']  = ta.ema(_c, length=20)
        _df['EMA_50']  = ta.ema(_c, length=50)
        _df['EMA_200'] = ta.ema(_c, length=200)
        _df['SMA_50']  = ta.sma(_c, length=50)
        _df['SMA_200'] = ta.sma(_c, length=200)
        _df['RSI_14']  = ta.rsi(_c, length=14)

        macd = ta.macd(_c)
        if macd is not None:
            for col in macd.columns: _df[col] = macd[col]

        bb = ta.bbands(_c, length=20)
        if bb is not None:
            for col in bb.columns: _df[col] = bb[col]

        stoch = ta.stoch(_df['High'], _df['Low'], _c)
        if stoch is not None:
            for col in stoch.columns: _df[col] = stoch[col]

        adx = ta.adx(_df['High'], _df['Low'], _c)
        if adx is not None:
            for col in adx.columns: _df[col] = adx[col]

        roc   = ta.roc(_c, length=12);                                    _df['ROC_12']   = roc   if roc   is not None else 0
        cci   = ta.cci(_df['High'], _df['Low'], _c, length=20);           _df['CCI_20']   = cci   if cci   is not None else 0
        willr = ta.willr(_df['High'], _df['Low'], _c, length=14);         _df['WILLR_14'] = willr if willr is not None else 0
        mfi   = ta.mfi(_df['High'], _df['Low'], _c, _df['Volume'], length=14); _df['MFI_14'] = mfi if mfi is not None else 0
        cmf   = ta.cmf(_df['High'], _df['Low'], _c, _df['Volume'], length=20); _df['CMF_20'] = cmf if cmf is not None else 0
        obv   = ta.obv(_c, _df['Volume']);                                 _df['OBV']      = obv   if obv   is not None else 0
        wma   = ta.wma(_c, length=20);                                     _df['WMA_20']   = wma   if wma   is not None else _c

        psar = ta.psar(_df['High'], _df['Low'], _c)
        if psar is not None:
            for col in psar.columns: _df[col] = psar[col]

        ichi = ta.ichimoku(_df['High'], _df['Low'], _c)
        if ichi is not None and isinstance(ichi, tuple):
            for part in ichi:
                if hasattr(part, 'columns'):
                    for col in part.columns: _df[col] = part[col]

        _df['REGIME'] = 'TREND'
        _df['VWAP']   = ((_df['High'] + _df['Low'] + _df['Close']) / 3 * _df['Volume']).cumsum() / _df['Volume'].cumsum()

        kc = ta.kc(_df['High'], _df['Low'], _c)
        if kc is not None:
            for col in kc.columns: _df[col] = kc[col]

        dc = ta.donchian(_df['High'], _df['Low'])
        if dc is not None:
            for col in dc.columns: _df[col] = dc[col]

        price = float(_df['Close'].iloc[-1])
        return _df, price
    except Exception:
        return None, None


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_signals_cached(symbol: str, yf_period: str):
    """Fetch OHLCV + compute indicators + detect signals. Cached 5 min."""
    try:
        from signal_engine import detect_signals
        _df, price = _fetch_df_cached(symbol, yf_period)
        if _df is None:
            return None, None
        sigs = detect_signals(_df)
        return sigs, price
    except Exception:
        return None, None


def _check_strategy_firing(sig_df, ind_keys: list[str], window: int = 3) -> dict:
    """
    Check if a combo strategy is currently firing.
    Returns dict with firing status and which indicators are active.
    """
    if sig_df is None or len(sig_df) == 0:
        return {'firing': False, 'active': [], 'missing': ind_keys}

    last_n = sig_df.tail(window)
    active, missing = [], []

    for key in ind_keys:
        buy_col = f"{key}_Buy"
        if buy_col not in last_n.columns:
            missing.append(key)
            continue
        fired = int(last_n[buy_col].sum()) > 0
        if fired:
            active.append(key)
        else:
            missing.append(key)

    firing = len(active) == len(ind_keys) and len(ind_keys) > 0
    return {'firing': firing, 'active': active, 'missing': missing}


def _run_full_strategy(_df, current_price):
    """Run all strategy engines and return BUY/NO TRADE verdict + price ladder."""
    try:
        from decision_tab import _get_pa_signal, _get_vp_signal, _get_pattern_signal
        from _levels import compute_structural_levels, price_ladder_html
        import pandas as pd

        df = _df.copy()
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])

        pa  = _get_pa_signal(df, current_price)
        vp  = _get_vp_signal(df, current_price)
        pat = _get_pattern_signal(df)

        signals = [s for s in [pa, vp, pat] if s is not None]
        buy_count  = sum(1 for s in signals if s.get('signal') == 'BUY')
        wait_count = len(signals) - buy_count

        if buy_count >= 2:
            verdict = 'BUY'; verdict_color = '#26A69A'
        elif buy_count == 1 and wait_count == 0:
            verdict = 'BUY'; verdict_color = '#26A69A'
        else:
            verdict = 'NO TRADE'
            verdict_color = '#ef5350' if wait_count > buy_count else '#FFC107'

        ladder_html = None
        if verdict == 'BUY':
            try:
                lv = compute_structural_levels(df, current_price, True)
                ladder_html = price_ladder_html(
                    lv['entry'], lv['stop'], lv['t1'], lv['t2'], lv['t3'], True,
                    lv.get('entry_quality', ''), lv.get('eq_col', '')
                )
            except Exception:
                pass

        return {
            'verdict': verdict,
            'verdict_color': verdict_color,
            'buy_count': buy_count,
            'total': len(signals),
            'signals': signals,
            'ladder_html': ladder_html,
        }
    except Exception:
        return None


def _render_live_signals(rc_favs: list) -> None:
    """Render Live Signal Check — one block per stock, no repeated info."""
    if not rc_favs:
        return

    st.markdown(
        "<div style='margin:2.4rem 0 1.0rem;display:flex;align-items:center;gap:0.6rem;'>"
        "<div style='width:3px;height:18px;border-radius:2px;background:#26A69A;"
        "box-shadow:0 0 8px #26A69A44;'></div>"
        "<span style='font-size:0.92rem;font-weight:700;color:#e0e0e0;"
        "text-transform:uppercase;letter-spacing:0.8px;'>Live Signal Check</span>"
        "</div>",
        unsafe_allow_html=True)

    # group saved strategies by symbol
    _sym_groups: dict = {}
    for _f in rc_favs:
        _sym = _f.get('symbol', '')
        if _sym not in _sym_groups:
            _sym_groups[_sym] = {'sname': _f.get('stock_name', ''), 'strats': []}
        _sym_groups[_sym]['strats'].append(_f)

    _buy_blocks  = []
    _wait_blocks = []

    for _sym, _sdata in sorted(_sym_groups.items()):
        with st.spinner(f"Analysing {_sym.replace('.SR','')}…"):
            _df, _price = _fetch_df_cached(_sym, '1y')

        if _df is None or _price is None:
            continue

        _result = _run_full_strategy(_df, _price)
        _block = {
            'sym':    _sym,
            'sname':  _sdata['sname'],
            'price':  _price,
            'strats': _sdata['strats'],
            'result': _result,
        }
        if _result and _result['verdict'] == 'BUY':
            _buy_blocks.append(_block)
        else:
            _wait_blocks.append(_block)

    def _render_stock_block(b):
        _res      = b['result']
        _vc       = _res['verdict_color'] if _res else '#555'
        _vt       = _res['verdict']       if _res else 'NO DATA'
        _sym_disp = b['sym'].replace('.SR', '')

        # each saved strategy row
        _rows_html = ''
        for _f in b['strats']:
            _rk    = _f.get('best_regime', 'TREND')
            _rc_   = _REGIME_COLORS.get(_rk, '#a78bfa')
            _ri_   = _REGIME_ICONS.get(_rk, '★')
            _wr    = float(_f.get('win_rate', 0) or 0)
            _pf    = float(_f.get('profit_factor', 0) or 0)
            _ea    = float(_f.get('expectancy', 0) or 0)
            _sig   = int(_f.get('signals', 0) or 0)
            _combo = _f.get('combo_indicators', '—')
            _pl    = (_f.get('period_label', '') or '').split('(')[0].strip()
            _wc_   = '#26A69A' if _wr >= 55 else ('#FFC107' if _wr >= 45 else '#ef5350')
            _ec_   = '#26A69A' if _ea > 0 else '#ef5350'
            _rows_html += (
                f"<div style='padding:0.65rem 1rem;border-bottom:1px solid #181818;'>"
                # first line: regime pill + period + combo name
                f"<div style='display:flex;align-items:center;gap:0.5rem;margin-bottom:0.45rem;flex-wrap:wrap;'>"
                f"<span style='font-size:0.65rem;font-weight:800;padding:0.15rem 0.55rem;"
                f"border-radius:20px;background:{_rc_};color:#0a0a0a;white-space:nowrap;'>"
                f"{_ri_}&nbsp;{_rk.title()}</span>"
                f"<span style='font-size:0.72rem;color:#505050;white-space:nowrap;'>{_pl}</span>"
                f"<span style='font-size:0.78rem;font-weight:600;color:#888;"
                f"overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0;'"
                f" title='{_combo}'>{_combo}</span>"
                f"</div>"
                # second line: stats
                f"<div style='display:flex;gap:1.4rem;flex-wrap:wrap;'>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Win Rate&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:{_wc_};'>{_wr:.0f}%</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Profit Factor&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:#aaa;'>{_pf:.2f}</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Expectancy&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:{_ec_};'>{_ea:+.2f}%</span></div>"
                f"<div><span style='font-size:0.62rem;color:#404040;'>Signals&nbsp;</span>"
                f"<span style='font-size:0.85rem;font-weight:900;color:#666;'>{_sig}</span></div>"
                f"</div>"
                f"</div>"
            )

        _sname_span = (f"<span style='font-size:0.7rem;color:#383838;font-weight:600;'>{b['sname']}</span>"
                       if b['sname'] else '')
        _html = (
            f"<div style='background:#111;border:1px solid #1e1e1e;"
            f"border-left:3px solid {_vc};border-radius:12px;overflow:hidden;"
            f"margin-bottom:0.8rem;'>"
            # header: stock name + verdict
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"padding:0.8rem 1rem;border-bottom:1px solid #1a1a1a;'>"
            f"<div style='display:flex;align-items:baseline;gap:0.5rem;'>"
            f"<span style='font-size:1.1rem;font-weight:900;color:#d0d0d0;'>{_sym_disp}</span>"
            f"{_sname_span}</div>"
            f"<span style='font-size:1.3rem;font-weight:900;color:{_vc};'>{_vt}</span>"
            f"</div>"
            # strategy rows
            f"{_rows_html}"
            f"</div>"
        )
        st.markdown(_html, unsafe_allow_html=True)
        if _res and _res['verdict'] == 'BUY' and _res.get('ladder_html'):
            st.markdown(_res['ladder_html'], unsafe_allow_html=True)

    # ── BUY signals ──────────────────────────────────────────────────────────
    if _buy_blocks:
        st.markdown(
            f"<div style='font-size:0.7rem;font-weight:800;color:#26A69A;"
            f"text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.5rem;'>"
            f"BUY Signal &nbsp;({len(_buy_blocks)})</div>",
            unsafe_allow_html=True)
        for _b in _buy_blocks:
            _render_stock_block(_b)

    # ── No Trade ─────────────────────────────────────────────────────────────
    if _wait_blocks:
        st.markdown(
            f"<div style='font-size:0.7rem;font-weight:800;color:#444;"
            f"text-transform:uppercase;letter-spacing:0.8px;margin:1.2rem 0 0.5rem;'>"
            f"Watching &nbsp;({len(_wait_blocks)})</div>",
            unsafe_allow_html=True)
        for _b in _wait_blocks:
            _render_stock_block(_b)


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO SCANNER PAGE  —  fast, all tickers, period filter, 3-col grid
# ══════════════════════════════════════════════════════════════════════════════

def render_auto_scanner_page() -> None:
    from scanner_engine import (scan_stock, scan_all_stocks, _REGIME_COLORS,
                                _REGIME_ICONS, _DAYS_MIN, _DAYS_MAX,
                                LIVE_SIGNAL_MAX_AGE as _LIVE_MAX_AGE,
                                parse_days as _parse_days)
    # Light-theme regime colours (the engine's are tuned for dark pages).
    # Hues kept apart from the gain/loss green/red and the blue action colour.
    _REGIME_COLORS = {'TREND': '#4B47C4', 'RANGE': '#086F8C', 'VOLATILE': '#8E3FBA'}
    from market_data import get_all_tadawul_tickers

    _PERIODS = ['Short', 'Medium', 'Long']

    _ticker_map = get_all_tadawul_tickers()   # {sym: name}
    _ALL_SYMS   = list(_ticker_map.keys())

    # ── helpers ───────────────────────────────────────────────────────────────
    def _ind_label(inds):
        # Use the engine's label map as the single source of truth. This local
        # dict only covered 13 of the 50 indicators, so the other 37 rendered
        # as raw keys ('VOLRSI', 'SWINGHL', 'CCIEXT'). It also meant the six
        # renamed indicators would have kept showing their old, misleading
        # names here even after the engine was corrected.
        from scanner_engine import _IND_LABEL as _D
        return ' + '.join(_D.get(k, k) for k in inds)

    def _wr_col(wr):
        return '#1B7A36' if wr >= 55 else ('#A34800' if wr >= 45 else '#C1121F')

    def _price_box(df, price):
        """Return price-ladder HTML or ''."""
        if df is None or price <= 0:
            return ''
        try:
            from _levels import compute_structural_levels
            lv  = compute_structural_levels(df, price, True)
            en  = lv['entry']; st_ = lv['stop']
            t1  = lv['t1'];    t2  = lv['t2']
            rp  = round(abs(en - st_) / en * 100, 1) if en else 0
            t1p = round((t1 - en) / en * 100, 1)     if en else 0
            t2p = round((t2 - en) / en * 100, 1)     if en else 0
            return (
                f"<div class='sc-pb'>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#0063D1;'></div>"
                f"<div class='sc-pcl'>Entry</div>"
                f"<div class='sc-pcv' style='color:#0063D1;'>{en:.2f}</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#C1121F;'></div>"
                f"<div class='sc-pcl'>Stop Loss</div>"
                f"<div class='sc-pcv' style='color:#C1121F;'>{st_:.2f}</div>"
                f"<div class='sc-pcs'>−{rp}%</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#1B7A36;'></div>"
                f"<div class='sc-pcl'>Target 1</div>"
                f"<div class='sc-pcv' style='color:#1B7A36;'>{t1:.2f}</div>"
                f"<div class='sc-pcs'>+{t1p}%</div>"
                f"</div>"
                f"<div class='sc-pc'>"
                f"<div class='sc-pcb' style='background:#15704A;'></div>"
                f"<div class='sc-pcl'>Target 2</div>"
                f"<div class='sc-pcv' style='color:#15704A;'>{t2:.2f}</div>"
                f"<div class='sc-pcs'>+{t2p}%</div>"
                f"</div>"
                f"</div>"
            )
        except Exception:
            return ''

    # ── CSS ───────────────────────────────────────────────────────────────────
    # Light, Apple-style design system. Colours are tokens (CSS variables) so
    # the whole page can be re-themed from this one block.
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
    :root{
      --bg:#F2F2F5; --card:#FFFFFF; --inset:#F7F7FA; --fill:#EDEDF1;
      --hair:#DEDEE3; --hair2:#C9C9CF;
      --t1:#111114; --t2:#3F3F46; --t3:#5C5C63; --t4:#8A8A91;
      --blue:#0063D1; --blue-bg:rgba(0,99,209,0.09);
      --green:#1B7A36; --green-bg:rgba(27,122,54,0.10);
      --red:#C1121F; --red-bg:rgba(193,18,31,0.08);
      --orange:#A34800; --orange-bg:rgba(163,72,0,0.10);
      --indigo:#4B47C4; --indigo-bg:rgba(75,71,196,0.09);
      --shadow:0 1px 2px rgba(17,17,20,0.05),0 8px 24px rgba(17,17,20,0.06);
      --shadow-sm:0 1px 2px rgba(17,17,20,0.06);
      --r-lg:20px; --r-md:14px; --r-sm:10px;
    }
    /* page canvas — overrides the app's dark shell while this page is open */
    .stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],
    section[data-testid="stSidebar"]{background:var(--bg)!important;}
    .stApp,.stApp p,.stApp span,.stApp div,.stApp label,.stApp button,.stApp input{
      -webkit-font-smoothing:antialiased;}
    [data-testid="stIconMaterial"],.material-symbols-rounded{
      font-family:'Material Symbols Rounded'!important;}
    header[data-testid="stHeader"],[data-testid="stToolbar"],
    [data-testid="stDecoration"]{display:none!important;}
    .main .block-container,div.block-container{
        max-width:1680px!important;padding:1.2rem 3.5rem 6rem!important;margin:0 auto!important;}
    /* st.markdown blocks that only inject <style> still take a row + gap in
       the layout; hide them so the page starts right at the title. */
    [data-testid="stElementContainer"]:has(> .stMarkdown [data-testid="stMarkdownContainer"] > style:only-child){
        display:none!important;}
    @media (max-width:1100px){.main .block-container,div.block-container{padding:1.6rem 1.4rem 4rem!important;}}
    .stApp h4{color:var(--t1)!important;}

    /* streamlit widgets on this page */
    .stApp .stButton button{background:var(--card)!important;color:var(--t1)!important;
        border:1px solid var(--hair)!important;border-radius:980px!important;
        font-weight:600!important;box-shadow:var(--shadow-sm)!important;
        transition:background .15s ease,border-color .15s ease!important;}
    .stApp .stButton button:hover{background:var(--fill)!important;border-color:var(--hair2)!important;}
    .stApp .stButton button p{color:inherit!important;}
    .stApp [data-testid="stTextInput"] input,.stApp [data-testid="stNumberInput"] input{
        background:var(--card)!important;color:var(--t1)!important;}
    .stApp [data-testid="stTextInput"]>div>div,.stApp [data-testid="stNumberInput"]>div>div{
        background:var(--card)!important;border-color:var(--hair)!important;}
    .stApp [data-testid="stProgress"] p{color:var(--t2)!important;}
    .stApp [data-testid="stProgress"]>div>div>div>div{background:var(--blue)!important;}
    .stApp [data-testid="stSpinner"] p,.stApp [data-testid="stSpinner"] div{color:var(--t2)!important;}
    .stApp [data-testid="stExpander"] details{background:var(--card)!important;
        border:1px solid var(--hair)!important;border-radius:var(--r-lg)!important;
        box-shadow:var(--shadow)!important;overflow:hidden;}
    .stApp [data-testid="stExpander"] summary{padding:0.95rem 1.2rem!important;}
    .stApp [data-testid="stExpander"] summary p{color:var(--t1)!important;font-weight:600!important;
        font-size:0.95rem!important;}
    .stApp [data-testid="stExpander"] summary:hover p{color:var(--blue)!important;}
    .stApp [data-testid="stExpander"] svg,.stApp [data-testid="stExpander"] [data-testid="stIconMaterial"]{
        color:var(--t3)!important;fill:var(--t3)!important;}
    .stApp [data-testid="stTooltipIcon"] svg{stroke:var(--t3)!important;}

    /* ── top bar ─────────────────────────────────────────────────────────── */
    .sc-tb{display:flex;align-items:flex-end;gap:2.2rem;margin-bottom:1.4rem;flex-wrap:wrap;}
    .sc-title{font-size:2.1rem;font-weight:700;color:var(--t1);letter-spacing:-0.035em;line-height:1.1;}
    .sc-sub{font-size:0.95rem;color:var(--t2);font-weight:400;margin-top:0.3rem;}
    .sc-div{display:none;}
    .sc-kv{font-size:1.6rem;font-weight:600;line-height:1;letter-spacing:-0.03em;
           font-variant-numeric:tabular-nums;}
    .sc-kl{font-size:0.78rem;font-weight:500;color:var(--t2);margin-top:0.3rem;}

    /* ── back button ─────────────────────────────────────────────────────── */
    .st-key-sc_back .stButton button{font-size:0.85rem!important;padding:0.45rem 1rem!important;
        min-height:auto!important;color:var(--blue)!important;}

    /* ── controls panel ──────────────────────────────────────────────────── */
    .sc-panel{display:none;}
    .sc-panel-row{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.4rem;}
    .sc-panel-row:last-child{margin-bottom:0;}
    .sc-ctrl-lbl{font-size:0.85rem;font-weight:600;color:var(--t2);white-space:nowrap;min-width:3.2rem;}
    .sc-vsep{width:1px;height:1.6rem;background:var(--hair);flex-shrink:0;margin:0.3rem auto 0;}

    /* period segmented control */
    [class*="st-key-scp_"] .stButton button,[class*="st-key-scd_"] .stButton button{
        background:var(--card)!important;border:1px solid var(--hair)!important;
        border-radius:980px!important;color:var(--t1)!important;
        font-size:0.9rem!important;font-weight:500!important;min-height:2.5rem!important;
        padding:0 1.1rem!important;text-transform:none!important;letter-spacing:0!important;
        box-shadow:var(--shadow-sm)!important;}
    [class*="st-key-scp_"] .stButton button:hover,[class*="st-key-scd_"] .stButton button:hover{
        border-color:var(--hair2)!important;background:var(--fill)!important;}
    [class*="st-key-scp_on"] .stButton button,[class*="st-key-scd_on"] .stButton button{
        background:var(--t1)!important;border-color:var(--t1)!important;color:#FFFFFF!important;
        font-weight:600!important;}
    [class*="st-key-scp_on"] .stButton button:hover,[class*="st-key-scd_on"] .stButton button:hover{
        background:#000!important;}
    .st-key-sc_days_box .stNumberInput input{border-radius:12px!important;color:var(--t1)!important;
        font-size:0.95rem!important;font-weight:600!important;text-align:center!important;
        font-variant-numeric:tabular-nums;}
    .st-key-sc_days_box [data-testid="stNumberInputContainer"]{border-radius:980px!important;
        border:1px solid var(--hair)!important;background:var(--card)!important;overflow:hidden;
        min-height:2.5rem;}
    .st-key-sc_days_box .stNumberInput button{background:var(--card)!important;border:none!important;
        color:var(--t2)!important;box-shadow:none!important;border-radius:0!important;}

    /* run scan — primary CTA */
    .st-key-sc_run .stButton button{background:var(--blue)!important;border:1px solid var(--blue)!important;
        color:#FFFFFF!important;font-size:0.95rem!important;font-weight:600!important;
        min-height:2.5rem!important;padding:0 1.4rem!important;text-transform:none!important;
        letter-spacing:0!important;box-shadow:0 4px 14px rgba(0,99,209,0.28)!important;}
    .st-key-sc_run .stButton button:hover{background:#0052AD!important;border-color:#0052AD!important;}

    /* ── section headings ────────────────────────────────────────────────── */
    .sc-h2{display:flex;align-items:baseline;gap:0.7rem;margin:2.2rem 0 0.9rem;}
    .sc-h2-t{font-size:1.45rem;font-weight:700;color:var(--t1);letter-spacing:-0.025em;}
    .sc-h2-s{font-size:0.9rem;color:var(--t2);}
    .sc-h2-c{margin-left:auto;font-size:0.85rem;color:var(--t2);font-variant-numeric:tabular-nums;}
    .sc-summary{display:flex;gap:0.5rem;flex-wrap:wrap;margin:0 0 1rem;}
    .sc-chip{display:inline-flex;align-items:center;gap:0.35rem;font-size:0.82rem;font-weight:500;
        padding:0.3rem 0.75rem;border-radius:980px;background:var(--card);border:1px solid var(--hair);
        color:var(--t2);font-variant-numeric:tabular-nums;}
    .sc-chip b{color:var(--t1);font-weight:600;}

    /* ── stock band (Section 1 — Scanned Strategies) ────────────────────── */
    .sc-band{margin:1.6rem 0 0.7rem;}
    .sc-band-hdr{display:flex;align-items:center;gap:0.7rem;padding:0 0.2rem;}
    .sc-sym{font-size:1.35rem;font-weight:700;color:var(--t1);letter-spacing:-0.025em;
            font-variant-numeric:tabular-nums;}
    .sc-sname{font-size:0.95rem;color:var(--t2);font-weight:400;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:22rem;}
    .sc-ct{margin-left:auto;font-size:0.8rem;color:var(--t2);font-weight:500;
           background:var(--card);border:1px solid var(--hair);border-radius:980px;padding:0.2rem 0.7rem;}

    /* ── regime card ─────────────────────────────────────────────────────── */
    .sc-rpill{font-size:0.78rem;font-weight:600;padding:0.25rem 0.7rem;border-radius:980px;
              white-space:nowrap;flex-shrink:0;color:#FFFFFF;letter-spacing:0;}
    .sc-rcard{border:1px solid var(--hair);border-radius:var(--r-lg);overflow:hidden;
              background:var(--card);height:100%;box-shadow:var(--shadow);}
    .sc-rcard-top{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;padding:1rem 1.1rem 0.6rem;}
    .sc-rcard-inds{padding:0 1.1rem 0.9rem;display:flex;flex-wrap:wrap;gap:0.35rem;align-items:center;}
    .sc-rind-tag{display:inline-block;background:var(--fill);border:none;border-radius:8px;
                 padding:0.22rem 0.55rem;font-size:0.8rem;font-weight:500;color:var(--t1);}
    .sc-rind-plus{display:inline-flex;align-items:center;justify-content:center;width:auto;height:auto;
                  background:none;border:none;color:var(--t4);font-size:0.8rem;font-weight:500;margin:0 0.05rem;}
    .sc-rcard-stats{display:grid;grid-template-columns:repeat(3,1fr);
                    margin:0 0.8rem;border-top:1px solid var(--hair);}
    .sc-rstat{padding:0.95rem 0.4rem 0.8rem;text-align:center;}
    .sc-rstat-v{font-size:1.55rem;font-weight:600;line-height:1;margin-bottom:0.4rem;
                letter-spacing:-0.03em;font-variant-numeric:tabular-nums;}
    .sc-rstat-l{font-size:0.75rem;font-weight:500;color:var(--t2);
                display:inline-flex;align-items:center;gap:0.3rem;}
    .sc-help{display:inline-flex;align-items:center;justify-content:center;width:15px;height:15px;
             border-radius:50%;background:var(--fill);border:none;color:var(--t3);
             font-size:0.62rem;font-weight:700;cursor:help;margin-left:0.25rem;}
    .sc-help-pill{display:inline-flex;align-items:center;justify-content:center;width:17px;height:17px;
                  border-radius:50%;background:var(--fill);border:none;color:var(--t3);
                  font-size:0.66rem;font-weight:700;cursor:help;transition:all .15s;}
    .sc-help-pill:hover{color:var(--blue);background:var(--blue-bg);}
    .sc-rcard-stats2{display:grid;grid-template-columns:repeat(3,1fr);margin:0 0.8rem;
                     border-top:1px solid var(--hair);}
    .sc-rstat2{padding:0.75rem 0.4rem 0.85rem;text-align:center;}
    .sc-rstat2-v{font-size:1.05rem;font-weight:600;line-height:1;margin-bottom:0.3rem;
                 font-variant-numeric:tabular-nums;}
    .sc-rstat2-l{font-size:0.72rem;font-weight:500;color:var(--t2);}
    .sc-cfire{display:inline-flex;align-items:center;gap:0.3rem;margin-left:auto;font-size:0.75rem;
              font-weight:600;padding:0.25rem 0.65rem;border-radius:980px;
              background:var(--green-bg);color:var(--green);}
    .sc-cfire::before{content:'';width:6px;height:6px;border-radius:50%;background:#1FA855;}

    /* ── more strategies ─────────────────────────────────────────────────── */
    .sc-alts{border-top:1px solid var(--hair);background:var(--inset);padding:0.9rem 0.9rem 0.9rem;}
    .sc-alts-hdr{display:flex;align-items:center;gap:0.4rem;font-size:0.8rem;font-weight:600;
                 color:var(--t2);margin-bottom:0.6rem;}
    .sc-alt-row{background:var(--card);border:1px solid var(--hair);border-radius:var(--r-md);
                padding:0.75rem 0.9rem 0.4rem;margin-bottom:0.55rem;}
    .sc-alt-row:last-child{margin-bottom:0;}
    .sc-alt-row .sc-rcard-stats,.sc-alt-row .sc-rcard-stats2{margin:0 -0.2rem!important;width:auto!important;}
    .sc-alt-row .sc-rstat-v{font-size:1.15rem!important;}
    .sc-alt-tags{display:flex;flex-wrap:wrap;gap:0.35rem;align-items:center;margin-bottom:0.55rem;}
    .sc-alt-fire{margin-left:auto;font-size:0.72rem;font-weight:600;padding:0.18rem 0.55rem;
                 border-radius:980px;background:var(--green-bg);border:none;color:var(--green);}

    /* ── live pulse ──────────────────────────────────────────────────────── */
    @keyframes lp{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(52,199,89,0.45);}
                  60%{opacity:.6;box-shadow:0 0 0 6px rgba(52,199,89,0);}}
    .sc-live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;
                 background:#1FA855;animation:lp 2s ease-out infinite;flex-shrink:0;}

    /* ── Live Signal Check heading ───────────────────────────────────────── */
    .lsc-section-hdr{display:flex;align-items:center;gap:0.7rem;margin:2.2rem 0 1.1rem;}
    .sc-h2{margin-top:3.2rem!important;}
    .lsc-section-line,.lsc-section-line-r{display:none;}
    .lsc-section-pill{display:flex;align-items:center;gap:0.6rem;}
    .lsc-section-label{font-size:1.45rem;font-weight:700;color:var(--t1);letter-spacing:-0.025em;}
    .lsc-section-count{font-size:0.85rem;font-weight:600;background:var(--green-bg);
                       color:var(--green);border-radius:980px;padding:0.15rem 0.6rem;
                       font-variant-numeric:tabular-nums;}

    /* indicator tags in live cards */
    .lsc-ind-tag{display:inline-block;background:var(--fill);border:none;border-radius:8px;
                 padding:0.25rem 0.6rem;font-size:0.82rem;font-weight:500;color:var(--t1);white-space:nowrap;}
    .lsc-ind-plus{display:inline-flex;align-items:center;justify-content:center;background:none;border:none;
                  color:var(--t4);font-size:0.82rem;font-weight:500;margin:0 0.05rem;width:auto;height:auto;}

    /* price ladder */
    .lsc-ladder{display:grid;grid-template-columns:repeat(5,1fr);gap:0.5rem;}
    .lsc-lc{padding:0.75rem 0.85rem;border-radius:var(--r-md);background:var(--inset);
            border:1px solid var(--hair);position:relative;text-align:left;overflow:hidden;}
    .lsc-lc-bar{position:absolute;top:0;left:0;bottom:0;width:3px;}
    .lsc-ll{font-size:0.75rem;font-weight:500;color:var(--t2);margin-bottom:0.3rem;}
    .lsc-lv{font-size:1.3rem;font-weight:600;line-height:1;letter-spacing:-0.03em;
            font-variant-numeric:tabular-nums;}
    .lsc-lp{font-size:0.78rem;font-weight:600;margin-top:0.3rem;font-variant-numeric:tabular-nums;}

    /* live card shell */
    .lsc-card2{background:var(--card);border:1px solid var(--hair);border-radius:var(--r-lg);
               overflow:hidden;box-shadow:var(--shadow);}
    .lsc-hdr2{display:flex;align-items:center;gap:0.6rem;padding:1rem 1.15rem 0.7rem;flex-wrap:wrap;}
    .lsc-sym2{font-size:1.35rem;font-weight:700;color:var(--t1);letter-spacing:-0.025em;}
    .lsc-name2{font-size:0.92rem;color:var(--t2);white-space:nowrap;overflow:hidden;
               text-overflow:ellipsis;max-width:12rem;}
    .lsc-price2{margin-left:auto;font-size:1.35rem;font-weight:600;color:var(--t1);
                letter-spacing:-0.03em;font-variant-numeric:tabular-nums;white-space:nowrap;}
    .lsc-price2 small{font-size:0.75rem;color:var(--t2);font-weight:500;margin-left:0.25rem;}
    .lsc-strat2{display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;padding:0 1.15rem 0.9rem;}
    .lsc-stats2{display:grid;grid-template-columns:repeat(4,1fr);margin:0 0.8rem;
                border-top:1px solid var(--hair);border-bottom:1px solid var(--hair);}
    .lsc-stat2{padding:0.85rem 0.4rem;text-align:center;}
    .lsc-stat2-v{font-size:1.4rem;font-weight:600;line-height:1;letter-spacing:-0.03em;
                 font-variant-numeric:tabular-nums;margin-bottom:0.35rem;}
    .lsc-stat2-l{font-size:0.75rem;font-weight:500;color:var(--t2);}
    .lsc-ladder-wrap{padding:0.9rem 0.9rem 1rem;}
    .lsc-when{margin-left:auto;display:inline-flex;align-items:center;gap:0.35rem;font-size:0.78rem;
              font-weight:600;padding:0.28rem 0.7rem;border-radius:980px;white-space:nowrap;}
    .lsc-when::before{content:'';width:6px;height:6px;border-radius:50%;background:currentColor;}
    .lsc-regime2{font-size:0.78rem;font-weight:600;padding:0.25rem 0.7rem;border-radius:980px;
                 white-space:nowrap;}

    /* buttons under each live card: Show chart · View strategy */
    [class*="st-key-lsc_ctoggle_"] .stButton button,
    [class*="st-key-lsc_goto_"] .stButton button{border-radius:980px!important;
        font-size:0.85rem!important;color:var(--blue)!important;min-height:2.2rem!important;
        margin-top:0.5rem!important;box-shadow:none!important;background:transparent!important;
        border:none!important;}
    [class*="st-key-lsc_ctoggle_"] .stButton button:hover,
    [class*="st-key-lsc_goto_"] .stButton button:hover{background:var(--blue-bg)!important;}
    [class*="st-key-lsc_goto_"] .stButton button p{color:var(--blue)!important;font-weight:600!important;}

    /* live card = entry plan: strategy line, then the price ladder */
    .lsc-card2 .lsc-ladder-wrap{margin:0 0.8rem;padding:0.9rem 0 1rem;border-top:1px solid var(--hair);}
    .lsc-more{display:inline-flex;align-items:center;font-size:0.72rem;font-weight:600;
        padding:0.18rem 0.6rem;border-radius:980px;background:var(--blue-bg);color:var(--blue);
        white-space:nowrap;cursor:help;}

    /* the stock card a "View strategy" tap jumped to */
    .sc-stock.sc-focus{border-color:var(--blue);
        box-shadow:0 0 0 3px rgba(0,99,209,0.18),var(--shadow);}
    .sc-tr.sc-tr-focus{background:rgba(0,99,209,0.10)!important;
        box-shadow:inset 4px 0 0 var(--blue)!important;}

    /* expander shell: the app styles every expander dark — neutralise here */
    .stApp [data-testid="stExpander"]{background:transparent!important;border:none!important;}

    /* top-bar KPIs */
    .sc-kpi{text-align:right;min-width:4.5rem;}
    .sc-kpi .sc-kv{color:var(--t1);}

    /* validation pill */
    .sc-vb{display:inline-flex;align-items:center;font-size:0.72rem;font-weight:600;
           padding:0.18rem 0.6rem;border-radius:980px;white-space:nowrap;cursor:help;}
    .sc-vb-ok{background:var(--green-bg);color:var(--green);}
    .sc-vb-warn{background:var(--orange-bg);color:var(--orange);}
    .sc-vb-bad{background:var(--red-bg);color:var(--red);}

    /* validation box */
    .sc-val{margin:0.2rem 0.8rem 0.9rem;padding:0.75rem 0.85rem;background:var(--inset);
            border:1px solid var(--hair);border-radius:var(--r-md);}
    .sc-val-h{display:flex;align-items:center;gap:0.3rem;font-size:0.78rem;font-weight:600;
              color:var(--t2);margin-bottom:0.55rem;}
    .sc-val-row{display:flex;align-items:center;gap:0.6rem;}
    .sc-val-c{flex:1;min-width:0;}
    .sc-val-l{font-size:0.72rem;color:var(--t2);margin-bottom:0.15rem;}
    .sc-val-v{display:flex;align-items:baseline;gap:0.4rem;font-variant-numeric:tabular-nums;}
    .sc-val-v b{font-size:1.05rem;font-weight:600;color:var(--t1);}
    .sc-val-n{font-size:0.75rem;color:var(--t3);}
    .sc-val-na{font-size:0.85rem;color:var(--t3);}
    .sc-val-arrow{color:var(--t4);font-size:1rem;}
    .sc-val-note{margin-top:0.55rem;font-size:0.75rem;line-height:1.45;color:var(--t2);}

    /* inputs: one rounded outline only (no inner base-web border) */
    .st-key-sc_search_box [data-baseweb="input"],.st-key-sc_search_box [data-baseweb="base-input"],
    .st-key-sc_days_box [data-baseweb="input"],.st-key-sc_days_box [data-baseweb="base-input"]{
        border:none!important;background:var(--card)!important;}
    .st-key-sc_days_box{margin-top:0!important;}
    .sc-h2{margin-top:1.2rem;}

    /* ── round 2: critique fixes ─────────────────────────────────────────── */
    /* segmented control (Short | Medium | Long | Days) */
    .st-key-sc_seg_box [role="radiogroup"],
    [class*="st-key-sc_flt_f"] [role="radiogroup"]{background:var(--fill)!important;border-radius:13px!important;
        padding:4px!important;display:inline-flex!important;gap:2px!important;flex-wrap:nowrap!important;}
    .st-key-sc_seg_box [role="radiogroup"] button,
    [class*="st-key-sc_flt_f"] [role="radiogroup"] button{background:transparent!important;border:none!important;
        box-shadow:none!important;border-radius:10px!important;color:var(--t2)!important;
        min-height:2.4rem!important;padding:0 1.6rem!important;font-weight:500!important;}
    .st-key-sc_seg_box [role="radiogroup"] button p,
    [class*="st-key-sc_flt_f"] [role="radiogroup"] button p{font-size:0.95rem!important;color:inherit!important;
        font-weight:inherit!important;}
    .st-key-sc_seg_box [role="radiogroup"] button:hover,
    [class*="st-key-sc_flt_f"] [role="radiogroup"] button:hover{color:var(--t1)!important;}
    .st-key-sc_seg_box [role="radiogroup"] button[aria-checked="true"],
    [class*="st-key-sc_flt_f"] [role="radiogroup"] button[aria-checked="true"]{
        background:#FFFFFF!important;color:var(--t1)!important;font-weight:600!important;
        box-shadow:0 1px 4px rgba(0,0,0,0.14),0 0 0 0.5px rgba(0,0,0,0.06)!important;}

    /* filter row (Win rate · Trades · Market regime) */
    [class*="st-key-sc_flt_f"] [role="radiogroup"] button{padding:0 1rem!important;
        min-height:2.25rem!important;}
    .sc-flt-l{font-size:0.82rem;font-weight:600;color:var(--t2);margin:0.4rem 0 0.35rem 0.15rem;}
    .sc-flt-sum{font-size:0.88rem;color:var(--t2);margin:0.2rem 0 0 0.15rem;}
    .sc-flt-sum b{color:var(--t1);font-weight:600;}
    .st-key-sc_flt_clear .stButton button{background:transparent!important;border:none!important;
        box-shadow:none!important;color:var(--blue)!important;font-weight:600!important;
        font-size:0.9rem!important;min-height:2.25rem!important;}
    .st-key-sc_flt_clear .stButton button:hover{background:var(--blue-bg)!important;}

    /* rank number on stock cards (1 = highest win rate) */
    .sc-rank{display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;
        min-width:2rem;height:2rem;padding:0 0.45rem;border-radius:980px;background:var(--fill);
        color:var(--t2);font-size:0.9rem;font-weight:700;font-variant-numeric:tabular-nums;cursor:help;}
    .sc-rank-top{background:var(--blue-bg);color:var(--blue);}
    .sc-grp{margin:1.6rem 0 1.1rem;padding:0.85rem 1.1rem;border-radius:var(--r-md);
        background:var(--fill);color:var(--t2);font-size:0.88rem;line-height:1.45;}
    .sc-grp b{color:var(--t1);font-weight:600;}
    .st-key-sc_run .stButton button{box-shadow:none!important;}
    .st-key-sc_days_box [data-baseweb="input"],.st-key-sc_days_box input{border-radius:12px!important;}
    .st-key-sc_days_box [data-testid="stNumberInputContainer"]{border-radius:12px!important;
        border:none!important;background:var(--fill)!important;}
    .st-key-sc_days_box [data-baseweb="input"],.st-key-sc_days_box [data-baseweb="base-input"],
    .st-key-sc_days_box input,.st-key-sc_days_box .stNumberInput button{background:var(--fill)!important;}

    /* search: filled, iOS style */
    .stApp .st-key-sc_search_box [data-testid="stTextInputRootElement"]{
        border:0!important;outline:0!important;box-shadow:none!important;background:#E8E8ED!important;
        border-radius:14px!important;overflow:hidden;}
    .stApp .st-key-sc_search_box [data-testid="stTextInputRootElement"] *{border:0!important;}
    .stApp .st-key-sc_search_box input{background:transparent!important;color:var(--t1)!important;
        font-size:1rem!important;padding:0.85rem 1.1rem!important;height:auto!important;}
    .stApp .st-key-sc_search_box input::placeholder{color:var(--t3)!important;opacity:1;}
    .stApp .st-key-sc_search_box [data-testid="stTextInputRootElement"]:focus-within{
        box-shadow:0 0 0 3px rgba(0,102,204,0.22)!important;}

    /* regime pill: quiet, coloured dot only */
    .sc-rpill{background:var(--fill)!important;color:var(--t1)!important;font-weight:600;
        display:inline-flex;align-items:center;gap:0.4rem;cursor:help;}
    .sc-rpill::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--rc,#5C5C63);}
    .sc-now-pill{font-size:0.75rem;font-weight:600;padding:0.25rem 0.65rem;border-radius:980px;
        background:var(--blue-bg);color:var(--blue);cursor:help;}
    .sc-rcard.sc-now{border-color:rgba(0,99,209,0.55);box-shadow:0 0 0 3px rgba(0,99,209,0.10),var(--shadow);}

    /* card body: neutral numbers, one caption line instead of a 2nd stat row */
    .sc-rcard{display:flex;flex-direction:column;}
    .sc-rcard-stats{border-top:none;padding-top:0.2rem;}
    .sc-rstat-v{color:var(--t1);}
    .sc-thin .sc-rstat-v{color:var(--t2)!important;}
    .sc-rcard-cap{margin:0 1.1rem 0.9rem;font-size:0.8rem;color:var(--t2);text-align:center;
        font-variant-numeric:tabular-nums;}
    .sc-val{margin:auto 0.8rem 0.9rem;background:var(--inset);}
    .sc-vb-warn{background:var(--fill);color:var(--t2);}

    /* collapsed alternatives */
    details.sc-alts{border-top:1px solid var(--hair);background:var(--card);padding:0;}
    details.sc-alts>summary{list-style:none;cursor:pointer;color:var(--blue);font-weight:500;
        font-size:0.88rem;padding:0.8rem 1.1rem;margin:0;}
    details.sc-alts>summary::-webkit-details-marker{display:none;}
    details.sc-alts>summary::after{content:' ›';}
    details.sc-alts[open]>summary::after{content:' ⌄';}
    details.sc-alts[open]{background:var(--inset);padding-bottom:0.8rem;}
    details.sc-alts .sc-alt-row{margin:0 0.8rem 0.6rem;padding:0.8rem 0.4rem 0.2rem;}
    details.sc-alts .sc-alt-tags{padding:0 0.5rem;margin-bottom:0;}
    details.sc-alts .sc-rcard-inds{padding:0.5rem 0.5rem 0.4rem;}
    details.sc-alts .sc-rcard-stats{margin:0 0.2rem;}
    details.sc-alts .sc-rcard-cap{margin:0 0.5rem 0.6rem;}

    /* live card price levels: no stripes, neutral numbers, colour on the % line only */
    .lsc-lc-bar{display:none;}
    .lsc-lc{background:var(--fill);border:none;}
    .lsc-lv{color:var(--t1)!important;}

    /* chart surface */
    [class*="st-key-lsc_chartwrap_"]{background:var(--card);border:1px solid var(--hair);
        border-radius:var(--r-lg);box-shadow:var(--shadow);padding:0.4rem 0.6rem 0.2rem;margin-top:0.5rem;}
    [class*="st-key-lsc_chartwrap_"] .lsc-card2{border:none!important;box-shadow:none!important;margin:0!important;}

    /* ── round 3: coloured indicator chips + table-style stock cards ─────── */
    .sc-chip-ind{display:inline-flex;align-items:center;font-size:0.84rem;font-weight:600;
        padding:0.28rem 0.7rem;border-radius:980px;white-space:nowrap;cursor:help;}
    .sc-chip-plus{color:var(--t4);font-weight:500;margin:0 0.3rem;font-size:0.85rem;}
    .sc-legend{display:flex;flex-wrap:wrap;align-items:center;gap:0.4rem 1rem;margin:0 0 1.1rem;
        font-size:0.82rem;color:var(--t2);}
    .sc-legend-t{font-weight:600;color:var(--t1);margin-right:0.2rem;}
    .sc-legend-i{display:inline-flex;align-items:center;gap:0.4rem;}
    .sc-legend-i i{display:inline-block;width:9px;height:9px;border-radius:3px;}

    .sc-stock{background:var(--card);border:1px solid var(--hair);border-radius:var(--r-lg);
        box-shadow:var(--shadow);margin:0 0 1.2rem;overflow:hidden;}
    .sc-stock-hdr{display:flex;align-items:center;gap:0.75rem;padding:1.1rem 1.5rem 0.9rem;}
    .sc-stock-hdr .sc-ct{margin-left:auto;}
    .sc-table{border-top:1px solid var(--hair);}
    .sc-tr{display:grid;align-items:center;gap:0 1.2rem;padding:0.95rem 1.5rem;
        grid-template-columns:minmax(150px,1.05fr) minmax(240px,2.5fr) 0.7fr 0.8fr 0.85fr 0.85fr minmax(190px,1.45fr);
        border-top:1px solid var(--hair);}
    .sc-table>.sc-tr:first-child{border-top:none;}
    .sc-th{padding-top:0.6rem;padding-bottom:0.6rem;background:var(--inset);font-size:0.78rem;
        font-weight:500;color:var(--t2);}
    .sc-th>div:nth-child(n+3):nth-child(-n+6){text-align:right;}
    .sc-tr-reg{display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap;cursor:help;}
    .sc-tr-ico{display:inline-flex;align-items:center;justify-content:center;width:1.7rem;height:1.7rem;
        border-radius:8px;background:var(--fill);color:var(--t1);font-size:0.9rem;}
    .sc-tr-rn{font-size:0.98rem;font-weight:600;color:var(--t1);}
    .sc-tr-alt{font-size:0.82rem;color:var(--t2);padding-left:2.15rem;cursor:default;}
    .sc-tr-strat{display:flex;align-items:center;flex-wrap:wrap;gap:0.35rem 0;}
    .sc-tr-strat .sc-cfire{margin-left:0.6rem;}
    .sc-tr-n{text-align:right;font-size:1.15rem;font-weight:600;color:var(--t1);
        font-variant-numeric:tabular-nums;letter-spacing:-0.01em;}
    .sc-tr-sm{font-size:0.75rem;font-weight:500;color:var(--t2);margin-top:0.15rem;letter-spacing:0;}
    .sc-thin .sc-tr-n{color:var(--t3);}
    .sc-thin .sc-tr-sm{color:var(--orange);}
    .sc-tv{display:flex;flex-direction:column;align-items:flex-start;gap:0.25rem;cursor:help;}
    .sc-tv-l{font-size:0.78rem;color:var(--t2);font-variant-numeric:tabular-nums;}
    .sc-tr-now{background:linear-gradient(90deg,rgba(0,99,209,0.06),rgba(0,99,209,0.015));
        box-shadow:inset 3px 0 0 var(--blue);}
    .sc-tr-sub{background:var(--inset);padding-top:0.75rem;padding-bottom:0.75rem;}
    .sc-tr-sub .sc-tr-n{font-size:1rem;}
    details.sc-more{border-top:1px solid var(--hair);}
    details.sc-more>summary{list-style:none;cursor:pointer;color:var(--blue);font-size:0.86rem;
        font-weight:500;padding:0.6rem 1.5rem 0.6rem 3.65rem;}
    details.sc-more>summary::-webkit-details-marker{display:none;}
    details.sc-more>summary::after{content:' ›';}
    details.sc-more[open]>summary::after{content:' ⌄';}
    details.sc-more>summary:hover{background:var(--inset);}
    @media (max-width:1150px){
      .sc-th{display:none;}
      .sc-tr{grid-template-columns:repeat(4,1fr);gap:0.6rem 1rem;}
      .sc-tr-reg,.sc-tr-strat,.sc-tv{grid-column:1/-1;}
      .sc-tr-n{text-align:left;}
    }

    /* Scanned Strategies: two cards side by side. Each strategy is a 3-line
       block: regime | validation · indicators · four labelled numbers. */
    .sc-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.2rem;
        align-items:start;margin:0 0 1.2rem;}
    .sc-grid .sc-stock{margin:0;}
    .sc-grid .sc-stock-hdr{padding:1rem 1.2rem 0.85rem;}
    .sc-grid .sc-tr{grid-template-columns:repeat(4,minmax(0,1fr));gap:0.55rem 0.9rem;align-items:start;
        padding:0.85rem 1.2rem;grid-template-areas:"reg reg val val" "strat strat strat strat" "wr pf exp tr";}
    .sc-grid .sc-tr>:nth-child(1){grid-area:reg;}
    .sc-grid .sc-tr>:nth-child(2){grid-area:strat;}
    .sc-grid .sc-tr>:nth-child(3){grid-area:wr;}
    .sc-grid .sc-tr>:nth-child(4){grid-area:pf;}
    .sc-grid .sc-tr>:nth-child(5){grid-area:exp;}
    .sc-grid .sc-tr>:nth-child(6){grid-area:tr;}
    .sc-grid .sc-tr>:nth-child(7){grid-area:val;justify-self:end;align-items:flex-end;text-align:right;}
    .sc-grid .sc-tr-n{text-align:left;font-size:1.05rem;}
    .sc-grid .sc-tr-n::before{content:attr(data-l);display:block;font-size:0.7rem;font-weight:500;
        color:var(--t2);margin-bottom:0.1rem;letter-spacing:0;}
    .sc-grid .sc-tr-alt{padding-left:0;}
    .sc-grid details.sc-more>summary{padding:0.6rem 1.2rem;}
    @media (max-width:900px){ .sc-grid{grid-template-columns:minmax(0,1fr);} }

    /* live signals table (under the Live Signal Check cards) */
    .lsc-tbl-hd{display:flex;align-items:baseline;gap:0.7rem;margin:1.8rem 0 0.2rem;}
    .lsc-tbl-t{font-size:1.15rem;font-weight:700;color:var(--t1);letter-spacing:-0.02em;}
    .lsc-tbl-s{font-size:0.86rem;color:var(--t2);}
    .lsc-tbl-wrap{background:var(--card);border:1px solid var(--hair);border-radius:var(--r-lg);
        box-shadow:var(--shadow);overflow:auto;max-height:660px;margin:0.4rem 0 0.4rem;}
    .stApp table.lsc-tbl{width:100%;border-collapse:separate!important;border-spacing:0;margin:0!important;
        font-size:0.86rem;color:var(--t1);font-variant-numeric:tabular-nums;border:none!important;}
    .stApp table.lsc-tbl th,.stApp table.lsc-tbl td{border:none!important;
        border-bottom:1px solid var(--hair)!important;padding:0.62rem 0.8rem!important;
        text-align:right;white-space:nowrap;}
    .stApp table.lsc-tbl thead th{position:sticky;top:0;z-index:2;background:var(--inset)!important;
        color:var(--t2);font-size:0.74rem;font-weight:600;vertical-align:bottom;line-height:1.25;}
    .stApp table.lsc-tbl tbody tr:nth-child(even) td{background:#FAFAFC;}
    .stApp table.lsc-tbl tbody tr:hover td{background:var(--blue-bg);}
    .stApp table.lsc-tbl tbody tr:last-child td{border-bottom:none!important;}
    .stApp table.lsc-tbl .l{text-align:left;}
    .stApp table.lsc-tbl .c{text-align:center;}
    .stApp table.lsc-tbl .rk{text-align:center;color:var(--t3);font-weight:600;width:2.6rem;}
    .stApp table.lsc-tbl .rk.top{color:var(--blue);}
    .stApp table.lsc-tbl .nm{font-weight:600;max-width:13rem;overflow:hidden;text-overflow:ellipsis;}
    .stApp table.lsc-tbl .sym{font-weight:600;}
    .stApp table.lsc-tbl .muted{color:var(--t3);}
    .stApp table.lsc-tbl .up{color:var(--green);font-weight:600;}
    .stApp table.lsc-tbl .dn{color:var(--red);font-weight:600;}
    .stApp table.lsc-tbl .wr{font-weight:700;font-size:0.92rem;}
    .stApp table.lsc-tbl .few{color:var(--orange);font-weight:600;}
    .st-key-lsc_xlsx [data-testid="stDownloadButton"] button{background:var(--card)!important;
        border:1px solid var(--hair)!important;color:var(--blue)!important;font-weight:600!important;
        border-radius:980px!important;min-height:2.4rem!important;box-shadow:var(--shadow)!important;}
    .st-key-lsc_xlsx [data-testid="stDownloadButton"] button p{color:var(--blue)!important;
        font-weight:600!important;}
    .st-key-lsc_xlsx [data-testid="stDownloadButton"] button:hover{background:var(--blue-bg)!important;}
    .lsc-regime2{background:var(--fill);color:var(--t1);}

    /* fewer "?" marks: the regime pill tooltip is enough */
    .sc-rcard-top .sc-help-pill{display:none;}
    </style>
    """, unsafe_allow_html=True)

    # ── session state defaults ────────────────────────────────────────────────
    _SS_DEFS = [
        ('sc_period',    'Medium'),
        ('sc_results',   None),
        ('sc_done',      False),
        ('sc_requested', False),     # only True after the user taps ↻ Scan
        ('sc_days_n',    60),          # custom window, in TRADING days
    ]
    for _k, _v in _SS_DEFS:
        if _k not in st.session_state:
            st.session_state[_k] = _v

    def _sc_days_selected(pk) -> bool:
        """True when the active period is a custom 'Days:N' window."""
        return isinstance(pk, str) and pk.startswith('Days:')

    def _sc_period_label(pk) -> str:
        _n = _parse_days(pk)
        return f"Last {_n} trading days" if _n else str(pk)

    # ── live-signal helpers ───────────────────────────────────────────────────
    def _sig_age(cb):
        """Bars since the strategy last started a signal (0 = today), or None.
        Results cached before `signal_age` existed only carry `firing`."""
        cb = cb or {}
        if 'signal_age' in cb:
            return cb['signal_age']
        return 0 if cb.get('firing') else None

    def _is_live(cb) -> bool:
        _a = _sig_age(cb)
        return _a is not None and _a <= _LIVE_MAX_AGE

    def _combos_of(v) -> tuple:
        """A regime's best strategy followed by its alternatives."""
        return (v, *(v.get('alt_combos') or [])) if v else ()

    def _wr_key(c):
        """Sort key for "highest win rate first"; a tie goes to the strategy
        with more trades, then to the higher expectancy."""
        c = c or {}
        return (float(c.get('win_rate', 0) or 0), int(c.get('total', 0) or 0),
                float(c.get('expectancy', 0) or 0))

    def _live_combos(row) -> list:
        """Strategies of the stock's CURRENT regime (best + runner-ups) that
        started a signal within the live window, highest win rate first."""
        cb = ((row.get('regimes') or {}).get(row.get('current_regime', 'RANGE'))
              or {})
        return sorted((c for c in _combos_of(cb) if _is_live(c)),
                      key=_wr_key, reverse=True)

    def _age_txt(age) -> str:
        # Ages count trading sessions back from the latest bar in the data.
        return ('New signal' if age == 0 else
                'Signal 1 session ago' if age == 1 else f'Signal {age} sessions ago')

    def _is_validated(cb) -> bool:
        # Results cached before this flag existed were all validated.
        return bool((cb or {}).get('validated', True))

    _VAL_BADGE_TIP = {
        True:    ('Validated: picked on the first 70% of the period, then stayed '
                  'profitable over 10+ trades on the last 30% it never saw.'),
        'few':   ('Not validated: profitable on the bars it was picked on, but the '
                  'held-back last 30% had fewer than 10 trades in this regime — too '
                  'few to confirm it. Numbers shown are the fitted ones.'),
        'lost':  ('Not validated: profitable on the bars it was picked on, but it '
                  'lost money on the held-back last 30%. Numbers shown are the '
                  'fitted ones — treat with caution.'),
        'short': ('Not validated: the scan window is too short to hold back a test '
                  'period. Numbers shown are the fitted ones.'),
    }

    def _val_badge(cb) -> str:
        """Validated / Not validated / Failed test pill with an explanatory tooltip."""
        if _is_validated(cb):
            _k, _t, _tip = 'ok', '✓ Validated', _VAL_BADGE_TIP[True]
        else:
            _r = (cb or {}).get('fail_reason', 'few')
            _k = 'bad' if _r == 'lost' else 'warn'
            _t = '✕ Failed test' if _r == 'lost' else 'Not validated'
            _tip = _VAL_BADGE_TIP.get(_r, _VAL_BADGE_TIP['few'])
        return f"<span class='sc-vb sc-vb-{_k}' title='{_tip}'>{_t}</span>"

    _VAL_HELP = (
        'The strategy was picked using the first 70% of the period, then '
        'checked once on the last 30% — bars the search never saw. Validated '
        'strategies show their held-back numbers in the big stats; strategies '
        'that were not validated show their fitted numbers. A big drop from '
        'Fitted to Held back means the strategy was curve-fitted.')

    def _val_box(cb) -> str:
        """Fitted → held-back comparison plus a plain-language verdict."""
        cb = cb or {}
        _is_wr = cb.get('is_win_rate')
        if _is_wr is None:
            return ''
        _ok  = _is_validated(cb)
        _rsn = cb.get('fail_reason', 'few')
        _ho_tot = int(cb.get('ho_total', cb.get('total', 0) if _ok else 0) or 0)
        _ho_wr  = cb.get('ho_win_rate', cb.get('win_rate') if _ok else None)
        _ho_exp = cb.get('ho_expectancy', cb.get('expectancy') if _ok else None)
        if not _ok and _rsn == 'short':
            _ho_html = "<span class='sc-val-na'>not enough history</span>"
        elif _ho_tot and _ho_wr is not None:
            _hc = _wr_col(float(_ho_wr)) if _ok else (
                'var(--red)' if _rsn == 'lost' else 'var(--t1)')
            _ho_html = (f"<b style='color:{_hc};'>{float(_ho_wr):.0f}%</b>"
                        f"<span class='sc-val-n'>{_ho_tot} trades</span>")
        else:
            _ho_html = "<span class='sc-val-na'>no trades</span>"
        if _ok:
            _note = (f"Only {_ho_tot} recent trades — weak evidence"
                     if (cb.get('thin_sample') or cb.get('low_sample')) else '')
        elif _rsn == 'lost':
            _note = 'Lost money on the recent test period. Numbers above are from the fitted period only.'
        elif _rsn == 'short':
            _note = 'Scan window too short to hold back a test period. Numbers above are fitted only.'
        else:
            _note = (f"{_ho_tot} of 10 recent trades needed to confirm. "
                     f"Numbers above are from the fitted period.")
        return (
            "<div class='sc-val'>"
            "<div class='sc-val-h'>Validation"
            f"<span class='sc-help' title='{_VAL_HELP}'>?</span></div>"
            "<div class='sc-val-row'>"
            f"<div class='sc-val-c'><div class='sc-val-l'>Fitted (first 70%)</div>"
            f"<div class='sc-val-v'><b>{float(_is_wr):.0f}%</b>"
            f"<span class='sc-val-n'>{int(cb.get('is_total') or 0)} trades</span></div></div>"
            "<div class='sc-val-arrow'>→</div>"
            f"<div class='sc-val-c'><div class='sc-val-l'>Held back (last 30%)</div>"
            f"<div class='sc-val-v'>{_ho_html}</div></div>"
            "</div>"
            + (f"<div class='sc-val-note'>{_note}</div>" if _note else '')
            + "</div>"
        )

    _PF_HELP  = ("Profit Factor = total won ÷ total lost across all past signals. "
                 "1.0 = breakeven, 2.0+ = strong, 3.0+ = exceptional.")
    _EXP_HELP = ("Expectancy = average % return per signal. +1.5% means each "
                 "signal on average gained 1.5%. Negative = losing strategy.")

    # ── indicator chips, coloured by indicator type ──────────────────────────
    # The type of every indicator comes from the guide's catalogue (single
    # source of truth), so a chip's colour always matches the guide's grouping.
    from scanner_guide import _INDICATORS as _GUIDE_INDS
    _IND_TYPES = [   # same order as scanner_guide._INDICATORS
        ('Trend',      '#4B47C4', '75,71,196'),
        ('Momentum',   '#A34800', '255,149,0'),
        ('Volume',     '#086F8C', '8,111,140'),
        ('Volatility', '#8E3FBA', '142,63,186'),
        ('Levels',     '#0063D1', '0,99,209'),
        ('Oversold',   '#B0124F', '194,24,91'),
        ('Position',   '#4A5A12', '120,140,30'),
    ]
    _IND_TYPE_OF = {k: i for i, (_c, _items) in enumerate(_GUIDE_INDS)
                    for (k, _cond, _w) in _items}

    def _chip(k) -> str:
        _i = _IND_TYPE_OF.get(k)
        _nm, _fg, _rgb = _IND_TYPES[_i] if _i is not None else ('', '#3F3F46', '63,63,70')
        return (f"<span class='sc-chip-ind' title='{_nm} indicator' "
                f"style='color:{_fg};background:rgba({_rgb},0.11);"
                f"box-shadow:inset 0 0 0 1px rgba({_rgb},0.22);'>{_ind_label([k])}</span>")

    def _chips(keys) -> str:
        return "<span class='sc-chip-plus'>+</span>".join(_chip(k) for k in keys)

    _IND_LEGEND = (
        "<div class='sc-legend'><span class='sc-legend-t'>Indicator types</span>"
        + ''.join(f"<span class='sc-legend-i'><i style='background:{_fg};'></i>{_nm}</span>"
                  for _nm, _fg, _rgb in _IND_TYPES)
        + "</div>")

    _REGIME_ICON = {'TREND': '↗', 'RANGE': '↔', 'VOLATILE': '⚡'}
    _REGIME_HELP = {
        'TREND':    ('Trending regime — directional, sustained price moves. '
                     'Best for momentum/breakout strategies.'),
        'RANGE':    ('Ranging regime — price oscillates between support and '
                     'resistance. Best for mean-reversion strategies.'),
        'VOLATILE': ('Volatile regime — large unpredictable swings. Hardest '
                     'to trade; strategies here use wider stops.'),
    }

    def _val_cell(c) -> str:
        """Validation badge plus one short line; full detail in the tooltip."""
        c = c or {}
        _ok  = _is_validated(c)
        _rsn = c.get('fail_reason', 'few')
        _ho_t = int(c.get('ho_total', c.get('total', 0) if _ok else 0) or 0)
        _ho_w = c.get('ho_win_rate', c.get('win_rate') if _ok else None)
        _is_w = c.get('is_win_rate')
        _is_t = int(c.get('is_total') or 0)
        if _ok:
            _line = f"Recent test {float(_ho_w):.0f}% · {_ho_t} trades"
        elif _rsn == 'lost':
            _line = f"Recent test {float(_ho_w or 0):.0f}% · lost money"
        elif _rsn == 'short':
            _line = "Window too short to test"
        else:
            _line = f"{_ho_t} of 10 recent trades"
        _tip = (f"Fitted (first 70%): {float(_is_w):.0f}% on {_is_t} trades. "
                if _is_w is not None else '')
        _tip += (f"Held back (last 30%): {float(_ho_w):.0f}% on {_ho_t} trades."
                 if (_ho_t and _ho_w is not None) else "Held back (last 30%): no trades.")
        return (f"<div class='sc-tv' title='{_tip}'>{_val_badge(c)}"
                f"<div class='sc-tv-l'>{_line}</div></div>")

    def _strat_row(c, regime, is_now=False, alt=False, focus=False) -> str:
        """One table row: regime · strategy · numbers · trades · validation.
        `focus` highlights the strategy a Live Signal Check card jumped to."""
        c = c or {}
        _w = float(c.get('win_rate', 0) or 0)
        _p = float(c.get('profit_factor', 0) or 0)
        _e = float(c.get('expectancy', 0) or 0)
        _n = int(c.get('total', 0) or 0)
        _thin = _n < 10
        if alt:
            _reg = "<div class='sc-tr-reg sc-tr-alt'>Alternative</div>"
        else:
            _reg = (f"<div class='sc-tr-reg' title='{_REGIME_HELP.get(regime, '')}'>"
                    f"<span class='sc-tr-ico'>{_REGIME_ICON.get(regime, '')}</span>"
                    f"<span class='sc-tr-rn'>{regime.title()}</span>"
                    + ("<span class='sc-now-pill' title='The stock is in this market regime "
                       "today, so this is the strategy that applies now.'>Today</span>"
                       if is_now else '')
                    + "</div>")
        _sig = (f"<span class='sc-cfire'>{_age_txt(_sig_age(c))}</span>"
                if _is_live(c) else '')
        return (
            f"<div class='sc-tr{' sc-tr-now' if is_now and not alt else ''}"
            f"{' sc-tr-sub' if alt else ''}{' sc-thin' if _thin else ''}"
            f"{' sc-tr-focus' if focus else ''}'>"
            + _reg
            + f"<div class='sc-tr-strat'>{_chips(c.get('indicators', []))}{_sig}</div>"
            # Each number carries its own label (data-l): the cards sit two per
            # row, too narrow for a shared column header.
            + f"<div class='sc-tr-n' data-l='Win rate'>{_w:.0f}%</div>"
            + f"<div class='sc-tr-n' data-l='Profit factor' title='{_PF_HELP}'>{_p:.1f}×</div>"
            + f"<div class='sc-tr-n' data-l='Expectancy' title='{_EXP_HELP}' "
              f"style='color:{'var(--red)' if _e <= 0 else 'var(--green)'};'>{_e:+.1f}%</div>"
            + f"<div class='sc-tr-n' data-l='Trades'>{_n}<div class='sc-tr-sm'>"
              f"{int(c.get('wins', 0) or 0)}W · "
              f"{int(c.get('losses', 0) or 0)}L{' · too few' if _thin else ''}</div></div>"
            + _val_cell(c)
            + "</div>")

    # ── top bar ───────────────────────────────────────────────────────────────
    _n_res  = len(st.session_state.sc_results or [])
    _n_fire = sum(1 for row in (st.session_state.sc_results or [])
                  if _live_combos(row))
    _n_fire_val = sum(1 for row in (st.session_state.sc_results or [])
                      if _live_combos(row) and _is_validated(_live_combos(row)[0]))
    _upd = (st.session_state.get('_sc_full_cache') or {}).get(f"{st.session_state.sc_period}|v3")
    _upd_txt = _time.strftime('%H:%M', _time.localtime(_upd[0])) if _upd else '—'
    _tl, _tr = st.columns([1, 0.12])
    with _tl:
        st.markdown(
            "<div class='sc-tb'>"
            "<div style='margin-right:auto;'><div class='sc-title'>Strategy Scanner</div>"
            "<div class='sc-sub'>The best indicator strategies for every Tadawul stock, "
            "in every market regime.</div></div>"
            f"<div class='sc-kpi'><div class='sc-kv' style='color:var(--green);'>{_n_fire}</div>"
            f"<div class='sc-kl'>Live signals</div></div>"
            f"<div class='sc-kpi'><div class='sc-kv'>{_n_fire_val}</div>"
            f"<div class='sc-kl'>Validated</div></div>"
            f"<div class='sc-kpi'><div class='sc-kv'>{_n_res}<span style='color:var(--t4);"
            f"font-weight:500;'>/{len(_ALL_SYMS)}</span></div>"
            f"<div class='sc-kl'>Stocks scanned</div></div>"
            f"<div class='sc-kpi'><div class='sc-kv'>{_upd_txt}</div>"
            f"<div class='sc-kl'>Updated</div></div>"
            "</div>",
            unsafe_allow_html=True)
    with _tr:
        with st.container(key="sc_back"):
            if st.button("← Back", key="sc_back_btn", use_container_width=True):
                st.session_state.show_champions_vault = False
                st.rerun()

    # ── Arabic guide: what the page does and how, incl. the background work ──
    from scanner_guide import render_scanner_guide
    render_scanner_guide()

    # ── controls panel ────────────────────────────────────────────────────────
    def _pill_row(label, options, state_key, prefix, reset_scan=False,
                  extra_cols=None):
        """Render a labeled row of pill buttons. Returns True if any clicked."""
        _cur = st.session_state[state_key]
        _n   = len(options)
        _widths = [0.42] + [0.65] * _n + (extra_cols or [])
        _cols = st.columns(_widths, gap="small")
        with _cols[0]:
            st.markdown(
                f"<div class='sc-ctrl-lbl' style='line-height:1.65rem;'>{label}</div>",
                unsafe_allow_html=True)
        for _i, (_lbl, _val) in enumerate(options):
            _active = 'on' if _cur == _val else f'off{_i}'
            with _cols[_i + 1]:
                with st.container(key=f"{prefix}_{_active}_{_i}"):
                    if st.button(_lbl, key=f"{prefix}_btn_{_val}",
                                 use_container_width=True):
                        st.session_state[state_key] = _val
                        if reset_scan:
                            st.session_state.sc_results = None
                            st.session_state.sc_done    = False
                        st.rerun()
        return _cols

    # Period tooltips
    from scanner_engine import _PERIOD_CFG as _PCFG

    def _period_tip(k, blurb):
        _w, _h, _p, _s = _PCFG[k]
        return (f"{k} = last {_w} trading days (~{_w / 250:.1f} years) scored, "
                f"{_h}-day max hold, +{_p * 100:g}% target / -{_s * 100:g}% stop. {blurb}")

    _PERIOD_HELP = {
        'Short':  _period_tip('Short', 'Swing signals that resolve within days; '
                                       'highest signal frequency, more noise.'),
        'Medium': _period_tip('Medium', 'Balanced: multi-week moves. The recommended default.'),
        'Long':   _period_tip('Long', 'Slow, multi-month moves; fewer signals.'),
    }
    _PERIOD_LBL_HELP = ("Choose how much history to scan and the exit rules used to "
                        "score past trades. " + " · ".join(
                            f"{k}: {_PCFG[k][0]} days" for k in ('Short', 'Medium', 'Long'))
                        + ". Longer periods give more reliable stats.")
    _SCAN_HELP = ("Run the scanner across all Tadawul symbols for the selected period. "
                  "Recomputes regime, fits strategies, and detects which ones are "
                  "currently firing.")
    _DAYS_HELP = (f"Scan the last N TRADING days ({_DAYS_MIN}-{_DAYS_MAX}). Tadawul runs "
                  "Sunday-Thursday, so weekends are never counted — 30 means 30 real "
                  "sessions (~6 weeks). Extra history is still loaded behind the scenes "
                  "to warm up long indicators like SMA 200, but only signals inside your "
                  "window are scored. Short windows give few signals and thin results — "
                  "below ~120 days expect many empty regimes.")

    # Row: [Short | Medium | Long | Days] segmented control · days box · Run Scan
    # Trading days, not calendar days: Tadawul runs Sun-Thu, and the data has
    # no Fri/Sat bars at all, so 30 here means 30 real sessions (~6 weeks).
    _days_active = _sc_days_selected(st.session_state.sc_period)
    _cur_seg = 'Days' if _days_active else st.session_state.sc_period

    def _on_seg():
        _v = st.session_state.get('sc_seg')
        if not _v:                       # tapping the active segment clears it
            st.session_state.sc_seg = _cur_seg
            return
        st.session_state.sc_period = (f"Days:{st.session_state.sc_days_n}"
                                      if _v == 'Days' else _v)
        st.session_state.sc_results   = None
        st.session_state.sc_done      = False
        st.session_state.sc_requested = False

    if not st.session_state.get('sc_seg'):
        st.session_state.sc_seg = _cur_seg
    _r1 = st.columns([4.2, 1.1, 1.5], gap="medium", vertical_alignment="center")
    with _r1[0]:
        with st.container(key="sc_seg_box"):
            st.segmented_control(
                "Period", _PERIODS + ['Days'], key="sc_seg", on_change=_on_seg,
                selection_mode="single", label_visibility="collapsed",
                help=_PERIOD_LBL_HELP + " Days = choose your own number of "
                     f"trading days ({_DAYS_MIN}-{_DAYS_MAX}).")
    with _r1[1]:
        if _days_active:
            with st.container(key="sc_days_box"):
                _dn = st.number_input(
                    "days", min_value=_DAYS_MIN, max_value=_DAYS_MAX,
                    value=int(st.session_state.sc_days_n), step=5,
                    key="sc_days_input", label_visibility="collapsed",
                    help=_DAYS_HELP)
            if int(_dn) != int(st.session_state.sc_days_n):
                st.session_state.sc_days_n    = int(_dn)
                st.session_state.sc_period    = f"Days:{int(_dn)}"
                st.session_state.sc_results   = None
                st.session_state.sc_done      = False
                st.session_state.sc_requested = False
                st.rerun()
    with _r1[2]:
        with st.container(key="sc_run"):
            if st.button("Run Scan", key="sc_run_btn", use_container_width=True,
                         help=_SCAN_HELP):
                st.session_state.sc_results   = None
                st.session_state.sc_done      = False
                st.session_state.sc_requested = True
                st.session_state.lsc_show_all = False
                st.rerun()

    # ── scan ─────────────────────────────────────────────────────────────────
    _sel_period = st.session_state.sc_period

    # Only scan when the user explicitly taps ↻ Run Scan — never on page load.
    if st.session_state.sc_requested and not st.session_state.sc_done:
        # Repeat taps of ↻ Run Scan for the same period used to redo the full
        # ~20-30s analysis from scratch every time, even with unchanged data.
        # Reuse a finished result for this period if it's still fresh (20 min,
        # matching the underlying data cache) so repeat runs are instant.
        _sc_cache = st.session_state.setdefault('_sc_full_cache', {})
        _cached   = _sc_cache.get(f"{_sel_period}|v3")
        if _cached is not None and (_time.time() - _cached[0]) < 1200:
            st.session_state.sc_results         = _cached[1]
            if len(_cached) > 2:
                st.session_state['_sc_raw'] = {'period': _sel_period, 'dfs': _cached[2]}
            st.session_state.sc_done            = True
            st.session_state.sc_show_all_strats = False
            st.session_state.sc_focus           = None
            st.rerun()

        from scanner_engine import download_all_raw, _analyse_df, resolve_period
        _out  = []
        # 1) Cached batch download, instant on a warm cache; hard-capped at
        #    ~240s worst case by a wall-clock budget inside download_all_raw so
        #    it can never hang forever. Medium/Long now pull 5y rather than
        #    6mo/2y (the scoring window has to be long enough to split into a
        #    fitted half and a held-back half), so a cold run takes longer.
        try:
            with st.spinner("Downloading Tadawul history in one request… "
                            "(up to ~2 min cold for 5 years of data)"):
                _raw = download_all_raw(tuple(_ALL_SYMS), _sel_period, _v=19)
        except Exception:
            # Download failed (network / cold connection). Reset so the button
            # returns to a ready state instead of leaving the UI stuck loading.
            st.session_state.sc_requested = False
            st.session_state.sc_done      = False
            st.error("Couldn't reach the market data service. Please tap ↻ Run Scan again.")
            st.stop()
        _prog = st.progress(0, text="Analysing strategies…")
        # 2) Per-symbol analysis with a live progress bar (this is the slow part,
        #    ~20s) so the user sees continuous movement instead of a frozen bar.
        _, _, _hold, _pt, _sl, _window = resolve_period(_sel_period)
        _tot = len(_ALL_SYMS)
        for _i, _sym in enumerate(_ALL_SYMS):
            _df = _raw.get(_sym)
            if _df is not None:
                try:
                    _data = _analyse_df(_df, _hold, _pt, _sl, window=_window)
                except Exception:
                    _data = None
                if _data:
                    _data['_sym']   = _sym
                    _data['_sname'] = _ticker_map.get(_sym, '')
                    _out.append(_data)
            if _i % 3 == 0 or _i == _tot - 1:
                _prog.progress((_i + 1) / _tot,
                               text=f"Analysing {_sym.replace('.SR','')} ({_i+1}/{_tot})")
        _prog.empty()
        # Keep the raw OHLCV so Live Signal Check cards can reuse it instead of
        # re-downloading every firing stock one by one.
        st.session_state['_sc_raw'] = {'period': _sel_period, 'dfs': _raw}
        st.session_state.sc_results      = _out
        st.session_state.sc_done         = True
        st.session_state.sc_show_all_strats = False
        st.session_state.sc_focus        = None
        # '|v3': results from before rows without a close were dropped and the
        # 7 indicators were corrected
        # (they showed 'nan' prices) must not be reused.
        _sc_cache[f"{_sel_period}|v3"] = (_time.time(), _out, _raw)
        st.rerun()

    if not st.session_state.sc_requested:
        st.markdown(
            "<div style='background:#FFFFFF;border:1px solid #DEDEE3;"
            "border-radius:12px;padding:4rem 2rem;text-align:center;'>"
            "<div style='font-size:1rem;font-weight:800;color:#6E6E75;'>"
            "Choose a period above, then tap ↻ Run Scan</div>"
            "<div style='font-size:0.68rem;color:#6E6E75;margin-top:0.5rem;'>"
            "The scanner does not run automatically — pick Short / Medium / Long, "
            "then start the scan.</div></div>",
            unsafe_allow_html=True)
        return

    _rows_all = st.session_state.sc_results or []
    if not _rows_all:
        st.markdown(
            "<div style='background:#FFFFFF;border:1px solid #DEDEE3;"
            "border-radius:12px;padding:4rem 2rem;text-align:center;'>"
            "<div style='font-size:1rem;font-weight:800;color:#6E6E75;'>"
            "No results — tap ↻ Run Scan</div></div>",
            unsafe_allow_html=True)
        return

    def _best_wr(row):
        regs = row.get('regimes') or {}
        vals = [float(cb.get('win_rate', 0) or 0) for cb in regs.values() if cb]
        return max(vals) if vals else 0.0

    def _has_firing(row):
        regs = row.get('regimes') or {}
        return any((cb or {}).get('firing') for cb in regs.values())

    # ── never render a losing strategy ───────────────────────────────────────
    # scanner_engine now rejects combos with expectancy <= 0 / profit factor
    # <= 1 at the source, so this is belt-and-braces for results still sitting
    # in session_state from a scan that ran before that gate existed. Showing a
    # negative-expectancy combo as a regime's "best strategy" hands the user a
    # strategy that lost money over its own backtest.
    def _profitable(cb) -> bool:
        if not cb:
            return False
        return (float(cb.get('expectancy', 0) or 0) > 0
                and float(cb.get('profit_factor', 0) or 0) > 1.0)

    for _r in _rows_all:
        _rg = _r.get('regimes') or {}
        for _rn in ('TREND', 'RANGE', 'VOLATILE'):
            if _rn in _rg and not _profitable(_rg.get(_rn)):
                _rg[_rn] = None
            elif _rg.get(_rn):
                _rg[_rn]['alt_combos'] = [_a for _a in (_rg[_rn].get('alt_combos') or [])
                                          if _profitable(_a)]

    # Drop stocks with no qualifying combo in any regime — empty cards are noise.
    _rows = [r for r in _rows_all
             if any((r.get('regimes') or {}).get(_rn) for _rn in ('TREND', 'RANGE', 'VOLATILE'))]

    # Every regime keeps its best profitable strategy; a stock only drops out
    # when no combo made money in any regime even on the bars it was fitted to.
    _rejected = len(_rows_all) - len(_rows)
    if not _rows:
        st.markdown(
            "<div style='background:#FFFFFF;border:1px solid #DEDEE3;"
            "border-radius:12px;padding:2.5rem 1.5rem;text-align:center;'>"
            "<div style='font-size:0.85rem;font-weight:800;color:#3F3F46;'>"
            "No profitable strategy found</div>"
            "<div style='font-size:0.66rem;color:#6E6E75;margin-top:0.5rem;"
            "line-height:1.5;'>"
            f"None of the {len(_rows_all)} scanned stocks had an indicator combo "
            "that made money in any regime over this period."
            "</div></div>",
            unsafe_allow_html=True)
        return

    # ── search bar (styled in the page CSS block) ────────────────────────────
    with st.container(key="sc_search_box"):
        _sc_query = st.text_input(
            " ", placeholder="🔍  Search symbol or company name…",
            key="sc_search_q", label_visibility="collapsed")
    _sc_q = (_sc_query or '').strip().lower()
    if _sc_q:
        _rows = [r for r in _rows
                 if _sc_q in r['_sym'].replace('.SR', '').lower()
                 or _sc_q in (r.get('_sname') or '').lower()]

    # ── filter: decides which strategies every section below shows ───────────
    _REGIMES = ('TREND', 'RANGE', 'VOLATILE')
    _F_WR = {'Any': 0, '60%+': 60, '70%+': 70, '80%+': 80}
    _F_TR = {'Any': 0, '10+': 10, '20+': 20}
    _F_RG = {'All': None, 'Trend': 'TREND', 'Range': 'RANGE', 'Volatile': 'VOLATILE'}
    _F_DEF = (('sc_f_wr', 'Any'), ('sc_f_tr', 'Any'), ('sc_f_rg', 'All'))
    for _k, _v in _F_DEF:
        if not st.session_state.get(_k):
            st.session_state[_k] = _v

    def _keep_one(key, default):
        # Tapping the selected segment would clear it; fall back to the default.
        if not st.session_state.get(key):
            st.session_state[key] = default

    def _clear_filters():
        for _k, _v in _F_DEF:
            st.session_state[_k] = _v

    _fc = st.columns([1.3, 1, 1.45, 0.75], gap="medium", vertical_alignment="bottom")
    for _col, (_key, _dflt), _lbl, _opts in zip(
            _fc, _F_DEF, ('Win rate', 'Trades', 'Market regime'), (_F_WR, _F_TR, _F_RG)):
        with _col:
            st.markdown(f"<div class='sc-flt-l'>{_lbl}</div>", unsafe_allow_html=True)
            with st.container(key=f"sc_flt_{_key[3:]}"):
                st.segmented_control(
                    _lbl, list(_opts), key=_key, on_change=_keep_one,
                    args=(_key, _dflt), selection_mode="single",
                    label_visibility="collapsed")
    _f_wr = _F_WR[st.session_state.sc_f_wr]
    _f_tr = _F_TR[st.session_state.sc_f_tr]
    _f_rg = _F_RG[st.session_state.sc_f_rg]
    _f_on = bool(_f_wr or _f_tr or _f_rg)
    if _f_on:
        with _fc[3], st.container(key="sc_flt_clear"):
            st.button("Clear filters", key="sc_flt_clear_btn", on_click=_clear_filters,
                      use_container_width=True)

    def _strats(row, rn) -> list:
        """The stock's strategies for regime `rn` that pass the filter,
        highest win rate first. The win rate is compared as displayed
        (rounded), so a strategy shown as 70% counts as 70%+."""
        return sorted(
            (c for c in _combos_of((row.get('regimes') or {}).get(rn))
             if round(float(c.get('win_rate', 0) or 0)) >= _f_wr
             and int(c.get('total', 0) or 0) >= _f_tr
             and _f_rg in (None, rn)),
            key=_wr_key, reverse=True)

    def _live_shown(row) -> list:
        """Live strategies of today's regime that pass the filter, best first."""
        return [c for c in _strats(row, row.get('current_regime', 'RANGE'))
                if _is_live(c)]

    _n_searched = len(_rows)
    _rows = [r for r in _rows if any(_strats(r, _rn) for _rn in _REGIMES)]
    if _f_on:
        st.markdown(
            f"<div class='sc-flt-sum'><b>{len(_rows)}</b> of {_n_searched} stocks have a "
            "strategy that matches the filter</div>",
            unsafe_allow_html=True)
    if not _rows:
        st.markdown(
            "<div style='background:var(--card);border:1px solid var(--hair);"
            "border-radius:var(--r-lg);padding:3rem 1.5rem;text-align:center;'>"
            "<div style='font-size:1.05rem;font-weight:600;color:var(--t1);'>"
            "No stock matches</div>"
            "<div style='font-size:0.9rem;color:var(--t2);margin-top:0.4rem;'>"
            + ("Try a lower win rate, fewer trades or another market regime."
               if _f_on else "Try another symbol or company name.")
            + "</div></div>",
            unsafe_allow_html=True)
        return

    # Highest win rate first, judged on the strategy for the stock's TODAY
    # regime (the one that applies now). Stocks with no strategy for today's
    # regime follow, by their best win rate in another regime.
    def _row_key(r):
        _now = _strats(r, r.get('current_regime'))
        _best = max((c for _rn in _REGIMES for c in _strats(r, _rn)), key=_wr_key)
        return (bool(_now), _wr_key(_now[0] if _now else _best))

    _rows.sort(key=_row_key, reverse=True)
    _all_combos = [c for r in _rows for _rn in _REGIMES for c in _strats(r, _rn)]
    _n_val = sum(1 for c in _all_combos if _is_validated(c))
    _n_fail = sum(1 for c in _all_combos
                  if not _is_validated(c) and c.get('fail_reason') == 'lost')

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Live Signal Check
    # ══════════════════════════════════════════════════════════════════════════
    _REGIME_SHORT = {'TREND': 'Trend', 'RANGE': 'Range', 'VOLATILE': 'Volatile'}

    # Only include stocks where one of the CURRENT regime's strategies started
    # a signal within the live window (_LIVE_MAX_AGE).
    _fire_rows_raw = [r for r in _rows if _live_shown(r)]

    def _lsc_score(row):
        cb = _live_shown(row)[0]
        return (_wr_key(cb), -(_sig_age(cb) or 0))

    # Highest win rate first (the stock's best live strategy); the fresher
    # signal breaks a tie.
    _fire_rows = sorted(_fire_rows_raw, key=_lsc_score, reverse=True)
    _n_signals = len(_fire_rows)

    _LSC_HELP = (f"Live Signal Check shows stocks where one of the strategies for "
                 f"the stock&#39;s CURRENT market regime (from Scanned Strategies) "
                 f"started a signal in the last "
                 f"{_LIVE_MAX_AGE + 1} trading days. The colored chip indicates how "
                 f"fresh the signal is — green = today, light green = 1 day ago, "
                 f"amber = older.")
    # section header
    st.markdown(
        f"<div class='lsc-section-hdr'>"
        f"<div class='lsc-section-line'></div>"
        f"<div class='lsc-section-pill'>"
        f"<span class='sc-live-dot'></span>"
        f"<span class='lsc-section-label'>Live Signal Check</span>"
        f"<span class='sc-help-pill' title='{_LSC_HELP}'>?</span>"
        + (f"<span class='lsc-section-count'>{_n_signals}</span>" if _n_signals else '')
        + f"</div>"
        f"<div class='lsc-section-line-r'></div>"
        f"</div>"
        f"<div class='sc-h2-s' style='margin:-0.6rem 0 1.2rem;'>Stocks where a strategy for "
        f"today's market regime started a buy signal in the last {_LIVE_MAX_AGE + 1} trading days. "
        f"Highest win rate first.</div>" + _IND_LEGEND,
        unsafe_allow_html=True)

    if not _fire_rows:
        st.markdown(
            "<div style='background:#FFFFFF;border:1px solid #DEDEE3;"
            "border-radius:14px;padding:3rem;text-align:center;'>"
            "<div style='font-size:0.75rem;font-weight:800;color:#6E6E75;"
            "text-transform:uppercase;letter-spacing:1.2px;'>No best-fit signals</div>"
            "<div style='font-size:0.62rem;color:#6E6E75;margin-top:0.4rem;'>"
            + ("No live signal matches the filter" if _f_on else
               f"No stock's current-regime strategy triggered in the last "
               f"{_LIVE_MAX_AGE + 1} trading days")
            + "</div></div>",
            unsafe_allow_html=True)
    else:
        # chart expand state
        if 'lsc_chart_open' not in st.session_state:
            st.session_state.lsc_chart_open = {}

        _LSC_PREVIEW = 10
        if 'lsc_show_all' not in st.session_state:
            st.session_state.lsc_show_all = False
        _fire_rows_shown = (_fire_rows if st.session_state.lsc_show_all
                            else _fire_rows[:_LSC_PREVIEW])
        _raw_cache = st.session_state.get('_sc_raw') or {}
        _raw_dfs   = (_raw_cache.get('dfs') or {}) if _raw_cache.get('period') == _sel_period else {}

        def _stock_df(sym):
            """The scan's own bars for `sym` (downloaded again only if missing)."""
            df = _raw_dfs.get(sym)
            if df is None:
                from scanner_engine import get_stock_df as _gsd
                df = _gsd(sym, _sel_period, _v=2)
            return df

        # ── price levels of a live signal (shared by the cards and the table) ──
        _RR_COL = {'Great': '#1B7A36', 'Good': '#A34800', 'Weak': '#C1121F'}
        _lv_cache = st.session_state.setdefault('_lsc_levels', {})

        def _lsc_levels(sym, df, price):
            """Entry / stop / targets from the stock's price structure, with the %
            distances and risk:reward the cards and the table show. None when they
            can't be computed. Cached: the table needs every live stock each rerun."""
            if df is None or price <= 0:
                return None
            key = (_sel_period, sym, len(df), round(price, 4))
            if key not in _lv_cache:
                try:
                    from _levels import compute_structural_levels
                    lv = compute_structural_levels(df, price, True)
                    en, sl, t1, t2 = lv['entry'], lv['stop'], lv['t1'], lv['t2']
                    rp  = round(abs(en - sl) / en * 100, 1) if en else 0
                    t1p = round((t1 - en) / en * 100, 1) if en else 0
                    t2p = round((t2 - en) / en * 100, 1) if en else 0
                    rr  = round(t1p / rp, 2) if rp else 0
                    _lv_cache[key] = {
                        'entry': en, 'stop': sl, 't1': t1, 't2': t2, 'sl_pct': rp,
                        't1_pct': t1p, 't2_pct': t2p, 'rr': rr,
                        'rr_label': 'Great' if rr >= 2 else 'Good' if rr >= 1.5 else 'Weak',
                        'quality': lv.get('entry_quality', '') or ''}
                except Exception:
                    _lv_cache[key] = None
            return _lv_cache[key]

        def _goto_strategy(sym):
            # "View strategy": Scanned Strategies shows and highlights this
            # stock's card, and the page scrolls to it once.
            st.session_state.sc_focus = sym
            st.session_state.sc_focus_nonce = st.session_state.get('sc_focus_nonce', 0) + 1

        for _ri in range(0, len(_fire_rows_shown), 2):
            _pair = _fire_rows_shown[_ri:_ri + 2]
            # Always 2 columns so a lone last card keeps the same width.
            _grid = st.columns(2, gap="medium")
            # Full-width area under this pair: an opened chart renders here
            # instead of inside its card's column (which left the other column
            # empty next to a tall chart).
            _chart_area = st.container()
            for _lsc_pos, (_col_slot, _row) in enumerate(zip(_grid, _pair), _ri + 1):
             with _col_slot:
              _sym        = _row['_sym']
              _sname      = _row['_sname']
              _sym_d      = _sym.replace('.SR', '')
              _regs       = _row.get('regimes', {})
              _price      = float(_row.get('price', 0) or 0)
              _cur_regime = _row.get('current_regime', 'RANGE')
              _df_f       = _stock_df(_sym)

              # Only the CURRENT regime's strategies count (do not advertise
              # off-regime signals). The highest-ranked live one leads the card;
              # any other live ones are listed under it.
              _live = _live_shown(_row)
              if not _live:
                  continue

              _best_rname = _cur_regime
              _best_combo = _live[0]
              # Rank of the leading live strategy within its regime (1 = best),
              # in the same order Scanned Strategies lists them.
              _reg_list = _strats(_row, _cur_regime)
              _best_rank = next((_i + 1 for _i, _c in enumerate(_reg_list)
                                 if _c is _best_combo), 1)
              _same_df = _sym in _raw_dfs   # same bars the engine indexed
              _best_col   = _REGIME_COLORS.get(_best_rname, '#5C5C63')
              _inds   = _best_combo.get('indicators', [])
              _alts   = _live[1:]

              # price ladder
              _ladder = ''; _en = _sl_p = _t1 = _t2 = 0.0
              _lvx = _lsc_levels(_sym, _df_f, _price)
              if _lvx:
                  try:
                      _en, _sl_p, _t1, _t2 = _lvx['entry'], _lvx['stop'], _lvx['t1'], _lvx['t2']
                      _eq   = _lvx['quality']
                      _rp, _t1p, _t2p, _rr = (_lvx['sl_pct'], _lvx['t1_pct'],
                                              _lvx['t2_pct'], _lvx['rr'])
                      _rr_c = _RR_COL[_lvx['rr_label']]
                      # tooltip text per quality level
                      _eq_tips = {
                          'OPTIMAL':  'Price is right at structural support — best possible entry. Low risk of stop hunt.',
                          'GOOD':     'Price is near support but slightly extended. Still a valid entry with manageable risk.',
                          'ELEVATED': 'Price has moved away from support. Risk is higher — consider waiting for a pullback.',
                          'CHASING':  'Price is far from support. Entering here risks a large stop or getting caught in a reversal.',
                      }
                      _eq_tip = _eq_tips.get(_eq, '')
                      _eq_html = (
                          f"<div class='lsc-lp' style='color:var(--t2);font-weight:500;' "
                          f"title='{_eq_tip}'>{_eq.title()} entry</div>"
                      ) if _eq else ''
                      # Ordered low → high price: Stop, Entry, Target 1, Target 2.
                      _ladder = (
                          f"<div class='lsc-ladder'>"
                          f"<div class='lsc-lc'><div class='lsc-ll'>Stop loss</div>"
                          f"<div class='lsc-lv'>{_sl_p:.2f}</div>"
                          f"<div class='lsc-lp' style='color:var(--red);'>−{_rp}%</div></div>"
                          f"<div class='lsc-lc' style='background:var(--blue-bg);'>"
                          f"<div class='lsc-ll'>Entry</div>"
                          f"<div class='lsc-lv'>{_en:.2f}</div>{_eq_html}</div>"
                          f"<div class='lsc-lc'><div class='lsc-ll'>Target 1</div>"
                          f"<div class='lsc-lv'>{_t1:.2f}</div>"
                          f"<div class='lsc-lp' style='color:var(--green);'>+{_t1p}%</div></div>"
                          f"<div class='lsc-lc'><div class='lsc-ll'>Target 2</div>"
                          f"<div class='lsc-lv'>{_t2:.2f}</div>"
                          f"<div class='lsc-lp' style='color:var(--green);'>+{_t2p}%</div></div>"
                          f"<div class='lsc-lc'><div class='lsc-ll'>Risk : Reward</div>"
                          f"<div class='lsc-lv'>1 : {_rr:.1f}</div>"
                          f"<div class='lsc-lp' style='color:{_rr_c};'>"
                          f"{_lvx['rr_label']}"
                          f"</div></div>"
                          f"</div>")
                  except Exception:
                      pass

              # ── Compute "when did this strategy fire" (date + time) ───────
              # Used inline next to the indicators row. No volume/trend/earnings
              # context badges — the user only cares about the signal itself.
              _fire_when_txt = ''
              _fire_when_c   = '#A34800'
              _eng_age  = _best_combo.get('signal_age')
              _eng_date = _best_combo.get('signal_date')
              if _eng_age is not None and _eng_date:
                  # The engine already found the signal bar — no need to
                  # rebuild every indicator for each card on every rerun.
                  _label = ('Latest session' if _eng_age == 0 else
                            '1 session earlier' if _eng_age == 1 else
                            f'{_eng_age} sessions earlier')
                  _fire_when_txt = f"{_label} · {_eng_date} 15:00"
                  _fire_when_c = ('#1B7A36' if _eng_age == 0 else
                                  '#1B7A36' if _eng_age == 1 else
                                  '#A34800' if _eng_age <= 5 else '#C1121F')
              elif _df_f is not None and len(_df_f) >= 21:
                  try:
                      import numpy as _np2
                      from scanner_engine import _build_states as _bs2
                      _st2 = _bs2(_df_f)
                      _N2 = len(_df_f)
                      if _inds and all(k in _st2 for k in _inds):
                          _ca2 = _st2[_inds[0]].copy()
                          for _ik2 in _inds[1:]:
                              _ca2 = _ca2 & _st2[_ik2]
                          _ed2 = _np2.zeros(_N2, dtype=_np2.int8)
                          _ed2[1:] = ((_ca2[1:] == 1) & (_ca2[:-1] == 0)).astype(_np2.int8)
                          _fires2 = _np2.where(_ed2 == 1)[0]
                          if len(_fires2):
                              _last_fire_i = int(_fires2[-1])
                              _bars_ago    = _N2 - 1 - _last_fire_i
                              # daily bars — show date + close-time (15:00 KSA)
                              _fire_ts = (_df_f['Date'].iloc[_last_fire_i]
                                          if 'Date' in _df_f.columns else None)
                              _fire_date_s = (str(_fire_ts)[:10]
                                              if _fire_ts is not None else '')
                              _label = ('Today' if _bars_ago == 0 else
                                        '1 day ago' if _bars_ago == 1 else
                                        f'{_bars_ago} days ago')
                              # KSA market close is 15:00; daily bar closes then
                              _fire_when_txt = (f"{_label} · {_fire_date_s} 15:00"
                                                if _fire_date_s else _label)
                              # Today=green (fresh), 1d=teal, ≤5d=amber, >5d=red
                              _fire_when_c = ('#1B7A36' if _bars_ago == 0 else
                                              '#1B7A36' if _bars_ago == 1 else
                                              '#A34800' if _bars_ago <= 5 else
                                              '#C1121F')
                  except Exception:
                      pass

              # indicator tags
              _ind_tags = _chips(_inds)

              # rank medal color
              # firing-time chip (solid-color filled, dark text)
              _fire_chip = (
                  f"<span style='margin-left:auto;font-size:0.6rem;font-weight:800;"
                  f"padding:0.22rem 0.6rem;border-radius:6px;"
                  f"background:{_fire_when_c};color:#FFFFFF;"
                  f"text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;'>"
                  f"{_fire_when_txt}</span>"
              ) if _fire_when_txt else ''

              # The card is the entry plan only. The strategy's numbers, and the
              # other strategies that also signalled, live in Scanned Strategies
              # (one tap away with "View strategy"), so only their count is here.
              _more = (f"<span class='lsc-more' title='{len(_alts)} more "
                       f"{'strategy' if len(_alts) == 1 else 'strategies'} for this regime "
                       f"also started a signal in the last {_LIVE_MAX_AGE + 1} trading days. "
                       f"View strategy shows them.'>+{len(_alts)} more signalling</span>"
                       if _alts else '')

              # ── main card ─────────────────────────────────────────────────
              _rank_lbl = ('Best fit' if _best_rank == 1 else f'Strategy #{_best_rank}')

              st.markdown(
                  "<div class='lsc-card2'>"
                  # header: symbol · name · price
                  "<div class='lsc-hdr2'>"
                  f"<span class='sc-rank{' sc-rank-top' if _lsc_pos <= 3 else ''}' "
                  f"title='Rank: highest win rate first'>{_lsc_pos}</span>"
                  f"<span class='lsc-sym2'>{_sym_d}</span>"
                  + (f"<span class='lsc-name2'>{_sname}</span>" if _sname else '')
                  + f"<span class='lsc-price2'>{_price:.2f}<small>SAR</small></span>"
                  "</div>"
                  # regime · rank · validation · when
                  "<div class='lsc-strat2' style='padding-bottom:0.6rem;'>"
                  f"<span class='lsc-regime2' title='{_REGIME_HELP.get(_best_rname, '')}'>"
                  f"{_REGIME_ICON.get(_best_rname, '')} {_best_rname.title()} · {_rank_lbl}</span>"
                  + _val_badge(_best_combo)
                  + _more
                  + (f"<span class='lsc-when' style='background:{_fire_when_c}1a;"
                     f"color:{_fire_when_c};'>{_fire_when_txt}</span>"
                     if _fire_when_txt else '')
                  + "</div>"
                  # indicators
                  f"<div class='lsc-strat2'>{_ind_tags}</div>"
                  + (f"<div class='lsc-ladder-wrap'>{_ladder}</div>" if _ladder else '')
                  + "</div>",
                  unsafe_allow_html=True)

              # ── chart toggle · jump to the stock's strategies ─────────────────
              _chart_key = f"lsc_chart_{_sym_d}"
              _is_open   = st.session_state.lsc_chart_open.get(_chart_key, False)
              _bc1, _bc2 = st.columns(2, gap="small")
              with _bc1, st.container(key=f"lsc_ctoggle_{_sym_d}"):
                  if st.button(
                      f"{'Hide chart' if _is_open else 'Show chart'}",
                      key=f"lsc_chart_btn_{_sym_d}",
                      use_container_width=True):
                      st.session_state.lsc_chart_open[_chart_key] = not _is_open
                      st.rerun()
              with _bc2, st.container(key=f"lsc_goto_{_sym_d}"):
                  st.button("View strategy ↓", key=f"lsc_goto_btn_{_sym_d}",
                            on_click=_goto_strategy, args=(_sym_d,),
                            use_container_width=True,
                            help="Jump to this stock's strategies in Scanned Strategies")

              # ── chart (shown when open) ───────────────────────────────────────
              if _is_open and _df_f is not None:
                with _chart_area, st.container(key=f"lsc_chartwrap_{_sym_d}"):
                    try:
                        import plotly.graph_objects as go
                        import numpy as _np
                        import pandas as _pd
                        from scanner_engine import _build_states

                        _states_all = _build_states(_df_f)
                        _N = len(_df_f)

                        # Match scanner_engine._eval filters so chart markers count
                        # equals the Wins/Losses/Total numbers in the box:
                        #   1. drop fires too close to the end (need `hold` bars to resolve)
                        #   2. keep only fires that happened in the card's target regime
                        from scanner_engine import _regime_arr as _rg_arr_fn
                        from scanner_engine import resolve_period as _rp_pre
                        _pcfg_sel_pre = st.session_state.get('sc_period', 'Medium')
                        _, _, _hold_pre, _, _, _ = _rp_pre(_pcfg_sel_pre)
                        try:
                            _reg_arr_chart = _rg_arr_fn(_df_f)
                        except Exception:
                            _reg_arr_chart = None

                        if _inds and all(k in _states_all for k in _inds):
                            _combo_arr = _states_all[_inds[0]].copy()
                            for _ik in _inds[1:]:
                                _combo_arr = _combo_arr & _states_all[_ik]
                            _edge = _np.zeros(_N, dtype=_np.int8)
                            _edge[1:] = ((_combo_arr[1:] == 1) & (_combo_arr[:-1] == 0)).astype(_np.int8)
                            _raw_idxs = _np.where(_edge == 1)[0]
                            # filter 1: drop fires with < hold bars remaining (can't resolve)
                            _raw_idxs = _raw_idxs[_raw_idxs < _N - _hold_pre]
                            # filter 2: keep only fires in this card's target regime
                            if _reg_arr_chart is not None:
                                _raw_idxs = _np.array([i for i in _raw_idxs
                                                       if i < len(_reg_arr_chart)
                                                       and _reg_arr_chart[i] == _best_rname])
                            _fire_idxs     = set(_raw_idxs.tolist())
                            # On the engine's own bars, mark exactly the trades
                            # behind the card's Wins/Losses/Total (held-back for
                            # validated strategies, fitted otherwise).
                            if _same_df and _best_combo.get('signal_idxs') is not None:
                                _fire_idxs = {int(_i) for _i in _best_combo['signal_idxs']}
                            # Live signal = the bar the card's signal started on.
                            _cur_firing    = _eng_age is not None and _eng_age <= _LIVE_MAX_AGE
                            _ind_states    = {k: bool(int(_states_all[k][-1]) == 1)
                                              for k in _inds if k in _states_all}
                        else:
                            _fire_idxs  = set()
                            _cur_firing = False
                            _ind_states = {}

                        # Show enough history that every counted signal is visible.
                        # The Total/Wins/Losses numbers in the box come from ALL fires
                        # in the lookback window — so the chart must span at least back
                        # to the earliest fire, plus a small padding for context.
                        _first_fire = (min(_fire_idxs) if _fire_idxs else _N - 60)
                        _tail_min   = max(60, _N - _first_fire + 10)  # at least 60 bars
                        _offset     = max(0, _N - _tail_min)
                        _cdf      = _df_f.iloc[_offset:].copy().reset_index(drop=True)
                        _today_s  = str(_cdf['Date'].iloc[-1])[:10] if 'Date' in _cdf.columns else ''
                        _xd       = (_pd.to_datetime(_cdf['Date'])
                                     if 'Date' in _cdf.columns else list(range(len(_cdf))))

                        # rich per-candle hover: OHLC + day change%, no guessing
                        _chg_pct = ((_cdf['Close'] - _cdf['Open']) / _cdf['Open'] * 100).round(2)
                        _hover_txt = [
                            f"<b>{str(_cdf['Date'].iloc[_i])[:10] if 'Date' in _cdf.columns else _i}</b><br>"
                            f"Open&nbsp;&nbsp;{_cdf['Open'].iloc[_i]:.2f}<br>"
                            f"High&nbsp;&nbsp;{_cdf['High'].iloc[_i]:.2f}<br>"
                            f"Low&nbsp;&nbsp;&nbsp;{_cdf['Low'].iloc[_i]:.2f}<br>"
                            f"Close&nbsp;{_cdf['Close'].iloc[_i]:.2f}<br>"
                            f"Chg&nbsp;&nbsp;&nbsp;{_chg_pct.iloc[_i]:+.2f}%"
                            for _i in range(len(_cdf))
                        ]

                        # Row 1: price. Row 2: proof panel — one strip per
                        # indicator showing the days its condition is true.
                        from plotly.subplots import make_subplots as _mksub
                        _n_proof = len(_inds) + 2          # + "All agree" + regime
                        fig = _mksub(rows=2, cols=1, shared_xaxes=True,
                                     vertical_spacing=0.035,
                                     row_heights=[0.68, 0.32] if _n_proof <= 5 else [0.6, 0.4])
                        fig.add_trace(go.Candlestick(
                            x=_xd,
                            open=_cdf['Open'], high=_cdf['High'],
                            low=_cdf['Low'],   close=_cdf['Close'],
                            increasing_line_color='#1FA855', decreasing_line_color='#E0282E',
                            increasing_fillcolor='#1FA855', decreasing_fillcolor='#E0282E',
                            line_width=1.4, whiskerwidth=0.85,
                            text=_hover_txt, hoverinfo='text', name=''))

                        # ── indicator overlays — the actual lines/bands whose
                        # crossover made the strategy fire, drawn on real price
                        # data so it's visible proof, not just a stat box.
                        _OVERLAY_COLORS = {
                            'EMA': ('#0063D1', '#8E3FBA'), 'SMA': ('#0063D1', '#8E3FBA'),
                            'WMA': ('#A33A00',), 'HULL': ('#086F8C',), 'VWAP': ('#A34800',),
                            'PSAR': ('#D4153F',), 'KELT': ('#A2845E', '#A2845E'),
                            'DONCH': ('#15704A', '#15704A'), 'BB': ('#8E3FBA', '#8E3FBA'),
                        }
                        try:
                            import pandas_ta as _ta_ov
                            _c_full = _df_f['Close'].astype(float)
                            _h_full = _df_f['High'].astype(float)
                            _l_full = _df_f['Low'].astype(float)
                            for _ov_k in _inds:
                                if _ov_k == 'EMA':
                                    _e20 = _ta_ov.ema(_c_full, 20); _e50 = _ta_ov.ema(_c_full, 50)
                                    if _e20 is not None:
                                        fig.add_trace(go.Scatter(x=_xd, y=_e20.iloc[_offset:],
                                            mode='lines', line=dict(color='#0063D1', width=1.3),
                                            name='EMA 20', hovertemplate='EMA20 %{y:.2f}<extra></extra>'))
                                    if _e50 is not None:
                                        fig.add_trace(go.Scatter(x=_xd, y=_e50.iloc[_offset:],
                                            mode='lines', line=dict(color='#8E3FBA', width=1.3),
                                            name='EMA 50', hovertemplate='EMA50 %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'SMA':
                                    _s50 = _c_full.rolling(50).mean(); _s200 = _c_full.rolling(200).mean()
                                    fig.add_trace(go.Scatter(x=_xd, y=_s50.iloc[_offset:],
                                        mode='lines', line=dict(color='#0063D1', width=1.3),
                                        name='SMA 50', hovertemplate='SMA50 %{y:.2f}<extra></extra>'))
                                    fig.add_trace(go.Scatter(x=_xd, y=_s200.iloc[_offset:],
                                        mode='lines', line=dict(color='#8E3FBA', width=1.3),
                                        name='SMA 200', hovertemplate='SMA200 %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'WMA':
                                    _w20 = _ta_ov.wma(_c_full, 20)
                                    if _w20 is not None:
                                        fig.add_trace(go.Scatter(x=_xd, y=_w20.iloc[_offset:],
                                            mode='lines', line=dict(color='#A33A00', width=1.3),
                                            name='WMA 20', hovertemplate='WMA20 %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'HULL':
                                    _hl = _ta_ov.hma(_c_full, 16)
                                    if _hl is not None:
                                        fig.add_trace(go.Scatter(x=_xd, y=_hl.iloc[_offset:],
                                            mode='lines', line=dict(color='#086F8C', width=1.3),
                                            name='Hull MA', hovertemplate='Hull %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'VWAP':
                                    _tp_ov = (_h_full + _l_full + _c_full) / 3
                                    _vo_ov = _df_f['Volume'].astype(float)
                                    _vwap_ov = (_tp_ov * _vo_ov).rolling(20).sum() / _vo_ov.rolling(20).sum()
                                    fig.add_trace(go.Scatter(x=_xd, y=_vwap_ov.iloc[_offset:],
                                        mode='lines', line=dict(color='#A34800', width=1.3, dash='dot'),
                                        name='VWAP', hovertemplate='VWAP %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'PSAR':
                                    _psar_ov = _ta_ov.psar(_h_full, _l_full, _c_full)
                                    if _psar_ov is not None:
                                        _long_col = [c2 for c2 in _psar_ov.columns if 'PSARl' in c2]
                                        if _long_col:
                                            fig.add_trace(go.Scatter(
                                                x=_xd, y=_psar_ov[_long_col[0]].iloc[_offset:],
                                                mode='markers', marker=dict(color='#D4153F', size=3),
                                                name='PSAR', hovertemplate='PSAR %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'BB':
                                    _bb_ov = _ta_ov.bbands(_c_full, 20)
                                    if _bb_ov is not None and _bb_ov.shape[1] >= 3:
                                        fig.add_trace(go.Scatter(x=_xd, y=_bb_ov.iloc[_offset:, 2],
                                            mode='lines', line=dict(color='#8E3FBA', width=1, dash='dot'),
                                            name='BB Upper', hovertemplate='BB Up %{y:.2f}<extra></extra>'))
                                        fig.add_trace(go.Scatter(x=_xd, y=_bb_ov.iloc[_offset:, 0],
                                            mode='lines', line=dict(color='#8E3FBA', width=1, dash='dot'),
                                            name='BB Lower', fill='tonexty',
                                            fillcolor='rgba(175,82,222,0.05)',
                                            hovertemplate='BB Low %{y:.2f}<extra></extra>'))
                                elif _ov_k == 'DONCH':
                                    _dc_ov = _h_full.rolling(20).max()
                                    fig.add_trace(go.Scatter(x=_xd, y=_dc_ov.iloc[_offset:],
                                        mode='lines', line=dict(color='#15704A', width=1.1, dash='dash'),
                                        name='Donchian Hi', hovertemplate='Donch Hi %{y:.2f}<extra></extra>'))
                        except Exception:
                            pass

                        # past fires — W/L outcome markers. Every trade is
                        # re-simulated with scanner_engine.simulate_trade, the
                        # exact function the backtest uses, so the markers and
                        # the Past signals table add up to the card's numbers.
                        from scanner_engine import simulate_trade as _sim_trade
                        from scanner_engine import resolve_period as _rp_b
                        _open_arr  = _df_f['Open'].values.astype(float)
                        _close_arr = _df_f['Close'].values.astype(float)
                        _high_arr  = _df_f['High'].values.astype(float)
                        _low_arr   = _df_f['Low'].values.astype(float)
                        _, _, _hold_b, _pt_b, _sl_b, _ = _rp_b(_sel_period)

                        _win_x, _win_y   = [], []
                        _loss_x, _loss_y = [], []
                        _sig_history_rows = []   # collect per-signal details for table

                        for _fi in sorted(_fire_idxs):
                            _ci = _fi - _offset
                            if _ci < 0 or _ci >= len(_cdf):
                                continue
                            _tr = _sim_trade(int(_fi), _open_arr, _high_arr, _low_arr,
                                             _close_arr, _hold_b, _pt_b, _sl_b)
                            if _tr is None:
                                continue          # unresolved — not counted in the card either
                            _xval = _xd.iloc[_ci] if hasattr(_xd, 'iloc') else _xd[_ci]
                            _yval = float(_cdf['Low'].iloc[_ci]) * 0.991
                            _e0, _e1 = _tr['entry_idx'], _tr['exit_idx']
                            _entry_p = _tr['entry']
                            _max_price = float(_np.max(_high_arr[_e0:_e1 + 1]))
                            _min_price = float(_np.min(_low_arr[_e0:_e1 + 1]))
                            _sig_history_rows.append({
                                'date': str(_df_f['Date'].iloc[_fi])[:10] if 'Date' in _df_f.columns else '',
                                'entry_date': str(_df_f['Date'].iloc[_e0])[:10] if 'Date' in _df_f.columns else '',
                                'entry': round(_entry_p, 2),
                                'exit': round(_tr['exit'], 2),
                                'max_price': round(_max_price, 2),
                                'min_price': round(_min_price, 2),
                                'return_pct': round(_tr['ret'] * 100, 2),
                                'max_gain_pct': round((_max_price - _entry_p) / _entry_p * 100, 2),
                                'max_dd_pct': round((_min_price - _entry_p) / _entry_p * 100, 2),
                                'bars_held': _e1 - _e0 + 1,
                                'outcome': _tr['outcome'],
                                'reason': _tr['reason'],
                            })
                            if _tr['outcome'] == 'win':
                                _win_x.append(_xval);  _win_y.append(_yval)
                            else:
                                _loss_x.append(_xval); _loss_y.append(_yval)

                        if _win_x:
                            fig.add_trace(go.Scatter(
                                x=_win_x, y=_win_y, mode='markers',
                                marker=dict(symbol='triangle-up', size=15,
                                            color='#1FA855', opacity=1.0,
                                            line=dict(width=1.5, color='#1FA855')),
                                hovertemplate='<b>Win ✓</b><extra></extra>', name='Win',
                                showlegend=False))
                        if _loss_x:
                            fig.add_trace(go.Scatter(
                                x=_loss_x, y=_loss_y, mode='markers',
                                marker=dict(symbol='triangle-up', size=15,
                                            color='#E0282E', opacity=1.0,
                                            line=dict(width=1.5, color='#E0282E')),
                                hovertemplate='<b>Loss ✗</b><extra></extra>', name='Loss',
                                showlegend=False))

                        # live-signal marker on the bar the signal started
                        _lx  = _xd.iloc[-1] if hasattr(_xd, 'iloc') else _xd[-1]
                        _lhi = float(_cdf['High'].iloc[-1])
                        if _cur_firing:
                            _si_c = max(0, len(_cdf) - 1 - int(_eng_age))
                            _sx   = _xd.iloc[_si_c] if hasattr(_xd, 'iloc') else _xd[_si_c]
                            _slo  = float(_cdf['Low'].iloc[_si_c])
                            fig.add_trace(go.Scatter(
                                x=[_sx], y=[_slo * 0.988],
                                mode='markers+text',
                                marker=dict(symbol='triangle-up', size=16,
                                            color='#A34800', opacity=1.0,
                                            line=dict(width=1, color='#A34800')),
                                text=['SIGNAL'], textposition='bottom center',
                                textfont=dict(size=8, color='#A34800'),
                                hovertemplate=f'SIGNAL — {_eng_date}<extra></extra>', name='',
                                showlegend=False))

                        fig.add_annotation(
                            x=_lx, y=_lhi,
                            text=f'<b>{_today_s}</b>',
                            showarrow=True, arrowhead=0, arrowcolor='#D2D2D7',
                            arrowwidth=1, ax=0, ay=-22,
                            font=dict(size=9, color='#A34800' if _cur_firing else '#5C5C63'),
                            bgcolor='rgba(255,255,255,0.85)', borderpad=3)

                        # levels
                        if _ladder:
                            for _lval, _lc, _ln, _ld in [
                                (_en,   '#0063D1', 'Entry', 'dash'),
                                (_t1,   '#1B7A36', 'T1',    'dot'),
                                (_t2,   '#15704A', 'T2',    'dot'),
                                (_sl_p, '#C1121F', 'Stop',  'dashdot')]:
                                fig.add_hline(
                                    row=1, col=1,
                                    y=_lval, line_color=_lc, line_dash=_ld,
                                    line_width=1.4, opacity=0.9,
                                    annotation_text=f'<b>{_ln}</b> {_lval:.2f}',
                                    annotation_font_color=_lc, annotation_font_size=9,
                                    annotation_bgcolor='rgba(255,255,255,0.85)',
                                    annotation_position='right')

                        # ── proof panel ─────────────────────────────────────
                        # One strip per indicator: coloured on the days its
                        # condition is true (same _build_states the scan used),
                        # then "All agree" (the AND) and the regime filter. A
                        # trade is opened exactly where "All agree" switches
                        # on during a day of this regime — that's what the
                        # triangles on both rows mark.
                        _proof_rows = []
                        try:
                            for _k in _inds:
                                if _k in _states_all:
                                    _ti = _IND_TYPE_OF.get(_k)
                                    _proof_rows.append((_ind_label([_k]),
                                                        _states_all[_k][_offset:].astype(int),
                                                        _IND_TYPES[_ti][1] if _ti is not None else '#3F3F46'))
                            if _inds and all(k in _states_all for k in _inds):
                                _proof_rows.append(('All agree', _combo_arr[_offset:].astype(int), '#111114'))
                            if _reg_arr_chart is not None:
                                _proof_rows.append((f'{_best_rname.title()} regime',
                                                    (_np.asarray(_reg_arr_chart[_offset:]) == _best_rname).astype(int),
                                                    '#8A8A91'))
                            # Drawn as a grey track + coloured squares on the
                            # "true" days (a Heatmap on this category axis
                            # crashes plotly.js in a subplot layout).
                            _xl = list(_xd)
                            for _lb, _z, _cl in _proof_rows:
                                fig.add_trace(go.Scatter(
                                    x=_xl, y=[_lb] * len(_xl), mode='lines',
                                    line=dict(color='#EDEDF1', width=10),
                                    hoverinfo='skip', showlegend=False), row=2, col=1)
                                _on = [_xl[_q] for _q in range(len(_xl)) if _z[_q]]
                                if _on:
                                    fig.add_trace(go.Scatter(
                                        x=_on, y=[_lb] * len(_on), mode='markers',
                                        marker=dict(symbol='square', size=9, color=_cl,
                                                    line=dict(width=0)),
                                        hovertemplate=f'{_lb}: <b>true</b><br>%{{x|%d %b %Y}}<extra></extra>',
                                        showlegend=False), row=2, col=1)
                            # trade entries on the "All agree" strip
                            if _win_x:
                                fig.add_trace(go.Scatter(
                                    x=_win_x, y=['All agree'] * len(_win_x), mode='markers',
                                    marker=dict(symbol='triangle-up', size=11, color='#1FA855',
                                                line=dict(width=1, color='#FFFFFF')),
                                    hovertemplate='Signal → win<extra></extra>', showlegend=False),
                                    row=2, col=1)
                            if _loss_x:
                                fig.add_trace(go.Scatter(
                                    x=_loss_x, y=['All agree'] * len(_loss_x), mode='markers',
                                    marker=dict(symbol='triangle-up', size=11, color='#E0282E',
                                                line=dict(width=1, color='#FFFFFF')),
                                    hovertemplate='Signal → loss<extra></extra>', showlegend=False),
                                    row=2, col=1)
                        except Exception:
                            _proof_rows = []

                        fig.update_layout(
                            xaxis2=dict(type='date', tickformat='%d %b', showgrid=False,
                                        tickfont=dict(size=10, color='#3F3F46'), nticks=10),
                            yaxis2=dict(type='category', autorange='reversed', showgrid=False,
                                        side='left', automargin=True, ticksuffix='  ',
                                        tickfont=dict(size=11, color='#111114')),
                        )
                        fig.update_layout(
                            paper_bgcolor='#FFFFFF', plot_bgcolor='#FFFFFF',
                            margin=dict(l=110 if _proof_rows else 4, r=86, t=32, b=10),
                            height=440 + 30 * len(_proof_rows),
                            font=dict(family='sans-serif'),
                            xaxis=dict(showgrid=True, gridcolor='#DEDEE3', zeroline=False,
                                       rangeslider=dict(visible=False),
                                       type='date', tickformat='%d %b',
                                       tickfont=dict(size=10, color='#5C5C63'), nticks=10),
                            yaxis=dict(showgrid=True, gridcolor='#DEDEE3', zeroline=False,
                                       tickfont=dict(size=10, color='#5C5C63'), side='right'),
                            legend=dict(orientation='h', yanchor='bottom', y=1.01,
                                        xanchor='left', x=0, font=dict(size=9, color='#3F3F46'),
                                        bgcolor='rgba(255,255,255,0)'),
                            showlegend=False,
                            hoverlabel=dict(bgcolor='#F2F2F5', bordercolor='#DEDEE3',
                                             font=dict(size=11, color='#111114', family='monospace')))
                        fig.update_xaxes(showspikes=True, spikecolor='#D2D2D7', spikethickness=1,
                                          spikemode='across', spikedash='dot')
                        fig.update_yaxes(showspikes=True, spikecolor='#D2D2D7', spikethickness=1,
                                          spikemode='across', spikedash='dot')

                        # indicator pills
                        _ind_pills = ''.join(
                            f"<span style='display:inline-flex;align-items:center;gap:0.25rem;"
                            f"padding:0.15rem 0.5rem;border-radius:20px;font-size:0.6rem;"
                            f"font-weight:900;"
                            f"background:{'rgba(52,199,89,0.14)' if _ind_states.get(k) else 'rgba(255,59,48,0.08)'};"
                            f"border:1px solid {'rgba(52,199,89,0.4)' if _ind_states.get(k) else 'rgba(255,59,48,0.22)'};"
                            f"color:{'#1B7A36' if _ind_states.get(k) else '#C1121F'};'>"
                            f"{'●' if _ind_states.get(k) else '○'}&thinsp;{_ind_label([k])}</span>"
                            for k in _inds)

                        _fire_lbl = (
                            f"<span class='lsc-when' style='background:var(--orange-bg);"
                            f"color:var(--orange);'>Signal · {_eng_date or _today_s}</span>"
                            if _cur_firing else
                            f"<span style='color:var(--t3);font-size:0.8rem;'>Last bar {_today_s}</span>")

                        st.markdown(
                            "<div class='lsc-card2' style='margin-top:0.4rem;border-radius:var(--r-lg) var(--r-lg) 0 0;"
                            "border-bottom:none;box-shadow:none;'>"
                            "<div class='lsc-hdr2' style='padding-bottom:0.5rem;'>"
                            f"<span style='font-size:1rem;font-weight:600;color:var(--t1);'>Signal history · {_sym_d}"
                            f"<span style='font-weight:400;color:var(--t2);margin-left:0.4rem;'>{_sname}</span></span>"
                            "<span class='sc-vb sc-vb-ok'>▲ Win</span>"
                            "<span class='sc-vb sc-vb-bad'>▲ Loss</span>"
                            f"<span style='margin-left:auto;'>{_fire_lbl}</span></div>"
                            f"<div class='lsc-strat2' style='padding-bottom:0.6rem;'>{_ind_pills}</div>"
                            "</div>",
                            unsafe_allow_html=True)
                        # theme=None: keep this light chart's own colours (the
                        # Streamlit theme follows the app's dark mode).
                        st.plotly_chart(fig, use_container_width=True, theme=None,
                                        config={'displayModeBar': False,
                                                'modeBarButtonsToRemove': [
                                                    'lasso2d', 'select2d', 'autoScale2d'],
                                                'displaylogo': False,
                                                'scrollZoom': True})

                        # Build Signal History Table HTML
                        _table_html = ""
                        if _sig_history_rows:
                            _sorted_rows = sorted(_sig_history_rows, key=lambda x: x['date'], reverse=True)
                            _tbody_rows = ""
                            for _ridx, _r in enumerate(_sorted_rows):
                                _is_win    = _r['outcome'] == 'win'
                                _out_color = '#1FA855' if _is_win else '#E0282E'
                                _out_rgb   = '47,211,174' if _is_win else '255,95,90'
                                _out_badge = (
                                    f"<span class='sc-vb sc-vb-{'ok' if _is_win else 'bad'}'>"
                                    f"{'Win' if _is_win else 'Loss'}</span>")

                                _ret_color = ('#1FA855' if _r['return_pct'] > 0
                                              else '#E0282E' if _r['return_pct'] < 0 else '#5C5C63')
                                _ret_val = f"{_r['return_pct']:+.2f}%"
                                _max_gain_val = f"{_r['max_gain_pct']:+.2f}%"
                                _max_dd_val   = f"{_r['max_dd_pct']:+.2f}%"

                                _reason_txt = {'target': 'hit target', 'stop': 'hit stop',
                                               'time': 'time exit'}.get(_r.get('reason'), '')
                                _row_tip = (
                                    f"Signal on {_r['date']} (all indicators agreed at that close); "
                                    f"entered next day {_r.get('entry_date', '')} at the open {_r['entry']:.2f}, "
                                    f"exited {_r['exit']:.2f} ({_reason_txt}) after {_r['bars_held']} day(s) — "
                                    f"{_r['outcome'].upper()} ({_ret_val}). "
                                    f"Best case reached {_r['max_price']:.2f} ({_max_gain_val}), "
                                    f"worst case dipped to {_r['min_price']:.2f} ({_max_dd_val})."
                                )
                                _row_bg = '#FFFFFF' if _ridx % 2 == 0 else '#F9F9FB'

                                _tbody_rows += (
                                    f"<tr class='sig-hist-row' title='{_row_tip}' "
                                    f"style='background:{_row_bg};border-bottom:1px solid #DEDEE3;'>"
                                    f"<td style='padding:0.6rem 0.5rem;white-space:nowrap;"
                                    f"color:#3F3F46;font-weight:700;vertical-align:middle;'>{_r['date']}</td>"
                                    f"<td style='padding:0.6rem 0.5rem;vertical-align:middle;'>{_out_badge}</td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:right;font-weight:800;"
                                    f"vertical-align:middle;color:#111114;'>{_r['entry']:.2f}</td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:right;vertical-align:middle;'>"
                                    f"<span style='color:#1FA855;font-weight:700;'>{_r['max_price']:.2f}</span><br/>"
                                    f"<span style='font-size:0.56rem;font-weight:800;color:#1FA855;"
                                    f"background:rgba(47,211,174,0.1);padding:1px 5px;border-radius:8px;'>{_max_gain_val}</span></td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:right;vertical-align:middle;'>"
                                    f"<span style='color:#E0282E;font-weight:700;'>{_r['min_price']:.2f}</span><br/>"
                                    f"<span style='font-size:0.56rem;font-weight:800;color:#E0282E;"
                                    f"background:rgba(255,95,90,0.1);padding:1px 5px;border-radius:8px;'>{_max_dd_val}</span></td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:right;color:#3F3F46;"
                                    f"font-weight:700;vertical-align:middle;'>{_r['exit']:.2f}"
                                    f"<div style='font-size:0.7rem;font-weight:500;color:#5C5C63;'>{_reason_txt}</div></td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:right;vertical-align:middle;'>"
                                    f"<span style='color:{_ret_color};font-weight:900;background:rgba({_out_rgb},0.1);"
                                    f"padding:2px 8px;border-radius:20px;'>{_ret_val}</span></td>"
                                    f"<td style='padding:0.6rem 0.5rem;text-align:center;vertical-align:middle;'>"
                                    f"<span style='color:#3F3F46;font-weight:700;background:#F2F2F5;"
                                    f"border:1px solid #DEDEE3;padding:2px 8px;border-radius:20px;"
                                    f"font-size:0.58rem;'>{_r['bars_held']}d</span></td>"
                                    f"</tr>"
                                )

                            _table_html = (
                                f"<style>"
                                f".sig-hist-scroll::-webkit-scrollbar {{ width: 6px; height: 6px; }}"
                                f".sig-hist-scroll::-webkit-scrollbar-track {{ background: #FFFFFF; }}"
                                f".sig-hist-scroll::-webkit-scrollbar-thumb {{ background: #F2F2F5; border-radius: 6px; }}"
                                f".sig-hist-scroll::-webkit-scrollbar-thumb:hover {{ background: #F2F2F5; }}"
                                f".sig-hist-row {{ transition: background .12s ease; cursor: help; }}"
                                f".sig-hist-row:hover {{ background: #F2F2F5 !important; }}"
                                f"</style>"
                                f"<div style='margin:0 0 0.5rem;background:var(--card);"
                                f"border:1px solid var(--hair);border-top:none;"
                                f"border-radius:0 0 var(--r-lg) var(--r-lg);padding:0.9rem 1rem 1rem;overflow:hidden;'>"
                                f"<div style='display:flex;align-items:baseline;gap:0.5rem;margin-bottom:0.6rem;'>"
                                f"<span style='font-size:1rem;font-weight:600;color:var(--t1);'>Past signals</span>"
                                f"<span style='font-size:0.85rem;color:var(--t2);'>{len(_sorted_rows)}</span>"
                                f"<span style='margin-left:auto;font-size:0.75rem;color:var(--t3);'>"
                                f"Hover a row for details</span>"
                                f"</div>"
                                f"<div class='sig-hist-scroll' style='overflow-x:auto;max-height:280px;overflow-y:auto;"
                                f"border-radius:12px;border:1px solid var(--hair);'>"
                                f"<table style='width:100%;border-collapse:collapse;font-size:0.82rem;"
                                f"color:var(--t1);line-height:1.35;font-variant-numeric:tabular-nums;'>"
                                f"<thead style='position:sticky;top:0;z-index:1;'>"
                                f"<tr style='border-bottom:1px solid var(--hair);color:var(--t2);font-size:0.75rem;"
                                f"text-align:left;background:var(--inset);'>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;'>Date</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;'>Outcome</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:right;'>Entry</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:right;'>Highest</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:right;'>Lowest</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:right;'>Exit</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:right;'>Return</th>"
                                f"<th style='padding:0.55rem 0.6rem;font-weight:500;text-align:center;'>Days</th>"
                                f"</tr>"
                                f"</thead>"
                                f"<tbody>"
                                f"{_tbody_rows}"
                                f"</tbody>"
                                f"</table>"
                                f"</div>"
                                f"</div>"
                            )
                        else:
                            _table_html = (
                                f"<div style='margin:0 0 0.5rem;background:var(--card);"
                                f"border:1px solid var(--hair);border-top:none;"
                                f"border-radius:0 0 var(--r-lg) var(--r-lg);padding:1.1rem;text-align:center;'>"
                                f"<span style='font-size:0.85rem;color:var(--t3);'>"
                                f"No past signals recorded in this regime</span>"
                                f"</div>"
                            )
                        st.markdown(_table_html, unsafe_allow_html=True)
                    except Exception:
                        pass

              st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        # ── expand / collapse button for Section 2 ────────────────────────────
        if len(_fire_rows) > _LSC_PREVIEW:
            _lsc_lbl = (f"Show all {len(_fire_rows)} signals  ↓"
                        if not st.session_state.lsc_show_all else "Show less ↑")
            if st.button(_lsc_lbl, key="lsc_expand", use_container_width=True):
                st.session_state.lsc_show_all = not st.session_state.lsc_show_all
                st.rerun()

        # ── every live signal as one table, downloadable as Excel ─────────────
        # Same rows and order as the cards (all of them, not just the preview),
        # so the table and the file always follow the filters above.
        import html as _html
        import math as _math
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
        from live_signal_export import build_live_signal_xlsx

        def _fin(v):
            return float(v) if v is not None and _math.isfinite(float(v)) else None

        _tbl = []
        for _r in _fire_rows:
            _cb = _live_shown(_r)[0]
            _p = float(_r.get('price', 0) or 0)
            _lv = _lsc_levels(_r['_sym'], _stock_df(_r['_sym']), _p) or {}
            _tbl.append({
                'name': _r.get('_sname') or '', 'symbol': _r['_sym'].replace('.SR', ''),
                'date': f"{_cb['signal_date']} 15:00" if _cb.get('signal_date') else '',
                'price': _fin(_p), 'entry': _fin(_lv.get('entry')), 'stop': _fin(_lv.get('stop')),
                'sl_pct': _fin(_lv.get('sl_pct')), 't1': _fin(_lv.get('t1')),
                't1_pct': _fin(_lv.get('t1_pct')), 't2': _fin(_lv.get('t2')),
                't2_pct': _fin(_lv.get('t2_pct')), 'rr': _fin(_lv.get('rr')),
                'rr_label': _lv.get('rr_label', ''),
                'win_rate': float(_cb.get('win_rate', 0) or 0),
                'trades': int(_cb.get('total', 0) or 0)})

        _now = _dt.now(_tz(_td(hours=3)))                  # Riyadh time
        _filters = (f"Win rate {st.session_state.sc_f_wr} · Trades {st.session_state.sc_f_tr} · "
                    f"Market regime {st.session_state.sc_f_rg}"
                    + (f' · Search "{_sc_query.strip()}"' if _sc_q else ''))
        try:
            _xlsx = build_live_signal_xlsx(
                _tbl, f"LIVE SIGNAL CHECK | {len(_tbl)} Stocks",
                f"Source: Strategy Scanner · Period: {_sc_period_label(_sel_period)} · "
                f"Filters: {_filters} · Highest win rate first · "
                f"Generated {_now:%Y-%m-%d %H:%M} (Riyadh)")
        except ImportError:                                 # xlsxwriter not installed
            _xlsx = None

        _tt, _tb = st.columns([1, 0.2], vertical_alignment="bottom")
        with _tt:
            st.markdown(
                "<div class='lsc-tbl-hd'><span class='lsc-tbl-t'>All live signals</span>"
                f"<span class='lsc-tbl-s'>{len(_tbl)} stocks · same order as the cards · "
                "prices in SAR</span></div>",
                unsafe_allow_html=True)
        with _tb, st.container(key="lsc_xlsx"):
            if _xlsx:
                st.download_button(
                    "Download Excel", data=_xlsx,
                    file_name=f"Live_Signal_Check_{len(_tbl)}_Stocks_with_Win_Rate_"
                              f"{_now:%Y-%m-%d}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    icon=":material/download:", on_click="ignore",
                    use_container_width=True, key="lsc_xlsx_btn")
            else:
                st.caption("Excel export needs the xlsxwriter package.")

        def _px(v):
            return f"{v:,.2f}" if v is not None else '—'

        def _pc(v, sign):
            return f"{sign}{v:.1f}%" if v is not None else '—'

        def _rrt(v):
            return f"1 : {v:.1f}" if v is not None else '—'

        _ths = ("<th class='c'>#</th><th class='l'>Stock</th><th class='c'>Symbol</th>"
                "<th class='c'>Analysis date</th><th>Price</th><th>Entry</th>"
                "<th>Stop loss</th><th>Stop %</th><th>Target 1</th><th>T1 %</th>"
                "<th>Target 2</th><th>T2 %</th><th class='c'>Risk : Reward</th>"
                "<th class='c'>Rating</th><th>Win rate</th><th class='c'>Trades</th>")
        _trs = ''.join(
            "<tr>"
            f"<td class='rk{' top' if _i <= 3 else ''}'>{_i}</td>"
            f"<td class='l nm' title='{_html.escape(_t['name'], quote=True)}'>"
            f"{_html.escape(_t['name'])}</td>"
            f"<td class='c sym'>{_t['symbol']}</td>"
            f"<td class='c muted'>{_t['date'] or '—'}</td>"
            f"<td>{_px(_t['price'])}</td><td>{_px(_t['entry'])}</td><td>{_px(_t['stop'])}</td>"
            f"<td class='dn'>{_pc(_t['sl_pct'], '−')}</td>"
            f"<td>{_px(_t['t1'])}</td><td class='up'>{_pc(_t['t1_pct'], '+')}</td>"
            f"<td>{_px(_t['t2'])}</td><td class='up'>{_pc(_t['t2_pct'], '+')}</td>"
            f"<td class='c'>{_rrt(_t['rr'])}</td>"
            f"<td class='c' style='color:{_RR_COL.get(_t['rr_label'], 'var(--t3)')};"
            f"font-weight:600;'>{_t['rr_label'] or '—'}</td>"
            f"<td class='wr' style='color:{_wr_col(_t['win_rate'])};'>{_t['win_rate']:.0f}%</td>"
            + (f"<td class='c few' title='Fewer than 10 trades: weak evidence'>{_t['trades']}</td>"
               if _t['trades'] < 10 else f"<td class='c'>{_t['trades']}</td>")
            + "</tr>"
            for _i, _t in enumerate(_tbl, 1))
        st.markdown(
            f"<div class='lsc-tbl-wrap'><table class='lsc-tbl'><thead><tr>{_ths}</tr></thead>"
            f"<tbody>{_trs}</tbody></table></div>",
            unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Scanned Strategy Grid
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        "<div class='sc-h2'><span class='sc-h2-t'>Scanned Strategies</span>"
        "<span class='sc-h2-s'>Up to 3 strategies per market regime for each stock · "
        "highest win rate first, judged on today's regime (the first row of each card)</span>"
        f"<span class='sc-h2-c'>{len(_rows)} stocks</span></div>"
        "<div class='sc-summary'>"
        f"<span class='sc-chip'><b>{len(_all_combos):,}</b> strategies</span>"
        f"<span class='sc-chip'><span class='sc-vb sc-vb-ok' style='padding:0 0.45rem;'>"
        f"{_n_val}</span> validated</span>"
        f"<span class='sc-chip'><span class='sc-vb sc-vb-warn' style='padding:0 0.45rem;'>"
        f"{len(_all_combos) - _n_val - _n_fail}</span> not validated</span>"
        f"<span class='sc-chip'><span class='sc-vb sc-vb-bad' style='padding:0 0.45rem;'>"
        f"{_n_fail}</span> failed test</span>"
        + (f"<span class='sc-chip'><b>{_rejected}</b> stocks without a profitable strategy</span>"
           if _rejected else '')
        + "</div>",
        unsafe_allow_html=True)

    _PREVIEW_COUNT = 6                 # three rows of two cards
    _show_all_key  = 'sc_show_all_strats'
    if _show_all_key not in st.session_state:
        st.session_state[_show_all_key] = False

    # A Live Signal Check card's "View strategy" asks for one stock: show the
    # list down to its card (it may sit past the preview), highlight the
    # strategy that signalled, and scroll there once.
    _focus = st.session_state.get('sc_focus')
    _focus_idx = next((i for i, r in enumerate(_rows)
                       if r['_sym'].replace('.SR', '') == _focus), None)
    _rows_to_show = (_rows if st.session_state[_show_all_key]
                     else _rows[:max(_PREVIEW_COUNT, (_focus_idx or 0) + 1)])

    st.markdown(_IND_LEGEND, unsafe_allow_html=True)

    # One card per stock, two side by side: a block per market regime (today's
    # first), alternatives folded under their regime's block. Cards come sorted
    # with every stock that has a strategy for today's regime first; a divider
    # separates the rest.
    _cards_today, _cards_other = [], []
    for _pos, _row in enumerate(_rows_to_show, 1):
        _sym_d = _row['_sym'].replace('.SR', '')
        _sname = _row['_sname']
        _cur_reg = _row.get('current_regime')
        _lists = {_rn: _strats(_row, _rn)
                  for _rn in sorted(_REGIMES, key=lambda _rn: _rn != _cur_reg)}
        _present = [_rn for _rn, _l in _lists.items() if _l]
        _live_now = _live_shown(_row)
        _has_fire = bool(_live_now)
        _is_focus = _sym_d == _focus
        _focus_cb = _live_now[0] if (_is_focus and _live_now) else None

        _body = ''
        for _rname in _present:
            _main, *_alts = _lists[_rname]
            _body += _strat_row(_main, _rname, is_now=(_rname == _cur_reg),
                                focus=_main is _focus_cb)
            if _alts:
                _body += (
                    f"<details class='sc-more'{' open' if any(_a is _focus_cb for _a in _alts) else ''}>"
                    "<summary title='Other indicator sets for "
                    "this regime, highest win rate first. None is a subset or superset of "
                    "another, and any two share under 60% of their trades (fitted part).'>"
                    f"{len(_alts)} more {'strategy' if len(_alts) == 1 else 'strategies'} "
                    f"for {_rname.title()}</summary>"
                    + ''.join(_strat_row(_a, _rname, alt=True, focus=_a is _focus_cb)
                              for _a in _alts)
                    + "</details>")

        (_cards_today if _lists.get(_cur_reg) else _cards_other).append(
            f"<div class='sc-stock sc-card-{_sym_d}{' sc-focus' if _is_focus else ''}'>"
            "<div class='sc-stock-hdr'>"
            f"<span class='sc-rank{' sc-rank-top' if _pos <= 3 else ''}' "
            f"title='Rank: highest win rate first'>{_pos}</span>"
            f"<span class='sc-sym'>{_sym_d}</span>"
            + (f"<span class='sc-sname'>{_sname}</span>" if _sname else '')
            + ("<span class='sc-cfire' style='margin-left:auto;'>Live signal</span>"
               if _has_fire else
               f"<span class='sc-ct'>{len(_present)} of 3 regimes</span>")
            + "</div>"
            + "<div class='sc-table'>" + _body + "</div>"
            + "</div>")

    if _cards_today:
        st.markdown(f"<div class='sc-grid'>{''.join(_cards_today)}</div>",
                    unsafe_allow_html=True)
    if _cards_other:
        st.markdown(
            "<div class='sc-grp'><b>No strategy for today's market regime"
            + (" matches the filter" if _f_on else "") + "</b> — "
            "the stocks below only have strategies for other regimes, ranked by "
            "their best win rate.</div>",
            unsafe_allow_html=True)
        st.markdown(f"<div class='sc-grid'>{''.join(_cards_other)}</div>",
                    unsafe_allow_html=True)

    # Scroll to the requested card once per "View strategy" tap. The script
    # runs in a tiny iframe and reaches the page it sits in.
    _nonce = st.session_state.get('sc_focus_nonce')
    if _focus_idx is not None and _nonce != st.session_state.get('sc_focus_done'):
        st.session_state.sc_focus_done = _nonce
        import streamlit.components.v1 as _components
        _js = ("<script>(function go(n) {"
               " const d = window.parent.document;"
               " const el = d.querySelector('.sc-card-SYM .sc-tr-focus')"
               " || d.querySelector('.sc-card-SYM');"
               " if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});"
               " else if (n < 50) setTimeout(function () { go(n + 1); }, 100);"
               "})(0);</script>").replace('SYM', _focus)
        _components.html(f"{_js}<!-- {_nonce} -->", height=0)

    # ── expand / collapse button for Section 1 ────────────────────────────
    if len(_rows) > _PREVIEW_COUNT:
        _remaining = len(_rows) - _PREVIEW_COUNT
        _btn_label = (
            f"Show all {len(_rows)} stocks  ↓"
            if not st.session_state[_show_all_key]
            else "Show less ↑"
        )
        st.markdown(
            "<style>"
            ".st-key-sc_expand_strats .stButton button{"
            "color:var(--blue)!important;font-size:0.9rem!important;font-weight:600!important;"
            "padding:0.5rem 1.2rem!important;margin:0.8rem 0 0.5rem!important;}"
            "</style>",
            unsafe_allow_html=True)
        if st.button(_btn_label, key="sc_expand_strats"):
            st.session_state[_show_all_key] = not st.session_state[_show_all_key]
            st.session_state.sc_focus = None      # "Show less" really shows less
            st.rerun()
