import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from apple_theme import (T1, T2, T3, T4, CARD, HAIR, HAIR2, GRID, BLUE, GREEN, RED, AMBER,
                         PURPLE, TEAL, ORANGE, INDIGO, UP, DOWN, FONT, SERIES, REGIME_COLORS,
                         rgba, style_fig)

# Light design: moving averages keep the same colour in every chart
# (EMA 20 teal, EMA 50 amber, EMA 200 purple); blue is kept for the main
# series (price area, MACD, %K, forecast).
_MA20, _MA50, _MA200 = TEAL, AMBER, PURPLE
_BB_LINE = rgba(T4, 0.55)
_BB_FILL = rgba(T4, 0.07)

# One title style for every chart: left-aligned, 15px semibold, T1, optional T3 subtitle.
def _title(text, sub=None):
    t = dict(text=text, x=0.02, xanchor='left',
             font=dict(size=15, color=T1, family=FONT, weight=600))
    if sub:
        t['subtitle'] = dict(text=sub, font=dict(size=12, color=T3, family=FONT))
    return t

# Display names for data keys (data keys stay unchanged).
_LABEL = {'TREND': 'Trend', 'RANGE': 'Range', 'VOLATILE': 'Volatile', 'UNKNOWN': 'Unknown',
          'MOMENTUM': 'Momentum', 'VOLATILITY': 'Volatility', 'VOLUME': 'Volume', 'MACD': 'MACD'}

def _disp(key):
    return _LABEL.get(key, key.title() if isinstance(key, str) and key.isupper() and len(key) > 4 else key)

def create_price_chart(df, chart_indicators, chart_type='Candlestick'):

    """Create modern, clear price chart with multiple chart types."""

    

    fig = go.Figure()

    

    # Add price chart based on selected type

    if chart_type == 'Candlestick':

        fig.add_trace(go.Candlestick(

            x=df['Date'],

            open=df['Open'],

            high=df['High'],

            low=df['Low'],

            close=df['Close'],

            name='Price',

            increasing_line_color=UP,

            increasing_fillcolor=UP,

            decreasing_line_color=DOWN,

            decreasing_fillcolor=DOWN

        ))

    elif chart_type == 'Line':

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['Close'],

            name='Price',

            line=dict(color=T1, width=2),

            mode='lines',

            hovertemplate='Date: %{x}<br>Price: %{y:.2f}<extra></extra>'

        ))

    elif chart_type == 'Area':

        # Invisible baseline at the data minimum so the fill does not pin the axis to 0
        fig.add_trace(go.Scatter(
            x=df['Date'], y=[df['Close'].min()] * len(df),
            mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'
        ))

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['Close'],

            name='Price',

            line=dict(color=BLUE, width=2),

            fill='tonexty',

            fillcolor=rgba(BLUE, 0.08),

            mode='lines',

            hovertemplate='Date: %{x}<br>Price: %{y:.2f}<extra></extra>'

        ))

    

    # Modern color palette

    indicator_colors = {

        'EMA 20': _MA20,

        'EMA 50': _MA50,

        'EMA 200': _MA200,

        'SMA 50': INDIGO,

        'SMA 200': ORANGE,

        'BB': T4,

        'VWAP': BLUE

    }

    

    if 'EMA 20' in chart_indicators and 'EMA_20' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_20'],

            name='EMA 20',

            line=dict(color=indicator_colors['EMA 20'], width=2.5),

            opacity=0.9

        ))

    

    if 'EMA 50' in chart_indicators and 'EMA_50' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_50'],

            name='EMA 50',

            line=dict(color=indicator_colors['EMA 50'], width=2.5),

            opacity=0.9

        ))

    

    if 'EMA 200' in chart_indicators and 'EMA_200' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_200'],

            name='EMA 200',

            line=dict(color=indicator_colors['EMA 200'], width=3, dash='dot'),

            opacity=0.8

        ))

    

    if 'SMA 50' in chart_indicators and 'SMA_50' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['SMA_50'],

            name='SMA 50',

            line=dict(color=indicator_colors['SMA 50'], width=2),

            opacity=0.9

        ))



    if 'SMA 200' in chart_indicators and 'SMA_200' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['SMA_200'],

            name='SMA 200',

            line=dict(color=indicator_colors['SMA 200'], width=2.5, dash='dot'),

            opacity=0.9

        ))



    if 'VWAP' in chart_indicators and 'VWAP' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['VWAP'],

            name='VWAP',

            line=dict(color=indicator_colors['VWAP'], width=1.8, dash='dash'),

            opacity=0.85

        ))

    

    if 'Bollinger Bands' in chart_indicators:

        if 'BBU_20_2.0' in df.columns and 'BBL_20_2.0' in df.columns:

            fig.add_trace(go.Scatter(

                x=df['Date'],

                y=df['BBU_20_2.0'],

                name='BB Upper',

                line=dict(color=indicator_colors['BB'], width=1, dash='dash'),

                opacity=0.5,

                showlegend=False

            ))

            fig.add_trace(go.Scatter(

                x=df['Date'],

                y=df['BBL_20_2.0'],

                name='Bollinger Bands',

                line=dict(color=indicator_colors['BB'], width=1, dash='dash'),

                fill='tonexty',

                fillcolor=_BB_FILL,

                opacity=0.5

            ))

    

    fig.update_layout(

        title=_title('Price Chart with Market Regimes'),

        yaxis_title='Price (SAR)',

        xaxis_title='',

        height=600,

        hovermode='x unified',

        xaxis_rangeslider_visible=False,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(

            gridcolor=GRID,

            showgrid=True,

            zeroline=False

        ),

        yaxis=dict(

            gridcolor=GRID,

            showgrid=True,

            zeroline=False

        ),

        legend=dict(

            orientation="h",

            yanchor="top",

            y=-0.08,

            xanchor="left",

            x=0,

            bgcolor='rgba(0,0,0,0)',

            font=dict(size=11)

        ),

        margin=dict(t=70, b=70, l=60, r=40)

    )

    

    return style_fig(fig)





def create_regime_distribution_chart(regime_counts):

    """Create modern pie chart."""

    

    labels = ['TREND', 'RANGE', 'VOLATILE']

    colors = [REGIME_COLORS[label] for label in labels]

    values = [regime_counts.get(label, 0) for label in labels]



    fig = go.Figure(data=[go.Pie(

        labels=[_disp(label) for label in labels],

        values=values,

        marker=dict(

            colors=colors,

            line=dict(color=CARD, width=3)

        ),

        hole=0.5,

        textinfo='label+percent',

        textfont=dict(size=14, family=FONT),

        insidetextfont=dict(color='#FFFFFF'),

        outsidetextfont=dict(color=T1),

        insidetextorientation='horizontal',

        hovertemplate='<b>%{label}</b><br>Days: %{value}<br>Percentage: %{percent}<extra></extra>'

    )])

    

    fig.update_layout(

        title=_title('Market Regime Distribution'),

        height=400,

        showlegend=False,

        paper_bgcolor=CARD,

        plot_bgcolor=CARD,

        font=dict(color=T2, family=FONT),

        margin=dict(t=60, b=20, l=20, r=20)

    )

    

    return style_fig(fig)





def create_adx_chart(df):

    """Create modern ADX chart."""

    

    fig = go.Figure()

    

    fig.add_trace(go.Scatter(

        x=df['Date'],

        y=df.get('ADX_14', [20]*len(df)),

        name='ADX',

        line=dict(color=PURPLE, width=2.5),

        fill='tozeroy',

        fillcolor=rgba(PURPLE, 0.08),

        hovertemplate='Date: %{x}<br>ADX: %{y:.2f}<extra></extra>'

    ))

    

    fig.add_hline(

        y=25,

        line_dash="dash",

        line_color=GREEN,

        line_width=1.5,

        opacity=0.7,

        annotation_text="Strong Trend (25)",

        annotation_position="right",

        annotation_font=dict(size=11, color=GREEN)

    )

    fig.add_hline(

        y=20,

        line_dash="dash",

        line_color=AMBER,

        line_width=1.5,

        opacity=0.7,

        annotation_text="Weak Trend (20)",

        annotation_position="right",

        annotation_font=dict(size=11, color=AMBER)

    )

    

    fig.update_layout(

        title=_title('Average Directional Index (ADX)'),

        yaxis_title='ADX Value',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=100)

    )

    

    return style_fig(fig)





def create_rsi_chart(df):

    """Create modern RSI chart."""

    

    fig = go.Figure()

    

    if 'RSI' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['RSI'],

            name='RSI',

            line=dict(color=PURPLE, width=2.5),

            hovertemplate='Date: %{x}<br>RSI: %{y:.2f}<extra></extra>'

        ))

        

        fig.add_hrect(

            y0=70, y1=100,

            fillcolor=RED, opacity=0.07,

            layer="below", line_width=0

        )

        fig.add_hrect(

            y0=0, y1=30,

            fillcolor=GREEN, opacity=0.07,

            layer="below", line_width=0

        )

        

        fig.add_hline(

            y=70,

            line_dash="dash",

            line_color=RED,

            line_width=1.5,

            opacity=0.7,

            annotation_text="Overbought (70)",

            annotation_position="right",

            annotation_font=dict(size=11, color=RED)

        )

        fig.add_hline(

            y=30,

            line_dash="dash",

            line_color=GREEN,

            line_width=1.5,

            opacity=0.7,

            annotation_text="Oversold (30)",

            annotation_position="right",

            annotation_font=dict(size=11, color=GREEN)

        )

    

    fig.update_layout(

        title=_title('Relative Strength Index (RSI)'),

        yaxis_title='RSI Value',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True, range=[0, 100]),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=100)

    )

    

    return style_fig(fig)





def create_macd_chart(df):

    """Create modern MACD chart."""

    

    fig = go.Figure()

    

    if 'MACD_12_26_9' in df.columns and 'MACDs_12_26_9' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['MACD_12_26_9'],

            name='MACD',

            line=dict(color=BLUE, width=2.2),

            hovertemplate='MACD: %{y:.3f}<extra></extra>'

        ))

        

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['MACDs_12_26_9'],

            name='Signal',

            line=dict(color=AMBER, width=2.2),

            hovertemplate='Signal: %{y:.3f}<extra></extra>'

        ))

        

        if 'MACDh_12_26_9' in df.columns:

            colors = [UP if val >= 0 else DOWN for val in df['MACDh_12_26_9']]

            fig.add_trace(go.Bar(

                x=df['Date'],

                y=df['MACDh_12_26_9'],

                name='Histogram',

                marker_color=colors,

                opacity=0.45,

                hovertemplate='Histogram: %{y:.3f}<extra></extra>'

            ))

        

        fig.add_hline(y=0, line_color=HAIR2, line_width=1, line_dash='solid')

    

    fig.update_layout(

        title=_title('MACD', 'Moving Average Convergence Divergence'),

        yaxis_title='MACD Value',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        hovermode='x unified',

        legend=dict(

            orientation="h",

            yanchor="top",

            y=-0.12,

            xanchor="left",

            x=0,

            bgcolor='rgba(0,0,0,0)',

            font=dict(size=12)

        ),

        margin=dict(t=80, b=70, l=60, r=40)

    )

    

    return style_fig(fig)





def create_bollinger_bands_chart(df):

    """Create modern Bollinger Bands chart with price."""

    

    fig = go.Figure()

    

    # Price candlestick

    fig.add_trace(go.Candlestick(

        x=df['Date'],

        open=df['Open'],

        high=df['High'],

        low=df['Low'],

        close=df['Close'],

        name='Price',

        increasing_line_color=UP,

        increasing_fillcolor=UP,

        decreasing_line_color=DOWN,

        decreasing_fillcolor=DOWN

    ))

    

    # Upper band

    if 'BBU_20_2.0' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['BBU_20_2.0'],

            name='Upper Band',

            line=dict(color=RED, width=1.2, dash='dash'),

            opacity=0.7,

            hovertemplate='Upper: %{y:.2f}<extra></extra>'

        ))

    

    # Middle band (SMA 20)

    if 'BBM_20_2.0' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['BBM_20_2.0'],

            name='SMA 20',

            line=dict(color=AMBER, width=2),

            fill=None,

            hovertemplate='SMA20: %{y:.2f}<extra></extra>'

        ))

    

    # Lower band

    if 'BBL_20_2.0' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['BBL_20_2.0'],

            name='Lower Band',

            line=dict(color=GREEN, width=1.2, dash='dash'),

            fill='tonexty',

            fillcolor=rgba(GREEN, 0.06),

            hovertemplate='Lower: %{y:.2f}<extra></extra>'

        ))

    

    fig.update_layout(

        title=_title('Bollinger Bands (Volatility & Overbought/Oversold)'),

        xaxis_rangeslider_visible=False,

        yaxis_title='Price',

        xaxis_title='',

        height=450,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=40)

    )

    

    return style_fig(fig)





def create_volume_chart(df):

    """Create volume analysis chart with moving average."""

    

    fig = go.Figure()

    

    if 'Volume' in df.columns:

        # Volume bars - color by price direction

        colors = [UP if df.iloc[i]['Close'] >= df.iloc[i]['Open'] else DOWN

                  for i in range(len(df))]

        

        fig.add_trace(go.Bar(

            x=df['Date'],

            y=df['Volume'],

            name='Volume',

            marker_color=colors,

            opacity=0.6,

            hovertemplate='Volume: %{y:,.0f}<extra></extra>'

        ))

        

        # Volume SMA 20

        vol_sma = df['Volume'].rolling(window=20).mean()

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=vol_sma,

            name='Vol SMA 20',

            line=dict(color=BLUE, width=2),

            hovertemplate='Vol MA: %{y:,.0f}<extra></extra>'

        ))

    

    fig.update_layout(

        title=_title('Volume Analysis (Confirmation Strength)'),

        yaxis_title='Volume',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=40)

    )

    

    return style_fig(fig)





def create_ema_chart(df):

    """Create Moving Averages trend chart (EMA 20/50/200)."""

    

    fig = go.Figure()

    

    # Price

    fig.add_trace(go.Scatter(

        x=df['Date'],

        y=df['Close'],

        name='Price',

        line=dict(color=T1, width=2),

        hovertemplate='Price: %{y:.2f}<extra></extra>'

    ))

    

    # EMA 20

    if 'EMA_20' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_20'],

            name='EMA 20',

            line=dict(color=_MA20, width=2),

            hovertemplate='EMA20: %{y:.2f}<extra></extra>'

        ))

    

    # EMA 50

    if 'EMA_50' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_50'],

            name='EMA 50',

            line=dict(color=_MA50, width=2),

            hovertemplate='EMA50: %{y:.2f}<extra></extra>'

        ))

    

    # EMA 200

    if 'EMA_200' in df.columns:

        fig.add_trace(go.Scatter(

            x=df['Date'],

            y=df['EMA_200'],

            name='EMA 200',

            line=dict(color=_MA200, width=2.5),

            hovertemplate='EMA200: %{y:.2f}<extra></extra>'

        ))

    

    fig.update_layout(

        title=_title('Exponential Moving Averages (Trend Confirmation)'),

        yaxis_title='Price',

        xaxis_title='',

        height=450,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=40)

    )   

    

    return style_fig(fig)





def create_stochastic_chart(df):

    """Create Stochastic Oscillator chart (momentum reversal signals)."""

    

    fig = go.Figure()

    

    # Calculate Stochastic if not present

    if 'Stoch_K' not in df.columns:

        # Calculate K% = (Close - Low14) / (High14 - Low14) * 100

        low14 = df['Low'].rolling(window=14).min()

        high14 = df['High'].rolling(window=14).max()

        k_percent = ((df['Close'] - low14) / (high14 - low14) * 100).fillna(50)

        d_percent = k_percent.rolling(window=3).mean()

    else:

        k_percent = df.get('Stoch_K', [50]*len(df))

        d_percent = df.get('Stoch_D', [50]*len(df))

    

    # %K line

    fig.add_trace(go.Scatter(

        x=df['Date'],

        y=k_percent,

        name='%K',

        line=dict(color=BLUE, width=2.2),

        hovertemplate='%K: %{y:.2f}<extra></extra>'

    ))

    

    # %D line (signal)

    fig.add_trace(go.Scatter(

        x=df['Date'],

        y=d_percent,

        name='%D (Signal)',

        line=dict(color=AMBER, width=2.2),

        hovertemplate='%D: %{y:.2f}<extra></extra>'

    ))

    

    # Overbought zone (80)

    fig.add_hrect(

        y0=80, y1=100,

        fillcolor=RED, opacity=0.07,

        layer="below", line_width=0

    )

    

    # Oversold zone (20)

    fig.add_hrect(

        y0=0, y1=20,

        fillcolor=GREEN, opacity=0.07,

        layer="below", line_width=0

    )

    

    fig.add_hline(y=80, line_dash="dash", line_color=RED, line_width=1.5, opacity=0.7,

                 annotation_text="Overbought (80)", annotation_position="right",

                 annotation_font=dict(size=11, color=RED))

    fig.add_hline(y=20, line_dash="dash", line_color=GREEN, line_width=1.5, opacity=0.7,

                 annotation_text="Oversold (20)", annotation_position="right",

                 annotation_font=dict(size=11, color=GREEN))

    fig.add_hline(y=50, line_color=HAIR2, line_width=1, line_dash="dot")

    

    fig.update_layout(

        title=_title('Stochastic Oscillator (Momentum & Reversal Signals)'),

        yaxis_title='Stochastic Value',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True, range=[0, 100]),

        hovermode='x unified',

        margin=dict(t=60, b=40, l=60, r=100)

    )

    

    return style_fig(fig)





def create_signal_strength_heatmap(df, latest):

    """Create signal strength heatmap showing indicator alignment."""

    

    # Calculate signal strengths (0-100 scale)

    signals = {}

    

    # ADX - Trend strength

    adx = latest.get('ADX_14', 20)

    signals['TREND'] = min(100, (adx / 30) * 100)  # Normalize to 100

    

    # RSI - Momentum

    rsi = latest.get('RSI', 50)

    if rsi > 70 or rsi < 30:

        signals['MOMENTUM'] = 100  # Strong signal

    elif rsi > 60 or rsi < 40:

        signals['MOMENTUM'] = 75

    else:

        signals['MOMENTUM'] = 50

    

    # MACD - Trend confirmation

    macd = latest.get('MACD_12_26_9', 0)

    macd_signal = latest.get('MACDs_12_26_9', 0)

    if macd > macd_signal:

        signals['MACD'] = 80

    elif macd < macd_signal:

        signals['MACD'] = 20

    else:

        signals['MACD'] = 50

    

    # Bollinger Bands - Volatility

    bb_upper = latest.get('BBU_20_2.0', latest['Close'] * 1.02)

    bb_lower = latest.get('BBL_20_2.0', latest['Close'] * 0.98)

    bb_pos = ((latest['Close'] - bb_lower) / (bb_upper - bb_lower) * 100) if bb_upper != bb_lower else 50

    signals['VOLATILITY'] = bb_pos

    

    # Volume - Confirmation

    if 'Volume' in df.columns and len(df) > 20:

        avg_vol = df.tail(20)['Volume'].mean()

        curr_vol = latest.get('Volume', avg_vol)

        signals['VOLUME'] = min(100, (curr_vol / avg_vol) * 100)

    else:

        signals['VOLUME'] = 50

    

    # Create heatmap

    signal_names = list(signals.keys())

    signal_values = list(signals.values())

    

    # Color code: Red (0-40) -> Yellow (40-60) -> Green (60-100)

    colors = []

    for val in signal_values:

        if val < 40:

            colors.append(RED)  # Red

        elif val < 60:

            colors.append(AMBER)  # Yellow

        else:

            colors.append(GREEN)  # Green

    

    fig = go.Figure()

    

    fig.add_trace(go.Bar(

        y=[_disp(n) for n in signal_names],

        x=signal_values,

        orientation='h',

        marker=dict(color=colors),

        text=[f'{v:.0f}%' for v in signal_values],

        textposition='auto',

        hovertemplate='%{y}: %{x:.0f}%<extra></extra>'

    ))

    

    fig.update_layout(

        title=_title('Signal Strength Alignment (Accuracy Gauge)'),

        xaxis_title='Strength %',

        yaxis_title='Indicator',

        height=320,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=True, range=[0, 100]),

        showlegend=False,

        margin=dict(t=60, b=40, l=120, r=40)

    )

    

    return style_fig(fig)





def create_signal_success_chart(results):

    """Create chart showing signal success rates."""

    indicators = []

    success_rates = []

    colors = []

    

    for indicator, data in results.items():

        if data['total_signals'] > 0:

            indicators.append(indicator)

            success_rates.append(data['success_rate'])

            

            if data['success_rate'] >= 60:

                colors.append(GREEN)

            elif data['success_rate'] >= 40:

                colors.append(AMBER)

            else:

                colors.append(RED)

    

    fig = go.Figure(data=[go.Bar(

        x=indicators,

        y=success_rates,

        marker_color=colors,

        text=[f"{rate:.1f}%" for rate in success_rates],

        textposition='auto',

        textfont=dict(size=14, family=FONT),

        insidetextfont=dict(color='#FFFFFF'),

        outsidetextfont=dict(color=T1),

        hovertemplate='<b>%{x}</b><br>Success Rate: %{y:.1f}%<extra></extra>'

    )])

    

    fig.update_layout(

        title=_title('Signal Success Rate by Indicator'),

        yaxis_title='Success Rate (%)',

        xaxis_title='',

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=False),

        yaxis=dict(gridcolor=GRID, showgrid=True, range=[0, 100]),

        margin=dict(t=60, b=40, l=60, r=40)

    )

    

    return style_fig(fig)





def create_regime_performance_chart(results):

    """Create chart showing performance by regime."""

    fig = go.Figure()

    

    regimes = ['TREND', 'RANGE', 'VOLATILE']

    

    for indicator, data in results.items():

        if data['total_signals'] > 0:

            values = [data['regime_performance'].get(regime, 0) for regime in regimes]

            fig.add_trace(go.Bar(

                name=indicator,

                x=[_disp(r) for r in regimes],

                y=values,

                text=values,

                textposition='auto'

            ))

    

    fig.update_layout(

        title=_title('Successful Signals by Market Regime'),

        yaxis_title='Number of Successful Signals',

        barmode='group',

        colorway=SERIES,

        height=400,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12),

        xaxis=dict(gridcolor=GRID, showgrid=False),

        yaxis=dict(gridcolor=GRID, showgrid=True)

    )

    

    return style_fig(fig)





def create_monthly_performance_chart(monthly_df):

    """Create chart showing monthly performance."""

    if monthly_df.empty:

        return None

    

    fig = make_subplots(

        rows=2, cols=1,

        subplot_titles=('Monthly Success Rate', 'Monthly Average Gain'),

        vertical_spacing=0.15

    )

    

    colors = [GREEN if rate >= 50 else RED for rate in monthly_df['success_rate']]

    

    fig.add_trace(

        go.Bar(x=monthly_df['month'], y=monthly_df['success_rate'], 

               marker_color=colors, name='Success Rate',

               text=[f"{rate:.1f}%" for rate in monthly_df['success_rate']],

               textposition='auto'),

        row=1, col=1

    )

    

    gain_colors = [GREEN if gain >= 0 else RED for gain in monthly_df['avg_gain']]

    

    fig.add_trace(

        go.Bar(x=monthly_df['month'], y=monthly_df['avg_gain'],

               marker_color=gain_colors, name='Avg Gain',

               text=[f"{gain:.2f}%" for gain in monthly_df['avg_gain']],

               textposition='auto'),

        row=2, col=1

    )

    

    fig.update_layout(

        height=600,

        showlegend=False,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=12)

    )

    

    fig.update_xaxes(gridcolor=GRID, showgrid=False)

    fig.update_yaxes(gridcolor=GRID, showgrid=True)

    

    return style_fig(fig)





def render_trading_system_chart(df, current_regime, cp, atr_pct, regime_stability):

    """Render the trading system forecast chart and metrics."""

    st.markdown(f"<div style='font-size:1.25rem; font-weight:700; color:{T1}; letter-spacing:-0.015em; margin:0.4rem 0 0.8rem 0;'>Trading System - Key Levels & Forecast</div>", unsafe_allow_html=True)



    fc_col1, fc_col2 = st.columns([1.2, 1.1], gap="small")

    with fc_col1:

        pred_horizon = st.slider("Forecast Horizon (trading days)", 5, 60, 20, key="ts_fc_horizon")

    with fc_col2:

        band_width = st.selectbox("Forecast Band", ["50% range", "80% range"], key="ts_fc_band")



    # Historical pattern analysis (regime-based)

    pattern_gains = []

    _reg_series = df['REGIME'].values

    _close_series = df['Close'].values

    _i = 0

    while _i < len(_reg_series) - 5:

        if _reg_series[_i] == current_regime:

            _start = _i

            while _i < len(_reg_series) and _reg_series[_i] == current_regime:

                _i += 1

            _dur = _i - _start

            if _dur >= 5 and _i + 20 < len(_close_series):

                _entry = _close_series[_start]

                _future = _close_series[min(_i + 20, len(_close_series) - 1)]

                _g = (_future - _entry) / _entry * 100

                pattern_gains.append(_g)

        else:

            _i += 1



    avg_pattern_gain = np.mean(pattern_gains) if pattern_gains else 0



    # Recent momentum trajectory (5-day slope of close)

    if len(df) >= 10:

        _slope_prices = df.tail(10)['Close'].values

        _slope_x = np.arange(len(_slope_prices))

        _slope_coef = np.polyfit(_slope_x, _slope_prices, 1)[0]

        price_slope_daily = _slope_coef

    else:

        price_slope_daily = 0



    if pattern_gains:

        p25 = np.percentile(pattern_gains, 25) * (pred_horizon / 20)

        p75 = np.percentile(pattern_gains, 75) * (pred_horizon / 20)

        p10 = np.percentile(pattern_gains, 10) * (pred_horizon / 20)

        p90 = np.percentile(pattern_gains, 90) * (pred_horizon / 20)

    else:

        p25 = -atr_pct

        p75 = atr_pct

        p10 = -atr_pct * 1.5

        p90 = atr_pct * 1.5



    band_low_pct = p25 if band_width == "50% range" else p10

    band_high_pct = p75 if band_width == "50% range" else p90



    trend_pct = (price_slope_daily * pred_horizon / cp * 100) if cp else 0

    regime_pct = avg_pattern_gain * (pred_horizon / 20)



    returns = np.log(df["Close"] / df["Close"].shift(1)).dropna()

    returns = returns.tail(min(90, len(returns))) if len(returns) > 0 else returns

    mu = returns.mean() if len(returns) > 0 else 0

    sigma = returns.std() if len(returns) > 1 else 0

    drift_pct = (np.exp(mu * pred_horizon) - 1) * 100

    z = 0.674 if band_width == "50% range" else 1.282

    drift_low_pct = (np.exp((mu - z * sigma) * pred_horizon) - 1) * 100

    drift_high_pct = (np.exp((mu + z * sigma) * pred_horizon) - 1) * 100



    if current_regime == "TREND":

        weights = np.array([0.5, 0.35, 0.15])

    elif current_regime == "RANGE":

        weights = np.array([0.1, 0.3, 0.6])

    else:

        weights = np.array([0.1, 0.6, 0.3])

    proj_pct = (weights[0] * trend_pct) + (weights[1] * drift_pct) + (weights[2] * regime_pct)

    band_low = (drift_low_pct + band_low_pct) / 2

    band_high = (drift_high_pct + band_high_pct) / 2



    proj_price = cp * (1 + proj_pct / 100)

    band_low_price = cp * (1 + band_low / 100)

    band_high_price = cp * (1 + band_high / 100)



    size_score = min(30, len(pattern_gains) * 2)

    stability_score = min(30, regime_stability * 0.3)

    vol_penalty = min(30, atr_pct * 6)

    confidence = max(25, min(85, 40 + size_score + stability_score - vol_penalty))



    summary_col1, summary_col2, summary_col3 = st.columns(3, gap="small")

    with summary_col1:

        st.metric("Projected Return", f"{proj_pct:+.1f}%")

    with summary_col2:

        st.metric("Forecast Price", f"{proj_price:.2f} SAR")

    with summary_col3:

        st.metric("Confidence", f"{confidence:.0f}%")

    st.caption("Model: Adaptive blend of trend, statistical drift, and regime history.")



    forecast_dates = pd.date_range(start=df.iloc[-1]['Date'], periods=pred_horizon + 1, freq='B')

    forecast_prices = [cp + (proj_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]

    fc_lower = [cp + (band_low_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]

    fc_upper = [cp + (band_high_price - cp) * (i / pred_horizon) for i in range(pred_horizon + 1)]



    hist_90 = df.tail(90)

    rc = go.Figure()

    rc.add_trace(go.Candlestick(

        x=hist_90['Date'], open=hist_90['Open'], high=hist_90['High'],

        low=hist_90['Low'], close=hist_90['Close'], name='Price',

        increasing_line_color=UP, increasing_fillcolor=UP,

        decreasing_line_color=DOWN, decreasing_fillcolor=DOWN

    ))

    if 'EMA_20' in hist_90.columns:

        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_20'],

            name='EMA 20', line=dict(color=_MA20, width=1.5, dash='dot'), opacity=0.9))

    if 'EMA_50' in hist_90.columns:

        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_50'],

            name='EMA 50', line=dict(color=_MA50, width=1.5, dash='dot'), opacity=0.9))

    if 'EMA_200' in hist_90.columns:

        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['EMA_200'],

            name='EMA 200', line=dict(color=_MA200, width=2, dash='dash'), opacity=0.9))

    if 'BBU_20_2.0' in hist_90.columns and 'BBL_20_2.0' in hist_90.columns:

        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['BBU_20_2.0'],

            line=dict(color=_BB_LINE, width=1), showlegend=False))

        rc.add_trace(go.Scatter(x=hist_90['Date'], y=hist_90['BBL_20_2.0'],

            line=dict(color=_BB_LINE, width=1), name='BB Bands',

            fill='tonexty', fillcolor=_BB_FILL))

    rc.add_trace(go.Scatter(x=list(forecast_dates), y=fc_upper,

        mode='lines', line=dict(width=0), showlegend=False, hoverinfo='skip'))

    rc.add_trace(go.Scatter(x=list(forecast_dates), y=fc_lower,

        mode='lines', line=dict(width=0), fill='tonexty',

        fillcolor=rgba(BLUE, 0.10), name='Forecast Band', hoverinfo='skip'))

    rc.add_trace(go.Scatter(x=list(forecast_dates), y=forecast_prices,

        mode='lines+markers', name=f'{pred_horizon}D Forecast',

        line=dict(color=BLUE, width=2, dash='dot'),

        marker=dict(size=3), hovertemplate='%{y:.2f} SAR<extra>Forecast</extra>'))

    rc.update_layout(

        xaxis_rangeslider_visible=False, height=480,

        plot_bgcolor=CARD, paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        xaxis=dict(gridcolor=GRID, showgrid=True),

        yaxis=dict(gridcolor=GRID, showgrid=True),

        legend=dict(orientation='h', y=1.02, x=1, xanchor='right',

                    bgcolor='rgba(0,0,0,0)', font=dict(size=10)),

        hovermode='x unified', margin=dict(t=20, b=30, l=60, r=110)

    )

    style_fig(rc)

    st.plotly_chart(rc, width="stretch", key="ts_price_chart", theme=None)





def create_combo_performance_chart(combo_data):

    """Create performance breakdown chart for a combination."""

    try:

        # Ensure we have the required keys

        total = combo_data.get('total', 0)

        successful = combo_data.get('successful', 0)

        failed = combo_data.get('failed', 0)

        

        # Fallback: calculate from success_rate if individual counts missing

        if (successful == 0 and failed == 0) and total > 0:

            success_rate = combo_data.get('success_rate', 50)

            successful = int(total * (success_rate / 100))

            failed = total - successful

        

        # Ensure we have valid numbers

        if successful < 0:

            successful = 0

        if failed < 0:

            failed = 0

        

        # If both are 0, use dummy data

        if successful == 0 and failed == 0:

            successful, failed = 1, 1

        

        fig = go.Figure(data=[

            go.Pie(

                labels=['Wins', 'Losses'],

                values=[successful, failed],

                marker=dict(colors=[GREEN, RED], line=dict(color=CARD, width=2)),

                textinfo='label+percent',

                insidetextfont=dict(color='#FFFFFF'),

                outsidetextfont=dict(color=T1),

                hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'

            )

        ])

        

        fig.update_layout(

            title=dict(text='Win / Loss Distribution', font=dict(size=14, color=T1, family=FONT)),

            height=280,

            plot_bgcolor=CARD,

            paper_bgcolor=CARD,

            font=dict(color=T2, family=FONT, size=11),

            showlegend=True,

            margin=dict(t=40, b=20, l=20, r=20)

        )

        return style_fig(fig)

    except Exception as e:

        # Return an empty error figure if something goes wrong

        import traceback

        print(f"Error in create_combo_performance_chart: {e}\n{traceback.format_exc()}")

        raise





def create_combo_regime_chart(regime_perf):

    """Create regime performance breakdown for a combination."""

    try:

        regimes = ['TREND', 'RANGE', 'VOLATILE']

        values = [regime_perf.get(r, 0) if regime_perf else 0 for r in regimes]

        colors = [REGIME_COLORS[r] for r in regimes]

        

        # Ensure all values are valid numbers

        values = [float(v) if v is not None else 0 for v in values]

        

        fig = go.Figure()

        fig.add_trace(go.Bar(

            x=regimes,

            y=values,

            marker=dict(color=colors),

            text=[f'{v:.0f}%' if v else '0%' for v in values],

            textposition='auto',

            hovertemplate='%{x}: %{y:.1f}%<extra></extra>'

        ))

        

        fig.update_layout(

            title=dict(text='Performance by Regime', font=dict(size=14, color=T1, family=FONT)),

            height=280,

            plot_bgcolor=CARD,

            paper_bgcolor=CARD,

            font=dict(color=T2, family=FONT, size=11),

            xaxis_title='Market Regime',

            yaxis_title='Win Rate %',

            yaxis=dict(range=[0, 100]),

            showlegend=False,

            margin=dict(t=40, b=40, l=50, r=20)

        )

        return style_fig(fig)

    except Exception as e:

        # Return error details if something goes wrong

        import traceback

        print(f"Error in create_combo_regime_chart: {e}\n{traceback.format_exc()}")

        raise





def create_combo_metrics_comparison(sorted_combos):

    """Create comparison chart of top 5 combos across key metrics."""

    combo_names = [c[0] for c in sorted_combos[:5]]

    win_rates = [c[1]['success_rate'] for c in sorted_combos[:5]]

    expectancies = [c[1]['expectancy'] for c in sorted_combos[:5]]

    profit_factors = [c[1]['profit_factor'] for c in sorted_combos[:5]]

    

    fig = go.Figure()

    fig.add_trace(go.Bar(name='Win Rate %', x=combo_names, y=win_rates, marker_color=BLUE))

    fig.add_trace(go.Bar(name='Expectancy %', x=combo_names, y=expectancies, marker_color=AMBER))

    fig.add_trace(go.Bar(name='Profit Factor', x=combo_names, y=profit_factors, marker_color=PURPLE))

    

    fig.update_layout(

        title=dict(text='Top 5 Combinations - Metrics Comparison', font=dict(size=15, color=T1, family=FONT)),

        height=350,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        barmode='group',

        xaxis_tickangle=-45,

        margin=dict(t=50, b=80, l=60, r=20)

    )

    return style_fig(fig)





def create_combo_consistency_chart(sorted_combos):

    """Create risk/reward profile chart."""

    combo_names = [c[0] for c in sorted_combos[:5]]

    avg_gains = [max(c[1]['avg_gain'], 0.01) for c in sorted_combos[:5]]

    avg_losses = [abs(min(c[1]['avg_loss'], -0.01)) for c in sorted_combos[:5]]

    

    fig = go.Figure()

    fig.add_trace(go.Bar(name='Avg Gain %', x=combo_names, y=avg_gains, marker_color=GREEN))

    fig.add_trace(go.Bar(name='Avg Loss %', x=combo_names, y=avg_losses, marker_color=RED))

    

    fig.update_layout(

        title=dict(text='Risk/Reward Profile', font=dict(size=14, color=T1, family=FONT)),

        height=320,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        barmode='group',

        xaxis_tickangle=-45,

        yaxis_title='Percentage %',

        margin=dict(t=50, b=80, l=60, r=20)

    )

    return style_fig(fig)







def create_consensus_agreement_chart(consensus_signals):

    """Create agreement level distribution chart."""

    agreement_counts = {2: 0, 3: 0, 4: 0, 5: 0}

    for signal in consensus_signals:

        count = signal['count']

        if count in agreement_counts:

            agreement_counts[count] += 1

    

    fig = go.Figure()

    fig.add_trace(go.Bar(

        x=list(agreement_counts.keys()),

        y=list(agreement_counts.values()),

        marker=dict(color=[AMBER, rgba(GREEN, 0.55), rgba(GREEN, 0.78), GREEN]),

        text=list(agreement_counts.values()),

        textposition='outside',

        textfont=dict(color=T1, size=12),

        cliponaxis=False,

        hovertemplate='%{x} indicators: %{y} signals<extra></extra>'

    ))

    

    fig.update_layout(

        title=dict(text='Consensus Agreement Distribution', font=dict(size=14, color=T1, family=FONT)),

        xaxis_title='Number of Agreeing Indicators',

        yaxis_title='Number of Signals',

        height=300,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        showlegend=False,

        margin=dict(t=40, b=40, l=60, r=20)

    )

    return style_fig(fig)





def create_consensus_timeline_chart(consensus_signals):

    """Create timeline of consensus signals."""

    if not consensus_signals:

        return None

    

    dates = [pd.to_datetime(s['date']) for s in consensus_signals]

    agreements = [s['count'] for s in consensus_signals]

    

    fig = go.Figure()

    fig.add_trace(go.Scatter(

        x=dates,

        y=agreements,

        mode='markers+lines',

        marker=dict(

            size=10,

            color=agreements,

            colorscale=[[0, RED], [0.5, AMBER], [1, GREEN]],

            showscale=True,

            colorbar=dict(title='Agreement'),

            line=dict(width=1, color='white')

        ),

        line=dict(color=HAIR2, width=1),

        hovertemplate='Date: %{x|%Y-%m-%d}<br>Agreement: %{y}<extra></extra>'

    ))

    

    fig.update_layout(

        title=dict(text='Consensus Signals Over Time', font=dict(size=14, color=T1, family=FONT)),

        xaxis_title='Date',

        yaxis_title='Number of Agreeing Indicators',

        height=320,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        xaxis=dict(gridcolor=GRID),

        yaxis=dict(gridcolor=GRID, range=[0, 6]),

        margin=dict(t=40, b=40, l=60, r=20)

    )

    return style_fig(fig)





def create_consensus_regime_chart(consensus_signals):

    """Create regime breakdown for consensus signals."""

    regime_counts = {}

    for s in consensus_signals:

        regime = s.get('regime', 'UNKNOWN')

        regime_counts[regime] = regime_counts.get(regime, 0) + 1

    

    regimes = list(regime_counts.keys())

    counts = list(regime_counts.values())

    colors = dict(REGIME_COLORS)

    colors_list = [colors.get(r, T4) for r in regimes]

    

    fig = go.Figure(data=[

        go.Pie(

            labels=regimes,

            values=counts,

            marker=dict(colors=colors_list, line=dict(color=CARD, width=2)),

            textinfo='label+percent',

            insidetextfont=dict(color='#FFFFFF'),

            outsidetextfont=dict(color=T1),

            hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'

        )

    ])

    

    fig.update_layout(

        title=dict(text='Consensus Signals by Market Regime', font=dict(size=14, color=T1, family=FONT)),

        height=300,

        plot_bgcolor=CARD,

        paper_bgcolor=CARD,

        font=dict(color=T2, family=FONT, size=11),

        margin=dict(t=40, b=20, l=20, r=20)

    )

    return style_fig(fig)





def placeholder_consensus():

    """Placeholder function."""

    pass




