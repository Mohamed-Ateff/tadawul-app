"""
scanner_engine.py  —  fast, realistic, up-to-5 indicators
"""
from __future__ import annotations
import streamlit as st
import numpy as np
import pandas as pd
import itertools
import math
import time

# (scoring_window_bars, hold, profit_target, stop_loss)
#
# `scoring_window_bars` is how many of the most recent bars signals are SCORED
# on. Every preset now also downloads _WARMUP_BARS of extra history in front of
# that window — the same treatment 'Days:N' always had — for two reasons:
#
#   1. Indicators need history before they mean anything. The old 'Short'
#      preset fetched 3mo (~63 bars) and scored from bar 0, which left 10 of
#      the 50 indicators mathematically unable to ever turn bullish (SMA
#      50/200, Ichimoku, CCI 20, Fib, New Hi/Lo, Dist. MA, RS vs TASI, RS vs
#      Sector, Squeeze, VWAP Bands) while most of the rest were still warming
#      up through the window they were being scored on.
#   2. The out-of-sample split in _analyse_df has to cut the scoring window in
#      two and still leave real trades in the test half. A 60-day hold cannot
#      be validated on 63 bars, so Long needs years of scoring window, not one.
#
# Windows are sized so the test half holds a usable number of trades at that
# preset's hold time: Short 180 bars / 5-day hold, Medium 375 / 20, Long 750 / 60.
_PERIOD_CFG = {
    'Short':  (180,  5, 0.03, 0.015),
    'Medium': (375, 20, 0.05, 0.030),
    'Long':   (750, 60, 0.08, 0.050),
}

# ── out-of-sample validation ─────────────────────────────────────────────────
# Fraction of the scoring window used to SEARCH for a strategy. The remainder is
# held back and never touched during the search, then used once to check whether
# the chosen strategy actually works on bars it was not fitted to.
_TRAIN_FRAC      = 0.70
# Minimum resolved trades required in the held-back half for a result to count.
#
# This floor has to be high, and the reason is subtle. A strategy is only shown
# if it stayed profitable on the held-back half, which is a filter applied to
# the test data — so the surviving win rates are biased upward no matter what.
# The size of that bias is set by this number. At 3 trades the filter is
# devastating: "profitable" needs roughly 2 of 3 wins, so every single survivor
# mechanically displays >=67%. Measured on random-walk input with the floor at
# 3, the held-back mean came out at 88.6% — HIGHER than the 57.3% fitted mean it
# was supposed to be a reality check on, which is the opposite of the point.
#
# At 10+ trades "profitable" only needs to beat the ~38% breakeven implied by
# +8%/-5% exits, so survivors span a wide, informative range instead of all
# looking perfect. Far fewer strategies clear it. That is the correct outcome.
_OOS_MIN_TRADES  = 10
# Below this many held-back trades the out-of-sample number is weak evidence.
_OOS_LOW_SAMPLE  = 15
# A scoring window shorter than this cannot be split into two halves that each
# hold enough trades to mean anything, so no strategy can be validated at all.
_MIN_SPLIT_SPAN  = 150
# Strategies shortlisted per regime (winner + runner-ups). Each one is tested
# once on the held-back half; only those that pass are shown.
_TOP_PER_REGIME  = 3

_REGIME_COLORS = {'TREND': '#26A69A', 'RANGE': '#4A9EFF', 'VOLATILE': '#FF6B6B'}
_REGIME_ICONS  = {'TREND': '↗',       'RANGE': '↔',       'VOLATILE': '⚡'}

# ── custom "last N trading days" periods ─────────────────────────────────────
# Period keys may be a preset name ('Short'/'Medium'/'Long') or 'Days:N' for a
# user-entered window of N trading days.
#
# N bounds the bars we SCORE SIGNALS ON, not the bars we download. Indicators
# like SMA 200 and Ichimoku need hundreds of bars before they mean anything, so
# fetching only N bars would leave them permanently flat and every "strategy"
# built on them would be an artifact. We therefore pull N + _WARMUP_BARS of
# history, let every indicator warm up on the earlier bars, then only count
# signals that fired inside the final N.
_WARMUP_BARS   = 260          # ~1 trading year of warm-up
_DAYS_MIN      = 20
_DAYS_MAX      = 2000
# Tadawul trades Sun-Thu (5 sessions/week), so N trading days spans about
# N * 7/5 calendar days; pad for public holidays.
_CAL_PER_BAR   = 1.55

DAYS_PREFIX = 'Days:'


def parse_days(period_key: str) -> int | None:
    """Return N for a 'Days:N' period key, else None."""
    if isinstance(period_key, str) and period_key.startswith(DAYS_PREFIX):
        try:
            return max(_DAYS_MIN, min(_DAYS_MAX, int(period_key[len(DAYS_PREFIX):])))
        except ValueError:
            return None
    return None


def _yf_period_for(total_bars: int) -> str:
    """Smallest yfinance period string covering `total_bars` trading days."""
    cal_days = int(total_bars * _CAL_PER_BAR) + 10
    for limit, label in ((30, '1mo'), (90, '3mo'), (180, '6mo'), (365, '1y'),
                         (730, '2y'), (1825, '5y'), (3650, '10y')):
        if cal_days <= limit:
            return label
    return 'max'


def resolve_period(period_key: str):
    """(yf_period, interval, hold, pt, sl, window) for a preset or 'Days:N' key.

    `window` is the number of most-recent bars that signals are scored on.
    Presets and 'Days:N' are handled identically now: both download
    window + _WARMUP_BARS of history and score only the final `window` bars,
    so indicators are always fully warmed up before any signal counts.
    """
    n = parse_days(period_key)
    if n is None:
        window, hold, pt, sl = _PERIOD_CFG.get(period_key, _PERIOD_CFG['Medium'])
        return (_yf_period_for(window + _WARMUP_BARS), '1d', hold, pt, sl, window)
    # Exit rules scale with the window: a 30-day scan shouldn't be judged on a
    # 60-day hold it has no room to resolve.
    if n <= 90:
        hold, pt, sl = _PERIOD_CFG['Short'][1:]
    elif n <= 250:
        hold, pt, sl = _PERIOD_CFG['Medium'][1:]
    else:
        hold, pt, sl = _PERIOD_CFG['Long'][1:]
    return (_yf_period_for(n + _WARMUP_BARS), '1d', hold, pt, sl, n)

_IND_LABEL = {
    # Trend
    'SMA': 'SMA 50/200', 'EMA': 'EMA 20/50', 'WMA': 'WMA 20',
    'PSAR': 'Par.SAR', 'ICHI': 'Ichimoku', 'MACD': 'MACD',
    'SUPER': 'SuperTrend', 'HULL': 'Hull MA',
    # Momentum
    'RSI': 'RSI 14', 'STOCH': 'Stochastic', 'ROC': 'ROC 12',
    'CCI': 'CCI 20', 'WILLR': 'Wm.%R', 'MOM': 'Momentum',
    'TSI': 'TSI', 'PPO': 'PPO', 'ELDER': 'Elder Ray',
    # Volume
    'OBV': 'OBV', 'MFI': 'MFI 14', 'CMF': 'CMF', 'VWAP': 'VWAP',
    'ADLINE': 'A/D Line', 'VOLMA': 'Vol MA', 'FORCE': 'Force Idx',
    'VOLRSI': 'Vol RSI',
    # Volatility
    'BB': 'Bol.Bands', 'ATR': 'ATR', 'KELT': 'Keltner',
    'DONCH': 'Donchian', 'SQZ': 'Squeeze', 'HV': 'Hist.Vol %',
    'STDEV': 'Std.Dev', 'CHAND': 'Chandelier',
    # Support & Resistance
    'PIVOT': 'Pivot Pts', 'FIB': 'Fib Levels', 'ADX': 'ADX',
    'VWAPB': 'VWAP Bands', 'PREVHL': 'Prev Hi/Lo', 'SWINGHL': 'Swing Hi/Lo',
    # Mean Reversion
    'RSIEXT': 'RSI Ext.', 'BBZ': 'BB Z-Score', 'DISTMA': 'Dist. MA',
    'STOCHEXT': 'Stoch Ext.', 'CCIEXT': 'CCI Ext.',
    # Single-stock trend/position measures.
    #
    # These six were labelled 'TASI Filter', 'Sector Filter', 'RS vs TASI',
    # 'RS vs Sector', 'Adv/Decline' and 'New Hi/Lo' — names that describe index,
    # sector and market-breadth data. None of that data is involved: every one
    # of them is computed from the single stock's own price series (see the
    # MARKET REGIME block in _build_states). A strategy card reading
    # "TASI Filter + RSI 14" told the user the market index had confirmed the
    # setup when nothing outside the stock had been consulted at all.
    #
    # Renamed to state exactly what each one tests. The maths is unchanged, so
    # results are identical — only the claim on screen is now true.
    'TASIF': 'Above MA50', 'SECTORF': '20d Return +',
    'RSTASI': '60d Return +', 'RSSECTOR': '20d Ret > Avg',
    'ADVDEC': 'Up-days 6/10', 'NEWHL': 'Near 60d High',
}


def _ind_labels(keys: list[str]) -> str:
    return ' + '.join(_IND_LABEL.get(k, k) for k in keys)


# ── build indicator state arrays ─────────────────────────────────────────────

def _col(df: pd.DataFrame | None, prefix: str) -> pd.Series | None:
    """First column whose name starts with `prefix` (pandas_ta output).

    Indicators are read by column NAME, never by position: pandas_ta's column
    order differs between versions (e.g. ADX is [ADX, ADXR, DMP, DMN] in
    0.4.x but [ADX, DMP, DMN] in 0.3.x), and positional reads silently tested
    the wrong lines."""
    if df is None:
        return None
    for name in df.columns:
        if str(name).startswith(prefix):
            return df[name]
    return None


def _cci(hi: pd.Series, lo: pd.Series, c: pd.Series, n: int = 20) -> pd.Series:
    """Commodity Channel Index, standard definition:
    (TP − SMA_n(TP)) / (0.015 × mean absolute deviation of TP over n).

    Computed here instead of ta.cci because pandas_ta 0.4.71b0 has an
    operator-precedence bug (tp - sma / (c*mad)) that made CCI almost never
    positive and CCI Ext. almost always true."""
    from numpy.lib.stride_tricks import sliding_window_view
    tp = ((hi + lo + c) / 3).astype(float)
    sma = tp.rolling(n).mean()
    vals = tp.values
    mad = np.full(len(vals), np.nan)
    if len(vals) >= n:
        win = sliding_window_view(vals, n)
        mad[n - 1:] = np.abs(win - win.mean(axis=1, keepdims=True)).mean(axis=1)
    mad_s = pd.Series(mad, index=tp.index).replace(0, np.nan)
    return (tp - sma) / (0.015 * mad_s)


def _build_states(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Build binary bullish-state arrays for every supported indicator.
    Each state is 1 when that indicator is currently bullish, 0 otherwise."""
    import pandas_ta as ta

    def safe(arr) -> np.ndarray:
        a = np.asarray(arr, dtype=float)
        return np.where(np.isnan(a), 0, a).astype(np.int8)

    c  = df['Close'].astype(float)
    hi = df['High'].astype(float)
    lo = df['Low'].astype(float)
    vo = df['Volume'].astype(float)
    cv = c.values
    hv = hi.values
    lv = lo.values
    vv = vo.values
    n  = len(df)
    s  = {}

    # ── TREND ───────────────────────────────────────────────────────────
    try:
        s50  = c.rolling(50).mean(); s200 = c.rolling(200).mean()
        s['SMA'] = safe(s50 > s200)
    except Exception: pass
    try:
        e20 = ta.ema(c, 20); e50 = ta.ema(c, 50)
        if e20 is not None and e50 is not None:
            s['EMA'] = safe(e20 > e50)
    except Exception: pass
    try:
        wma20 = ta.wma(c, 20)
        if wma20 is not None:
            s['WMA'] = safe(cv > wma20.values)
    except Exception: pass
    try:
        psar = ta.psar(hi, lo, c)
        if psar is not None:
            # bullish when long stop active (PSARl column non-NaN)
            long_col = [col for col in psar.columns if 'PSARl' in col]
            if long_col:
                s['PSAR'] = safe(~psar[long_col[0]].isna())
    except Exception: pass
    try:
        # Tenkan-sen (9) above Kijun-sen (26). Columns are picked BY NAME: the
        # old code matched ITS-or-ISA and took the first hit, which in
        # pandas_ta's column order [ISA, ISB, ITS, IKS, ICS] compared the two
        # cloud spans instead.
        ich = ta.ichimoku(hi, lo, c)
        if ich is not None and isinstance(ich, tuple) and len(ich) >= 1:
            ich_df = ich[0]
            tk, kj = _col(ich_df, 'ITS_'), _col(ich_df, 'IKS_')
            if tk is not None and kj is not None:
                s['ICHI'] = safe(tk > kj)
    except Exception: pass
    try:
        # MACD line above its signal line (by name: the columns are
        # [MACD, MACDh, MACDs], so position 1 is the histogram, not the signal).
        m = ta.macd(c)
        if m is not None:
            ml, ms = _col(m, 'MACD_'), _col(m, 'MACDs_')
            if ml is not None and ms is not None:
                s['MACD'] = safe(ml > ms)
    except Exception: pass
    try:
        st_ = ta.supertrend(hi, lo, c)
        if st_ is not None:
            dir_col = [col for col in st_.columns if 'SUPERTd' in col]
            if dir_col:
                s['SUPER'] = safe(st_[dir_col[0]] > 0)
    except Exception: pass
    try:
        hull = ta.hma(c, 16)
        if hull is not None:
            s['HULL'] = safe(cv > hull.values)
    except Exception: pass

    # ── MOMENTUM ────────────────────────────────────────────────────────
    try:
        rsi = ta.rsi(c, 14)
        if rsi is not None:
            s['RSI'] = safe((rsi > 50) & (rsi < 75))
    except Exception: pass
    try:
        st2 = ta.stoch(hi, lo, c)
        if st2 is not None:
            s['STOCH'] = safe((st2.iloc[:, 0] > 40) & (st2.iloc[:, 0] < 80))
    except Exception: pass
    try:
        roc = ta.roc(c, 12)
        if roc is not None:
            s['ROC'] = safe(roc > 0)
    except Exception: pass
    try:
        cci = _cci(hi, lo, c, 20)
        s['CCI'] = safe((cci > 0) & (cci < 150))
    except Exception: pass
    try:
        wr = ta.willr(hi, lo, c, 14)
        if wr is not None:
            s['WILLR'] = safe((wr > -50) & (wr < -20))
    except Exception: pass
    try:
        mom = ta.mom(c, 10)
        if mom is not None:
            s['MOM'] = safe(mom > 0)
    except Exception: pass
    try:
        tsi = ta.tsi(c)
        if tsi is not None:
            tsi_col = tsi.iloc[:, 0] if hasattr(tsi, 'iloc') else tsi
            s['TSI'] = safe(tsi_col > 0)
    except Exception: pass
    try:
        # PPO line above its signal line (by name: [PPO, PPOh, PPOs]).
        ppo = ta.ppo(c)
        if ppo is not None:
            pl, ps = _col(ppo, 'PPO_'), _col(ppo, 'PPOs_')
            if pl is not None and ps is not None:
                s['PPO'] = safe(pl > ps)
    except Exception: pass
    try:
        # Elder Ray bull power: high - EMA13 > 0
        e13 = ta.ema(c, 13)
        if e13 is not None:
            s['ELDER'] = safe(hv > e13.values)
    except Exception: pass

    # ── VOLUME ──────────────────────────────────────────────────────────
    try:
        obv = ta.obv(c, vo)
        if obv is not None:
            ov = obv.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = ((ov[5:] > ov[:-5]) & (cv[5:] > cv[:-5])).astype(np.int8)
            s['OBV'] = rise
    except Exception: pass
    try:
        mfi = ta.mfi(hi, lo, c, vo, 14)
        if mfi is not None:
            s['MFI'] = safe((mfi > 50) & (mfi < 80))
    except Exception: pass
    try:
        # CMF computed manually (pandas_ta.cmf signature unreliable across versions)
        rng = (hi - lo).replace(0, np.nan)
        mfm = ((c - lo) - (hi - c)) / rng
        mfv = mfm * vo
        cmf_ = mfv.rolling(20).sum() / vo.rolling(20).sum()
        s['CMF'] = safe(cmf_ > 0)
    except Exception: pass
    try:
        tp   = (hi + lo + c) / 3
        vwap = (tp * vo).rolling(20).sum() / vo.rolling(20).sum()
        s['VWAP'] = safe(cv > vwap.values)
    except Exception: pass
    try:
        ad = ta.ad(hi, lo, c, vo)
        if ad is not None:
            adv = ad.values
            rise = np.zeros(n, dtype=np.int8)
            rise[5:] = (adv[5:] > adv[:-5]).astype(np.int8)
            s['ADLINE'] = rise
    except Exception: pass
    try:
        vol_ma = vo.rolling(20).mean()
        s['VOLMA'] = safe(vv > vol_ma.values)
    except Exception: pass
    try:
        # Force Index: close-diff * volume, then EMA13
        fi = (c.diff() * vo).ewm(span=13, adjust=False).mean()
        s['FORCE'] = safe(fi > 0)
    except Exception: pass
    try:
        vol_chg = vo.pct_change().fillna(0)
        vol_rsi = ta.rsi(vol_chg.add(1.0), 14)
        if vol_rsi is not None:
            s['VOLRSI'] = safe(vol_rsi > 50)
    except Exception: pass

    # ── VOLATILITY ──────────────────────────────────────────────────────
    try:
        bb = ta.bbands(c, 20)
        if bb is not None and bb.shape[1] >= 3:
            s['BB'] = safe(cv >= bb.iloc[:, 1].values)
    except Exception: pass
    try:
        atr = ta.atr(hi, lo, c, 14)
        if atr is not None:
            atrp = (atr / c).fillna(0)
            atr_ma = atrp.rolling(20).mean()
            s['ATR'] = safe(atrp > atr_ma)
    except Exception: pass
    try:
        kc = ta.kc(hi, lo, c, 20)
        if kc is not None and kc.shape[1] >= 3:
            s['KELT'] = safe(cv > kc.iloc[:, 1].values)
    except Exception: pass
    try:
        dc_hi = hi.rolling(20).max()
        s['DONCH'] = safe(cv >= dc_hi.values * 0.98)
    except Exception: pass
    try:
        # Squeeze: Bollinger Bands inside the Keltner Channel = volatility
        # compressed. Bullish when a squeeze was on during any of the previous
        # 5 sessions and price now closes above the 20-day middle (the
        # breakout leg). The old code only tested close > upper Keltner and
        # never looked at the squeeze at all.
        bb2 = ta.bbands(c, 20); kc2 = ta.kc(hi, lo, c, 20)
        if bb2 is not None and kc2 is not None:
            bbl, bbu, bbm = _col(bb2, 'BBL_'), _col(bb2, 'BBU_'), _col(bb2, 'BBM_')
            kcl, kcu = _col(kc2, 'KCL'), _col(kc2, 'KCU')
            if all(x is not None for x in (bbl, bbu, bbm, kcl, kcu)):
                sq_on = ((bbl > kcl) & (bbu < kcu)).astype(float)
                recent_sq = sq_on.shift(1).rolling(5).max() > 0
                s['SQZ'] = safe(recent_sq & (c > bbm))
    except Exception: pass
    try:
        ret = c.pct_change()
        hv_ = ret.rolling(20).std() * (252 ** 0.5) * 100
        hv_ma = hv_.rolling(20).mean()
        s['HV'] = safe(hv_ > hv_ma)
    except Exception: pass
    try:
        sd = c.rolling(20).std()
        sd_ma = sd.rolling(20).mean()
        s['STDEV'] = safe(sd > sd_ma)
    except Exception: pass
    try:
        # Chandelier exit (long): highest_high(22) - 3 * ATR(22)
        atr22 = ta.atr(hi, lo, c, 22)
        if atr22 is not None:
            chand = hi.rolling(22).max() - 3 * atr22
            s['CHAND'] = safe(cv > chand.values)
    except Exception: pass

    # ── SUPPORT & RESISTANCE ────────────────────────────────────────────
    try:
        # Pivot points: bullish above PP = (H+L+C)/3 of prior bar
        pp = ((hi + lo + c) / 3).shift(1)
        s['PIVOT'] = safe(cv > pp.values)
    except Exception: pass
    try:
        # Fib: 61.8% retracement of 60-bar range
        hh60 = hi.rolling(60).max(); ll60 = lo.rolling(60).min()
        fib_618 = ll60 + 0.618 * (hh60 - ll60)
        s['FIB'] = safe(cv > fib_618.values)
    except Exception: pass
    try:
        # +DI above -DI with ADX > 20 (by name: this pandas_ta returns
        # [ADX, ADXR, DMP, DMN], so position 1 was ADXR, not +DI).
        adx = ta.adx(hi, lo, c)
        if adx is not None:
            a, dp, dn = _col(adx, 'ADX_'), _col(adx, 'DMP_'), _col(adx, 'DMN_')
            if all(x is not None for x in (a, dp, dn)):
                s['ADX'] = safe((dp > dn) & (a > 20))
    except Exception: pass
    try:
        tp2 = (hi + lo + c) / 3
        vwap_b = (tp2 * vo).rolling(20).sum() / vo.rolling(20).sum()
        vwap_std = (tp2 - vwap_b).rolling(20).std()
        vwap_upper = vwap_b + vwap_std
        s['VWAPB'] = safe(cv > vwap_upper.values)
    except Exception: pass
    try:
        prev_high = hi.shift(1).rolling(20).max()
        s['PREVHL'] = safe(cv > prev_high.values)
    except Exception: pass
    try:
        # Swing high: most recent local-max-high of 10 bars
        swing = hi.rolling(10).max().shift(1)
        s['SWINGHL'] = safe(cv > swing.values)
    except Exception: pass

    # ── MEAN REVERSION ──────────────────────────────────────────────────
    try:
        rsi2 = ta.rsi(c, 14)
        if rsi2 is not None:
            s['RSIEXT'] = safe(rsi2 < 35)
    except Exception: pass
    try:
        bb3 = ta.bbands(c, 20)
        if bb3 is not None and bb3.shape[1] >= 3:
            mid = bb3.iloc[:, 1]; std = (bb3.iloc[:, 2] - bb3.iloc[:, 1]) / 2.0
            z = (c - mid) / std
            s['BBZ'] = safe(z < -1.5)
    except Exception: pass
    try:
        ma50 = c.rolling(50).mean()
        dist = (c - ma50) / ma50
        s['DISTMA'] = safe(dist < -0.05)
    except Exception: pass
    try:
        st3 = ta.stoch(hi, lo, c)
        if st3 is not None:
            s['STOCHEXT'] = safe(st3.iloc[:, 0] < 20)
    except Exception: pass
    try:
        s['CCIEXT'] = safe(_cci(hi, lo, c, 20) < -100)
    except Exception: pass

    # ── SINGLE-STOCK TREND / POSITION ────────────────────────────────────
    # These six are computed ENTIRELY from this stock's own price series. No
    # index, sector or market-breadth data is fetched anywhere in this module.
    # They were previously labelled as if they were (TASI Filter, RS vs TASI,
    # Adv/Decline, ...); see _IND_LABEL for why that was corrected. Keep the
    # names here honest if these are ever changed.
    try:
        # Stock above its own 50-day MA
        ma50f = c.rolling(50).mean()
        s['TASIF'] = safe(cv > ma50f.values)
    except Exception: pass
    try:
        # 20-day return positive
        ret20 = c.pct_change(20)
        s['SECTORF'] = safe(ret20 > 0)
    except Exception: pass
    try:
        # 60-day return positive
        ret60 = c.pct_change(60)
        s['RSTASI'] = safe(ret60 > 0)
    except Exception: pass
    try:
        # 20d return > its own 60-day average
        ret20b = c.pct_change(20)
        ret20_ma = ret20b.rolling(60).mean()
        s['RSSECTOR'] = safe(ret20b > ret20_ma)
    except Exception: pass
    try:
        # More than 6 up-days in the last 10 (this stock's own up-days)
        up = (c.diff() > 0).astype(int)
        adv = up.rolling(10).sum()
        s['ADVDEC'] = safe(adv > 5)
    except Exception: pass
    try:
        # Within 3% of this stock's own 60-day high
        hh = hi.rolling(60).max()
        s['NEWHL'] = safe(cv >= hh.values * 0.97)
    except Exception: pass

    return s


# ── regime per bar ────────────────────────────────────────────────────────────

def _regime_arr(df: pd.DataFrame) -> np.ndarray:
    """
    Per-bar regime classifier using CAUSAL (expanding-window) cutoffs.

    Each bar's TREND/VOLATILE threshold is computed ONLY from bars up to and
    including that bar — never from future bars. An earlier version used a
    single quantile cutoff computed from the ENTIRE series (including bars
    far in the future relative to the bar being classified), which leaked
    future trend/volatility distribution into today's regime label — a real
    lookahead-bias bug that inflated per-regime backtest stats. Expanding
    quantiles fix that: at each bar, only what was knowable "as of that day"
    is used.

    Trade-off: since we can no longer force a fixed 30/30/40 split using
    future knowledge, some stocks will legitimately have a sparse or empty
    TREND/VOLATILE bucket — that's an honest result, not a bug. The
    downstream `min_signals` gate already handles sparse regimes by
    returning no combo rather than fabricating one.
    """
    n = len(df)
    if n < 30:
        return np.array(['RANGE'] * n, dtype=object)
    try:
        import pandas_ta as ta
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        atr = ta.atr(df['High'], df['Low'], df['Close'], 14)
        if adx is None or atr is None:
            return np.array(['RANGE'] * n, dtype=object)
        av   = adx.iloc[:, 0].fillna(0).values.astype(float)
        atrp = (atr / df['Close']).fillna(0).values.astype(float)

        # Skip warm-up bars — cutoffs need some history before they're stable
        warm = max(20, n // 5)

        # 70th percentile of ADX → TREND cutoff, 65th percentile of ATR/close
        # → VOLATILE cutoff, computed as an EXPANDING window (causal: bar i's
        # cutoff only ever sees bars <= i).
        adx_cut_s = pd.Series(av).expanding(min_periods=warm).quantile(0.70)
        atr_cut_s = pd.Series(atrp).expanding(min_periods=warm).quantile(0.65)

        # Light absolute clamps: never call total noise "TREND", never call
        # a calm stock "VOLATILE" just because its top-decile ATR is tiny.
        adx_cut = adx_cut_s.clip(lower=15.0, upper=35.0).values
        atr_cut = atr_cut_s.clip(lower=0.008, upper=0.05).values

        valid = np.arange(n) >= warm
        out = np.full(n, 'RANGE', dtype=object)
        is_trend = valid & (av > adx_cut)
        is_vol   = valid & (atrp > atr_cut) & (~is_trend)
        out[is_trend] = 'TREND'
        out[is_vol]   = 'VOLATILE'
        return out
    except Exception:
        pass
    return np.array(['RANGE'] * n, dtype=object)


# ── one simulated trade (shared by the backtest and the page's chart) ────────

def simulate_trade(i: int, open_arr, high_arr, low_arr, close,
                   hold: int, pt: float, sl: float) -> dict | None:
    """The single trade model every displayed statistic is measured with.

    Signal on bar i → enter at the OPEN of bar i+1. On each of the next `hold`
    bars (the entry bar is day 1) the stop is checked against that day's LOW,
    then the target against its HIGH; if both are crossed the same day the stop
    is assumed first (daily bars can't tell which came first — the
    conservative, honest assumption). A hit is booked at exactly -sl / +pt.
    If neither is hit, exit at the CLOSE of the last held bar; win if > 0.

    Returns None when the trade can't be resolved (no next bar / bad price).
    """
    entry_idx = i + 1
    n = len(close)
    if entry_idx >= len(open_arr) or entry_idx >= n:
        return None
    entry = float(open_arr[entry_idx])
    if not entry > 0:
        return None
    for j in range(hold):
        idx = entry_idx + j
        if idx >= n:
            break
        if (low_arr[idx] - entry) / entry <= -sl:
            return {'outcome': 'loss', 'ret': -sl, 'entry_idx': entry_idx,
                    'exit_idx': idx, 'entry': entry, 'exit': entry * (1 - sl),
                    'reason': 'stop'}
        if (high_arr[idx] - entry) / entry >= pt:
            return {'outcome': 'win', 'ret': pt, 'entry_idx': entry_idx,
                    'exit_idx': idx, 'entry': entry, 'exit': entry * (1 + pt),
                    'reason': 'target'}
    last_idx = min(entry_idx + hold - 1, n - 1)
    if last_idx < entry_idx:
        return None
    g = (close[last_idx] - entry) / entry
    return {'outcome': 'win' if g > 0 else 'loss', 'ret': g, 'entry_idx': entry_idx,
            'exit_idx': last_idx, 'entry': entry, 'exit': float(close[last_idx]),
            'reason': 'time'}


# ── evaluate an N-indicator combo ─────────────────────────────────────────────

def _eval(states_list: list[np.ndarray], close: np.ndarray,
          hold: int, pt: float, sl: float,
          regime_arr: np.ndarray | None = None,
          target_regime: str | None = None,
          min_signals: int = 5,
          open_arr: np.ndarray | None = None,
          high_arr: np.ndarray | None = None,
          low_arr: np.ndarray | None = None,
          min_idx: int = 0,
          max_idx: int | None = None,
          require_profit: bool = True) -> dict | None:
    """
    Evaluate when ALL indicators in states_list are simultaneously bullish.

    `min_idx` drops signals before that bar — used by custom "last N trading
    days" scans, where earlier bars exist only to warm the indicators up.
    If regime_arr + target_regime given, only score signals in that regime.
    Minimum `min_signals` resolved signals required (default 5). Sparse regimes
    can call with min_signals=3 so we still return a real best-fit combo.

    `max_idx` drops signals at or after that bar. Together with `min_idx` it
    restricts scoring to one half of the split used for out-of-sample
    validation: the search runs on [min_idx, max_idx), the check runs on
    [split_idx, end).

    `require_profit` (default True) rejects any combo that did not actually make
    money — see the gate below. Score = expectancy * sqrt(total).

    Entry/exit modeling (realistic, not same-bar-close):
    - Entry is the OPEN of the bar AFTER the signal bar — you can't know a bar
      closed bullish until after the market closes, so same-bar-close entry
      would be trading on a price you couldn't have acted on yet.
    - Stop-loss/take-profit are checked against each held day's intraday
      High/Low, not just its close — a close-only check misses stops that
      were genuinely triggered intraday and would have exited the trade.
      If open_arr/high_arr/low_arr aren't provided, falls back to the old
      close-only same-bar model (kept for any caller that hasn't been
      updated to pass OHLC).
    """
    combo = states_list[0].copy()
    for arr in states_list[1:]:
        combo = combo & arr
    combo = combo.astype(np.int8)

    # rising edge only (new alignment)
    edge = np.zeros(len(combo), dtype=np.int8)
    edge[1:] = ((combo[1:] == 1) & (combo[:-1] == 0)).astype(np.int8)
    idxs = np.where(edge == 1)[0]
    idxs = idxs[idxs < len(close) - hold]
    if min_idx > 0:
        idxs = idxs[idxs >= min_idx]
    if max_idx is not None:
        idxs = idxs[idxs < max_idx]

    # filter to target regime if provided
    if regime_arr is not None and target_regime is not None:
        idxs = np.array([i for i in idxs
                         if i < len(regime_arr) and regime_arr[i] == target_regime])

    if len(idxs) < min_signals:
        return None

    _has_ohlc = open_arr is not None and high_arr is not None and low_arr is not None

    wins = 0; losses = 0
    gains: list[float] = []; loss_vals: list[float] = []
    trade_idxs: list[int] = []   # signal bars that actually resolved into a trade

    for i in idxs:
        if _has_ohlc:
            _t = simulate_trade(int(i), open_arr, high_arr, low_arr, close, hold, pt, sl)
            if _t is None:
                continue
            outcome = (_t['outcome'], _t['ret'])
        else:
            entry = close[i]
            if entry <= 0:
                continue
            outcome = None
            for j in range(1, hold + 1):
                if i + j >= len(close):
                    break
                g = (close[i + j] - entry) / entry
                if g <= -sl:
                    outcome = ('loss', g); break
                if g >= pt:
                    outcome = ('win', g); break
            if outcome is None and i + hold < len(close):
                g = (close[i + hold] - entry) / entry
                outcome = ('win', g) if g > 0 else ('loss', g)
        if outcome is None:
            continue
        trade_idxs.append(int(i))
        if outcome[0] == 'win':
            wins += 1; gains.append(outcome[1])
        else:
            losses += 1; loss_vals.append(abs(outcome[1]))

    total = wins + losses
    if total < min_signals:
        return None

    wr  = wins / total * 100
    avg_g = float(np.mean(gains)     * 100) if gains     else 0.0
    avg_l = float(np.mean(loss_vals) * 100) if loss_vals else 0.0
    _sum_gains = sum(gains) if gains else 0.0
    _sum_losses = sum(loss_vals) if loss_vals else 0.0
    if _sum_losses > 0 and _sum_gains > 0:
        pf_raw = _sum_gains / _sum_losses
    elif _sum_losses == 0 and _sum_gains > 0:
        pf_raw = 9.9
    else:
        pf_raw = 0.0
    pf = min(round(pf_raw, 2), 9.9)
    exp   = wr / 100 * avg_g - (1 - wr / 100) * avg_l

    # ── profitability gate ───────────────────────────────────────────────────
    # A combo that lost money is not a result, it's a rejection.
    #
    # Selection used to rank on `win_rate * sqrt(total)`, which cannot tell a
    # profitable combo from an unprofitable one: expectancy and profit factor
    # were computed, displayed, and then ignored when picking the winner. So a
    # regime containing no real edge did not return "nothing" — it returned its
    # least-bad loser, and the UI presented that as the regime's best strategy.
    # Measured on pure random-walk input, 9 of 24 regime slots came back with
    # negative expectancy, down to WR 13.3% / PF 0.25 / expectancy -3.27.
    #
    # Gate here, because this is the single function every displayed strategy
    # passes through: the greedy expansion, the sparse-regime pair search and
    # the tied-alternatives search all score candidates with it, so a loser can
    # no longer enter as a winner, as a growth step, or as an "alternative".
    # Regimes with no profitable combo now stay empty, which the cascade and the
    # UI already handle — an empty slot is the honest answer.
    # Gate on the expectancy as displayed (2 dp) so a shown strategy never
    # reads +0.00, and on the unrounded profit factor so a held-back result
    # that made a small profit is never rounded down to "lost money".
    if require_profit and (round(exp, 2) <= 0 or pf_raw <= 1.0):
        return None

    # Rank by money-per-trade weighted by sample size, not by win rate. A 90%
    # win rate built on +0.5% wins and -5% losses loses money; win rate alone
    # cannot see that, expectancy can.
    score = exp * math.sqrt(total)

    return {
        'win_rate': round(wr, 1),
        'profit_factor': pf,
        'expectancy': round(exp, 2),
        'avg_gain': round(avg_g, 2),
        'avg_loss': round(avg_l, 2),
        'total': total,
        'wins':  wins,
        'losses': losses,
        'score': score,
        # Fingerprint of the trades this combo actually resolved. Two combos
        # with the same fingerprint took literally the same trades, so they are
        # the same strategy wearing different indicator names — callers use
        # this to avoid presenting one as an independent alternative to the
        # other. Note this tracks RESOLVED trades, not raw signal bars: a
        # looser combo can fire on extra bars that never resolve into a trade,
        # which leaves every displayed stat identical while the raw signal
        # lists differ.
        'signal_idxs': tuple(trade_idxs),
    }


# ── live-signal detection ────────────────────────────────────────────────────

def _combo_arr(states: dict[str, np.ndarray], keys: list[str]) -> np.ndarray:
    """AND of every indicator state in `keys`."""
    a = states[keys[0]].copy()
    for k in keys[1:]:
        a = a & states[k]
    return a.astype(np.int8)


def _is_fresh_signal(states: dict[str, np.ndarray], keys: list[str]) -> bool:
    """True only when the combo JUST aligned — on the final bar and not before.

    This has to match what the backtest measures. `_eval` counts a trade only
    on a RISING EDGE: the bar where the combo first becomes true, entered at
    the next open. `firing` used to mean "every indicator is bullish right
    now", which is a different and far more common event — measured across all
    50 indicators, only 17.8% of bars in an ON state are rising edges.

    The result was that a stock could show "● FIRING" on day 14 of an ongoing
    alignment while the win rate printed beside it had been measured entirely
    on day-1 entries. The alert and the statistic were describing different
    trades. Requiring the edge makes them the same event, at the cost of far
    fewer alerts — which is the honest count.
    """
    a = _combo_arr(states, keys)
    if len(a) < 2:
        return False
    return bool(a[-1] == 1 and a[-2] == 0)


# A signal stays "live" for this many bars after the rising edge: 0 = today
# only, 2 = today plus the two previous sessions (3 trading days).
LIVE_SIGNAL_MAX_AGE = 2


def _signal_age(states: dict[str, np.ndarray], keys: list[str],
                reg_arr: np.ndarray | None = None,
                target_regime: str | None = None) -> int | None:
    """Bars since the combo's most recent rising edge (0 = it aligned on the
    final bar), or None if it never aligned. Same event `_eval` trades on —
    including its regime filter: with reg_arr/target_regime given, only edges
    on bars of that regime count, since the strategy's stats were measured on
    exactly those entries."""
    a = _combo_arr(states, keys)
    if len(a) < 2:
        return None
    edges = np.where((a[1:] == 1) & (a[:-1] == 0))[0] + 1
    if reg_arr is not None and target_regime is not None:
        edges = edges[np.asarray(reg_arr)[edges] == target_regime]
    if not len(edges):
        return None
    return int(len(a) - 1 - edges[-1])


# ── greedy indicator expansion to up to 5 ────────────────────────────────────

def _grow_combo(seed_keys: list[str], all_states: dict[str, np.ndarray],
                close: np.ndarray, regime_arr: np.ndarray,
                hold: int, pt: float, sl: float,
                target_regime: str, max_size: int = 5,
                min_size: int = 3, min_signals: int = 5,
                open_arr: np.ndarray | None = None,
                high_arr: np.ndarray | None = None,
                low_arr: np.ndarray | None = None,
                min_idx: int = 0,
                max_idx: int | None = None) -> dict | None:
    """
    Start from seed_keys, greedily add indicators within target_regime.
    Below min_size: pick the most profitable addition (even if score drops from
    the lower total) so the combo reaches 3+ indicators when possible.
    At/above min_size: only add if score strictly improves.

    Every candidate is scored through `_eval`, which rejects unprofitable
    combos, so growth can neither start from nor pass through a losing combo.
    """
    remaining = [k for k in all_states if k not in seed_keys]
    current_keys = list(seed_keys)
    current_res  = _eval([all_states[k] for k in current_keys],
                          close, hold, pt, sl, regime_arr, target_regime,
                          min_signals=min_signals,
                          open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
    if current_res is None:
        return None

    while len(current_keys) < max_size and remaining:
        below_min = len(current_keys) < min_size
        best_add = None
        # Below min_size, rank additions on expectancy (quality per trade)
        # rather than score, so a combo can still reach 3 indicators when the
        # extra filter trims the sample. Every candidate is already profitable,
        # so expectancy > 0 and -1.0 is a safe "nothing chosen yet" sentinel.
        best_metric = -1.0 if below_min else current_res['score']
        best_res_local = None
        for k in remaining:
            candidate_keys = current_keys + [k]
            res = _eval([all_states[k2] for k2 in candidate_keys],
                         close, hold, pt, sl, regime_arr, target_regime,
                         min_signals=min_signals,
                         open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
            if res is None:
                continue
            metric = res['expectancy'] if below_min else res['score']
            if metric > best_metric:
                best_metric = metric
                best_add    = k
                best_res_local = res
        if best_add is None:
            break
        current_keys.append(best_add)
        remaining.remove(best_add)
        current_res = best_res_local

    # ── drop indicators that never constrain a signal ────────────────────────
    # Below min_size the loop above scores candidates on win_rate against a
    # starting metric of -1.0, so it will happily bolt on an indicator that
    # changes nothing at all just to reach 3 indicators. That produced combos
    # like "VOLRSI + PIVOT + EMA 20/50" whose trades are identical to plain
    # "VOLRSI + PIVOT" — the extra name implies a third condition had to align
    # when it never did, and it also let the alternatives search rediscover the real
    # subset and show it as a separate "tied" strategy with identical stats.
    # Remove any indicator whose removal leaves the exact same signal bars.
    if len(current_keys) > 2:
        for _k in list(current_keys):
            if len(current_keys) <= 2:
                break
            _trial = [x for x in current_keys if x != _k]
            _tr = _eval([all_states[x] for x in _trial], close, hold, pt, sl,
                        regime_arr, target_regime, min_signals=min_signals,
                        open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
            if _tr is not None and _tr['signal_idxs'] == current_res['signal_idxs']:
                current_keys = _trial
                current_res  = _tr

    # figure out dominant regime among signal bars
    combo = _combo_arr(all_states, current_keys)
    edge = np.zeros(len(combo), dtype=np.int8)
    edge[1:] = ((combo[1:] == 1) & (combo[:-1] == 0)).astype(np.int8)
    idxs = np.where(edge == 1)[0]
    rc = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
    for i in idxs:
        r = str(regime_arr[i]) if i < len(regime_arr) else 'RANGE'
        if r in rc:
            rc[r] += 1
    dom = max(rc, key=rc.get)

    # firing: the combo JUST aligned on the last bar — the same rising-edge
    # event the win rate above was measured on, not merely "still aligned".
    firing = _is_fresh_signal(all_states, current_keys)

    return {**current_res,
            'indicators': current_keys,
            'label': _ind_labels(current_keys),
            'best_regime': dom,
            'firing': firing}


# ── main cached entry point ───────────────────────────────────────────────────

@st.cache_data(ttl=1200, show_spinner=False)
def scan_stock(symbol: str, period_key: str, _v: int = 10) -> dict | None:
    """
    Single-stock entry — extracts from a pre-built batch cache when available,
    otherwise downloads individually. Cached 20 min.
    """
    return _process_stock_df(symbol, period_key)


@st.cache_data(ttl=1200, show_spinner=False)
def scan_all_stocks(symbols: tuple, period_key: str, _v: int = 20) -> dict:
    """
    Batch-download all symbols in one yfinance call, then process each.
    Returns {symbol: result_dict_or_None}.  Cached 20 min.
    """
    import yfinance as yf

    yf_per, interval, hold, pt, sl, _window = resolve_period(period_key)
    sym_list = list(symbols)

    # Cold connections occasionally stall forever, leaving the UI stuck on
    # "loading". Cap each request with a timeout and retry a couple of times
    # so the very first Run Scan completes instead of hanging.
    raw = None
    for _attempt in range(3):
        try:
            raw = yf.download(
                sym_list, period=yf_per, interval=interval,
                progress=False, auto_adjust=True, group_by='ticker',
                threads=True, timeout=20,
            )
            if raw is not None and not raw.empty:
                break
            raw = None
        except Exception:
            raw = None
        if _attempt < 2:
            time.sleep(1.0)   # brief backoff before retrying a cold request

    out: dict = {}
    for sym in sym_list:
        try:
            if raw is None:
                out[sym] = None
                continue
            # extract per-symbol slice from multi-ticker download
            if isinstance(raw.columns, pd.MultiIndex):
                if sym not in raw.columns.get_level_values(0):
                    out[sym] = None
                    continue
                df = raw[sym].copy()
            else:
                # single ticker fallback (unlikely here but safe)
                df = raw.copy()
            # A row without a close (e.g. today's unfinished bar for some symbols)
            # would make price/levels NaN and corrupt every indicator on it.
            df = df.dropna(subset=['Close']).reset_index()
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            if len(df) < hold + 20:
                out[sym] = None
                continue
            out[sym] = _analyse_df(df, hold, pt, sl, window=_window)
        except Exception:
            out[sym] = None
    # A completely empty batch means the download failed (not that every stock
    # genuinely has no data). Raise so st.cache_data does NOT cache the failure
    # — otherwise a retry would keep returning this empty result for 20 min.
    if not any(v for v in out.values()):
        raise RuntimeError("scan_all_stocks: no market data returned")
    return out


@st.cache_data(ttl=1200, show_spinner=False)
def download_all_raw(symbols: tuple, period_key: str, _v: int = 19) -> dict:
    """
    Batch-download all symbols in one yfinance call and return the cleaned
    OHLCV DataFrame per symbol: {symbol: df_or_None}. Cached 20 min.

    This is the fast part of a scan (~9s). It is split out from the heavy
    per-symbol analysis so the caller can run the analysis with a live
    progress bar instead of freezing on "Downloading…" for the whole scan.
    """
    import yfinance as yf
    import threading

    yf_per, interval, hold, pt, sl, _window = resolve_period(period_key)
    sym_list = list(symbols)

    # yfinance's own `timeout=` param does not reliably bound how long the
    # call blocks when run inside Streamlit's per-session worker thread (a
    # stalled TCP connect can hang past it). To guarantee the UI never hangs
    # forever, run the download in a supervisor thread and give up after a
    # hard wall-clock deadline — the leaked thread is daemonized so it can't
    # block app shutdown, and we simply treat the attempt as failed.
    def _attempt_download(_box: dict) -> None:
        try:
            _box['raw'] = yf.download(
                sym_list, period=yf_per, interval=interval,
                progress=False, auto_adjust=True, group_by='ticker',
                threads=True, timeout=20,
            )
        except Exception:
            _box['raw'] = None

    # A cold full-market batch (283 symbols) measures ~35s, so the previous
    # 35s per-attempt deadline sat right on the boundary and reported a
    # perfectly healthy download as "couldn't reach the market data service".
    # Give each attempt real headroom, but keep an overall wall-clock budget
    # so a genuinely stalled connection still can't hang the UI forever.
    # Medium and Long now fetch 5y instead of 6mo/2y, because the scoring
    # window has to be long enough to split into a fitted half and a held-back
    # half that each contain real trades. That is roughly 2.5x the rows, so the
    # old 90s/120s deadlines would have started reporting a healthy download as
    # a network failure.
    _ATTEMPT_DEADLINE = 180.0
    _TOTAL_BUDGET     = 240.0

    raw = None
    _t_start = time.time()
    for _attempt in range(2):
        _remaining = _TOTAL_BUDGET - (time.time() - _t_start)
        if _remaining <= 5:
            break
        _box: dict = {}
        _th = threading.Thread(target=_attempt_download, args=(_box,), daemon=True)
        _th.start()
        _th.join(min(_ATTEMPT_DEADLINE, _remaining))
        _candidate = _box.get('raw') if not _th.is_alive() else None
        if _candidate is not None and not _candidate.empty:
            raw = _candidate
            break
        if _attempt == 0:
            time.sleep(1.0)

    dfs: dict = {}
    for sym in sym_list:
        try:
            if raw is None:
                dfs[sym] = None
                continue
            if isinstance(raw.columns, pd.MultiIndex):
                if sym not in raw.columns.get_level_values(0):
                    dfs[sym] = None
                    continue
                df = raw[sym].copy()
            else:
                df = raw.copy()
            # A row without a close (e.g. today's unfinished bar for some symbols)
            # would make price/levels NaN and corrupt every indicator on it.
            df = df.dropna(subset=['Close']).reset_index()
            if 'Datetime' in df.columns:
                df = df.rename(columns={'Datetime': 'Date'})
            df['Date'] = pd.to_datetime(df['Date'])
            if len(df) < hold + 20:
                dfs[sym] = None
                continue
            dfs[sym] = df
        except Exception:
            dfs[sym] = None
    # Raise on total failure so st.cache_data doesn't cache an empty result.
    if not any(v is not None for v in dfs.values()):
        raise RuntimeError("download_all_raw: no market data returned")
    return dfs


def _process_stock_df(symbol: str, period_key: str) -> dict | None:
    """Download + analyse a single symbol (fallback path)."""
    try:
        import yfinance as yf
        yf_per, interval, hold, pt, sl, _window = resolve_period(period_key)
        df = yf.download(symbol, period=yf_per, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or len(df) < hold + 20:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.reset_index()
        if 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        return _analyse_df(df, hold, pt, sl, window=_window)
    except Exception:
        return None


@st.cache_data(ttl=1200, show_spinner=False)
def get_stock_df(symbol: str, period_key: str, _v: int = 8) -> 'pd.DataFrame | None':
    """Fetch OHLCV df for a single symbol — used for price ladder / charts."""
    try:
        import yfinance as yf
        yf_per, interval, hold, pt, sl, _window = resolve_period(period_key)
        df = yf.download(symbol, period=yf_per, interval=interval,
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 5:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.dropna(subset=['Close']).reset_index()
        if 'Datetime' in df.columns:
            df = df.rename(columns={'Datetime': 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except Exception:
        return None


def _best_combo_for_regime(states: dict, close: np.ndarray,
                            reg_arr: np.ndarray | None,
                            hold: int, pt: float, sl: float,
                            target_regime: str | None,
                            min_signals: int = 5,
                            min_size: int = 3,
                            open_arr: np.ndarray | None = None,
                            high_arr: np.ndarray | None = None,
                            low_arr: np.ndarray | None = None,
                            min_idx: int = 0,
                            max_idx: int | None = None) -> dict | None:
    """Find the best 2..5 indicator combo for a target regime (or overall if None).

    `min_signals` controls the statistical-significance floor. Sparse regimes
    can call with min_signals=3 so we still surface a real best-fit combo.
    `min_size` is the minimum number of indicators in the combo (default 3,
    can be lowered to 2 for sparse regimes where 3-indicator AND-overlaps are
    too rare).
    """
    keys = list(states.keys())
    if len(keys) < 2:
        return None
    ind_scores: list[tuple[float, str]] = []
    ind_results: dict[str, dict] = {}
    for k in keys:
        r = _eval([states[k]], close, hold, pt, sl, reg_arr, target_regime,
                  min_signals=min_signals,
                  open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
        if r:
            ind_scores.append((r['score'], k))
            ind_results[k] = r
    if not ind_scores:
        return None
    ind_scores.sort(reverse=True)

    # Try greedy expansion from the top-2 seeds when we have enough candidates.
    grown = None
    if len(ind_scores) >= 2:
        seed = [ind_scores[0][1], ind_scores[1][1]]
        if reg_arr is None or target_regime is None:
            dummy_arr = np.array(['ALL'] * len(close), dtype=object)
            grown = _grow_combo(seed, states, close, dummy_arr,
                                hold, pt, sl, 'ALL',
                                max_size=5, min_size=min_size,
                                min_signals=min_signals,
                                open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
        else:
            grown = _grow_combo(seed, states, close, reg_arr,
                                hold, pt, sl, target_regime,
                                max_size=5, min_size=min_size,
                                min_signals=min_signals,
                                open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
        if grown is not None:
            return grown

    # Fallback (only reached when min_size <= 2): the top-2 seeds didn't
    # have enough AND-overlap. Brute-force scan all pairs of the top
    # candidates and return the best 2-indicator combo. This is the
    # honest sparse-regime answer — a real 2-indicator strategy, not a
    # 1-indicator "combo" (which isn't a combo at all).
    if min_size <= 2:
        # Brute-force pair search for sparse regimes. We can't rely on the
        # per-indicator score list here — an indicator with 1 in-regime fire
        # got filtered out, but its AND with another indicator might still
        # produce 2+ overlapping fires inside the regime.
        # So we search ALL indicator pairs. _eval is microseconds; for ~45
        # indicators that's ~990 pairs — still trivial.
        all_keys = list(states.keys())
        best_res = None
        best_score = -1.0
        for i in range(len(all_keys)):
            for j in range(i + 1, len(all_keys)):
                ka, kb = all_keys[i], all_keys[j]
                r = _eval([states[ka], states[kb]], close, hold, pt, sl,
                           reg_arr, target_regime, min_signals=min_signals,
                           open_arr=open_arr, high_arr=high_arr, low_arr=low_arr, min_idx=min_idx, max_idx=max_idx)
                if r is None:
                    continue
                if r['score'] > best_score:
                    best_score = r['score']
                    best_res = (r, [ka, kb])
        if best_res is not None:
            res, keys2 = best_res
            res = dict(res)
            res['indicators'] = keys2
            res['label']      = _ind_labels(keys2)
            # dominant regime among signal bars
            combo_arr = states[keys2[0]] & states[keys2[1]]
            edge = np.zeros(len(combo_arr), dtype=np.int8)
            edge[1:] = ((combo_arr[1:] == 1) & (combo_arr[:-1] == 0)).astype(np.int8)
            idxs = np.where(edge == 1)[0]
            rc = {'TREND': 0, 'RANGE': 0, 'VOLATILE': 0}
            for ix in idxs:
                r2 = str(reg_arr[ix]) if (reg_arr is not None and ix < len(reg_arr)) else 'RANGE'
                if r2 in rc:
                    rc[r2] += 1
            res['best_regime'] = max(rc, key=rc.get)
            res['firing']      = _is_fresh_signal(states, keys2)
            return res
    return None


def _find_runner_ups(winner: dict, states: dict, close: np.ndarray,
                     reg_arr: np.ndarray | None, hold: int, pt: float,
                     sl: float, target_regime: str,
                     min_signals: int, max_alts: int = 2,
                     open_arr: np.ndarray | None = None,
                     high_arr: np.ndarray | None = None,
                     low_arr: np.ndarray | None = None,
                     min_idx: int = 0,
                     max_idx: int | None = None) -> list[dict]:
    """Find the next-best OTHER real indicator combos (size 2-3) for this
    regime, ranked by the same fitted score as the winner, at the same
    min_signals floor. Bounded to pairs and triples of the 12 strongest single
    indicators so cost stays trivial (no full 2^45 search).

    Everything here is scored on the fitted half only — the held-back half is
    never consulted, so the shortlist is fixed before validation runs.
    """
    # How much of the winner's trade history an "alternative" may share before
    # it stops being independent evidence. 0.6 = at most 60% of trades in
    # common. Raise it to surface more (more lookalikes), lower it for stricter
    # independence.
    _MAX_OVERLAP = 0.6

    win_keys = set(winner['indicators'])
    all_keys = list(states.keys())

    def _ev(keys: list[str]):
        return _eval([states[k] for k in keys], close, hold, pt, sl,
                     reg_arr, target_regime, min_signals=min_signals,
                     open_arr=open_arr, high_arr=high_arr, low_arr=low_arr,
                     min_idx=min_idx, max_idx=max_idx)

    # Rank all single indicators by score so we only combine the strongest few.
    singles: list[tuple[float, str]] = []
    for k in all_keys:
        r = _ev([k])
        if r:
            singles.append((r['score'], k))
    singles.sort(reverse=True)
    _TOP_N = 12
    top_keys = [k for _s, k in singles[:_TOP_N]]

    # Every profitable pair and triple among them, best fitted score first.
    cands: list[tuple[float, list[str], dict]] = []
    for size in (2, 3):
        for keys in itertools.combinations(top_keys, size):
            keys = list(keys)
            ks = set(keys)
            # A subset (or superset) of the winner is not an independent
            # strategy — it is the winner with a filter removed or added.
            if ks <= win_keys or win_keys <= ks:
                continue
            r = _ev(keys)
            if r is not None:
                cands.append((r['score'], keys, r))
    cands.sort(key=lambda t: t[0], reverse=True)

    # Trades the winner actually took. Any "alternative" that entered on
    # mostly the same bars is the winner rewritten, not a second strategy.
    win_sig = winner.get('signal_idxs')
    accepted_sigs: list[set] = [set(win_sig)] if win_sig else []
    accepted_keys: list[set] = []
    out: list[dict] = []
    for _score, keys, res in cands:
        if len(out) >= max_alts:
            break
        # Same subset/superset rule against runner-ups already accepted.
        _ks = set(keys)
        if any(_ks <= _a or _a <= _ks for _a in accepted_keys):
            continue
        _sig = set(res.get('signal_idxs') or ())
        if _sig and any(_p and len(_sig & _p) / len(_sig | _p) > _MAX_OVERLAP
                        for _p in accepted_sigs):
            continue
        accepted_sigs.append(_sig)
        accepted_keys.append(_ks)
        alt = dict(res)
        alt['indicators'] = keys
        alt['label']      = _ind_labels(keys)
        if _sig and win_sig:
            _w = set(win_sig)
            alt['overlap_pct'] = round(100 * len(_sig & _w) / len(_sig | _w))
        out.append(alt)
    return out


def _merge_oos(fitted: dict, tested: dict) -> dict:
    """Display dict: out-of-sample stats on top, fitted stats kept under `is_`.

    The numbers a user acts on have to be the ones measured on bars the search
    never saw, so the out-of-sample result takes the plain keys ('win_rate',
    'profit_factor', 'expectancy', ...) that the UI and the sorting already
    read. The fitted numbers are preserved under an `is_` prefix so both can be
    shown side by side — a wide gap between them is itself the useful signal
    that a strategy was curve-fitted rather than real.
    """
    out = dict(fitted)
    for _k in ('win_rate', 'profit_factor', 'expectancy', 'avg_gain',
               'avg_loss', 'total', 'wins', 'losses', 'score'):
        out[f'is_{_k}'] = fitted.get(_k)
        out[_k]         = tested[_k]
    out['is_signal_idxs'] = fitted.get('signal_idxs')
    out['signal_idxs']    = tested['signal_idxs']
    out['validated']      = True
    out['oos_total']      = tested['total']
    # Sample-size warnings must describe the numbers actually on screen, which
    # are now the held-back ones — not the (larger) fitted sample.
    out['low_sample']     = tested['total'] < _OOS_LOW_SAMPLE
    out['thin_sample']    = tested['total'] < _OOS_MIN_TRADES + 2
    for _k in ('win_rate', 'expectancy', 'total'):
        out[f'ho_{_k}'] = tested[_k]
    return out


def _mark_unvalidated(fitted: dict, held_back: dict | None,
                      too_short: bool) -> dict:
    """Display dict for a strategy that did NOT pass the held-back test.

    It keeps its fitted numbers (the only ones it has that are profitable) and
    carries what happened on the held-back bars under `ho_` so the UI can show
    both and flag it clearly. `fail_reason`: 'short' = window too short to
    split, 'few' = under _OOS_MIN_TRADES held-back trades, 'lost' = it lost
    money on the held-back bars.
    """
    out = dict(fitted)
    for _k in ('win_rate', 'profit_factor', 'expectancy', 'avg_gain',
               'avg_loss', 'total', 'wins', 'losses', 'score'):
        out[f'is_{_k}'] = fitted.get(_k)
    out['is_signal_idxs'] = fitted.get('signal_idxs')
    out['validated']      = False
    _tot = int(fitted.get('total', 0) or 0)
    out['low_sample']     = _tot < 10
    out['thin_sample']    = _tot < 5
    if held_back is not None:
        for _k in ('win_rate', 'expectancy', 'total'):
            out[f'ho_{_k}'] = held_back[_k]
    else:
        out['ho_total'] = 0
    if too_short:
        out['fail_reason'] = 'short'
    elif (held_back is None or held_back['total'] < _OOS_MIN_TRADES):
        out['fail_reason'] = 'few'
    else:
        out['fail_reason'] = 'lost'
    return out


def _analyse_df(df: pd.DataFrame, hold: int, pt: float, sl: float,
                window: int | None = None) -> dict | None:
    """
    Per-regime analysis: for EACH regime (TREND / RANGE / VOLATILE) independently
    search for the best 3..5 indicator combo using ONLY signals that fired while
    the market was in that regime. If a regime has no qualifying combo, that
    slot stays empty — never reuse another regime's combo, that's a lie.

    "Qualifying" includes having made money: `_eval` rejects any combo with
    expectancy <= 0 or profit factor <= 1, so no regime can return a losing
    strategy. A regime with no profitable combo returns None for that slot.

    `window` limits scoring to the last N bars (custom "last N trading days"
    scans). Bars before it still feed indicator warm-up.
    """
    try:
        price   = float(df['Close'].iloc[-1])
        states  = _build_states(df)
        reg_arr = _regime_arr(df)
        close   = df['Close'].values
        open_   = df['Open'].values
        high_   = df['High'].values
        low_    = df['Low'].values
        keys    = list(states.keys())

        if len(keys) < 2:
            return None

        # Earlier bars are warm-up only: indicators are computed across the
        # whole series, but no signal before this bar counts toward the stats.
        min_idx = max(0, len(close) - window) if window else 0

        # ── out-of-sample split ──────────────────────────────────────────────
        # The search runs inside [min_idx, train_max). The chosen strategy is
        # then checked once on [split_idx, end) — bars the search never saw —
        # and it is those held-back numbers that get displayed.
        #
        # Why this is necessary: the search tries ~45 single indicators, ~990
        # pairs and a greedy expansion up to 5 indicators, separately for each
        # regime, and keeps the maximum. The maximum of hundreds of noisy
        # candidates is high whether or not any edge exists. Run against pure
        # random-walk prices, the scanner reported a mean 62.9% win rate while
        # random entries under identical exit rules won 33.8% of the time — a
        # convincing-looking edge measured on data that contains none.
        #
        # The fitted half is chosen to look good and so is not evidence of
        # anything. The held-back half is evidence. Strategies that pass it
        # show their held-back numbers and are marked validated; strategies
        # that fail it are still shown (every regime gets its best strategy),
        # but keep their fitted numbers and are marked NOT validated.
        span      = len(close) - min_idx
        split_idx = min_idx + int(_TRAIN_FRAC * span)
        # A fitted trade must also CLOSE before the test half begins, or the
        # fitted stats would be computed partly from held-back prices.
        train_max = split_idx - hold
        max_idx   = train_max
        # Held-back signals need room to resolve before the data runs out.
        test_span = (len(close) - hold) - split_idx
        if span < _MIN_SPLIT_SPAN or train_max - min_idx < 40 or test_span < 20:
            # Not enough history to fit and validate on separate bars: search
            # the whole window, and mark every result as not validated.
            split_idx = None
            max_idx   = None

        _dates = pd.to_datetime(df['Date']) if 'Date' in df.columns else None

        best_per_regime: dict[str, dict | None] = {}
        for target_regime in ('TREND', 'RANGE', 'VOLATILE'):
            # Cascade across (min_signals, min_combo_size). Try strict 5-fire
            # 3-indicator combos first (best evidence), then progressively
            # relax to 3-fire 2-indicator combos. Each combo returned is
            # still real — same indicators, same regime filter, same outcome
            # walk; we're only lowering the *minimum sample size* needed to
            # report it. This avoids the alternative of either copying
            # another regime's combo (a lie) or showing empty boxes
            # everywhere (useless).
            # Minimum sample sizes raised from (2-5) to (10-15): with only a
            # handful of historical trades, a "100% win rate" is statistical
            # noise, not evidence of an edge — especially since this combo was
            # already picked as the single best-scoring one out of hundreds of
            # candidates searched. Fewer stocks/regimes will qualify, but every
            # win rate shown now rests on a real sample.
            grown = None
            cascade = [
                (15, 3), (12, 3), (10, 3),   # ideal: 3+ indicator combos, 10-15+ signals
                (15, 2), (12, 2), (10, 2),   # 2-indicator combos, 10-15+ signals
                (8, 2), (6, 2), (5, 2),      # low-confidence fallback — still a
                                             # real backtested combo, just fewer
                                             # samples. Flagged via low_sample
                                             # below rather than hidden.
                (4, 2), (3, 2), (2, 2),      # last resort so every regime that
                                             # actually OCCURRED gets a strategy
                                             # rather than an empty box. Two or
                                             # three trades prove nothing on
                                             # their own, so these are flagged
                                             # thin_sample and the UI warns.
            ]
            for _ms, _msz in cascade:
                grown = _best_combo_for_regime(
                    states, close, reg_arr, hold, pt, sl, target_regime,
                    min_signals=_ms, min_size=_msz,
                    open_arr=open_, high_arr=high_, low_arr=low_,
                    min_idx=min_idx, max_idx=max_idx)
                if grown is not None:
                    grown['min_signals_used'] = _ms
                    grown['min_size_used']    = _msz
                    grown['low_sample']       = _ms < 10
                    # Below 5 resolved trades a win rate is noise, not evidence.
                    grown['thin_sample']      = int(grown.get('total', 0) or 0) < 5
                    break
            if grown is None:
                # Nothing qualified even at the lowest floor (min_signals=2):
                # either the regime has too few signals, or every combo in it
                # lost money. Both are honest "no strategy here" answers, and an
                # empty slot is the only truthful way to say so — the previous
                # behaviour of surfacing the least-bad loser gave the user a
                # negative-expectancy strategy labelled as the regime's best.
                best_per_regime[target_regime] = None
                continue
            # Runner-ups are ranked on the FITTED half, so this has to run
            # before anything is swapped over to held-back numbers.
            try:
                _runners = _find_runner_ups(
                    grown, states, close, reg_arr, hold, pt, sl,
                    target_regime, min_signals=grown['min_signals_used'],
                    max_alts=_TOP_PER_REGIME - 1,
                    open_arr=open_, high_arr=high_, low_arr=low_,
                    min_idx=min_idx, max_idx=max_idx)
            except Exception:
                _runners = []
            # Fixed shortlist, ordered by fitted score, decided before the
            # held-back half is looked at.
            _shortlist = sorted([grown, *_runners],
                                key=lambda c: c['score'], reverse=True)

            # ── the out-of-sample test ───────────────────────────────────────
            # One check per shortlisted strategy, and the shortlist is never
            # topped up. Trying combo after combo until enough pass the
            # held-back half would fit the held-back half too, and destroy the
            # only unbiased estimate available.
            def _held_back(_keys: list[str], strict: bool):
                # strict: the real test (enough trades AND profitable).
                # not strict: just report what happened on the held-back bars.
                return _eval([states[k] for k in _keys], close, hold, pt, sl,
                             reg_arr, target_regime,
                             min_signals=_OOS_MIN_TRADES if strict else 1,
                             open_arr=open_, high_arr=high_, low_arr=low_,
                             min_idx=split_idx, max_idx=None,
                             require_profit=strict)

            _shown = []
            for _c in _shortlist:
                _oos = (_held_back(_c['indicators'], True)
                        if split_idx is not None else None)
                if _oos is not None:
                    _vc = _merge_oos(_c, _oos)
                else:
                    _ho = (_held_back(_c['indicators'], False)
                           if split_idx is not None else None)
                    _vc = _mark_unvalidated(_c, _ho, split_idx is None)
                _vc['best_regime'] = target_regime
                _vc['signal_age']  = _signal_age(states, _c['indicators'],
                                                 reg_arr, target_regime)
                _vc['firing']      = _vc['signal_age'] == 0
                _shown.append(_vc)
            # Validated strategies first; within each group keep fitted rank.
            _shown.sort(key=lambda c: not c['validated'])

            # Date of each strategy's most recent displayed entry, and of the
            # bar its latest signal started on.
            if _dates is not None:
                for _c in _shown:
                    _si = _c.get('signal_idxs')
                    if _si:
                        _c['last_trade_date'] = str(_dates.iloc[_si[-1]])[:10]
                    if _c['signal_age'] is not None:
                        _c['signal_date'] = str(
                            _dates.iloc[len(_dates) - 1 - _c['signal_age']])[:10]
            top = _shown[0]
            top['alt_combos'] = _shown[1:]
            best_per_regime[target_regime] = top

        current_regime = str(reg_arr[-1]) if len(reg_arr) else 'RANGE'
        return {'regimes': best_per_regime, 'price': price,
                'current_regime': current_regime}

    except Exception:
        return None
