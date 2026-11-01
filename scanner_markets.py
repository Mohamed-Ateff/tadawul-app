"""The markets the Strategy Scanner can scan: Saudi stocks, commodities, Egyptian stocks.

Everything that differs between markets lives here: the symbols, the currency
or unit of each price, how a symbol is shown, and the wording of the page. The
scanning engine itself is the same for all of them.

Which symbols are listed was measured on Yahoo Finance (2026-11-01, 5 years of
daily bars), not assumed:

  * Commodities: front-month futures. Left out because their Yahoo bars carry no
    real trading: PL=F platinum, PA=F palladium, ALI=F aluminum (more than 60% of
    the bars have High = Low, about half have no volume). Spot symbols (XAU=X ...)
    return nothing.
  * Egypt: plain tickers such as COMI.CA. The ISIN-style symbols Yahoo's screener
    lists (EGS...CA) have a single bar and no history, so they can't be used. Also
    left out: symbols where 30%+ of the last 250 bars have High = Low (ORAS, SAIB,
    DCCC, DEIN, MEGM, MISR, MMAT, GPPL, SPHT, SEIGA, BIDI, EOSB, TRTO) and MKIT,
    whose last bar is from August 2026. QNBE, TAQA, EKHO and VALU have no data at all.
"""
from __future__ import annotations

# (symbol: (name, unit of its Yahoo quote, Arabic name for the search box))
# USX on Yahoo = US cents, hence the ¢ units.
_COMMODITIES = {
    'GC=F': ('Gold', 'USD/oz', 'ذهب دهب'),
    'SI=F': ('Silver', 'USD/oz', 'فضة فضه'),
    'HG=F': ('Copper', 'USD/lb', 'نحاس'),
    'CL=F': ('Crude Oil WTI', 'USD/barrel', 'نفط خام بترول'),
    'BZ=F': ('Brent Crude', 'USD/barrel', 'برنت نفط خام بترول'),
    'NG=F': ('Natural Gas', 'USD/MMBtu', 'غاز طبيعي'),
    'HO=F': ('Heating Oil', 'USD/gallon', 'زيت تدفئة'),
    'RB=F': ('Gasoline', 'USD/gallon', 'بنزين'),
    'ZW=F': ('Wheat', 'US¢/bushel', 'قمح'),
    'ZC=F': ('Corn', 'US¢/bushel', 'ذرة'),
    'ZS=F': ('Soybeans', 'US¢/bushel', 'فول صويا'),
    'KC=F': ('Coffee', 'US¢/lb', 'قهوة'),
    'SB=F': ('Sugar', 'US¢/lb', 'سكر'),
    'CC=F': ('Cocoa', 'USD/ton', 'كاكاو'),
    'CT=F': ('Cotton', 'US¢/lb', 'قطن'),
    'LE=F': ('Live Cattle', 'US¢/lb', 'ماشية'),
}

# Yahoo quotes these EGX lines in US dollars; every other Egyptian stock is in EGP.
_EGX_USD = ('CFGH.CA', 'EGBE.CA', 'FAITA.CA', 'MOIL.CA', 'NAHO.CA')

_EGX = {
    'AALR.CA': 'General Co. for Land Reclamation', 'ABUK.CA': 'Abu Qir Fertilizers',
    'ACAMD.CA': 'Arab Co. for Asset Management', 'ACGC.CA': 'Arabia Cotton Ginning',
    'ADCI.CA': 'Arab Drug Company', 'ADIB.CA': 'Abu Dhabi Islamic Bank Egypt',
    'ADPC.CA': 'Arab Dairy Products', 'AFDI.CA': 'Al Ahly Development & Investment',
    'AFMC.CA': 'Alexandria Flour Mills', 'AIFI.CA': 'Atlas Investment & Food Industries',
    'AJWA.CA': 'Ajwa Food Industries Egypt', 'ALCN.CA': 'Alexandria Container & Cargo',
    'ALUM.CA': 'Arab Aluminum', 'AMER.CA': 'Amer Group Holding',
    'AMES.CA': 'Alexandria New Medical Center', 'AMIA.CA': 'Arab Moltaqa Investments',
    'AMOC.CA': 'Alexandria Mineral Oils', 'AMPI.CA': 'Al Moasher',
    'APSW.CA': 'Unirab Polvara Spinning & Weaving', 'ARAB.CA': 'Arab Developers Holding',
    'ARCC.CA': 'Arabian Cement', 'AREH.CA': 'Real Estate Egyptian Consortium',
    'ASCM.CA': 'ASEC Mining (ASCOM)', 'ASPI.CA': 'Aspire Capital Holding',
    'ATLC.CA': 'Al Tawfeek Leasing', 'ATQA.CA': 'Misr National Steel (Ataqa)',
    'AXPH.CA': 'Alexandria Pharmaceuticals', 'BIGP.CA': 'El-Barbary Investment Group',
    'BINV.CA': 'B Investments Holding', 'BIOC.CA': 'GlaxoSmithKline Egypt',
    'BTFH.CA': 'Beltone Holding', 'CAED.CA': 'Cairo Educational Services',
    'CANA.CA': 'Suez Canal Bank', 'CCAP.CA': 'Qalaa Holdings',
    'CCRS.CA': 'Gulf Canadian Real Estate', 'CEFM.CA': 'Middle Egypt Flour Mills',
    'CERA.CA': 'Arab Ceramic', 'CFGH.CA': 'Concrete Fashion Group',
    'CICH.CA': 'CI Capital Holding', 'CIEB.CA': 'Credit Agricole Egypt',
    'CIRA.CA': 'CIRA Education', 'CLHO.CA': 'Cleopatra Hospitals',
    'CNFN.CA': 'Contact Financial Holding', 'COMI.CA': 'Commercial International Bank (CIB)',
    'COPR.CA': 'Copper Commercial Investment', 'COSG.CA': 'Cairo Oil & Soap',
    'CPCI.CA': 'Kahira Pharmaceuticals', 'CSAG.CA': 'Canal Shipping Agencies',
    'DAPH.CA': 'Development & Engineering Consultants', 'DOMT.CA': 'Domty (Arabian Food Industries)',
    'DSCW.CA': 'Dice Garments', 'DTPP.CA': 'Delta Printing & Packaging',
    'EALR.CA': 'Arab Co. for Land Reclamation', 'EASB.CA': 'Egyptian Arabian Securities',
    'EAST.CA': 'Eastern Company', 'EBSC.CA': 'Osool ESB Securities',
    'ECAP.CA': 'Al Ezz Ceramics & Porcelain', 'EDFM.CA': 'East Delta Flour Mills',
    'EEII.CA': 'Arab Engineering Industries', 'EFIC.CA': 'Egyptian Financial & Industrial',
    'EFID.CA': 'Edita Food Industries', 'EFIH.CA': 'e-finance',
    'EGAL.CA': 'Egypt Aluminum', 'EGAS.CA': 'Egypt Gas',
    'EGBE.CA': 'Egyptian Gulf Bank', 'EGCH.CA': 'Egyptian Chemical Industries',
    'EGREF.CA': 'Egyptian Real Estate Fund', 'EGTS.CA': 'Egyptian Resorts',
    'EHDR.CA': 'Egyptians Housing & Development', 'ELEC.CA': 'Electro Cable Egypt',
    'ELKA.CA': 'Cairo Housing & Development', 'ELNA.CA': 'El Nasr Agricultural Crops',
    'ELSH.CA': 'Al-Shams Housing', 'ELWA.CA': 'El Wadi International Investment',
    'EMFD.CA': 'Emaar Misr', 'ENGC.CA': 'ICON (Industrial Engineering)',
    'EPCO.CA': 'Egypt for Poultry', 'EPPK.CA': 'El Ahram Printing & Packaging',
    'ETEL.CA': 'Telecom Egypt', 'ETRS.CA': 'Egytrans',
    'EXPA.CA': 'Export Development Bank', 'FAIT.CA': 'Faisal Islamic Bank',
    'FAITA.CA': 'Faisal Islamic Bank (USD)', 'FERC.CA': 'Ferchem Misr',
    'FNAR.CA': 'Al Fanar Construction', 'FWRY.CA': 'Fawry',
    'GBCO.CA': 'GB Corp', 'GDWA.CA': 'Gadwa Industrial Development',
    'GGCC.CA': 'Giza General Contracting', 'GIHD.CA': 'Gharbia Islamic Housing',
    'GMCI.CA': 'GMC Group', 'GRCA.CA': 'Grand Capital',
    'GSSC.CA': 'General Silos & Storage', 'GTWL.CA': 'Golden Textiles & Wool',
    'HDBK.CA': 'Housing & Development Bank', 'HELI.CA': 'Heliopolis Housing',
    'HRHO.CA': 'EFG Holding', 'ICID.CA': 'International Investment & Development',
    'IDRE.CA': 'Ismailia Development & Real Estate', 'IEEC.CA': 'Industrial & Engineering Projects',
    'IFAP.CA': 'International Agricultural Crops', 'INEG.CA': 'Integrated Engineering Group',
    'INFI.CA': 'Ismailia National Food Industries', 'IRON.CA': 'Egyptian Iron & Steel',
    'ISMA.CA': 'Ismailia Misr Poultry', 'ISMQ.CA': 'Iron & Steel Mines & Quarries',
    'ISPH.CA': 'Ibnsina Pharma', 'JUFO.CA': 'Juhayna Food',
    'KABO.CA': 'El-Nasr Clothing (KABO)', 'KWIN.CA': 'El Kahera El Watania Investment',
    'KZPC.CA': 'Kafr El Zayat Pesticides', 'LCSW.CA': 'Lecico Egypt',
    'LUTS.CA': 'Lotus Agricultural Investments', 'MAAL.CA': 'Marseille Almasreia',
    'MASR.CA': 'Madinet Masr', 'MBSC.CA': 'Misr Beni Suef Cement',
    'MCQE.CA': 'Misr Cement (Qena)', 'MCRO.CA': 'Macro Group Pharmaceuticals',
    'MENA.CA': 'Mena Touristic & Real Estate', 'MEPA.CA': 'Medical Packaging',
    'MFPC.CA': 'Misr Fertilizers (MOPCO)', 'MFSC.CA': 'Egypt Free Shops',
    'MHOT.CA': 'Misr Hotels', 'MICH.CA': 'Misr Chemical Industries',
    'MILS.CA': 'North Cairo Flour Mills', 'MIPH.CA': 'Minapharm',
    'MOED.CA': 'Egyptian Modern Education', 'MOIL.CA': 'Maridive & Oil Services',
    'MOIN.CA': 'Mohandes Insurance', 'MOSC.CA': 'Misr Oils & Soap',
    'MPCI.CA': 'Memphis Pharmaceuticals', 'MPCO.CA': 'Mansoura Poultry',
    'MPRC.CA': 'Egyptian Media Production City', 'MTIE.CA': 'MM Group',
    'NAHO.CA': 'Naeem Holding', 'NCCW.CA': 'Nasr Civil Works',
    'NEDA.CA': 'Northern Upper Egypt Development', 'NHPS.CA': 'National Housing Syndicates',
    'NINH.CA': 'Nozha International Hospital', 'NIPH.CA': 'Nile Pharmaceuticals',
    'OBRI.CA': 'El-Ebour Real Estate', 'OCDI.CA': 'SODIC',
    'OCPH.CA': 'October Pharma', 'ODIN.CA': 'ODIN Investments',
    'OFH.CA': 'O B Financial Holding', 'OIH.CA': 'Orascom Investment Holding',
    'OLFI.CA': 'Obour Land', 'ORHD.CA': 'Orascom Development Egypt',
    'ORWE.CA': 'Oriental Weavers', 'PHAR.CA': 'EIPICO (Egyptian Intl Pharma)',
    'PHDC.CA': 'Palm Hills', 'PHTV.CA': 'Pyramisa Hotels',
    'PRCL.CA': 'General Ceramic & Porcelain', 'PRDC.CA': 'Pioneers Properties',
    'PRMH.CA': 'Prime Holding', 'RACC.CA': 'Raya Customer Experience',
    'RAKT.CA': 'Rakta Paper', 'RAYA.CA': 'Raya Holding',
    'RMDA.CA': 'Rameda', 'ROTO.CA': 'Rowad Tourism',
    'RREI.CA': 'Arab Real Estate Investment', 'RTVC.CA': 'Remco Tourism Villages',
    'SAUD.CA': 'alBaraka Bank Egypt', 'SCEM.CA': 'Sinai Cement',
    'SCFM.CA': 'South Cairo & Giza Flour Mills', 'SCTS.CA': 'Suez Canal Technology Settling',
    'SDTI.CA': 'Sharm Dreams', 'SEIG.CA': 'Saudi Egyptian Investment & Finance',
    'SIPC.CA': 'Sabaa Pharmaceutical', 'SKPC.CA': 'Sidi Kerir Petrochemicals',
    'SMFR.CA': 'Samad Misr (Egyfert)', 'SNFC.CA': 'Sharkia National Food',
    'SPIN.CA': 'Alexandria Spinning & Weaving', 'SPMD.CA': 'Speed Medical',
    'SUGR.CA': 'Delta Sugar', 'SVCE.CA': 'South Valley Cement',
    'SWDY.CA': 'Elsewedy Electric', 'TALM.CA': 'Taaleem Management',
    'TMGH.CA': 'Talaat Moustafa Group', 'UEFM.CA': 'Upper Egypt Mills',
    'UEGC.CA': 'El-Saeed Contracting', 'UNIP.CA': 'Universal Paper & Packaging',
    'UNIT.CA': 'United Housing & Development', 'WCDF.CA': 'Middle & West Delta Flour Mills',
    'WKOL.CA': 'Wadi Kom Ombo Land Reclamation', 'ZEOT.CA': 'Extracted Oil & Derivatives',
    'ZMID.CA': 'Zahraa El Maadi Investment',
}

# label: on the Market control · in_text: the same inside a sentence ·
# noun/nouns: wording of the page ("3 stocks") ·
# everything: "every Tadawul stock" in the page's subtitle · days_note: the
# trading week, for the Days help · cur: the currency of its prices ('' = each
# symbol has its own unit) · close: the daily close time written next to a
# signal's date · clean: drop the bars Yahoo fills in on days nothing traded.
MARKETS = {
    'SA': {'label': 'Saudi stocks', 'in_text': 'Saudi stocks', 'noun': 'stock', 'nouns': 'stocks',
           'everything': 'every Tadawul stock', 'days_note': 'Tadawul runs Sunday-Thursday, so',
           'cur': 'SAR', 'close': '15:00', 'clean': False,
           'search': 'Search symbol or company name…'},
    'COM': {'label': 'Commodities', 'in_text': 'commodities', 'noun': 'commodity', 'nouns': 'commodities',
            'everything': 'gold, silver, oil and other commodities',
            'days_note': 'Futures trade Monday-Friday, so',
            'cur': '', 'close': '', 'clean': True,
            'search': 'Search gold, silver, oil…'},
    'EG': {'label': 'Egyptian stocks', 'in_text': 'Egyptian stocks', 'noun': 'stock', 'nouns': 'stocks',
           'everything': 'every Egyptian Exchange stock with usable data',
           'days_note': 'The Egyptian Exchange runs Sunday-Thursday, so',
           'cur': 'EGP', 'close': '', 'clean': True,
           'search': 'Search symbol or company name…'},
}
DEFAULT_MARKET = 'SA'


def market_symbols(market: str) -> dict:
    """{Yahoo symbol: name} of a market, in scan order."""
    if market == 'COM':
        return {s: v[0] for s, v in _COMMODITIES.items()}
    if market == 'EG':
        return dict(_EGX)
    from market_data import get_all_tadawul_tickers
    return get_all_tadawul_tickers()


def short_symbol(sym: str) -> str:
    """The symbol as the page shows it ('1120.SR' -> '1120', 'GC=F' -> 'GC').
    Also used in widget keys and CSS classes, so it has to stay letters and digits."""
    for tail in ('.SR', '.CA', '=F'):
        if sym.endswith(tail):
            return sym[:-len(tail)]
    return sym


def unit_of(sym: str) -> str:
    """The symbol's price unit when it differs from its market's currency, else ''."""
    if sym in _COMMODITIES:
        return _COMMODITIES[sym][1]
    return 'USD' if sym in _EGX_USD else ''


def search_text(sym: str, name: str) -> str:
    """What the search box matches for a symbol, lower case."""
    extra = _COMMODITIES[sym][2] if sym in _COMMODITIES else ''
    return f"{short_symbol(sym)} {name} {extra}".lower()
