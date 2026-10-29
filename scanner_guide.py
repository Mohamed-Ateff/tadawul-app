"""Arabic in-page guide for the Strategy Scanner page.

Explains, for a non-technical reader, everything the page does on screen and
behind it: data source, periods, market regimes, every indicator, how signals
and backtests work, every formula, the 70/30 validation, Live Signal Check,
the entry/target/stop levels, caching, known limitations, and where each
setting lives in the code.

Numbers that are settings in scanner_engine.py are read from it at render
time, so the guide stays correct when a setting is changed. Numbers that are
hard-coded inside functions are written here and their location is listed in
the "where to change it" table.
"""
from __future__ import annotations

import streamlit as st


# ── indicator catalogue ──────────────────────────────────────────────────────
# (key, condition for "on" — in Arabic, warning or '')
# Conditions describe what the code ACTUALLY tests with the installed
# pandas_ta (0.4.71b0); where that differs from the indicator's name, the
# warning column says so.
_INDICATORS = [
    ('اتجاه', [
        ('SMA',   'متوسط 50 يوم أعلى من متوسط 200 يوم', ''),
        ('EMA',   'المتوسط الأسي 20 أعلى من المتوسط الأسي 50', ''),
        ('WMA',   'الإغلاق أعلى من المتوسط الموزون 20', ''),
        ('PSAR',  'مؤشر Parabolic SAR تحت السعر (اتجاه صاعد) — إعدادات 0.02 / 0.2', ''),
        ('ICHI',  'خط Tenkan-sen (9) أعلى من خط Kijun-sen (26) في إيشيموكو', ''),
        ('MACD',  'خط MACD أعلى من خط الإشارة (Signal) — إعدادات 12 / 26 / 9', ''),
        ('SUPER', 'اتجاه SuperTrend صاعد — طول 7 ومضاعف 3', ''),
        ('HULL',  'الإغلاق أعلى من Hull MA 16', ''),
    ]),
    ('زخم', [
        ('RSI',   'RSI(14) بين 50 و75', ''),
        ('STOCH', 'الاستوكاستك %K (14,3,3) بين 40 و80', ''),
        ('ROC',   'معدل التغير خلال 12 يوم موجب', ''),
        ('CCI',   'CCI(20) بين 0 و150 (محسوب بالمعادلة القياسية داخل الكود)', ''),
        ('WILLR', 'Williams %R(14) بين −50 و−20', ''),
        ('MOM',   'الإغلاق أعلى من إغلاق قبل 10 أيام', ''),
        ('TSI',   'مؤشر TSI (13 / 25) أعلى من الصفر', ''),
        ('PPO',   'خط PPO أعلى من خط الإشارة — 12 / 26 (متوسط بسيط) وإشارة 9', ''),
        ('ELDER', 'أعلى سعر في اليوم أعلى من EMA 13 (قوة المشترين موجبة)', ''),
    ]),
    ('حجم وسيولة', [
        ('OBV',    'OBV أعلى من قيمته قبل 5 أيام، والإغلاق أعلى من إغلاق قبل 5 أيام', ''),
        ('MFI',    'MFI(14) بين 50 و80', ''),
        ('CMF',    'Chaikin Money Flow (20) موجب', ''),
        ('VWAP',   'الإغلاق أعلى من VWAP متحرك لآخر 20 يوم (ليس VWAP الجلسة)', ''),
        ('ADLINE', 'خط التجميع/التصريف أعلى من قيمته قبل 5 أيام', ''),
        ('VOLMA',  'حجم اليوم أعلى من متوسط حجم آخر 20 يوم', ''),
        ('FORCE',  'Force Index (متوسط أسي 13) موجب', ''),
        ('VOLRSI', 'مؤشر RSI(14) محسوب على تغيّر الحجم أعلى من 50', ''),
    ]),
    ('تذبذب', [
        ('BB',     'الإغلاق عند أو أعلى من الخط الأوسط لبولنجر (متوسط 20)', ''),
        ('ATR',    'نسبة ATR(14) إلى السعر أعلى من متوسطها لآخر 20 يوم (التذبذب يزيد)', ''),
        ('KELT',   'الإغلاق أعلى من الخط الأوسط لقناة كلتنر (EMA 20)', ''),
        ('DONCH',  'الإغلاق في حدود 2% من أعلى سعر خلال 20 يوم', ''),
        ('SQZ',    'انضغاط: نطاقات بولنجر كانت جوه قناة كلتنر في أي جلسة من آخر 5 جلسات، '
                   'والإغلاق النهارده أعلى من الخط الأوسط (متوسط 20) — بداية خروج من الانضغاط', ''),
        ('HV',     'التذبذب التاريخي (20 يوم) أعلى من متوسطه لآخر 20 يوم', ''),
        ('STDEV',  'الانحراف المعياري للإغلاق (20) أعلى من متوسطه لآخر 20 يوم', ''),
        ('CHAND',  'الإغلاق أعلى من Chandelier Exit = أعلى قمة 22 يوم − 3 × ATR(22)', ''),
    ]),
    ('دعم ومقاومة', [
        ('PIVOT',   'الإغلاق أعلى من نقطة ارتكاز اليوم السابق (أعلى + أدنى + إغلاق) ÷ 3', ''),
        ('FIB',     'الإغلاق أعلى من مستوى 61.8% من مدى آخر 60 يوم', ''),
        ('ADX',     '‎+DI أعلى من ‎−DI و ADX أكبر من 20 (اتجاه صاعد له قوة)', ''),
        ('VWAPB',   'الإغلاق أعلى من VWAP (20) + انحراف معياري واحد', ''),
        ('PREVHL',  'الإغلاق أعلى من أعلى قمة في الـ20 يوم السابقة (اختراق)', ''),
        ('SWINGHL', 'الإغلاق أعلى من أعلى قمة في الـ10 أيام السابقة', ''),
    ]),
    ('ارتداد من تشبع بيعي (الإشارة هنا تعني أن السهم "نزل زيادة")', [
        ('RSIEXT',   'RSI(14) أقل من 35', ''),
        ('BBZ',      'Z-Score بولنجر أقل من −1.5 (السعر بعيد تحت المتوسط)', ''),
        ('DISTMA',   'الإغلاق أقل من متوسط 50 يوم بأكثر من 5%', ''),
        ('STOCHEXT', 'الاستوكاستك %K أقل من 20', ''),
        ('CCIEXT',   'CCI(20) أقل من −100', ''),
    ]),
    ('موقع السهم واتجاهه (من سعر السهم نفسه فقط)', [
        ('TASIF',    'الإغلاق أعلى من متوسط 50 يوم', ''),
        ('SECTORF',  'العائد خلال 20 يوم موجب', ''),
        ('RSTASI',   'العائد خلال 60 يوم موجب', ''),
        ('RSSECTOR', 'عائد 20 يوم أعلى من متوسطه لآخر 60 يوم', ''),
        ('ADVDEC',   '6 أيام صاعدة أو أكثر من آخر 10 أيام', ''),
        ('NEWHL',    'الإغلاق في حدود 3% من أعلى قمة خلال 60 يوم', ''),
    ]),
]


# ── small HTML helpers (no blank lines: Markdown would break the HTML) ───────
def _table(head: list[str], rows: list[list[str]]) -> str:
    h = ''.join(f"<th>{c}</th>" for c in head)
    b = ''.join('<tr>' + ''.join(f"<td>{c}</td>" for c in r) + '</tr>' for r in rows)
    return f"<div class='sg-tw'><table class='sg-t'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>"


def _sec(num: int, title: str, body: str, open_: bool = False) -> str:
    # id = the section's built-in number (stable when sections are re-ordered);
    # the page's "؟" links open the guide on it (data-sg='<num>').
    return (f"<details class='sg-d' id='sg-sec-{num}'{' open' if open_ else ''}><summary>"
            f"<span class='sg-n'>{num}</span>{title}</summary>"
            f"<div class='sg-b'>{body}</div></details>")


def _ltr(s: str) -> str:
    return f"<code dir='ltr'>{s}</code>"


def _l(s) -> str:
    """Keep a number / formula left-to-right inside Arabic text.

    Uses the Unicode isolate controls LRI (U+2066) … PDI (U+2069) as well as
    a dir='ltr' span: in a right-to-left paragraph the span alone was not
    enough and '4 × 5% = 20%' rendered reversed."""
    return (f"<span dir='ltr' style='unicode-bidi:isolate;white-space:nowrap'>"
            f"⁦{s}⁩</span>")


def _pm(pt: float, sl: float) -> str:
    """'هدف +5% · وقف −3%' — each number isolated so bidi can't reorder it."""
    return (f"<span style='white-space:nowrap'>هدف {_l(f'+{pt * 100:g}%')} · "
            f"وقف {_l(f'−{sl * 100:g}%')}</span>")


def _note(s: str, kind: str = 'info') -> str:
    return f"<div class='sg-note sg-{kind}'>{s}</div>"


def _idea(why: str, logic: str, how: str, cond: str) -> str:
    """One 'idea' card for the «الفكرة والمنطق» group: why it exists, the logic
    behind it, how it was built, and its conditions / thresholds."""
    rows = [('ليه اتعملت', why), ('المنطق', logic), ('اتطبقت إزاي', how), ('الشروط', cond)]
    return ("<div class='sg-idea'>" + ''.join(
        f"<div class='sg-idea-r'><span class='sg-idea-k'>{k}</span><div class='sg-idea-v'>{v}</div></div>"
        for k, v in rows if v) + "</div>")


# ── bidi: keep Latin / numeric runs left-to-right inside Arabic text ─────────
# In a right-to-left paragraph a run like "<25: +6" or "master ≥ 60" gets its
# signs reordered ("6+ :25>"). Every such run is wrapped in a Unicode isolate
# (LRI … PDI) so it reads exactly as written, while the runs themselves follow
# the Arabic right-to-left order. Text inside <code> and <style> is left alone.
import re as _re_bidi

_LTR_RUN = _re_bidi.compile(r"[A-Za-z0-9$(<>≥≤±+−\-][A-Za-z0-9$ .,:/+\-−<>≥≤±%×÷=()|²_'…&]*")
_TAG = _re_bidi.compile(r"(<[A-Za-z/!][^>]*>)")       # real tags only ("<25" is text)


def _iso(m) -> str:
    run = m.group(0)
    core = run.rstrip(" .,:(")
    tail = run[len(core):]
    if not _re_bidi.search(r"[A-Za-z0-9]", core):
        return run
    if core.startswith("(") and core.count("(") > core.count(")"):
        return run                     # unbalanced "(" before Arabic text: leave it
    return f"⁦{core}⁩{tail}"


def _bidi_fix(html: str) -> str:
    out, skip = [], 0
    for part in _TAG.split(html):
        if _TAG.fullmatch(part):
            tag = part.lower()
            if tag.startswith(("<code", "<style")):
                skip += 1
            elif tag.startswith(("</code", "</style")):
                skip = max(0, skip - 1)
            out.append(part)
        elif skip or not part.strip():
            out.append(part)
        else:
            out.append(_LTR_RUN.sub(_iso, part))
    return "".join(out)


_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');
.sg,.sg *{font-family:'IBM Plex Sans Arabic','Inter',-apple-system,'Segoe UI',Tahoma,sans-serif!important;}
.sg{direction:rtl;text-align:right;color:#111114;font-size:0.95rem;line-height:1.85;
    -webkit-font-smoothing:antialiased;padding:0.2rem 0.1rem 0.4rem;}
.sg p{margin:0.25rem 0 0.7rem;color:#26262B;}
.sg ul,.sg ol{margin:0.2rem 0 0.8rem;padding-right:1.25rem;padding-left:0;color:#26262B;}
.sg li{margin:0.25rem 0;}
.sg li::marker{color:#8A8A91;}
.sg b{color:#111114;font-weight:600;}
.sg code{font-family:'SF Mono',Menlo,Consolas,monospace!important;background:#F2F2F7;border:none;
         border-radius:6px;padding:0.08rem 0.4rem;color:#111114;font-size:0.8rem;unicode-bidi:isolate;direction:ltr;}
.sg-intro{padding:0.4rem 0.3rem 1rem;}
.sg-intro h3{margin:0 0 0.5rem;font-size:1.5rem;font-weight:700;color:#111114;letter-spacing:-0.01em;}
.sg-lead{font-size:1.02rem;color:#26262B;}
.sg-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:0.6rem;margin:1rem 0 0.4rem;}
.sg-step{background:#F2F2F5;border-radius:14px;padding:0.8rem 0.9rem;}
.sg-step-n{display:inline-flex;align-items:center;justify-content:center;width:1.6rem;height:1.6rem;
           border-radius:50%;background:#0063D1;color:#fff;font-size:0.8rem;font-weight:600;margin-bottom:0.35rem;}
.sg-step-t{font-size:0.88rem;color:#111114;line-height:1.5;}
.sg-list{background:#FFFFFF;border:1px solid #DEDEE3;border-radius:16px;overflow:hidden;margin-top:0.6rem;}
.sg-d{border-bottom:1px solid #DEDEE3;scroll-margin-top:90px;}
/* a section a "؟" on the page just opened: its title glows for a moment */
.st-key-sg_wrap .sg .sg-d.sg-flash>summary{background:#D6E8FF!important;transition:background .4s ease;}
.sg-d:last-child{border-bottom:none;}
.sg-d summary{cursor:pointer;padding:0.85rem 1.1rem;font-weight:500;color:#111114;font-size:0.98rem;
              list-style:none;display:flex;align-items:center;gap:0.75rem;transition:background .15s ease;}
.sg-d summary:hover{background:#F9F9FB;}
.sg-d summary::-webkit-details-marker{display:none;}
.sg-d summary::after{content:'‹';margin-right:auto;color:#C7C7CC;font-size:1.3rem;line-height:1;
                     transition:transform .2s ease;}
.sg-d[open] summary::after{transform:rotate(-90deg);}
.sg-d[open] summary{background:#F9F9FB;}
.sg-n{display:inline-flex;align-items:center;justify-content:center;min-width:1.75rem;height:1.75rem;
      border-radius:8px;background:#EAF3FF;color:#0063D1;font-size:0.8rem;font-weight:600;}
.sg-b{padding:0.4rem 1.4rem 1.2rem 1.4rem;background:#F9F9FB;}
.sg-b h4{margin:1rem 0 0.3rem!important;font-size:0.95rem!important;font-weight:600!important;color:#111114!important;}
.sg-tw{overflow-x:auto;margin:0.5rem 0 0.9rem;background:#FFFFFF;border:1px solid #DEDEE3;border-radius:12px;}
.sg-t{border-collapse:collapse;width:100%;font-size:0.86rem;}
.sg-t th{background:#F2F2F5;color:#3F3F46;font-weight:500;padding:0.55rem 0.75rem;text-align:right;
         border-bottom:1px solid #DEDEE3;white-space:nowrap;}
.sg-t td{padding:0.6rem 0.75rem;border-bottom:1px solid #F0F0F3;vertical-align:top;color:#26262B;}
.sg-t tr:last-child td{border-bottom:none;}
.sg-note{border-radius:12px;padding:0.7rem 0.9rem;margin:0.6rem 0;font-size:0.88rem;line-height:1.7;}
.sg-info{background:#EAF3FF;color:#082F5F;}
.sg-warn{background:#FFF4E5;color:#5E3200;}
.sg-bad{background:#FFEDEC;color:#6E0A06;}
.sg-ok{background:#E9F7EE;color:#0E3F22;}
.sg-note b{color:inherit;}
.sg-pill{display:inline-block;font-size:0.78rem;font-weight:600;padding:0.12rem 0.6rem;border-radius:980px;
         white-space:nowrap;}
.sg .sg-sub{font-size:0.8rem;color:#5C5C63!important;margin-top:0.15rem;}
.sg-gh{display:flex;align-items:baseline;gap:0.6rem;margin:1.4rem 0.2rem 0.5rem;}
.sg-gh span{font-size:1.1rem;font-weight:600;color:#111114;}
.sg-gh small{font-size:0.85rem;color:#3F3F46;}
@media (max-width:900px){.sg-steps{grid-template-columns:repeat(2,1fr);}}
.sg-idea{display:grid;gap:0.55rem;margin:0.5rem 0 0.4rem;}
.sg-idea-r{display:grid;grid-template-columns:7.5rem 1fr;gap:0.9rem;align-items:start;background:#FFFFFF;
           border:1px solid #DEDEE3;border-radius:12px;padding:0.75rem 0.95rem;}
.sg-idea-k{font-weight:600;color:#0063D1;font-size:0.88rem;padding-top:0.1rem;}
.sg-idea-v{color:#26262B;font-size:0.93rem;line-height:1.8;}
@media (max-width:700px){.sg-idea-r{grid-template-columns:1fr;gap:0.25rem;}}
/* the search / test split, drawn as a time bar (oldest on the right) */
.sg-split{display:flex;gap:4px;margin:0.6rem 0 0.2rem;}
.sg-split>div{border-radius:10px;padding:0.6rem 0.8rem;font-size:0.86rem;font-weight:600;line-height:1.45;}
.sg-split small{display:block;font-weight:500;font-size:0.76rem;}
.st-key-sg_wrap .sg .sg-split-a{background:#E4E4EA;color:#111114!important;}
.st-key-sg_wrap .sg .sg-split-b{background:#0063D1;color:#FFFFFF!important;}
.st-key-sg_wrap .sg .sg-split-b small{color:#FFFFFF!important;}
.sg-split-axis{display:flex;justify-content:space-between;font-size:0.76rem;color:#5C5C63;margin:0 0.2rem 0.8rem;}
.st-key-sg_wrap .sg .sg-idea-v{color:#26262B!important;}
.st-key-sg_wrap .sg .sg-idea-k{color:#0063D1!important;}
/* The app colours every expander <summary> light grey (!important); the
   guide's section titles are <summary> elements inside the expander, so they
   need an explicit, more specific colour. */
.st-key-sg_wrap .sg .sg-d>summary,.st-key-sg_wrap .sg .sg-d>summary *{color:#111114!important;}
.st-key-sg_wrap .sg .sg-d>summary .sg-n{color:#0063D1!important;}
.st-key-sg_wrap .sg p,.st-key-sg_wrap .sg li,.st-key-sg_wrap .sg td{color:#26262B!important;}
.st-key-sg_wrap .sg th{color:#3F3F46!important;}
.st-key-sg_wrap .sg b,.st-key-sg_wrap .sg h3,.st-key-sg_wrap .sg h4,.st-key-sg_wrap .sg .sg-gh span{color:#111114!important;}
/* expander header: light in both states (Streamlit's dark theme paints the
   open header near-black) */
.st-key-sg_wrap [data-testid="stExpander"] details>summary{background:#FFFFFF!important;
    color:#111114!important;transition:background .15s ease;}
.st-key-sg_wrap [data-testid="stExpander"] details>summary:hover{background:#F7F7FA!important;}
.st-key-sg_wrap [data-testid="stExpander"] details[open]>summary{border-bottom:1px solid #DEDEE3;}
.st-key-sg_wrap [data-testid="stExpander"] details>summary *{color:#111114!important;}
.st-key-sg_wrap [data-testid="stExpanderDetails"]{background:#FFFFFF!important;}
/* expander title: right-to-left, Arabic font */
.st-key-sg_wrap [data-testid="stExpander"] summary{direction:rtl;text-align:right;}
.st-key-sg_wrap [data-testid="stExpander"] summary p{font-family:'IBM Plex Sans Arabic','Inter',sans-serif!important;
    font-size:1rem!important;font-weight:600!important;}
</style>
"""


def _build_html() -> str:
    from scanner_engine import (_PERIOD_CFG, _WARMUP_BARS, _TRAIN_FRAC,
                                _OOS_MIN_TRADES, _OOS_LOW_SAMPLE, _MIN_SPLIT_SPAN,
                                _TOP_PER_REGIME, LIVE_SIGNAL_MAX_AGE,
                                _DAYS_MIN, _DAYS_MAX, _IND_LABEL)

    train_pct = round(_TRAIN_FRAC * 100)
    test_pct = 100 - train_pct
    live_days = LIVE_SIGNAL_MAX_AGE + 1
    n_ind = sum(len(v) for _, v in _INDICATORS)

    # ── period table, computed from _PERIOD_CFG ─────────────────────────────
    _ar_name = {'Short': 'قصيرة (Short)', 'Medium': 'متوسطة (Medium)', 'Long': 'طويلة (Long)'}
    period_rows = []
    for k, (win, hold, pt, sl) in _PERIOD_CFG.items():
        split = int(_TRAIN_FRAC * win)
        period_rows.append([
            f"<b>{_ar_name.get(k, k)}</b>",
            f"{win} يوم تداول (≈ {win / 250:.1f} سنة)",
            f"≈ {split} يوم للبحث + {win - split} يوم للاختبار"
            f"<div style='font-size:0.78rem;color:#5C5C63;'>آخر {hold} يوم في كل جزء لإغلاق الصفقات فقط</div>",
            f"{hold} يوم",
            f"<span dir='ltr' style='color:#1B7A36;unicode-bidi:isolate'>+{pt * 100:g}%</span>",
            f"<span dir='ltr' style='color:#C1121F;unicode-bidi:isolate'>−{sl * 100:g}%</span>",
        ])
    s_hold, s_pt, s_sl = _PERIOD_CFG['Short'][1:]
    m_hold, m_pt, m_sl = _PERIOD_CFG['Medium'][1:]
    l_hold, l_pt, l_sl = _PERIOD_CFG['Long'][1:]

    # ── indicator tables ─────────────────────────────────────────────────────
    ind_html = ''
    for cat, items in _INDICATORS:
        rows = []
        for key, cond, warn in items:
            lbl = _IND_LABEL.get(key, key)
            rows.append([
                f"<b dir='ltr'>{lbl}</b>",
                cond + (f"<div class='sg-note sg-bad' style='margin:0.3rem 0 0;'>⚠ {warn}</div>"
                        if warn else ''),
            ])
        ind_html += f"<h4>{cat} ({len(items)})</h4>" + _table(['المؤشر', 'متى يكون "إيجابي" (= 1)'], rows)

    S = []  # sections

    # 1 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(1, 'مصدر البيانات: منين بتيجي الأسعار؟', (
        "<ul>"
        "<li><b>قائمة الأسهم:</b> قائمة ثابتة مكتوبة داخل الكود فيها <b>283 شركة</b> من السوق الرئيسية "
        "وسوق نمو، كل رمز ينتهي بـ " + _ltr('.SR') + ". القائمة لا تتحدث تلقائياً؛ أي إدراج جديد لازم يتضاف يدوياً. "
        "مؤشر تاسي العام <b>غير</b> موجود فيها.</li>"
        "<li><b>مزوّد الأسعار:</b> Yahoo Finance عن طريق مكتبة " + _ltr('yfinance') + "، بطلب واحد مجمّع لكل الأسهم.</li>"
        "<li><b>نوع البيانات:</b> شموع <b>يومية</b> (افتتاح، أعلى، أدنى، إغلاق، حجم)، والأسعار <b>معدّلة</b> "
        "للتوزيعات والتجزئة (" + _ltr('auto_adjust=True') + ").</li>"
        f"<li><b>كمية التاريخ:</b> يتم تحميل فترة التحليل + <b>{_WARMUP_BARS} يوم إضافي على الأقل</b> قبلها؛ "
        "عملياً بيتطلب من Yahoo أصغر فترة جاهزة تغطي ده (سنتين أو 5 أو 10 سنين)، فالتسخين غالباً أطول من سنة. "
        "الأيام دي بتخلي المؤشرات الطويلة زي متوسط 200 يوم تتحسب صح قبل أول يوم بيتحسب فيه أي إشارة، "
        "وإشاراتها نفسها <b>لا تُحتسب</b>.</li>"
        "<li><b>المهلة:</b> محاولتين للتحميل، كل محاولة أقصاها 180 ثانية، والإجمالي أقصاه 240 ثانية. "
        "لو فشل التحميل بالكامل تظهر رسالة \"Couldn't reach the market data service\" وتقدر تضغط Run Scan تاني.</li>"
        "<li>أي سهم بياناته أقل من (مدة الاحتفاظ + 20 يوم) يتم استبعاده.</li>"
        "</ul>"
        + _note("البيانات بتيجي من Yahoo وليس من تداول مباشرة، فممكن يكون فيها تأخير أو "
                "أخطاء من مصدرها، وآخر شمعة أثناء ساعات التداول قد تكون شمعة اليوم الجارية وهي لم تُغلق بعد.", 'warn')
    )))

    # 2 ────────────────────────────────────────────────────────────────────────
    from scanner_engine import resolve_period as _rp
    _yf_ar = {'1mo': 'شهر', '3mo': '3 شهور', '6mo': '6 شهور', '1y': 'سنة', '2y': 'سنتين',
              '5y': '5 سنين', '10y': '10 سنين', 'max': 'كل التاريخ المتاح'}

    def _trade_len(h):
        if h <= 5:
            return 'أسبوع تداول واحد'
        if h <= 22:
            return 'حوالي شهر'
        return f'حوالي {round(h / 21)} شهور'

    period_rows2 = []
    for k, (win, hold, pt, sl) in _PERIOD_CFG.items():
        split = int(_TRAIN_FRAC * win)
        be = sl / (pt + sl) * 100
        period_rows2.append([
            f"<b>{k}</b>",
            f"{hold} جلسة<div class='sg-sub'>{_trade_len(hold)}</div>",
            _pm(pt, sl),
            f"{be:.0f}%",
            f"{win} جلسة<div class='sg-sub'>≈ {win / 21:.0f} شهر</div>",
            f"بحث {_l(split - hold)} · اختبار {_l(win - split - hold)}",
            _yf_ar.get(_rp(k)[0], _rp(k)[0]),
        ])

    S.append(_sec(2, 'الفترات: Short و Medium و Long — كام يوم بالظبط وليه', (
        "<p>الفترة هي أهم اختيار في الصفحة، لأنها بتحدد <b>نوع الصفقة</b> اللي بندور عليها: "
        "هتمسك السهم أقصى قد إيه، هتبيع عند ربح قد إيه، وهتقفل على خسارة قد إيه. "
        "كل صفقة في الماضي بتتحاكى بالقواعد دي بالظبط، فنفس السهم ممكن يطلع له استراتيجية مختلفة في كل فترة.</p>"
        + _table(['الفترة', 'أقصى مدة للصفقة', 'الهدف / الوقف', 'نسبة النجاح اللي تكفي للتعادل',
                  'أيام بتتحلل', 'أيام إشارات للبحث / للاختبار', 'بيانات بتتحمّل'], period_rows2)
        + "<p class='sg-sub'>الجلسة = يوم تداول (تداول شغال من الأحد للخميس، يعني حوالي 21 جلسة في الشهر). "
        "\"أيام إشارات\" = الأيام اللي ممكن تطلع فيها إشارة؛ آخر أيام كل جزء محجوزة إن الصفقة تلحق تقفل.</p>"
        "<h4>ليه الهدف أكبر من الوقف؟</h4>"
        f"<p>في Short الهدف ضعف الوقف ({_pm(s_pt, s_sl)})، وفي Medium وLong حوالي مرة ونص "
        f"({_pm(m_pt, m_sl)} و {_pm(l_pt, l_sl)}). النتيجة إن الاستراتيجية ممكن تكسب حتى لو نجحت في أقل "
        f"من نص صفقاتها: في Medium مثلاً، لو 4 صفقات من 10 كسبوا ({_l('4 × 5% = 20%')}) و6 خسروا ({_l('6 × 3% = 18%')}) "
        "يبقى لسه كسبان. علشان كده <b>Win rate لوحده ما يكفيش</b> تحكم بيه — بص على Expectancy وProfit factor.</p>"
        "<h4>ليه الصفقة الأطول هدفها ووقفها أوسع؟</h4>"
        "<p>السهم بيتحرك في 3 شهور أكتر بكتير من أسبوع. وقف 1.5% لصفقة هتفضل 60 جلسة هيضرب من أول هزة عادية، "
        "وهدف 3% صغير جداً على حركة 3 شهور. فكل ما الصفقة أطول، الهدف والوقف أوسع.</p>"
        "<h4>ليه عدد الأيام اللي بتتحلل مختلف؟</h4>"
        f"<p>آخر {test_pct}% من الأيام بتتحجز للاختبار، ولازم يطلع فيها {_OOS_MIN_TRADES} صفقات على الأقل. "
        "بس آخر أيام كل جزء ما ينفعش يطلع فيها إشارة، لأن الصفقة لازم تلحق تقفل قبل ما الجزء يخلص: "
        f"{s_hold} جلسات بس في Short، لكن {l_hold} جلسة كاملة في Long. "
        f"فلو Long اتحلل على {_PERIOD_CFG['Medium'][0]} جلسة بس، جزء الاختبار كان هيفضل فيه حوالي "
        f"{_PERIOD_CFG['Medium'][0] - int(_TRAIN_FRAC * _PERIOD_CFG['Medium'][0]) - l_hold} يوم ممكن يطلع فيهم إشارة، "
        f"ودول قليلين جداً. علشان كده Long بيتحلل على {_PERIOD_CFG['Long'][0]} جلسة "
        f"(≈ {_PERIOD_CFG['Long'][0] / 250:.0f} سنين)، فيفضل "
        f"{_PERIOD_CFG['Long'][0] - int(_TRAIN_FRAC * _PERIOD_CFG['Long'][0]) - l_hold} يوم إشارات للاختبار.</p>"
        "<h4>ليه بيتحمّل بيانات أكتر من الأيام اللي بتتحلل؟</h4>"
        f"<p>المؤشرات محتاجة تاريخ قبل ما يبقى ليها معنى: متوسط 200 يوم مثلاً ما ينفعش يتحسب قبل 200 جلسة. "
        f"فبيتحمّل على الأقل {_WARMUP_BARS} جلسة زيادة قبل فترة التحليل (عملياً Yahoo بيدّي فترات جاهزة، "
        "فـShort بيحمّل سنتين مع إنه بيحلل حوالي 9 شهور بس). الإشارات اللي في أيام التسخين دي <b>مش بتتحسب</b>.</p>"
        "<h4>أختار أنهي؟</h4>"
        "<p>على حسب أسلوبك: لو بتشتري وتبيع خلال أيام اختار <b>Short</b>، لو بتمسك السهم أسابيع اختار "
        "<b>Medium</b> (ودي الافتراضية)، ولو بتستثمر لشهور اختار <b>Long</b>. "
        "Long مش بيدّي إشارات أقل؛ بالعكس، بيحلل أيام أكتر فغالباً بيطلع صفقات تاريخية أكتر. "
        f"الفرق إن كل صفقة بتقعد مدة أطول (لحد {l_hold} جلسة) وهدفها ووقفها أبعد.</p>"
        f"<h4>Days: عدد أيام بتختاره بنفسك</h4>"
        f"<p>تكتب عدد جلسات من {_DAYS_MIN} لـ{_DAYS_MAX}. قواعد الخروج بتتحدد لوحدها: لحد 90 جلسة بقواعد Short، "
        f"لحد 250 بقواعد Medium، وأكتر من كده بقواعد Long. لو العدد أقل من {_MIN_SPLIT_SPAN}، "
        f"أو بين 251 و263 (لأن صفقات Long الـ{l_hold} جلسة ما بتسيبش مكان كفاية للاختبار)، "
        "مش هينفع يتعمل اختبار، وكل الاستراتيجيات هتظهر Not validated.</p>"
        + _note("تغيير الفترة بيمسح النتايج الحالية، ولازم تضغط Run Scan تاني. "
                "الصفحة ما بتعملش أي تحليل لوحدها لما تفتحها.", 'info')
    )))

    # 3 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(3, 'حالات السوق: TREND و RANGE و VOLATILE', (
        "<p>كل يوم في تاريخ السهم بياخد تصنيف واحد من 3، باستخدام مؤشرين: "
        "<b>ADX(14)</b> لقياس قوة الاتجاه، و<b>ATR(14) ÷ السعر</b> لقياس حجم التذبذب.</p>"
        + _table(['الحالة', 'الشرط', 'معناها'], [
            ["<span style='color:#4B47C4;font-weight:600'>TREND</span>",
             'ADX أعلى من حد الاتجاه', 'السهم في اتجاه واضح وقوي'],
            ["<span style='color:#8E3FBA;font-weight:600'>VOLATILE</span>",
             'ليس TREND، و ATR÷السعر أعلى من حد التذبذب', 'حركة عنيفة بدون اتجاه واضح'],
            ["<span style='color:#086F8C;font-weight:600'>RANGE</span>",
             'أي يوم غير اللي فوق', 'حركة عرضية بين دعم ومقاومة'],
        ])
        + "<h4>إزاي الحدود بتتحسب</h4><ul>"
        "<li><b>حد الاتجاه</b> = النسبة المئوية الـ70 لقيم ADX للسهم نفسه، محصورة بين 15 و35.</li>"
        "<li><b>حد التذبذب</b> = النسبة المئوية الـ65 لقيم ATR÷السعر للسهم نفسه، محصورة بين 0.8% و5%.</li>"
        "<li>الحدود دي بتتحسب لكل يوم <b>من اليوم نفسه والأيام اللي قبله فقط</b> (نافذة متمددة)، "
        "يعني التصنيف لا يستخدم أي معلومة من المستقبل.</li>"
        "<li>أول أيام في التاريخ (أكبر من 20 يوم أو خُمس البيانات) تُعتبر RANGE لحد ما يتجمع تاريخ كافي.</li>"
        "<li><b>حالة السهم الحالية</b> = تصنيف آخر يوم في البيانات.</li></ul>"
        + _note("الحدود نسبية لكل سهم: \"TREND\" لسهم هادئ ممكن تكون حركة عادية لسهم تاني. "
                "والاستراتيجية بتتقاس على أيام نفس الحالة فقط.", 'info')
    )))

    # 4 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(4, f'المؤشرات الفنية ({n_ind} مؤشر) وشرط كل واحد', (
        f"<p>كل مؤشر بيتحول لقيمة بسيطة لكل يوم: <b>1</b> (إيجابي) أو <b>0</b> (لا). "
        "كل المؤشرات محسوبة من بيانات السهم نفسه فقط — لا يتم استخدام مؤشر تاسي أو بيانات القطاع، "
        "حتى المؤشرات اللي اسمها في الكود فيه TASI أو SECTOR (لهذا أسماؤها المعروضة تصف ما تحسبه فعلاً).</p>"
        "<p>المصدر: مكتبة " + _ltr('pandas_ta') + " لـ 30 مؤشر، والباقي محسوب يدوياً بالكود. "
        "أي مؤشر ما يقدرش يتحسب لسهم (تاريخ قصير مثلاً) يتشال من البحث لهذا السهم بس.</p>"
        + _note("كل مؤشر بيُقرأ من المكتبة <b>باسم العمود</b> مش بترتيبه، وCCI محسوب بالمعادلة القياسية داخل "
                "الكود بدل دالة المكتبة (اللي فيها خطأ حسابي). اتراجعت 7 مؤشرات (Ichimoku، MACD، CCI، CCI Ext.، "
                "PPO، ADX، Squeeze) على حسابات مستقلة وطابقت 100%.", 'ok')
        + ind_html
    )))

    # 5 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(5, 'الاستراتيجية والإشارة: يعني إيه "إشارة"؟', (
        "<ul>"
        "<li><b>الاستراتيجية</b> = مجموعة من 2 إلى 5 مؤشرات من القائمة، لازم <b>كلهم</b> يكونوا إيجابيين في نفس اليوم.</li>"
        "<li><b>الإشارة</b> = أول يوم يتحقق فيه الشرط ده بعد ما كان مش متحقق "
        "(اليوم اللي قبله كان فيه مؤشر واحد على الأقل سلبي). الأيام اللي بعده والشرط لسه متحقق "
        "<b>لا تُعتبر إشارات جديدة</b>.</li>"
        "<li>كل الإشارات بتتحسب على الشمعة اليومية. لو شغلت الفحص <b>بعد إغلاق السوق</b> (15:00 بتوقيت السعودية) "
        "الإشارة بتكون نهائية. لكن لو شغلته <b>أثناء التداول</b>، آخر شمعة ممكن تكون شمعة اليوم اللي لسه ما قفلتش، "
        "فإشارة \"New signal\" ممكن تظهر وتختفي قبل الإغلاق.</li>"
        "<li>الإشارة تُحتسب للاستراتيجية فقط لو اليوم ده كان من <b>نفس حالة السوق</b> بتاعة الاستراتيجية.</li>"
        "<li>كل الاستراتيجيات <b>شراء فقط</b> — الصفحة لا تبحث عن صفقات بيع على المكشوف.</li>"
        "</ul>"
    )))

    # 6 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(6, 'محاكاة الصفقات في الماضي (Backtest)', (
        "<p>لكل إشارة في الماضي، البرنامج بيعمل صفقة وهمية بالقواعد دي:</p><ol>"
        "<li><b>الدخول</b>: سعر <b>افتتاح اليوم التالي</b> للإشارة (لأنك ما تعرفش إن الإشارة حصلت غير بعد الإغلاق).</li>"
        "<li><b>كل يوم</b> خلال مدة الاحتفاظ (بدءاً من يوم الدخول نفسه): "
        "لو أدنى سعر وصل لوقف الخسارة ← <b>خسارة</b>. وإلا لو أعلى سعر وصل للهدف ← <b>ربح</b>.</li>"
        "<li>لو الوقف والهدف اتلمسوا في نفس اليوم، يُفترض إن <b>الوقف ضرب الأول</b> (افتراض متحفظ، "
        "لأن الشمعة اليومية لا توضح أيهما حصل أولاً).</li>"
        "<li>لو ما حصلش ولا واحد لحد آخر يوم في مدة الاحتفاظ: الخروج على <b>إغلاق آخر يوم</b>، "
        "وتُحسب ربح لو العائد أكبر من صفر وخسارة لو صفر أو أقل.</li>"
        "<li>الإشارات اللي لسه ما خلصتش مدة الاحتفاظ بتاعتها (قريبة من النهاية) لا تُحتسب.</li></ol>"
        + _note("المحاكاة <b>لا تحسب</b> عمولات البيع والشراء ولا ضريبة ولا الانزلاق السعري، "
                "ولا يوجد فلتر سيولة (الأسهم قليلة التداول بتتحلل زي الكبيرة). "
                "ولو السعر فتح بفجوة تحت الوقف، تُسجل الخسارة على أنها قيمة الوقف بالظبط، "
                "فالخسارة الحقيقية في الحالة دي كانت هتبقى أكبر.", 'warn')
    )))

    # 7 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(7, 'العمليات الحسابية: كل رقم على الشاشة بيتحسب إزاي', (
        _table(['الرقم', 'المعادلة', 'معناه'], [
            ['<b>Total</b>', 'عدد الصفقات اللي اكتملت', 'حجم العينة — كل ما زاد كل ما الرقم أوثق'],
            ['<b>Wins / Losses</b>', 'عدد الصفقات الرابحة / الخاسرة', ''],
            ['<b>Win Rate</b>', _ltr('Wins ÷ Total × 100'), 'نسبة الصفقات الرابحة'],
            ['<b>Avg Gain / Avg Loss</b>', 'متوسط نسبة الربح في الصفقات الرابحة / متوسط نسبة الخسارة في الخاسرة',
             'بيظهر تحت أرقام كل استراتيجية جنب عدد الصفقات الكسبانة والخسرانة (avg)، ويُستخدم لحساب Expectancy'],
            ['<b>Profit Factor</b>', _ltr('مجموع نسب الربح ÷ مجموع نسب الخسارة'),
             'أكبر من 1 = الاستراتيجية كسبت. لو مفيش خسائر خالص يظهر 9.9 (والحد الأقصى 9.9)'],
            ['<b>Expectancy</b>', _ltr('WinRate × AvgGain − (1 − WinRate) × AvgLoss'),
             'متوسط العائد المتوقع من الصفقة الواحدة، بالنسبة المئوية'],
            ['<b>Score</b> (داخلي)', _ltr('Expectancy × √Total'),
             'رقم ترتيب داخلي لا يظهر: يكافئ الربح للصفقة مع عدد صفقات أكبر'],
        ])
        + "<h4>مثال</h4><p>10 صفقات: 6 رابحة بمتوسط +5%، و4 خاسرة بمتوسط −3%. "
        "Win Rate = 60%. Profit Factor = (6×5) ÷ (4×3) = 30 ÷ 12 = 2.5. "
        "Expectancy = 0.6×5 − 0.4×3 = +1.8% للصفقة.</p>"
        + _note("مهم: نسبة نجاح 45% ممكن تكون مربحة جداً لو الهدف أكبر من الوقف. "
                f"في فترة Medium الهدف والوقف {_pm(m_pt, m_sl)}، "
                f"فنقطة التعادل تقريباً عند نسبة نجاح {m_sl / (m_pt + m_sl) * 100:.0f}% فقط. "
                "لذلك الأهم هو Expectancy و Profit Factor مش Win Rate لوحده.", 'info')
        + _note("أي استراتيجية Expectancy بتاعتها صفر أو أقل، أو Profit Factor بتاعها 1 أو أقل، "
                "<b>في جزء البحث</b> يتم رفضها نهائياً ولا تظهر. لكن الاستراتيجية اللي كانت رابحة في جزء البحث "
                "وخسرت في جزء الاختبار بتفضل ظاهرة بشارة <b>✕ Failed test</b> وبأرقام جزء البحث، فخلي بالك منها.", 'warn')
    )))

    # 8 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(8, f'البحث عن أفضل استراتيجية واختبار الـ{train_pct}/{test_pct}', (
        "<p>لكل سهم، ولكل حالة سوق على حدة (TREND ثم RANGE ثم VOLATILE):</p>"
        f"<h4>أ) تقسيم الفترة</h4><p>فترة التحليل بتتقسم جزئين: <b>أول {train_pct}%</b> (الأقدم) للبحث، "
        f"و<b>آخر {test_pct}%</b> (الأحدث) للاختبار. البحث لا يرى الجزء الأحدث نهائياً، "
        "وأي صفقة في جزء البحث لازم تكون خلصت قبل بداية جزء الاختبار.</p>"
        "<h4>ب) البحث (في جزء البحث فقط)</h4><ol>"
        f"<li>يُقيَّم كل مؤشر من الـ{n_ind} لوحده ويترتبوا حسب الـScore.</li>"
        "<li>أفضل مؤشرين يبدأوا الاستراتيجية. لو عددها أقل من الحد المطلوب (3)، يُضاف المؤشر اللي يدي "
        "أعلى Expectancy حتى لو الـScore نزل. بعد كده يُضاف مؤشر في كل مرة بشرط إنه يحسّن الـScore، "
        "لحد 5 مؤشرات بحد أقصى. في مراحل المؤشرين، لو أفضل مؤشرين مع بعض ما نفعوش، "
        "تتجرب كل الثنائيات الممكنة ويتختار أفضل ثنائي.</li>"
        "<li>أي مؤشر وجوده ما بيغيرش ولا صفقة بيتشال (علشان الاسم ما يوحيش بشرط إضافي مش حقيقي).</li>"
        "<li>البحث يبدأ بأعلى معايير (15 صفقة على الأقل و3 مؤشرات)، ولو ما لقاش حاجة "
        "ينزل تدريجياً لحد أقل حد (صفقتين ومؤشرين) — علشان كل حالة سوق حصلت تاخد استراتيجية لو فيه أي تركيبة رابحة.</li>"
        f"<li>بعد إيجاد الأفضل، يدور على <b>حتى {_TOP_PER_REGIME - 1} استراتيجية بديلة</b>: "
        "من أقوى 12 مؤشر، كل الثنائيات والثلاثيات، بشرط ألا تكون نفس الاستراتيجية بمؤشر زيادة أو ناقص، "
        "وألا تشترك في أكثر من 60% من نفس الصفقات مع استراتيجية قبلها. "
        f"لذلك يظهر لكل حالة <b>حتى {_TOP_PER_REGIME} استراتيجيات</b>.</li></ol>"
        "<h4>ج) الاختبار (مرة واحدة لكل استراتيجية)</h4>"
        f"<p>كل استراتيجية من القائمة تتجرب مرة واحدة على الـ{test_pct}% الأحدث. تنجح لو حققت "
        f"<b>{_OOS_MIN_TRADES} صفقات أو أكثر</b> في نفس حالة السوق <b>و</b> كانت رابحة (Expectancy > 0 و Profit Factor > 1).</p>"
        + _table(['الشارة', 'معناها', 'الأرقام الكبيرة في الكارت'], [
            ["<span class='sg-pill' style='background:#E9F7EE;color:#1B7A36'>✓ Validated</span>",
             f"نجحت في الاختبار على بيانات لم يرها البحث. <b>الأقوى والأوثق.</b>",
             f"من جزء الاختبار (آخر {test_pct}%)"],
            ["<span class='sg-pill' style='background:#F2F2F5;color:#3F3F46'>Not validated</span>",
             f"رابحة في جزء البحث، لكن جزء الاختبار كان فيه أقل من {_OOS_MIN_TRADES} صفقات في الحالة دي "
             "(أو الفترة كلها قصيرة جداً للتقسيم). <b>لم تُختبر بعد</b> — مش معناها إنها فاشلة.",
             f"من جزء البحث (أول {train_pct}%)، أو من الفترة كلها لو كانت أقصر من إنها تتقسم"],
            ["<span class='sg-pill' style='background:#FFEDEC;color:#C1121F'>✕ Failed test</span>",
             "اتختبرت على عدد كافي من الصفقات <b>وخسرت</b>. الأفضل تجنبها.",
             f"من جزء البحث (أول {train_pct}%)"],
        ])
        + "<h4>صندوق Validation تحت كل كارت</h4>"
        "<p>فيه رقمين جنب بعض: <b>Fitted (first 70%)</b> = نسبة النجاح وعدد الصفقات في جزء البحث، "
        "و<b>Held back (last 30%)</b> = نفس الأرقام في جزء الاختبار. مثلاً 46% من 13 صفقة ← 50% من 12 صفقة. "
        "لو الرقم نزل كتير من Fitted لـ Held back، فالاستراتيجية غالباً كانت \"متفصّلة\" على الماضي. "
        "\"no trades\" يعني مفيش ولا صفقة في جزء الاختبار.</p>"
        + _note("ليه الاختبار ده مهم: لما تجرب مئات التركيبات على نفس البيانات، "
                "أكيد واحدة هتطلع ممتازة بالصدفة. اتجرب الماسح على أسعار عشوائية تماماً "
                "فأعطى نسبة نجاح وهمية 62.9%. الجزء اللي البحث ما شافهوش هو الدليل الحقيقي الوحيد.", 'warn')
        + "<h4>ترتيب العرض</h4><p>جوه البحث، الاستراتيجية الأحسن بتتختار بالـScore (القسم 7). لكن في الصفحة "
        "كل حاجة بتترتب بنسبة النجاح من الأعلى، والعلامة (✓ Validated / Not validated / ✕ Failed test) "
        "بتفضل ظاهرة جنب كل استراتيجية، ولو عايز الـValidated بس فيه فلتر Validation. "
        f"علامة \"weak evidence\" تظهر لو صفقات الاختبار أقل من {_OOS_LOW_SAMPLE}. "
        "الشرح المبسّط للاختبار ده في القسم 18.</p>"
    )))

    # 9 ────────────────────────────────────────────────────────────────────────
    S.append(_sec(9, 'جدول Scanned Strategies: كل استراتيجيات كل سهم', (
        "<p>تحت Live Signal Check فيه كارت لكل سهم (كارتين جنب بعض)، وجواه جزء لكل حالة سوق "
        f"(↗ Trend، ↔ Range، ⚡ Volatile) لقينا لها استراتيجية كسبت في جزء البحث — ممكن تكون نجحت أو فشلت "
        "في الاختبار بعد كده، وده مكتوب في Validation. الكروت مترتبة بنسبة النجاح لاستراتيجية حالة السوق "
        "اللي السهم فيها النهارده (أول جزء في الكارت، عليه Today)، والأسهم اللي مالهاش استراتيجية للحالة دي "
        "بتيجي بعد خط فاصل. بيظهر أول 6 وتحتهم Show all.</p>"
        + _table(['الجزء', 'معناه'], [
            ['Market regime', 'حالة السوق. شارة <b>Today</b> وخط أزرق على الشمال = دي الحالة اللي السهم فيها دلوقتي، '
                              'يعني دي الاستراتيجية اللي تنطبق النهارده.'],
            ['Strategy', 'المؤشرات اللي لازم <b>كلها</b> تتحقق في نفس اليوم. لون كل مؤشر بيقول نوعه (المفتاح فوق القسم).'],
            ['Win rate', 'نسبة الصفقات الكسبانة.'],
            ['Profit factor', 'إجمالي المكسب ÷ إجمالي الخسارة. أكبر من 1 = الاستراتيجية كسبت.'],
            ['Expectancy', 'متوسط المكسب في الصفقة الواحدة (%). أهم رقم في الصف.'],
            ['Trades', 'عدد الصفقات. لو أقل من 10 الأرقام بتبهت '
                       'ويظهر "too few" لأن عينة صغيرة كده مش موثوقة.'],
            ['الخط الأخضر والأحمر', 'الصفقات الكسبانة (winning) والخسرانة (losing): عدد كل نوع ومتوسط نسبته '
                                    '(القسم 20).'],
            ['Strategy details ›', 'بيفتح شروط الشراء والبيع، والصفقات خلصت إزاي، وكل صفقة بتاريخها '
                                   '(القسم 20).'],
            ['Validation', 'نجحت في الاختبار ولا لأ (القسم 18 بيشرحها بالتفصيل)، وتحتها سطر بأرقام الاختبار. '
                           'حط الماوس عليها تشوف أرقام جزء البحث وجزء الاختبار جنب بعض.'],
        ])
        + f"<p>تحت الصف ممكن تلاقي \"2 more strategies for Range ›\": دي استراتيجيات تانية لنفس الحالة "
        f"(لحد {_TOP_PER_REGIME - 1})، مختلفة فعلاً: مش جزء من مؤشرات استراتيجية فوقها ولا فيها كل مؤشراتها "
        "وزيادة، والصفقات المشتركة بينها وبين أي استراتيجية فوقها أقل من 60% من مجموع صفقات الاتنين مع بعض "
        "(محسوبة على جزء البحث).</p>"
        f"<p>شارة <b>New signal</b> أو <b>Signal 1 session ago</b> على أي استراتيجية = بدأت إشارة في آخر "
        f"{live_days} جلسات على يوم من نفس حالتها. شارة <b>Live signal</b> جنب اسم السهم = السهم موجود فوق في "
        "Live Signal Check. البحث والفلاتر بيشتغلوا على الأقسام كلها مع بعض.</p>"
        "<h4>الأرقام أعلى الصفحة</h4>"
        + _table(['الرقم', 'معناه'], [
            ['Live signals', 'عدد الأسهم اللي فيها إشارة حية (Live Signal Check من غير بحث).'],
            ['Validated', 'كام سهم منهم فيه إشارة حية واحدة على الأقل من استراتيجية ✓ Validated '
                          '(نفس الأسهم اللي فلتر Validation بيسيبها في Live Signal Check).'],
            ['Stocks scanned', 'الأسهم اللي بياناتها نزلت واتحللت من إجمالي القائمة.'],
            ['Updated', 'وقت آخر فحص في الجلسة دي (— لو مفيش).'],
        ])
    )))

    # 10 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(10, 'Live Signal Check: الفرص اللي ممكن تتحرك عليها دلوقتي', (
        "<p>ده أول قسم في الصفحة وأهمها عملياً: الأسهم اللي فيها إشارة شراء جديدة. السهم بيظهر هنا لما "
        f"استراتيجية من استراتيجيات <b>حالة السوق اللي هو فيها دلوقتي</b> تبدأ إشارة في آخر {live_days} جلسات "
        "تداول، على يوم كان من نفس الحالة. الترتيب: الأعلى نسبة نجاح الأول (نسبة الاستراتيجية اللي إدّت "
        "الإشارة)، ولو اتساووا الأكتر صفقات. بيظهر أول 10 وتحتهم Show all.</p>"
        "<p>الكارت <b>خطة دخول بس</b>: أرقام الاستراتيجية نفسها (Win rate والصفقات و Profit factor) "
        "في Scanned Strategies، وزرار View strategy بيوديك عليها.</p>"
        "<h4>إزاي تقرا الكارت</h4>"
        + _table(['الجزء', 'معناه'], [
            ['الرمز والاسم والسعر', 'السعر = آخر سعر في البيانات وقت الفحص. بعد الإغلاق ده سعر إغلاق اليوم، '
                                    'لكن لو الفحص اتعمل والسوق شغال ممكن يبقى سعر الجلسة الجارية (متأخر شوية)، '
                                    'وما بيتحدثش لوحده.'],
            ['↔ Range · Best fit', 'حالة السوق، وترتيب الاستراتيجية فيها (Best fit = الأولى، أو Strategy #2 / #3).'],
            ['✓ Validated / Not validated / ✕ Failed test',
             'نتيجة الاستراتيجية في الاختبار (القسم 8). خلي بالك: ممكن يظهر كارت لاستراتيجية ✕ Failed test، '
             'يعني خسرت في جزء الاختبار، فالأحسن تتجنبها.'],
            ['Latest session · التاريخ', 'إمتى بدأت الإشارة. Latest session = آخر جلسة في البيانات، '
                                       '1 session earlier = الجلسة اللي قبلها، وهكذا. الإشارة بتتأكد بعد إغلاق الجلسة دي.'],
            ['+2 more signalling', 'استراتيجيات تانية لنفس الحالة بتدي إشارة برضه — تأكيد إضافي. '
                                   'تفاصيلها في Scanned Strategies.'],
            ['المؤشرات الملونة', 'شروط الاستراتيجية — كلها اتحققت في يوم الإشارة.'],
            ['Stop loss · Entry · Target 1 · Target 2 · Risk : Reward',
             'مستويات مقترحة من شكل الشارت (القسم 11). مهم: دي <b>مش</b> نفس قواعد الاختبار.'],
            ['Show chart', 'الشارت وجدول Past signals اللي بيثبتوا النتايج (القسم 17).'],
            ['View strategy ↓', 'بينزلك على نفس السهم في Scanned Strategies، ويعلّم الكارت بإطار أزرق ويظلل '
                                'الاستراتيجية اللي إدّت الإشارة. هناك تلاقي Win rate والصفقات والـValidation.'],
        ])
        + "<h4>الفلاتر (تحت مربع البحث)</h4>"
        + _table(['الفلتر', 'بيعمل إيه'], [
            ['Win rate', 'يخفي أي استراتيجية نسبة نجاحها أقل من اللي اخترته (60%+ / 70%+ / 80%+).'],
            ['Trades', 'يخفي أي استراتيجية صفقاتها أقل من 10 أو 20 — أحسن طريقة تبعد بيها الأرقام المبهرة '
                       'اللي جاية من صفقات قليلة.'],
            ['Market regime', 'يعرض استراتيجيات حالة سوق واحدة بس (Trend / Range / Volatile).'],
            ['Validation', 'Validated بس، أو Not validated بس (القسم 18).'],
        ])
        + "<p>الفلاتر بتشتغل على الاستراتيجيات في الصفحة كلها: كروت Live Signal Check، والجدول، والإكسل، "
        "و Scanned Strategies. لما يكون فيه فلتر شغال بيظهر سطر بعدد الأسهم المطابقة، وزرار "
        "<b>Clear filters</b> يرجّع كله.</p>"
        "<h4>جدول All live signals وملف الإكسل</h4>"
        "<p>تحت الكروت جدول فيه <b>كل</b> الإشارات الحية بعد الفلاتر (مش أول 10 بس)، بنفس ترتيب الكروت: "
        "السعر، الدخول، الوقف، الأهداف ونسبها، Risk : Reward وتقييمه (Great / Good — القسم 19 بيشرحه)، "
        "نسبة النجاح، عدد الصفقات (بالبرتقاني لو أقل من 10)، وجنبه الكسبانة (Wins) والخسرانة (Losses). "
        "زرار <b>Download Excel</b> بينزّل نفس الجدول ملف إكسل منسّق، "
        "فوقه الفترة والفلاتر اللي اخترتها ووقت التحميل.</p>"
    )))

    # 11 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(11, 'مستويات Entry و Target 1 و Target 2 و Stop Loss', (
        _note("مهم جداً: هذه المستويات <b>منفصلة</b> عن الاختبار التاريخي. "
              f"نسبة النجاح في الكارت اتحسبت بقواعد الفترة الثابتة (مثلاً في Medium: {_pm(m_pt, m_sl)} "
              f"خلال {m_hold} يوم)، وليس بهذه المستويات. المستويات دي <b>لم يتم اختبارها تاريخياً</b>؛ "
              "هي مقترحة من شكل الشارت فقط.", 'bad')
        + "<ul>"
        "<li><b>Entry</b> = آخر سعر إغلاق في البيانات (وليس سعر لحظي). في الاختبار التاريخي الدخول كان على افتتاح اليوم التالي.</li>"
        "<li><b>Stop Loss</b>، بالترتيب: (1) تحت أقرب \"شمعة طلب\" — شمعة خضراء ذيلها السفلي ≥ 30% من مداها — "
        "بمسافة أمان. (2) وإلا تحت أقرب قاع (Pivot Low). (3) وإلا السعر − 1.5 × ATR. "
        "وبعدين يتراجع: لو المسافة أقل من 0.8 × ATR يتحط الوقف على 1.5 × ATR تحت السعر، "
        "ولو أكبر من 2.5 × ATR يتحط على 2 × ATR. (ATR هنا = متوسط بسيط للمدى الحقيقي True Range "
        "لآخر 14 يوم، شاملاً الفجوات عن إغلاق اليوم السابق).</li>"
        "<li><b>المرشحين للأهداف</b>: امتدادات فيبوناتشي لآخر موجة صاعدة، القمم السابقة، متوسط 50 و200، "
        "الحد العلوي لبولنجر، أعلى سعر في 52 أسبوع، والأرقام الصحيحة (Round numbers). "
        "المستويات القريبة من بعض (أقل من 1.5%) تُدمج.</li>"
        "<li><b>Target 1</b> = أقرب مستوى يبعد 1.5 مرة على الأقل من مسافة الوقف (R)، وإلا السعر + 1.618 × R.</li>"
        "<li><b>Target 2</b> = أقرب مستوى يبعد 2.5 × R على الأقل وأعلى من Target 1، وإلا السعر + 2.618 × R.</li>"
        "<li><b>Risk:Reward</b> = نسبة ربح Target 1 ÷ نسبة الخسارة للوقف. ≥ 2 = Great، ≥ 1.5 = Good، أقل = Weak. "
        "لاحظ إن Target 1 بيتختار أصلاً على بعد ≥ 1.5R، فالنسبة غالباً 1.5 أو أكثر.</li>"
        "<li><b>جودة الدخول</b> (تحت Entry): مقياس لبعد الوقف عن السعر بوحدات ATR: "
        "OPTIMAL (قريب جداً) ← GOOD ← ELEVATED. CHASING لا تظهر أبداً عملياً، لأن مسافة الوقف محدودة "
        "بـ 2.5 × ATR والمقياس لا يمكن يوصل لـ 3 × ATR.</li>"
        "</ul>"
        "<p>Great و Good بيتحددوا إزاي وليه، بالتفصيل وبمثال: القسم 19.</p>"
    )))

    # 12 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(12, 'اللي بيحصل في الخلفية: التشغيل والتخزين المؤقت', (
        "<ol>"
        "<li>عند فتح الصفحة: لا يحصل أي تحميل أو تحليل.</li>"
        "<li>عند الضغط على ↻ Run Scan: تحميل أسعار كل الأسهم في طلب واحد (أول مرة غالباً لحد دقيقتين تقريباً، "
        "والحد الأقصى قبل ما يعتبره فشل ≈ 4 دقائق)، "
        "ثم تحليل الأسهم واحد واحد مع شريط تقدم (≈ 40–70 ثانية).</li>"
        "<li><b>تخزين مؤقت للأسعار</b>: 20 دقيقة، مشترك بين كل المستخدمين على نفس السيرفر.</li>"
        "<li><b>تخزين مؤقت للنتائج</b>: 20 دقيقة لكل مستخدم ولكل فترة — لو ضغطت Run Scan تاني لنفس الفترة "
        "خلال 20 دقيقة النتيجة تظهر فوراً بدون إعادة حساب.</li>"
        "<li>لذلك البيانات المعروضة ممكن تكون أقدم من لحظة الضغط بحد أقصى ≈ 40 دقيقة.</li>"
        "<li>مستويات الدخول والأهداف بتتحسب لكل كارت معروض، مع تخزين مؤقت داخل الجلسة.</li>"
        "</ol>"
    )))

    # 13 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(13, 'حدود ومحاذير لازم تكون عارفها', (
        "<ul>"
        "<li><b>الأداء التاريخي لا يضمن المستقبل.</b> الصفحة أداة فرز وبحث، وليست توصية استثمارية.</li>"
        "<li><b>NOT VALIDATED</b> أرقامها من نفس البيانات اللي اتختارت عليها، فطبيعي تكون أحلى من الواقع.</li>"
        "<li><b>لا عمولات ولا انزلاق ولا ضرائب</b> في المحاكاة، فالعائد الحقيقي أقل.</li>"
        "<li><b>لا فلتر سيولة</b>: سهم ضعيف التداول قد يصعب الدخول والخروج منه بالأسعار المحسوبة.</li>"
        "<li><b>فجوات الأسعار</b>: الخسارة بعد فجوة هبوط تُسجل بقيمة الوقف فقط.</li>"
        "<li><b>المستويات (Entry/Targets/Stop)</b> لم تُختبر تاريخياً، ومختلفة عن قواعد الاختبار.</li>"
        "<li><b>نسخة مكتبة المؤشرات</b> " + _ltr('pandas_ta') + " مش مثبّتة على رقم محدد في "
        + _ltr('requirements.txt') + ". الكود دلوقتي بيقرا أعمدتها بالاسم وبيحسب CCI بنفسه، "
        "فتغيير النسخة أقل خطورة، لكن نسخة مختلفة ممكن لسه تغيّر تفاصيل حسابات صغيرة.</li>"
        "<li>قائمة الأسهم ثابتة ولا تتحدث تلقائياً بالإدراجات الجديدة.</li>"
        "<li>الأسهم حديثة الإدراج (تاريخ أقصر من الفترة + 260 يوم) بتتحلل بتسخين أقل للمؤشرات.</li>"
        "</ul>"
    )))

    # 14 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(14, 'لو عايز تغيّر حاجة: كل إعداد مكانه فين', (
        "<p>كل الإعدادات في ملف " + _ltr('scanner_engine.py') + " إلا لو مكتوب غير كده:</p>"
        + _table(['عايز تغيّر', 'الإعداد في الكود', 'القيمة الحالية'], [
            ['طول الفترات، مدة الاحتفاظ، الهدف، الوقف', _ltr('_PERIOD_CFG'),
             ' · '.join(f"{k}: {w}/{h}/{p * 100:g}%/{s * 100:g}%" for k, (w, h, p, s) in _PERIOD_CFG.items())],
            ['أيام التسخين قبل الفترة', _ltr('_WARMUP_BARS'), f"{_WARMUP_BARS}"],
            ['نسبة جزء البحث', _ltr('_TRAIN_FRAC'), f"{_TRAIN_FRAC} ({train_pct}%)"],
            ['أقل عدد صفقات للنجاح في الاختبار', _ltr('_OOS_MIN_TRADES'), f"{_OOS_MIN_TRADES}"],
            ['حد \"weak evidence\"', _ltr('_OOS_LOW_SAMPLE'), f"{_OOS_LOW_SAMPLE}"],
            ['أقل فترة يمكن تقسيمها', _ltr('_MIN_SPLIT_SPAN') + ' + شرطين داخل ' + _ltr('_analyse_df()'),
             f"{_MIN_SPLIT_SPAN} · جزء البحث ≥ 40 يوم · جزء الاختبار ≥ 20 يوم (بعد طرح مدة الاحتفاظ)"],
            ['عدد الاستراتيجيات لكل حالة', _ltr('_TOP_PER_REGIME'), f"{_TOP_PER_REGIME}"],
            ['مدة اعتبار الإشارة \"حية\"', _ltr('LIVE_SIGNAL_MAX_AGE'), f"{LIVE_SIGNAL_MAX_AGE} (= {live_days} أيام)"],
            ['حدود أيام Days', _ltr('_DAYS_MIN / _DAYS_MAX'), f"{_DAYS_MIN} – {_DAYS_MAX}"],
            ['حدود حالات السوق (70% / 65% والحدود)', _ltr('_regime_arr()'), 'ADX 70% [15–35] · ATR 65% [0.8%–5%]'],
            ['شروط المؤشرات وإعداداتها', _ltr('_build_states()'), f"{n_ind} مؤشر"],
            ['أسماء المؤشرات المعروضة', _ltr('_IND_LABEL'), ''],
            ['مراحل البحث (أقل صفقات / أقل مؤشرات)', _ltr('cascade داخل _analyse_df()'), '(15,3) … (2,2)'],
            ['أقصى تشابه بين البدائل / عدد المؤشرات المرشحة', _ltr('_find_runner_ups()'), '60% · أقوى 12'],
            ['شرط الربحية', _ltr('_eval()'), 'Expectancy > 0 و Profit Factor > 1'],
            ['الدخول والأهداف والوقف في Live Signal Check', _ltr('_levels.py'), '1.5R / 2.5R …'],
            ['قائمة الأسهم', _ltr('market_data.py → get_all_tadawul_tickers()'), '283 سهم'],
            ['عدد الكروت المعروضة قبل Show all', _ltr('favorites_tab.py: _PREVIEW_COUNT / _LSC_PREVIEW'), '6 / 10'],
            ['مدة التخزين المؤقت للأسعار / للنتائج',
             _ltr('scanner_engine.py: ttl=1200') + ' · ' + _ltr('favorites_tab.py: 1200'),
             '20 دقيقة / 20 دقيقة'],
        ])
        + _note("أي تغيير في إعدادات " + _ltr('scanner_engine.py') + " بيظهر تلقائياً في هذا الدليل، "
                "لأن الأرقام فيه مقروءة من الكود مباشرة.", 'ok')
    )))

    # 15 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(15, 'قاموس المصطلحات', _table(['المصطلح', 'المعنى'], [
        ['Regime / حالة السوق', 'تصنيف اليوم: اتجاه (TREND)، عرضي (RANGE)، متذبذب (VOLATILE)'],
        ['Strategy / استراتيجية', 'مجموعة مؤشرات لازم تكون كلها إيجابية في نفس الوقت'],
        ['Signal / إشارة', 'أول يوم تتحقق فيه كل شروط الاستراتيجية'],
        ['Backtest', 'محاكاة الاستراتيجية على أسعار الماضي'],
        ['Fitted', f'نتائج جزء البحث (أول {train_pct}% من الفترة)'],
        ['Held back', f'نتائج جزء الاختبار (آخر {test_pct}%) اللي البحث ما شافهوش'],
        ['Validated', 'نجحت في جزء الاختبار'],
        ['Win Rate', 'نسبة الصفقات الرابحة'],
        ['Profit Factor', 'إجمالي الأرباح ÷ إجمالي الخسائر'],
        ['Expectancy', 'متوسط العائد المتوقع للصفقة الواحدة'],
        ['ATR', 'متوسط المدى اليومي للسعر (مقياس التذبذب)'],
        ['R', 'المسافة بين سعر الدخول ووقف الخسارة'],
        ['Risk:Reward', 'الربح المتوقع مقابل الخسارة المحتملة'],
        ['n=', 'عدد الصفقات'],
    ])))

    # 16 ───────────────────────────────────────────────────────────────────────
    _ex_e = 100.0
    S.append(_sec(16, 'مثال كامل: من الإشارة لحد نتيجة الصفقة', (
        "<p>خلينا نمشي مع استراتيجية واحدة خطوة بخطوة على فترة <b>Medium</b>. "
        "الأرقام هنا للتوضيح، لكن القواعد هي نفس اللي البرنامج بيستخدمها بالظبط.</p>"
        "<h4>1. الاستراتيجية</h4>"
        "<p><b>Vol RSI + Vol MA</b> لحالة <b>↔ Range</b>. يعني شرطين لازم يتحققوا في نفس اليوم: "
        "مؤشر RSI لتغيّر الحجم أعلى من 50، وحجم اليوم أعلى من متوسط حجم آخر 20 جلسة.</p>"
        "<h4>2. يوم الإشارة</h4>"
        "<p>أول يوم يتحقق فيه الشرطين مع بعض (اليوم اللي قبله كان واحد منهم على الأقل مش متحقق)، "
        "والسهم يومها في حالة Range. ده بيبان بعد إغلاق السوق. لو الشرطين فضلوا متحققين أيام بعدها، "
        "دي <b>مش</b> إشارات جديدة.</p>"
        "<h4>3. الدخول والخروج</h4>"
        f"<p>بنشتري على <b>افتتاح الجلسة اللي بعدها</b>. لو الافتتاح {_ex_e:.0f} ريال: "
        f"الهدف {_ex_e * (1 + m_pt):.0f} (+{m_pt * 100:g}%) والوقف {_ex_e * (1 - m_sl):.0f} (−{m_sl * 100:g}%). "
        f"بعد كده كل جلسة لمدة {m_hold} جلسة بنبص على أقل وأعلى سعر فيها:</p>"
        + _table(['اللي حصل', 'النتيجة'], [
            [f"أقل سعر نزل لـ{_ex_e * (1 - m_sl):.0f}", f"<b>خسارة</b> <span dir='ltr' style='unicode-bidi:isolate'>−{m_sl * 100:g}%</span>"
                                                     " — حتى لو نفس الجلسة لمست الهدف كمان، بنفترض الوقف ضرب الأول"],
            [f"أعلى سعر وصل لـ{_ex_e * (1 + m_pt):.0f}", f"<b>ربح</b> <span dir='ltr' style='unicode-bidi:isolate'>+{m_pt * 100:g}%</span>"],
            [f"عدّت {m_hold} جلسة من غير ده", f"بنبيع على إغلاق الجلسة رقم {m_hold}: ربح لو أعلى من "
                                             f"{_ex_e:.0f}، وخسارة لو مساوي أو أقل"],
        ])
        + "<h4>4. من صفقة لنتيجة</h4>"
        "<p>ده بيتكرر مع كل إشارة في الماضي. لو مثلاً طلع 12 صفقة: 6 كسبت +5% و6 خسرت −3%:</p>"
        + _table(['الرقم', 'الحساب', 'النتيجة'], [
            ['Win rate', _l('6 ÷ 12'), _l('50%')],
            ['Profit factor', _l('(6 × 5%) ÷ (6 × 3%) = 30 ÷ 18'), _l('1.7×')],
            ['Expectancy', _l('0.5 × 5% − 0.5 × 3%'), _l('+1.0%') + ' للصفقة'],
        ])
        + "<p>يعني رغم إن نص الصفقات بس كسبت، الاستراتيجية في المتوسط بتكسب 1% في كل صفقة.</p>"
        "<h4>5. هتلاقي ده فين على الشاشة</h4>"
        "<p>Win rate و Profit factor و Expectancy وعدد الصفقات (وتحته الكسبانة W والخسرانة L) هتلاقيهم "
        "في جزء الاستراتيجية في Scanned Strategies — زرار View strategy في كارت Live Signal Check بيوديك عليه، "
        "وجدول All live signals فيه نسبة النجاح وعدد الصفقات والكسبانة والخسرانة كمان. "
        "ولو ضغطت Show chart هتلاقي كل صفقة من الـ12 على الشارت، وفي جدول Past signals بسعر دخولها "
        "وخروجها وسبب الخروج (القسم 17).</p>"
    )))

    # 17 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(17, 'إزاي تتأكد بنفسك إن النتايج حقيقية', (
        "<p>اضغط <b>Show chart</b> تحت أي كارت في Live Signal Check. هتلاقي حاجتين:</p>"
        "<h4>الشارت</h4>"
        "<ul>"
        "<li><b>فوق:</b> شموع السعر، ومثلثات على كل صفقة اتحسبت في الكارت (أخضر = ربح، أحمر = خسارة)، "
        "ومثلث برتقالي SIGNAL على الإشارة الحالية، وخطوط الدخول والأهداف والوقف.</li>"
        "<li><b>تحت:</b> شريط لكل مؤشر في الاستراتيجية، متلون بلون نوعه في الأيام اللي شرطه متحقق فيها بس. "
        "بعدين شريط <b>All agree</b> (الأيام اللي كل الشروط متحققة فيها مع بعض)، وشريط حالة السوق "
        "(الأيام اللي السهم كان فيها في نفس الحالة).</li>"
        "</ul>"
        "<p>كل مثلث بيقع في يوم الإشارة، وده يوم <b>All agree بيبدأ فيه</b> (اليوم اللي قبله كان فاضي) "
        "وشريط حالة السوق متلون. الشراء نفسه بيكون على افتتاح الجلسة اللي بعده. "
        "تقدر تتأكد من ده بعينك لأي مثلث. الأشرطة دي متحسبة بنفس الكود اللي عمل الفحص بالظبط.</p>"
        "<h4>جدول Past signals</h4>"
        "<p>كل صف = صفقة واحدة: يوم الإشارة، سعر الدخول (افتتاح اليوم اللي بعده)، أعلى وأقل سعر وصله السهم "
        "وهي مفتوحة، سعر الخروج وسببه (<b>hit target</b> = لمس الهدف، <b>hit stop</b> = ضرب الوقف، "
        "<b>time exit</b> = خلصت المدة)، العائد، وعدد الجلسات. حط الماوس على أي صف تشوف القصة كاملة.</p>"
        + _note("الجدول والمثلثات بيتحسبوا بنفس الدالة اللي عملت الفحص (" + _ltr('simulate_trade') + "). "
                "اتأكدنا على كل الاستراتيجيات في فحص كامل: عدد الصفوف الكسبانة والخسرانة بيطابق Wins وLosses "
                "في الكارت 100%.", 'ok')
        + "<h4>اختبار سريع تعمله في 30 ثانية</h4>"
        "<ol><li>اختار أي صف في Past signals ولاحظ تاريخه.</li>"
        "<li>دوّر على اليوم ده في الشارت: لازم تلاقي مثلث، وتحته كل أشرطة المؤشرات متلونة، و<b>All agree</b> بادئ يومها.</li>"
        "<li>عدّ الصفوف اللي عليها Win واللي عليها Loss في عمود Outcome: لازم يساووا W و L تحت عدد الصفقات "
        "في جزء الاستراتيجية في Scanned Strategies (View strategy بيوديك عليه)، والرقم اللي جنب عنوان "
        "Past signals لازم يساوي Trades.</li></ol>"
        "<p>الاستراتيجيات Validated بتعرض صفقات آخر 30% بس (جزء الاختبار)، والـNot validated بتعرض صفقات "
        "أول 70%. علشان كده المثلثات ممكن تكون في جزء من الشارت بس.</p>"
    )))

    # 18 ───────────────────────────────────────────────────────────────────────
    # The plain-language version of section 8's test, for readers who only want
    # to know what the badge means and how far to trust it.
    _mw = _PERIOD_CFG['Medium'][0]
    _ms = int(_TRAIN_FRAC * _mw)
    S.append(_sec(18, '✓ Validated: يعني إيه، وليه أهم علامة في الصفحة', _bidi_fix(
        "<p><b>باختصار:</b> ✓ Validated يعني الاستراتيجية نجحت في <b>امتحان على أيام ما شافتهاش</b> "
        "وهي بتتختار. ده أقوى دليل في الصفحة إن الاستراتيجية مش صدفة.</p>"
        "<h4>المشكلة اللي بيحلها</h4>"
        "<p>تخيّل طالب حافظ إجابات امتحان السنة اللي فاتت. لو امتحنته في نفس الامتحان هيجيب 100%، "
        "بس ده ما يثبتش إنه فاهم. الماسح بيعمل حاجة شبه كده: بيجرّب مئات التركيبات من المؤشرات على تاريخ "
        "السهم ويختار أحسنها. ولما تجرّب مئات التركيبات على نفس الأيام، لازم واحدة تطلع \"ممتازة\" بالصدفة، "
        "كأنها حافظة الامتحان. واتجرّب ده فعلاً: على أسعار عشوائية مفيهاش أي نمط، الماسح طلّع "
        "نسبة نجاح 62.9%! يعني الرقم لوحده ممكن يكون وهم.</p>"
        "<h4>الحل: امتحان جديد</h4>"
        "<p>الفترة اللي بتتحلل بتتقسم جزئين بالترتيب الزمني:</p>"
        "<div class='sg-split'>"
        f"<div class='sg-split-a' style='flex:{train_pct}'>أول {train_pct}% · البحث (Fitted)"
        "<small>هنا بتتختار الاستراتيجية</small></div>"
        f"<div class='sg-split-b' style='flex:{test_pct}'>آخر {test_pct}% · الاختبار (Held back)"
        "<small>مخفي وقت البحث</small></div></div>"
        "<div class='sg-split-axis'><span>الأقدم</span><span>الأحدث</span></div>"
        "<ol>"
        f"<li>البرنامج بيدوّر على أحسن استراتيجية في <b>أول {train_pct}%</b> من الأيام (الأقدم) بس.</li>"
        f"<li><b>آخر {test_pct}%</b> (الأحدث) بيتخبّى عنه خالص وهو بيدوّر.</li>"
        f"<li>بعد ما يختار، بيجرّب الاستراتيجية <b>مرة واحدة</b> على الأيام المخبية، من غير أي تعديل.</li>"
        "</ol>"
        f"<p>مثال على فترة Medium: بيتحلل {_mw} جلسة (≈ سنة ونص). أول {_ms} جلسة للبحث، "
        f"وآخر {_mw - _ms} جلسة للاختبار.</p>"
        "<h4>النتيجة: واحدة من 3 علامات</h4>"
        + _table(['العلامة', 'بتطلع امتى', 'الأرقام اللي بتشوفها', 'تعمل إيه'], [
            ["<span class='sg-pill' style='background:#E9F7EE;color:#1B7A36'>✓ Validated</span>",
             f"في الأيام المخبية عملت <b>{_OOS_MIN_TRADES} صفقات أو أكتر</b> (في نفس حالة السوق) "
             "<b>وكسبت</b> (Expectancy أكبر من صفر و Profit factor أكبر من 1).",
             "أرقام الاختبار نفسه، وهي أصدق أرقام في الصفحة.",
             "<b>أقوى دليل.</b> ابدأ بيها."],
            ["<span class='sg-pill' style='background:#F2F2F5;color:#3F3F46'>Not validated</span>",
             f"كسبت في جزء البحث، بس في الأيام المخبية عملت <b>أقل من {_OOS_MIN_TRADES} صفقات</b>، "
             "وده عدد قليل ما يكفيش نحكم بيه (أو الفترة كلها أقصر من إنها تتقسم).",
             "أرقام جزء البحث، وغالباً أحلى من الحقيقة.",
             "<b>مش فاشلة، بس لسه ما اتثبتتش.</b> بص على عدد الصفقات و Expectancy قبل ما تثق فيها."],
            ["<span class='sg-pill' style='background:#FFEDEC;color:#C1121F'>✕ Failed test</span>",
             f"اتختبرت على {_OOS_MIN_TRADES} صفقات أو أكتر <b>وخسرت</b>.",
             "أرقام جزء البحث (اللي كانت حلوة)، مع إن الاختبار خسر.",
             "<b>ابعد عنها.</b>"],
        ])
        + "<h4>ليه أغلب الاستراتيجيات Not validated؟</h4>"
        f"<p>مش لأنها وحشة. السبب إن الـ{_OOS_MIN_TRADES} صفقات صعب يتجمعوا في جزء الاختبار:</p><ul>"
        f"<li>جزء الاختبار قصير ({_mw - _ms} جلسة في Medium).</li>"
        "<li>صفقات الاستراتيجية بتتحسب في <b>حالة سوق واحدة</b> بس: استراتيجية Volatile مثلاً بتتحسب لها "
        "الأيام المتذبذبة بس من جزء الاختبار.</li>"
        "<li>الإشارة محتاجة كل المؤشرات (من 2 لـ 5) يتفقوا في نفس اليوم، وده بيحصل قليل.</li></ul>"
        "<p>فطبيعي معظم الاستراتيجيات تعمل صفقات قليلة في الاختبار، ويطلع في كل فحص عدد قليل جداً "
        "✓ Validated (ممكن 15 أو 20 من أكتر من ألف استراتيجية). ده مش عيب: معناه إن العلامة دي صعبة، "
        "فقيمتها عالية.</p>"
        "<h4>مثال يوضح ليه العلامة مهمة</h4>"
        + _table(['السهم', 'العلامة', 'Win rate', 'الصفقات', 'الحكم'], [
            ['A', 'Not validated', '100%', '3 (من جزء البحث)',
             'رقم مبهر، بس من 3 صفقات بس ولسه ما اتختبرش. خلي بالك.'],
            ['B', '✓ Validated', '67%', '12 (من جزء الاختبار)',
             'أقل في الشكل، بس اتثبت على أيام جديدة، فهو <b>أوثق</b>.'],
        ])
        + "<p>الصفحة بترتب بنسبة النجاح، فـ A هيظهر قبل B. علشان كده العلامة مهمة: هي اللي بتقولك "
        "تثق في الرقم قد إيه.</p>"
        "<h4>تشوف الأرقام بنفسك فين</h4>"
        f"<p>في Scanned Strategies، تحت العلامة سطر زي <b>{_l('Recent test 75% · 12 trades')}</b> "
        f"(نتيجة الاختبار) أو <b>3 of {_OOS_MIN_TRADES} recent trades</b> (الاختبار عمل 3 صفقات بس من "
        f"الـ{_OOS_MIN_TRADES} المطلوبين). حط الماوس عليه تشوف الرقمين جنب بعض: Fitted (أول {train_pct}%) "
        f"و Held back (آخر {test_pct}%). لو نسبة النجاح نزلت كتير من الأول للتاني (مثلاً من 80% لـ 45%)، "
        "الاستراتيجية كانت حافظة الماضي.</p>"
        "<h4>فلتر Validation</h4>"
        + _table(['الاختيار', 'بيعرض إيه'], [
            ['<b>All</b>', 'كل الاستراتيجيات بعلاماتها (الافتراضي).'],
            ['<b>Validated</b>', 'اللي نجحت في الاختبار بس. هتلاقي أسهم أقل بكتير، وده طبيعي.'],
            ['<b>Not validated</b>', 'كل اللي ما اتثبتتش، ومنها ✕ Failed test.'],
        ])
        + "<p>الفلتر بيشتغل على الصفحة كلها: كروت Live Signal Check، والجدول، وملف الإكسل، "
        "و Scanned Strategies.</p>"
        + _note("<b>الترتيب كدليل، من الأقوى للأضعف:</b> ✓ Validated، بعدها Not validated بـ 10 صفقات أو أكتر "
                "و Expectancy كويس، وفي الآخر Not validated بصفقات قليلة. وما تدخلش على ✕ Failed test.", 'ok')
        + _note("حتى ✓ Validated مش ضمان: نجحت على فترة واحدة جديدة، والسوق ممكن يتغير. "
                "الصفحة أداة فرز، مش توصية.", 'warn')
    )))

    # 19 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(19, 'Great و Good في عمود Rating: بيتحددوا إزاي، وليه', _bidi_fix(
        "<p><b>باختصار:</b> Great و Good بيقولولك الصفقة شكلها مربح قد إيه: المكسب لحد أول هدف "
        "أكبر من الخسارة لو الوقف ضرب بكام مرة.</p>"
        "<h4>بيتحسب إزاي</h4>"
        "<p><b>Risk : Reward</b> = المكسب لحد Target 1 ÷ الخسارة لحد الوقف.</p>"
        + _table(['', 'مثال: Nayifat (4081) في جدول All live signals يوم 28 أكتوبر 2026'], [
            ['الدخول', '8.62'],
            ['الوقف', '8.27، يعني خسارة <b>4.1%</b>'],
            ['Target 1', '9.57، يعني مكسب <b>11.0%</b>'],
            ['Risk : Reward', f"{_l('11.0 ÷ 4.1 = 2.7')}، فبيظهر <b>1 : 2.7</b>"],
            ['Rating', '<b>Great</b> (لأنه 2 أو أكتر)'],
        ])
        + "<p><b>القاعدة:</b> 2 أو أكتر = <b>Great</b> · من 1.5 لحد أقل من 2 = <b>Good</b> · "
        "أقل من 1.5 = <b>Weak</b>.</p>"
        "<h4>المنطق: محتاج تكسب كام صفقة علشان ما تخسرش؟</h4>"
        + _table(['Risk : Reward', 'Rating', 'نسبة النجاح اللي تكفيك علشان ما تخسرش'], [
            [_l('1 : 1'), 'Weak', '50% (صفقة صح من كل 2)'],
            [_l('1 : 1.5'), '<b>Good</b>', '40%'],
            [_l('1 : 2'), '<b>Great</b>', '33% (صفقة صح من كل 3)'],
            [_l('1 : 3'), '<b>Great</b>', '25% (صفقة صح من كل 4)'],
        ])
        + f"<p>المعادلة: النسبة اللي تكفيك = {_l('1 ÷ (1 + Risk:Reward)')}. يعني كل ما المكسب أبعد من "
        "الخسارة، كل ما تقدر تغلط أكتر وتفضل كسبان: عند 1 : 2 ممكن تخسر صفقتين من كل 3 وتطلع على "
        "التعادل. علشان كده 2 هو حد Great.</p>"
        "<h4>ليه هتلاقي Good و Great بس تقريباً؟</h4>"
        "<p>الأهداف بتتحط على مقاومات حقيقية في الشارت (قمم سابقة، متوسطات، فيبوناتشي، أرقام صحيحة)، "
        "و Target 1 بيتختار على <b>أقرب مقاومة بعيدة مرة ونص على الأقل</b> من مسافة الوقف. "
        "فنادراً ما تقل عن 1 : 1.5. الفرق بينهم:</p><ul>"
        "<li><b>Great:</b> أقرب مقاومة بعيدة — الطريق لحد الهدف ضعف مسافة الوقف أو أكتر.</li>"
        "<li><b>Good:</b> فيه مقاومة أقرب، ممكن السعر يقف عندها بدري.</li></ul>"
        + _note("التقييم ده عن <b>شكل الصفقة</b> (المسافات)، مش عن نجاحها في الماضي: الدخول والوقف "
                "والأهداف جايين من شكل الشارت وما اتختبروش تاريخياً، و Win rate في الجدول اتحسب بقواعد "
                f"ثابتة (في Medium: {_pm(m_pt, m_sl)}). استخدم Rating مع Win rate وعدد الصفقات "
                "و ✓ Validated، مش لوحده.", 'warn')
    )))

    # 20 ───────────────────────────────────────────────────────────────────────
    S.append(_sec(20, 'الصفقات الكسبانة والخسرانة، و Strategy details', _bidi_fix(
        "<p><b>باختصار:</b> تحت أرقام كل استراتيجية فيه خط أخضر وأحمر: الأخضر = الصفقات اللي كسبت، "
        "والأحمر = اللي خسرت، وجنب كل لون عدد الصفقات ومتوسط نسبتها. وتحته "
        "<b>Strategy details ›</b>: دوس عليه يفتح كل حاجة عن الاستراتيجية.</p>"
        "<h4>الخط الأخضر والأحمر</h4>"
        + _table(['اللي مكتوب', 'معناه'], [
            [_l('13 winning trades · avg +8.0%'), '13 صفقة كسبت، والواحدة كسبت في المتوسط 8.0%'],
            [_l('2 losing trades · avg −5.0%'), 'صفقتين خسروا، والواحدة خسرت في المتوسط 5.0%'],
            ['طول الأخضر والأحمر', 'نسبة كل نوع من إجمالي الصفقات — نفس Win rate بس مرسومة'],
        ])
        + "<h4>جوه Strategy details</h4>"
        + _table(['الجزء', 'معناه'], [
            ['Buy when all … are true', 'شرط كل مؤشر بالعربي (نفس جدول المؤشرات في القسم 4). لازم كلهم '
                                        'يتحققوا في نفس اليوم، في يوم من نفس حالة السوق، والشراء على '
                                        'افتتاح اليوم اللي بعده.'],
            ['Sell at whichever comes first', 'البيع عند الهدف أو الوقف أو إغلاق آخر يوم في المدة — أيهم ييجي '
                                              'الأول. بيختلفوا حسب الفترة اللي اخترتها (القسم 2).'],
            ['How the trades ended', 'كام صفقة وصلت للهدف، وكام ضربت الوقف، وكام اتقفلت لما المدة خلصت، '
                                     'ومتوسط عدد الأيام في الصفقة.'],
            ['Every trade', 'كل صفقة لوحدها: يوم الشراء (Bought)، النتيجة (Result)، اتقفلت إزاي (Ended by)، '
                            'وعدد أيامها (Days). الأحدث فوق.'],
            ['Validation', 'نسبة النجاح في جزء البحث جنب نسبتها في جزء الاختبار (القسم 8).'],
        ])
        + "<h4>مثال</h4>"
        f"<p>في فترة Long الهدف {_l(f'+{l_pt * 100:g}%')} والوقف {_l(f'−{l_sl * 100:g}%')} والمدة "
        f"{l_hold} يوم. استراتيجية مكتوب تحتها <b>{_l('13 winning trades · avg +8.0%')}</b> و "
        "<b>0 losing trades</b>: يعني الـ13 صفقة كلهم وصلوا للهدف، وعلشان كده Expectancy = +8.0% "
        "و Profit factor = 9.9 (مفيش خسارة خالص، و 9.9 هو أعلى رقم).</p>"
        f"<p>ولو مكتوب <b>{_l('5 winning trades · avg +6.2%')}</b> و "
        f"<b>{_l('6 losing trades · avg −4.1%')}</b>: "
        f"Expectancy = {_l('(5 × 6.2 − 6 × 4.1) ÷ 11 = +0.6%')} للصفقة. يعني رغم إن الخسرانة أكتر، "
        "الاستراتيجية كسبانة لأن مكسب الكسبانة أكبر من خسارة الخسرانة.</p>"
        + _note("ليه متوسط المكسب ممكن يطلع أقل من الهدف؟ لأن فيه صفقات بتتقفل في آخر يوم من المدة "
                "بمكسب صغير قبل ما توصل للهدف. وبنفس الشكل متوسط الخسارة ممكن يطلع أقل من الوقف.", 'info')
        + _note("الصفقات اللي في الليستة هي بالظبط الصفقات اللي الأرقام اتحسبت منها: لو الاستراتيجية "
                "✓ Validated فهي صفقات جزء الاختبار (آخر 30%)، ولو لأ فهي صفقات جزء البحث (أول 70%). "
                "وكلها من الماضي ومن غير عمولات (القسم 6)، فمش ضمان للي جاي.", 'warn')
    )))

    def _step(n, t):
        return f"<div class='sg-step'><div class='sg-step-n'>{n}</div><div class='sg-step-t'>{t}</div></div>"

    # Reader-facing sections first, technical internals after. Sections are
    # built in their logical order (1..18) above, then re-ordered and
    # renumbered here; cross references ("القسم N") are remapped to match.
    import re as _re
    _reading = [2, 3, 16, 10, 9, 20, 18, 19, 17, 15]
    _tech = [1, 4, 5, 6, 7, 8, 11, 12, 13, 14]
    _new_no = {old: new for new, old in enumerate(_reading + _tech, start=1)}

    intro = (
        "<div class='sg-intro'>"
        "<h3>إزاي الصفحة دي بتشتغل</h3>"
        "<p class='sg-lead'>الصفحة بتاخد كل سهم من الـ283 سهم في السوق السعودي، وتجرّب عليه مئات "
        "التركيبات من 50 مؤشر فني على أسعاره في الماضي، وتشوف أنهي تركيبة كانت بتكسب — "
        "لكل حالة سوق لوحدها (اتجاه، عرضي، متذبذب). بعدين بتختبر التركيبة دي على آخر جزء من التاريخ "
        "ما اتبنتش عليه، وتقولك أي سهم فيه إشارة شراء جديدة دلوقتي.</p>"
        "<p>الفكرة إن نفس المؤشر ممكن ينفع في سهم وما ينفعش في سهم تاني، وممكن ينفع والسوق عرضي "
        "وما ينفعش والسوق في اتجاه. فبدل قاعدة واحدة لكل الأسهم، كل سهم بياخد القاعدة اللي "
        "اشتغلت عليه هو بالذات — ومعاها كل الأرقام اللي تخليك تحكم بنفسك تثق فيها قد إيه.</p>"
        "<div class='sg-steps'>"
        + _step(1, 'اختار الفترة: Short أو Medium أو Long أو Days')
        + _step(2, 'اضغط <b>Run Scan</b> واستنى التحليل يخلص')
        + _step(3, 'راجع الفرص في <b>Live Signal Check</b>، وابدأ باللي عليها ✓ Validated '
                   f'(القسم {_new_no[18]} بيشرح ليه)')
        + _step(4, 'اضغط <b>View strategy</b> على أي كارت تشوف تفاصيل استراتيجيته في Scanned Strategies')
        + "</div>"
        + _note("مش لازم تدوّر هنا: في الصفحة، دوس على أي <b>؟</b> أو أي كلمة تحتها خط منقّط "
                "(أو على علامة ✓ Validated)، والدليل هيتفتح على القسم اللي بيشرحها على طول.", 'info')
        + "</div>"
    )

    def _renum(html: str) -> str:
        html = _re.sub(r"<span class='sg-n'>(\d+)</span>",
                       lambda m: f"<span class='sg-n'>{_new_no[int(m.group(1))]}</span>", html)
        return _re.sub(r"القسم (\d+)", lambda m: f"القسم {_new_no.get(int(m.group(1)), m.group(1))}", html)

    def _group(title: str, sub: str, nums: list) -> str:
        return (f"<div class='sg-gh'><span>{title}</span><small>{sub}</small></div>"
                "<div class='sg-list'>" + ''.join(_renum(S[n - 1]) for n in nums) + "</div>")

    return (_CSS + "<div class='sg notranslate' translate='no' lang='ar'>" + intro
            + _group('قراءة الصفحة', 'إيه اللي بتشوفه على الشاشة ومعناه', _reading)
            + _bidi_fix(_ideas_html())
            + _group('التفاصيل الفنية', 'إزاي كل حاجة بتتحسب — للي عايز يفهم أعمق أو يغيّر إعداد', _tech)
            + "</div>")


def _ideas_html() -> str:
    """«الفكرة والمنطق»: why each part of the scanner exists, its logic, how it is
    built and its conditions. Lettered sections so they never clash with the
    numbered ones."""
    from scanner_engine import (_PERIOD_CFG, _TRAIN_FRAC, _OOS_MIN_TRADES, _OOS_LOW_SAMPLE,
                                _TOP_PER_REGIME, LIVE_SIGNAL_MAX_AGE, _WARMUP_BARS)
    tr = round(_TRAIN_FRAC * 100)
    live_days = LIVE_SIGNAL_MAX_AGE + 1
    per = ' · '.join(f"{k}: {w} جلسة، احتفاظ {h} يوم، هدف +{pt * 100:g}% ووقف −{sl * 100:g}%"
                     for k, (w, h, pt, sl) in _PERIOD_CFG.items())
    ideas = [
        ("ليه بندوّر لكل سهم على قاعدته هو", _idea(
            "كل سهم ليه «شخصية»: سهم بنك تقيل بيتحرك بهدوء ومع الاتجاه، وسهم صغير بيرتد بعنف من التشبع. "
            "قاعدة واحدة لكل السوق بتنجح في نوع وتفشل في التاني.",
            "بدل ما نفترض إن مؤشر معين شغال، بنجرّب على تاريخ السهم نفسه مئات التركيبات من 50 مؤشر ونشوف "
            "أنهي واحدة كانت فعلاً بتكسب فيه.",
            "<code>scanner_engine._analyse_df</code> لكل سهم، والنتيجة متخزنة في الجلسة.",
            "التركيبة لازم تكون كسبانة: متوسط ربح الصفقة (expectancy) أكبر من صفر <b>و</b> Profit factor أكبر من 1، "
            "وإلا مش بتتعرض خالص.")),
        ("ليه أحسن استراتيجية لكل حالة سوق لوحدها", _idea(
            "المؤشر اللي بيكسب والسوق في اتجاه (متوسطات، اختراقات) غالبًا بيخسر والسوق عرضي، والعكس صحيح "
            "لمؤشرات التشبع.",
            "بنقسم تاريخ السهم لأيام TREND وRANGE وVOLATILE، ونقيّم كل تركيبة على أيام كل حالة لوحدها. "
            "وبعدين النهارده بنبص على حالة السوق الحالية ونستخدم استراتيجيتها هي.",
            "الحالة بتتحسب لكل يوم، والصفقات بتتحسب لحالتها يوم الإشارة.",
            f"لكل حالة لحد {_TOP_PER_REGIME} استراتيجيات: الأحسن + بدائل مختلفة فعلاً "
            "(مش أكتر من 60% من صفقاتها مشتركة مع اللي قبلها)، عشان البديل يبقى دليل مستقل مش نسخة.")),
        ("ليه بنقسم التاريخ: جزء للبحث وجزء للاختبار", _idea(
            "لما تجرب مئات التركيبات لازم واحدة تطلع ممتازة بالصدفة. ده أخطر فخ في الاختبار التاريخي.",
            f"بندوّر على الأحسن في أول {tr}% من الفترة بس، وبعدين نختبرها على آخر {100 - tr}% اللي ماشافتهاش. "
            "لو كسبت هناك كمان يبقى فيه سبب حقيقي مش صدفة.",
            "<code>_TRAIN_FRAC</code> و<code>_merge_oos</code> في <code>scanner_engine.py</code>.",
            f"✓ Validated = كسبانة في جزء الاختبار وبعدد صفقات ≥ {_OOS_MIN_TRADES}. أقل من {_OOS_LOW_SAMPLE} صفقة "
            "بيتكتب إن العينة صغيرة. اللي مااتأكدتش بتتعرض بعلامة واضحة بدل ما تتخفي — طلب صاحب التطبيق، "
            "عشان تشوف كل حاجة وتحكم بنفسك؛ ولو عايز الـValidated بس فيه فلتر Validation.")),
        ("ليه البحث بيختار بمتوسط الربح، والصفحة بترتب بنسبة النجاح", _idea(
            "استراتيجية بتكسب 90% من المرات +0.5% وتخسر 10% −5% بتخسر فلوس رغم نسبتها العالية — "
            "علشان كده البحث نفسه ما بيعتمدش على نسبة النجاح.",
            "جوه البحث، التركيبة الأحسن بتتختار بمتوسط ربح الصفقة مضروب في جذر عدد الصفقات، عشان النتيجة اللي "
            "على صفقات أكتر تبقى أوثق. بعد كده الصفحة بتعرض النتايج مترتبة بنسبة النجاح لأنها الأسهل في القراءة "
            "(طلب صاحب التطبيق)، وكل استراتيجية معروضة كسبانة أصلاً.",
            "<code>_eval</code>: الاختيار = expectancy × √(عدد الصفقات). ترتيب الصفحة: <code>_wr_key</code> "
            "في <code>favorites_tab.py</code>.",
            "لما تقارن بنسبة النجاح بص على عدد الصفقات (فلتر Trades) وعلامة Validated: 100% من 3 صفقات "
            "أضعف من 70% من 15.")),
        ("ليه المحاكاة متحفظة", _idea(
            "اختبار متفائل بيطلّع أرقام أحلى من اللي هتعيشه فعلاً.",
            "الدخول على <b>افتتاح اليوم التالي</b> للإشارة (لأنك بتشوف الإشارة بعد الإغلاق)، ولو الوقف والهدف "
            "اتلمسوا في نفس اليوم بنفترض إن الوقف اتضرب الأول (أسوأ حالة)، والخروج عند المستوى بالظبط.",
            "<code>scanner_engine.simulate_trade</code> — ونفس الدالة بترسم صفقات الرسم البياني، فاللي على الرسم هو "
            "نفس اللي اتحسب.",
            "لو المدة خلصت من غير ما يلمس حاجة، بنخرج على إغلاق آخر يوم.")),
        ("ليه 3 فترات بأهداف ووقف مختلفة", _idea(
            "اللي بيتداول أيام غير اللي بيستثمر شهور: الحركة المتوقعة والصبر والمخاطرة مختلفين.",
            "كل ما المدة أطول، الحركة المتوقعة أكبر، فالهدف والوقف أبعد وفترة البحث أطول. نسبة الهدف للوقف حوالي "
            "2 لـ 1 في القصير وأقل شوية في الطويل.",
            f"<code>_PERIOD_CFG</code>: {per}.",
            f"قبل أي فترة بنحسب المؤشرات على حوالي {_WARMUP_BARS} جلسة زيادة (سنة) عشان المتوسطات الطويلة تبقى صح.")),
        ("ليه الإشارة الحية لازم تكون عمرها 3 أيام بالكتير", _idea(
            "إشارة من أسبوعين غالبًا الحركة بتاعتها حصلت خلاص، والدخول دلوقتي مطاردة.",
            "بنعرض في Live Signal Check بس الأسهم اللي استراتيجيتها (لحالة السوق الحالية) بدأت إشارتها "
            f"في آخر {live_days} جلسات.",
            "<code>LIVE_SIGNAL_MAX_AGE</code> و<code>_signal_age</code> في <code>scanner_engine.py</code>.",
            "الإشارة لازم تكون من استراتيجيات القسم الأول بالظبط ولنفس حالة السوق اللي إحنا فيها النهارده.")),
    ]
    secs = [_sec(_AR_LETTERS_SG[i], t, b) for i, (t, b) in enumerate(ideas)]
    return ("<div class='sg-gh'><span>الفكرة والمنطق</span>"
            "<small>ليه كل جزء اتعمل كده، المنطق وراه، اتطبق إزاي، وبأي شروط</small></div>"
            "<div class='sg-list'>" + ''.join(secs) + "</div>")


_AR_LETTERS_SG = "أبجدهوزحطيكلمن"


# Clicking anything on the page that carries data-sg='<section id>' (the "؟"
# marks, the Validated badges) opens this guide on that section. Installed once
# into the page itself, so it keeps working across Streamlit reruns.
_HELP_LINKS_JS = """function (w, d) {
  if (w.__sgHelp) return;
  w.__sgHelp = true;
  d.addEventListener('click', function (e) {
    var q = e.target.closest && e.target.closest('[data-sg]');
    if (!q) return;
    e.preventDefault();
    e.stopPropagation();
    var exp = d.querySelector('.st-key-sg_wrap details'), opened = false;
    if (exp && !exp.open) {
      var s = exp.querySelector('summary');
      if (s) { s.click(); opened = true; }
    }
    var id = 'sg-sec-' + q.getAttribute('data-sg'), n = 0;
    (function go() {
      var sec = d.getElementById(id);
      if (!sec) { if (n++ < 40) w.setTimeout(go, 100); return; }
      sec.open = true;
      var jump = function () { sec.scrollIntoView({behavior: 'smooth', block: 'start'}); };
      // Scroll once the guide has opened, and again after it has finished
      // laying out (opening it shifts everything below).
      w.setTimeout(jump, opened ? 350 : 0);
      w.setTimeout(jump, opened ? 1200 : 700);
      sec.classList.add('sg-flash');
      w.setTimeout(function () { sec.classList.remove('sg-flash'); }, 2200);
    })();
  }, true);
}"""


def _install_help_links() -> None:
    """Put the _HELP_LINKS_JS click handler into the page. st.markdown does not
    run scripts, so a zero-height component iframe adds it to its parent page
    (and, if the page refuses inline scripts, attaches it from the iframe)."""
    import json
    import streamlit.components.v1 as components
    components.html(
        "<script>(function () {"
        " var w = window.parent, d = w.document;"
        " if (w.__sgHelp) return;"
        f" var install = {_HELP_LINKS_JS};"
        " try {"
        "  var s = d.createElement('script');"
        f"  s.textContent = '(' + {json.dumps(_HELP_LINKS_JS)} + ')(window, document);';"
        "  d.head.appendChild(s);"
        " } catch (err) {}"
        " if (!w.__sgHelp) install(w, d);"
        "})();</script>",
        height=0)


def render_scanner_guide() -> None:
    """Collapsible Arabic guide shown at the top of the Strategy Scanner page."""
    # The guide CSS (incl. the RTL rule for this expander's title) has to be on
    # the page before the expander renders, so it is emitted separately.
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.container(key="sg_wrap"):
        with st.expander("📘  دليل الصفحة بالعربي",
                         expanded=bool(st.session_state.get('_sg_open', False))):
            _html = _build_html()
            if st.session_state.get('_sg_open_sections'):   # screenshot/test hook
                _html = _re_bidi.sub(r"<details class='sg-d'( id='[^']*')?>",
                                     r"<details class='sg-d'\1 open>", _html)
            st.markdown(_html, unsafe_allow_html=True)
    _install_help_links()
