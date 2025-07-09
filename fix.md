# Single Stock Analysis Enhancement Plan

## 🎯 Overview

Enhance the single stock analysis feature to be more interactive and user-friendly while maintaining core functionality and adhering to the technical specification.

## ✅ Current Functionality (PRESERVE)

- Database-first data fetching approach
- Technical indicators calculation (MA, RSI, MACD)
- Fundamental analysis integration
- Value & Momentum strategy scoring
- Auto-navigation from batch analysis
- Add to watchlist functionality

## 🚀 Enhancement Suggestions

### 1. **Quick Action Toolbar**

**Location**: Add below the stock header section
**Code to Add**: In `ui/single_stock.py` after the watchlist button section

```python
# Quick action toolbar
st.markdown("---")
quick_col1, quick_col2, quick_col3, quick_col4, quick_col5 = st.columns(5)

with quick_col1:
    if st.button("🔄 Refresh Data", help="Fetch latest market data"):
        # Clear cache for this ticker
        st.session_state[f'cache_{ticker}'] = None
        st.rerun()

with quick_col2:
    if st.button("📋 Compare", help="Add to comparison list"):
        if 'comparison_list' not in st.session_state:
            st.session_state.comparison_list = []
        if ticker not in st.session_state.comparison_list:
            st.session_state.comparison_list.append(ticker)
            st.success(f"Added {ticker} to comparison")

with quick_col3:
    if st.button("📰 News", help="Show latest news"):
        st.session_state[f'show_news_{ticker}'] = not st.session_state.get(f'show_news_{ticker}', False)

with quick_col4:
    if st.button("📈 Similar", help="Find similar stocks"):
        st.session_state[f'show_similar_{ticker}'] = True

with quick_col5:
    if st.button("🎯 Set Alert", help="Set price alert"):
        st.session_state[f'show_alert_{ticker}'] = True
```

### 2. **Interactive Price Chart Enhancements**

**Location**: Replace the current chart code in `ui/single_stock.py`
**Remove**: Lines containing the basic plotly chart
**Replace With**:

```python
# Enhanced interactive chart with drawing tools
def create_interactive_chart(stock_data, ticker, indicators):
    fig = go.Figure()

    # Candlestick chart
    fig.add_trace(go.Candlestick(
        x=stock_data.index,
        open=stock_data['open'],
        high=stock_data['high'],
        low=stock_data['low'],
        close=stock_data['close'],
        name='Price',
        increasing_line_color='green',
        decreasing_line_color='red'
    ))

    # Add volume with better visibility
    fig.add_trace(go.Bar(
        x=stock_data.index,
        y=stock_data['volume'],
        name='Volume',
        yaxis='y2',
        marker_color='lightblue',
        opacity=0.3
    ))

    # Add moving averages with better styling
    for ma_period, color in [(20, 'orange'), (50, 'blue'), (200, 'purple')]:
        ma_key = f'sma_{ma_period}'
        if ma_key in indicators:
            fig.add_trace(go.Scatter(
                x=stock_data.index,
                y=indicators[ma_key],
                mode='lines',
                name=f'MA{ma_period}',
                line=dict(color=color, width=2),
                hovertemplate=f'MA{ma_period}: %{{y:.2f}}<br>Date: %{{x}}'
            ))

    # Enhanced layout with dark theme option
    fig.update_layout(
        title=f'{ticker} - Interactive Price Analysis',
        yaxis=dict(title='Price', side='left'),
        yaxis2=dict(title='Volume', overlaying='y', side='right'),
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(count=5, label="5D", step="day", stepmode="backward"),
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        ),
        height=600,
        hovermode='x unified',
        dragmode='pan'  # Enable panning by default
    )

    # Add modebar with drawing tools
    config = {
        'modeBarButtonsToAdd': [
            'drawline',
            'drawopenpath',
            'drawclosedpath',
            'drawcircle',
            'drawrect',
            'eraseshape'
        ],
        'displaylogo': False,
        'displayModeBar': True
    }

    return fig, config

# Use the enhanced chart
fig, config = create_interactive_chart(stock_data, ticker, indicators)
st.plotly_chart(fig, use_container_width=True, config=config)
```

### 3. **Real-time Signal Dashboard**

**Location**: Add after technical indicators section
**Code to Add**:

```python
# Signal Dashboard
st.subheader("📊 Live Signal Dashboard")

# Create metric cards for key signals
dash_col1, dash_col2, dash_col3, dash_col4 = st.columns(4)

with dash_col1:
    tech_score = signals.get('tech_score', 0)
    delta_color = "normal" if tech_score >= 50 else "inverse"
    st.metric(
        "Technical Score",
        f"{tech_score}/100",
        delta=f"{tech_score - 50} vs neutral",
        delta_color=delta_color
    )

with dash_col2:
    rsi_value = indicators.get('rsi', [0])[-1] if 'rsi' in indicators else 0
    rsi_signal = "🟢 Bullish" if rsi_value > 50 else "🔴 Bearish"
    st.metric("RSI Signal", rsi_signal, f"{rsi_value:.1f}")

with dash_col3:
    ma_signal = "🟢" if signals.get('above_ma40') else "🔴"
    st.metric("Trend", f"{ma_signal} MA40", 
              "Above" if signals.get('above_ma40') else "Below")

with dash_col4:
    vm_signal = signals.get('value_momentum_signal', 'HOLD')
    signal_color = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}.get(vm_signal, "⚪")
    st.metric("V&M Signal", f"{signal_color} {vm_signal}")

# Interactive signal explanation
with st.expander("🎯 Understanding the Signals", expanded=False):
    st.markdown("""
    ### Signal Interpretation Guide

    **Technical Score (0-100)**
    - 70+ = Strong Buy Signal
    - 50-70 = Neutral/Hold
    - Below 50 = Caution/Sell Signal

    **RSI (Relative Strength Index)**
    - Above 70 = Overbought (potential reversal)
    - 50-70 = Bullish momentum
    - 30-50 = Bearish momentum
    - Below 30 = Oversold (potential bounce)

    **Trend (MA40)**
    - Price above 40-day MA = Uptrend
    - Price below 40-day MA = Downtrend

    **V&M Signal (Value & Momentum)**
    - Combines technical and fundamental analysis
    - BUY = Both technical and fundamentals are strong
    - HOLD = Mixed signals
    - SELL = Weak technical or fundamental indicators
    """)
```

### 4. **Comparison Mode**

**Location**: Add new section after main analysis
**Code to Add**:

```python
# Stock Comparison Feature
if st.session_state.get('comparison_list'):
    st.markdown("---")
    st.subheader("📊 Stock Comparison")

    comparison_tickers = st.multiselect(
        "Compare with:",
        options=st.session_state.comparison_list,
        default=st.session_state.comparison_list[:3]  # Max 3 for clarity
    )

    if comparison_tickers:
        # Fetch comparison data
        comparison_data = {}
        for comp_ticker in comparison_tickers:
            comp_data = data_fetcher.get_stock_data(comp_ticker, timeframe_value, period_value)
            if not comp_data.empty:
                comparison_data[comp_ticker] = comp_data

        # Normalized price comparison
        fig_comp = go.Figure()

        for comp_ticker, comp_data in comparison_data.items():
            # Normalize to percentage change
            normalized = (comp_data['close'] / comp_data['close'].iloc[0] - 1) * 100
            fig_comp.add_trace(go.Scatter(
                x=comp_data.index,
                y=normalized,
                mode='lines',
                name=comp_ticker,
                hovertemplate=f'{comp_ticker}: %{{y:.2f}}%<br>Date: %{{x}}'
            ))

        # Add current stock
        normalized_current = (stock_data['close'] / stock_data['close'].iloc[0] - 1) * 100
        fig_comp.add_trace(go.Scatter(
            x=stock_data.index,
            y=normalized_current,
            mode='lines',
            name=f"{ticker} (Current)",
            line=dict(width=3),
            hovertemplate=f'{ticker}: %{{y:.2f}}%<br>Date: %{{x}}'
        ))

        fig_comp.update_layout(
            title="Relative Performance Comparison (%)",
            yaxis_title="Percentage Change",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig_comp, use_container_width=True)
```

### 5. **Smart Alerts System**

**Location**: Add modal/dialog functionality
**Code to Add**:

```python
# Price Alert Setting
if st.session_state.get(f'show_alert_{ticker}'):
    with st.form(f"alert_form_{ticker}"):
        st.subheader("🎯 Set Price Alert")

        alert_col1, alert_col2 = st.columns(2)

        with alert_col1:
            alert_type = st.selectbox(
                "Alert Type",
                ["Price Above", "Price Below", "% Change", "Volume Spike"]
            )

        with alert_col2:
            if alert_type in ["Price Above", "Price Below"]:
                alert_value = st.number_input(
                    "Target Price",
                    value=float(current_price),
                    min_value=0.0,
                    step=0.01
                )
            elif alert_type == "% Change":
                alert_value = st.number_input(
                    "Percentage Change",
                    value=5.0,
                    min_value=0.0,
                    max_value=100.0,
                    step=0.5
                )
            else:  # Volume Spike
                alert_value = st.number_input(
                    "Volume Multiplier",
                    value=2.0,
                    min_value=1.0,
                    step=0.1
                )

        alert_note = st.text_area("Note (optional)", height=60)

        if st.form_submit_button("Set Alert"):
            # Store alert in session state (in production, save to DB)
            if 'alerts' not in st.session_state:
                st.session_state.alerts = []

            st.session_state.alerts.append({
                'ticker': ticker,
                'type': alert_type,
                'value': alert_value,
                'note': alert_note,
                'created': datetime.now()
            })

            st.success(f"Alert set for {ticker}: {alert_type} {alert_value}")
            st.session_state[f'show_alert_{ticker}'] = False
            st.rerun()
```

### 6. **Enhanced Mobile Responsiveness**

**Location**: Add CSS styling at the beginning of display_single_stock_analysis()
**Code to Add**:

```python
# Mobile-responsive CSS
st.markdown("""
<style>
    /* Mobile-friendly adjustments */
    @media (max-width: 768px) {
        /* Stacked metrics on mobile */
        div[data-testid="metric-container"] {
            padding: 0.5rem;
        }

        /* Responsive charts */
        .js-plotly-plot {
            max-width: 100%;
            overflow-x: auto;
        }

        /* Compact buttons */
        .stButton > button {
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
        }

        /* Responsive tables */
        .dataframe {
            font-size: 0.75rem;
        }
    }

    /* Enhanced metric cards */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border-radius: 0.5rem;
        padding: 1rem;
        border: 1px solid rgba(28, 131, 225, 0.2);
        transition: all 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Signal badges */
    .signal-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: bold;
        font-size: 0.875rem;
        margin: 0.25rem;
    }

    .signal-buy {
        background-color: #28a745;
        color: white;
    }

    .signal-sell {
        background-color: #dc3545;
        color: white;
    }

    .signal-hold {
        background-color: #ffc107;
        color: black;
    }
</style>
""", unsafe_allow_html=True)
```

### 7. **Quick Stats Summary Card**

**Location**: Add before the main analysis sections
**Code to Add**:

```python
# Quick Stats Card
with st.container():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <h3 style="margin: 0; color: white;">Quick Analysis Summary</h3>
    </div>
    """, unsafe_allow_html=True)

    quick_stats_cols = st.columns(5)

    with quick_stats_cols[0]:
        price_change = ((current_price - prev_close) / prev_close) * 100
        st.markdown(f"""
        <div style="text-align: center;">
            <h4>${current_price:.2f}</h4>
            <p style="color: {'green' if price_change > 0 else 'red'};">
                {'+' if price_change > 0 else ''}{price_change:.2f}%
            </p>
        </div>
        """, unsafe_allow_html=True)

    with quick_stats_cols[1]:
        pe_ratio = fundamentals.get('peRatio', 'N/A')
        st.markdown(f"""
        <div style="text-align: center;">
            <h4>P/E: {pe_ratio}</h4>
            <p>Valuation</p>
        </div>
        """, unsafe_allow_html=True)

    with quick_stats_cols[2]:
        volume_avg = stock_data['volume'].mean()
        volume_today = stock_data['volume'].iloc[-1]
        volume_ratio = volume_today / volume_avg
        st.markdown(f"""
        <div style="text-align: center;">
            <h4>{volume_ratio:.1f}x</h4>
            <p>Vol vs Avg</p>
        </div>
        """, unsafe_allow_html=True)

    with quick_stats_cols[3]:
        fifty_two_high = stock_data['high'].rolling(252).max().iloc[-1]
        distance_from_high = ((fifty_two_high - current_price) / fifty_two_high) * 100
        st.markdown(f"""
        <div style="text-align: center;">
            <h4>-{distance_from_high:.1f}%</h4>
            <p>From 52W High</p>
        </div>
        """, unsafe_allow_html=True)

    with quick_stats_cols[4]:
        volatility = stock_data['close'].pct_change().std() * np.sqrt(252) * 100
        st.markdown(f"""
        <div style="text-align: center;">
            <h4>{volatility:.1f}%</h4>
            <p>Annual Vol</p>
        </div>
        """, unsafe_allow_html=True)
```

## 🔧 Implementation Priority

### Phase 1 (Quick Wins - 1-2 hours)

1. Quick Action Toolbar
1. Enhanced Mobile Responsiveness
1. Quick Stats Summary Card
1. Signal Dashboard

### Phase 2 (Medium Effort - 2-4 hours)

1. Interactive Price Chart Enhancements
1. Comparison Mode
1. Smart Alerts System

### Phase 3 (Future Enhancements)

1. News integration
1. Similar stocks finder
1. Advanced charting patterns
1. Social sentiment analysis

## ⚠️ Important Notes

1. **Maintain Core Functionality**: All enhancements preserve the existing technical and fundamental analysis
1. **Database-First Approach**: No changes to the data fetching logic as per technical_spec.md
1. **Performance**: All additions use efficient caching and avoid unnecessary API calls
1. **Mobile-First**: All UI enhancements are designed to work well on mobile devices
1. **Backwards Compatible**: Changes don’t break existing functionality or integrations

## 🚀 Testing Checklist

- [ ] Single stock analysis loads correctly from batch analysis
- [ ] All technical indicators calculate properly
- [ ] Fundamental analysis displays correctly
- [ ] Interactive features work on mobile
- [ ] Comparison mode handles multiple stocks
- [ ] Alerts can be set and stored
- [ ] Quick action buttons trigger correct actions
- [ ] Charts render properly with drawing tools
- [ ] Performance remains fast with caching

## 📝 Additional Recommendations

1. **User Preferences**: Store chart preferences (indicators shown, timeframe) in session state
1. **Export Options**: Add ability to export analysis as PDF or image
1. **Keyboard Shortcuts**: Implement shortcuts for power users (e.g., ‘C’ for compare, ‘R’ for refresh)
1. **Tooltips**: Add helpful tooltips explaining each indicator and metric
1. **Loading States**: Show skeleton loaders during data fetching for better UX