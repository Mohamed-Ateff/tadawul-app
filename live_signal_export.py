"""Excel export of the Strategy Scanner's Live Signal Check table.

build_live_signal_xlsx() turns the rows shown in the page's table into a styled
.xlsx: navy title bar, blue header with filter arrows, banded rows, green/red
percentages, frozen header and first column, ready to print on A4 landscape.
"""
from __future__ import annotations

import io

# (header, row key, column width, kind) — kinds pick the cell format below.
COLUMNS = [
    ('Stock Name',            'name',     24, 'name'),
    ('Symbol',                'symbol',    9, 'text'),
    ('Analysis Date',         'date',     17, 'text'),
    ('Displayed Price (SAR)', 'price',    13, 'price'),
    ('Entry Price (SAR)',     'entry',    13, 'price'),
    ('Stop Loss Price (SAR)', 'stop',     14, 'price'),
    ('Stop Loss %',           'sl_pct',   11, 'loss'),
    ('Target 1 Price (SAR)',  't1',       13, 'price'),
    ('Target 1 %',            't1_pct',   11, 'gain'),
    ('Target 2 Price (SAR)',  't2',       13, 'price'),
    ('Target 2 %',            't2_pct',   11, 'gain'),
    ('Risk : Reward',         'rr',       12, 'rr'),
    ('Risk : Reward Rating',  'rr_label', 15, 'rating'),
    ('Win Rate (%)',          'win_rate', 12, 'winrate'),
    ('Trades',                'trades',    9, 'int'),
]

NAVY, BLUE, BAND, GRID = '#0B2545', '#1F4E79', '#DDEBF7', '#C9D6E3'
INK, MUTED = '#111114', '#4A5563'
GREEN, ORANGE, RED = '#1B7A36', '#A34800', '#C1121F'
RATING_COLOR = {'Great': GREEN, 'Good': ORANGE, 'Weak': RED}
PCT = '"+"0.0%;"−"0.0%'          # signed, with a real minus sign


def build_live_signal_xlsx(rows: list[dict], title: str, subtitle: str) -> bytes:
    """rows: dicts with the COLUMNS keys; prices in SAR, the three % columns and
    win_rate in percent (4.1 = 4.1%), sl_pct as a positive distance."""
    import xlsxwriter

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {'in_memory': True})
    wb.set_properties({'title': title, 'subject': 'Live Signal Check',
                       'author': 'Strategy Scanner', 'comments': subtitle})
    ws = wb.add_worksheet('Live Signal Check')
    base = {'font_name': 'Calibri', 'font_size': 10, 'valign': 'vcenter'}
    n_col = len(COLUMNS)

    def fmt(**kw):
        return wb.add_format({**base, **kw})

    title_f = fmt(bold=True, font_size=16, font_color='#FFFFFF', bg_color=NAVY, indent=1)
    sub_f = fmt(font_size=9, font_color=MUTED, bg_color='#EEF3F8', indent=1,
                bottom=1, bottom_color=GRID)
    head_f = fmt(bold=True, font_color='#FFFFFF', bg_color=BLUE, align='center',
                 text_wrap=True, border=1, border_color='#FFFFFF')
    note_f = fmt(font_size=9, italic=True, font_color=MUTED, text_wrap=True, valign='top')

    cell_cache: dict = {}

    def cell(kind, band, rating=''):
        """Body format for a column kind on a white (band=0) or blue (band=1) row."""
        key = (kind, band, rating)
        if key not in cell_cache:
            kw = {'border': 1, 'border_color': GRID, 'align': 'center', 'font_color': INK,
                  'bg_color': BAND if band else '#FFFFFF'}
            if kind == 'name':
                kw.update(bold=True, align='left', indent=1)
            elif kind == 'price':
                kw.update(num_format='#,##0.00')
            elif kind == 'loss':
                kw.update(num_format=PCT, font_color=RED)
            elif kind == 'gain':
                kw.update(num_format=PCT, font_color=GREEN)
            elif kind == 'rr':
                kw.update(num_format='"1 : "0.0')
            elif kind == 'rating':
                kw.update(bold=True, font_color=RATING_COLOR.get(rating, INK))
            elif kind == 'winrate':
                kw.update(bold=True, num_format='0%')
            elif kind == 'int':
                kw.update(num_format='0')
            cell_cache[key] = fmt(**kw)
        return cell_cache[key]

    # Title, subtitle, a thin spacer, then the header row.
    ws.set_row(0, 30)
    ws.merge_range(0, 0, 0, n_col - 1, title, title_f)
    ws.set_row(1, 20)
    ws.merge_range(1, 0, 1, n_col - 1, subtitle, sub_f)
    ws.set_row(2, 6)
    ws.set_row(3, 34)
    for c, (head, _key, width, _kind) in enumerate(COLUMNS):
        ws.set_column(c, c, width)
        ws.write(3, c, head, head_f)

    first = 4
    for i, r in enumerate(rows):
        row, band = first + i, i % 2
        ws.set_row(row, 20)
        for c, (_head, key, _width, kind) in enumerate(COLUMNS):
            v = r.get(key)
            f = cell(kind, band, r.get('rr_label', '') if kind == 'rating' else '')
            if v is None or v == '':
                ws.write_blank(row, c, None, f)
            elif kind == 'loss':
                ws.write_number(row, c, -abs(float(v)) / 100, f)
            elif kind in ('gain', 'winrate'):
                ws.write_number(row, c, float(v) / 100, f)
            elif kind in ('price', 'rr', 'int'):
                ws.write_number(row, c, float(v), f)
            else:
                ws.write_string(row, c, str(v), f)
    last = first + len(rows) - 1

    if rows:
        ws.autofilter(3, 0, last, n_col - 1)
        wr_col = [k for _h, k, _w, _t in COLUMNS].index('win_rate')
        ws.conditional_format(first, wr_col, last, wr_col, {
            'type': 'data_bar', 'bar_color': '#9DC3E6', 'bar_solid': True,
            'min_type': 'num', 'min_value': 0, 'max_type': 'num', 'max_value': 1})
    else:
        last = first
        ws.set_row(first, 24)
        ws.merge_range(first, 0, first, n_col - 1,
                       'No live signal matches the filters.', cell('text', 0))

    ws.set_row(last + 2, 30)
    ws.merge_range(last + 2, 0, last + 2, n_col - 1,
                   'Win Rate (%) is the win rate of the leading live strategy; Trades is how many '
                   'past signals it is based on (fewer than 10 is weak evidence). Entry, stop and '
                   'targets come from the stock\'s price structure. Prices in SAR. '
                   'Not investment advice.', note_f)

    ws.freeze_panes(first, 1)
    ws.hide_gridlines(2)
    ws.set_tab_color(BLUE)
    ws.set_landscape()
    ws.set_paper(9)                       # A4
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(0, 3)
    ws.set_margins(left=0.3, right=0.3, top=0.4, bottom=0.5)
    ws.set_footer('&L&8Strategy Scanner · Live Signal Check&R&8Page &P of &N')
    wb.close()
    return buf.getvalue()
