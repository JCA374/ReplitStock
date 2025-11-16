# 📊 Weekly Consolidated Report Specification

**Purpose**: Single consolidated HTML/CSV report with top stock recommendations across all market cap tiers.

**Frequency**: Weekly (every Friday after market close at 18:00 Stockholm time)

**Output Files**:
- `weekly_analysis_2025-01-17.html` (Primary - formatted report)
- `weekly_analysis_2025-01-17.csv` (Secondary - Excel compatible)
- `weekly_analysis_2025-01-17.json` (Optional - programmatic access)

---

## 📋 Report Structure

### 1. Executive Summary (Top of Report)

```
═══════════════════════════════════════════════════════════════
WEEKLY STOCK ANALYSIS REPORT
Week of January 13-17, 2025
═══════════════════════════════════════════════════════════════

Analysis Date: Friday, January 17, 2025 at 18:00 CET
Stocks Analyzed: 352 Swedish stocks (100 large, 143 mid, 109 small cap)
Analysis Method: Research-Optimized Value & Momentum Hybrid Strategy
Expected Performance: 8-12% annual alpha, 0.8-1.2 Sharpe ratio

═══════════════════════════════════════════════════════════════
KEY FINDINGS
═══════════════════════════════════════════════════════════════

Top Recommendations: 45 stocks total (15 large, 20 mid, 10 small cap)

Market Overview:
  • Large Cap: 87 stocks passed initial filters → Top 15 selected
  • Mid Cap: 102 stocks passed initial filters → Top 20 selected
  • Small Cap: 64 stocks passed initial filters → Top 10 selected

Average Scores:
  • Large Cap: Composite Score 78.5/100 (Tech: 82.1, Fundamental: 71.2)
  • Mid Cap: Composite Score 76.2/100 (Tech: 80.3, Fundamental: 68.4)
  • Small Cap: Composite Score 74.8/100 (Tech: 79.6, Fundamental: 65.7)

Recommended Portfolio Allocation:
  • Large Cap: 60% (15 stocks) - Lower risk, steady returns
  • Mid Cap: 30% (20 stocks) - Balanced risk/return
  • Small Cap: 10% (10 stocks) - Higher risk, growth potential

Changes from Last Week:
  • 8 new entries (3 large, 3 mid, 2 small)
  • 8 stocks dropped from top picks
  • Average score improvement: +2.3 points
```

---

### 2. Large Cap Recommendations (60% Allocation)

```
═══════════════════════════════════════════════════════════════
LARGE CAP RECOMMENDATIONS (Top 15 of 100 stocks)
Market Cap > 100B SEK | Lower Risk | Steady Growth
═══════════════════════════════════════════════════════════════

Rank | Ticker    | Company Name        | Score | Tech | Fund | Price  | Recommendation
-----|-----------|---------------------|-------|------|------|--------|---------------
  1  | INVE-B.ST | Investor AB         | 92.5  | 94.2 | 88.7 | 245.60 | STRONG BUY ⬆️
  2  | ATCO-A.ST | Atlas Copco A       | 89.3  | 91.5 | 85.1 | 187.40 | STRONG BUY ⬆️
  3  | HEXA-B.ST | Hexagon AB          | 87.8  | 90.1 | 83.2 | 124.30 | BUY
  4  | EVO.ST    | Evolution Gaming    | 86.5  | 89.7 | 80.9 | 1,234  | BUY
  5  | SAND.ST   | Sandvik AB          | 85.2  | 88.3 | 79.4 | 234.20 | BUY
  ...  (continues for 15 stocks)

═══════════════════════════════════════════════════════════════
TOP 3 DETAILED ANALYSIS
═══════════════════════════════════════════════════════════════

1. INVE-B.ST - Investor AB (Score: 92.5)
   ────────────────────────────────────────────────────
   Market Cap: 852B SEK | Sector: Financial Services

   TECHNICAL INDICATORS (94.2/100):
   • Price vs MA200: ✅ +12.3% above (strong uptrend)
   • Price vs MA20: ✅ +4.2% above (short-term momentum)
   • RSI (7-day): 62 ✅ (Cardwell: bullish > 50)
   • Volume Confirmation: ✅ 1.8× average volume (research: 65% success)
   • 52-Week High: 94% of high ✅ (near all-time high)
   • MACD: Bullish crossover ✅
   • KAMA Trend: Strong uptrend ✅

   FUNDAMENTAL METRICS (88.7/100):
   • Piotroski F-Score: 8/9 ✅ (eliminates value traps)
   • Gross Profitability: 34.5% ✅ (superior indicator)
   • P/E Ratio: 18.3 ✅ (reasonable valuation)
   • Profit Margin: 28.4% ✅
   • Revenue Growth: 12.3% YoY ✅
   • Debt/Equity: 0.34 ✅ (low leverage)

   RECOMMENDATION: STRONG BUY ⬆️
   • Exceptional technical and fundamental scores
   • Strong institutional backing
   • Consistent dividend payer
   • Low risk, steady growth

   [PRICE CHART: 1-year trend with MA200, MA20, volume]

2. ATCO-A.ST - Atlas Copco A (Score: 89.3)
   ────────────────────────────────────────────────────
   [Similar detailed breakdown]

3. HEXA-B.ST - Hexagon AB (Score: 87.8)
   ────────────────────────────────────────────────────
   [Similar detailed breakdown]

═══════════════════════════════════════════════════════════════
COMPLETE LARGE CAP LIST (All 15 stocks)
═══════════════════════════════════════════════════════════════

Rank | Ticker    | Score | Tech | Fund | Price  | MA200 | RSI | Vol  | P/E  | Piotr
-----|-----------|-------|------|------|--------|-------|-----|------|------|------
  1  | INVE-B.ST | 92.5  | 94.2 | 88.7 | 245.60 | +12%  | 62  | 1.8× | 18.3 | 8
  2  | ATCO-A.ST | 89.3  | 91.5 | 85.1 | 187.40 | +10%  | 58  | 1.6× | 22.1 | 8
  3  | HEXA-B.ST | 87.8  | 90.1 | 83.2 | 124.30 | +8%   | 56  | 1.5× | 19.7 | 7
  ... (continues for all 15)
```

---

### 3. Mid Cap Recommendations (30% Allocation)

```
═══════════════════════════════════════════════════════════════
MID CAP RECOMMENDATIONS (Top 20 of 143 stocks)
Market Cap 10-100B SEK | Balanced Risk/Return | Growth Potential
═══════════════════════════════════════════════════════════════

Rank | Ticker    | Company Name        | Score | Tech | Fund | Price  | Recommendation
-----|-----------|---------------------|-------|------|------|--------|---------------
  1  | KINV-B.ST | Kinnevik AB         | 88.7  | 92.3 | 82.1 | 156.20 | STRONG BUY ⬆️
  2  | SWED-A.ST | Swedbank A          | 86.4  | 89.7 | 80.5 | 234.50 | BUY
  3  | SEB-A.ST  | SEB A               | 85.1  | 88.4 | 79.2 | 167.30 | BUY
  ...  (continues for 20 stocks)

[Similar detailed structure as Large Cap]
  • Top 3 detailed analysis
  • Complete table with all 20 stocks
  • Key metrics and indicators
```

---

### 4. Small Cap Recommendations (10% Allocation)

```
═══════════════════════════════════════════════════════════════
SMALL CAP RECOMMENDATIONS (Top 10 of 109 stocks)
Market Cap 1-10B SEK | Higher Risk | High Growth Potential
═══════════════════════════════════════════════════════════════

⚠️  WARNING: Small cap stocks carry higher risk and volatility
    Recommended allocation: Maximum 10% of portfolio

Rank | Ticker    | Company Name        | Score | Tech | Fund | Price  | Recommendation
-----|-----------|---------------------|-------|------|------|--------|---------------
  1  | XXXX.ST   | Company Name        | 82.3  | 87.5 | 73.2 | 45.60  | BUY
  2  | YYYY.ST   | Company Name        | 80.8  | 86.1 | 71.4 | 67.30  | BUY
  ...  (continues for 10 stocks)

[Similar detailed structure as Large Cap]
  • Top 3 detailed analysis
  • Complete table with all 10 stocks
  • Risk warnings prominent
```

---

### 5. Portfolio Construction Guide

```
═══════════════════════════════════════════════════════════════
RECOMMENDED PORTFOLIO CONSTRUCTION
═══════════════════════════════════════════════════════════════

Based on Modern Portfolio Theory and research-backed allocation:

TIER ALLOCATION:
┌─────────────────┬──────────┬──────────┬──────────────────┐
│ Tier            │ % Alloc  │ # Stocks │ Risk Level       │
├─────────────────┼──────────┼──────────┼──────────────────┤
│ Large Cap       │   60%    │    15    │ Low              │
│ Mid Cap         │   30%    │    20    │ Medium           │
│ Small Cap       │   10%    │    10    │ High             │
└─────────────────┴──────────┴──────────┴──────────────────┘

EXAMPLE 100,000 SEK PORTFOLIO:
• Large Cap: 60,000 SEK across 15 stocks (~4,000 SEK each)
• Mid Cap: 30,000 SEK across 20 stocks (~1,500 SEK each)
• Small Cap: 10,000 SEK across 10 stocks (~1,000 SEK each)

DIVERSIFICATION:
• Total stocks: 45
• Sector diversification: Automatic via scoring
• Market cap diversification: 60/30/10 split
• Rebalancing: Weekly review, quarterly reallocation

RISK MANAGEMENT:
• Stop Loss: 8% below entry price (research-backed)
• Position Sizing: Equal weight within each tier
• Maximum Single Stock: 4% of total portfolio
• Review Frequency: Weekly (every Friday)
```

---

### 6. Week-over-Week Comparison

```
═══════════════════════════════════════════════════════════════
CHANGES FROM LAST WEEK
═══════════════════════════════════════════════════════════════

NEW ENTRIES (8 stocks):
  Large Cap:
    • INVE-B.ST (Investor AB) - Score improved from 72.3 → 92.5
    • SAND.ST (Sandvik AB) - Met volume confirmation threshold
    • VOLV-B.ST (Volvo B) - Piotroski F-Score improved 6 → 8

  Mid Cap:
    • KINV-B.ST (Kinnevik AB) - Strong momentum breakout
    • SWED-A.ST (Swedbank A) - Technical score surge
    • SEB-A.ST (SEB A) - Fundamental improvement

  Small Cap:
    • XXXX.ST - New entry with strong growth
    • YYYY.ST - Volume confirmation triggered

DROPPED FROM LIST (8 stocks):
  Large Cap:
    • ERIC-B.ST (Ericsson B) - RSI dropped below 50 (Cardwell)
    • HM-B.ST (H&M B) - Volume confirmation lost
    • TELIA.ST (Telia) - Piotroski F-Score fell to 5

  Mid Cap:
    • [3 stocks with technical deterioration]

  Small Cap:
    • [2 stocks failed fundamental filters]

SCORE CHANGES (Significant moves):
  Improved:
    • INVE-B.ST: 72.3 → 92.5 (+20.2 points) - Exceptional
    • ATCO-A.ST: 84.1 → 89.3 (+5.2 points)
    • HEXA-B.ST: 82.6 → 87.8 (+5.2 points)

  Declined:
    • [Stocks that dropped but still made top N]
```

---

### 7. Market Statistics & Filters

```
═══════════════════════════════════════════════════════════════
ANALYSIS STATISTICS
═══════════════════════════════════════════════════════════════

STOCKS ANALYZED:
  • Total Universe: 352 Swedish stocks
  • Large Cap: 100 stocks analyzed
  • Mid Cap: 143 stocks analyzed
  • Small Cap: 109 stocks analyzed

FILTER PASS RATES:
  Technical Filters:
    • Above MA200 (long-term uptrend): 68% pass rate
    • Above MA20 (short-term momentum): 72% pass rate
    • RSI > 50 (Cardwell bullish): 64% pass rate
    • Volume confirmation (1.5× avg): 48% pass rate ← Critical filter
    • Near 52-week high (85%+): 34% pass rate

  Fundamental Filters:
    • Profitable (positive margins): 89% pass rate
    • Piotroski F-Score ≥ 7: 42% pass rate ← Critical filter
    • Gross Profitability ≥ 20%: 56% pass rate
    • P/E < 30: 78% pass rate
    • Revenue growth positive: 67% pass rate

  Combined Filters:
    • Passed all technical filters: 24% (85 stocks)
    • Passed all fundamental filters: 31% (109 stocks)
    • Passed ALL filters: 16% (56 stocks)
    • Selected as top picks: 13% (45 stocks)

AVERAGE SCORES:
  • All analyzed stocks: 52.3/100
  • Stocks passing filters: 68.7/100
  • Top picks (selected): 76.8/100
  • Score range: 45.2 - 92.5
  • Standard deviation: 12.4 points
```

---

### 8. Methodology Summary

```
═══════════════════════════════════════════════════════════════
ANALYSIS METHODOLOGY
═══════════════════════════════════════════════════════════════

RESEARCH-BACKED APPROACH:
Based on academic research (2018-2025) for Swedish stock market.
Expected performance: 8-12% annual alpha, 0.8-1.2 Sharpe ratio.

TECHNICAL ANALYSIS (70% weight):
  • RSI (7-period, Cardwell method): RSI > 50 = bullish
  • Volume Confirmation: 1.5× average = 65% success vs 39%
  • KAMA (adaptive MA): Reduces false signals 30-40%
  • MA200 & MA20: Long-term and short-term trend
  • MACD: Momentum confirmation
  • 52-week high proximity: Jegadeesh & Titman research

FUNDAMENTAL ANALYSIS (30% weight):
  • Gross Profitability: (Revenue - COGS) / Assets (superior to P/E)
  • Piotroski F-Score: 9-point quality score, ≥7 required
  • Profitability: Positive margins required
  • Valuation: P/E < 30 for reasonableness
  • Growth: Revenue and earnings trends

VALUE & MOMENTUM HYBRID:
  • Pure momentum Sharpe: 0.67
  • Pure value Sharpe: 0.73
  • Hybrid (50/50) Sharpe: 1.42 ← Best performance
  • Our blend: 70/30 technical/fundamental

REBALANCING:
  • Weekly review: Every Friday at 18:00 CET
  • Quarterly reallocation: Adjust positions
  • Research shows weekly optimal for Swedish stocks
```

---

### 9. Disclaimer & Risk Warning

```
═══════════════════════════════════════════════════════════════
DISCLAIMER
═══════════════════════════════════════════════════════════════

⚠️  IMPORTANT RISK INFORMATION:

This report is for informational purposes only and does not constitute
investment advice, financial advice, or a recommendation to buy or sell
any securities.

RISKS:
• Past performance does not guarantee future results
• Stock prices can go down as well as up
• You may lose some or all of your invested capital
• Small cap stocks carry higher volatility and risk
• Market conditions can change rapidly

LIMITATIONS:
• Analysis based on historical data and research
• Expected performance (8-12% alpha) is not guaranteed
• Individual results may vary significantly
• Market crashes can impact all stocks

RECOMMENDATIONS:
• Consult a licensed financial advisor before investing
• Only invest money you can afford to lose
• Diversify across asset classes (not just stocks)
• Understand your risk tolerance
• Review positions regularly

DATA SOURCES:
• Price data: Yahoo Finance
• Fundamentals: Yahoo Finance
• Analysis: Automated algorithm (not human review)
• Research: Academic papers 2018-2025

Last Updated: Friday, January 17, 2025 at 18:00 CET
═══════════════════════════════════════════════════════════════
```

---

## 📊 CSV Format Structure

**File**: `weekly_analysis_2025-01-17.csv`

```csv
Tier,Rank,Ticker,Company,CompositeScore,TechScore,FundScore,Price,MA200Dist,MA20Dist,RSI7,Volume1.5x,Near52wHigh,MACD,PiotroskiScore,GrossProfitability,PE,ProfitMargin,RevenueGrowth,DebtEquity,Recommendation
large_cap,1,INVE-B.ST,Investor AB,92.5,94.2,88.7,245.60,+12.3%,+4.2%,62,Yes,94%,Bullish,8,34.5%,18.3,28.4%,12.3%,0.34,STRONG BUY
large_cap,2,ATCO-A.ST,Atlas Copco A,89.3,91.5,85.1,187.40,+10.1%,+3.8%,58,Yes,91%,Bullish,8,31.2%,22.1,24.7%,10.5%,0.42,STRONG BUY
... (continues for all 45 stocks)
```

**Columns Explanation**:
- `Tier`: large_cap, mid_cap, small_cap
- `Rank`: 1-15, 1-20, 1-10 within tier
- `Ticker`: Stock ticker symbol
- `Company`: Company name
- `CompositeScore`: Overall score (0-100)
- `TechScore`: Technical analysis score (0-100)
- `FundScore`: Fundamental analysis score (0-100)
- `Price`: Current stock price (SEK)
- `MA200Dist`: Distance from 200-day MA (%)
- `MA20Dist`: Distance from 20-day MA (%)
- `RSI7`: 7-period RSI value
- `Volume1.5x`: Yes/No - meets 1.5× volume requirement
- `Near52wHigh`: % of 52-week high
- `MACD`: Bullish/Bearish signal
- `PiotroskiScore`: 0-9 score
- `GrossProfitability`: (Revenue - COGS) / Assets (%)
- `PE`: P/E ratio
- `ProfitMargin`: Net profit margin (%)
- `RevenueGrowth`: YoY revenue growth (%)
- `DebtEquity`: Debt to equity ratio
- `Recommendation`: STRONG BUY, BUY, HOLD

---

## 🎨 HTML Formatting Guidelines

**Styling**:
- Clean, professional layout with tables
- Color coding: Green for positive metrics, Red for negative
- Charts embedded as images (generated via matplotlib/plotly)
- Responsive design for mobile viewing
- Print-friendly CSS

**Sections**:
1. Header with date and summary (blue background)
2. Executive summary (gray box)
3. Tier sections with alternating backgrounds
4. Tables with hover effects
5. Charts with captions
6. Footer with disclaimer (red box)

**Fonts**:
- Headers: Bold, 16-20pt
- Body: 11-12pt
- Tables: Monospace for numbers
- Consistent spacing and margins

---

## 📅 File Naming Convention

**Pattern**: `weekly_analysis_{YYYY-MM-DD}.{ext}`

**Examples**:
- `weekly_analysis_2025-01-17.html`
- `weekly_analysis_2025-01-17.csv`
- `weekly_analysis_2025-01-17.json`

**Archive Location**: `reports/history/2025/01/`

**Retention**: Keep 180 days (6 months) of weekly reports

---

## 🔄 Generation Workflow

1. **Data Collection** (Friday 17:30-17:45)
   - Fetch latest price data for all 352 stocks
   - Update fundamentals cache
   - Verify data completeness

2. **Analysis** (Friday 17:45-17:55)
   - Calculate all technical indicators
   - Calculate all fundamental metrics
   - Generate composite scores
   - Apply filters
   - Rank stocks within tiers

3. **Report Generation** (Friday 17:55-18:00)
   - Generate HTML report
   - Generate CSV export
   - Generate JSON data
   - Save to reports directory
   - Archive previous week's report

4. **Validation** (Friday 18:00)
   - Verify all 45 stocks present
   - Check score calculations
   - Validate file integrity
   - Log completion status

---

## ✅ Quality Checklist

Before publishing weekly report, verify:

- [ ] All 352 stocks analyzed
- [ ] Exactly 15 large cap picks
- [ ] Exactly 20 mid cap picks
- [ ] Exactly 10 small cap picks
- [ ] All scores between 0-100
- [ ] All technical indicators calculated
- [ ] All fundamental metrics present
- [ ] Piotroski F-Score ≥ 7 for all picks
- [ ] Volume confirmation (1.5×) for all picks
- [ ] RSI > 50 (Cardwell) for all picks
- [ ] Charts generated successfully
- [ ] CSV export valid
- [ ] HTML renders correctly
- [ ] Disclaimer included
- [ ] Week-over-week comparison accurate
- [ ] Files saved with correct naming

---

## 📧 Optional Email Summary

If email notifications enabled:

**Subject**: Weekly Stock Analysis - January 17, 2025 (45 Picks)

**Body**:
```
Your weekly stock analysis is ready!

Top Picks This Week:
• 15 Large Cap stocks (60% allocation)
• 20 Mid Cap stocks (30% allocation)
• 10 Small Cap stocks (10% allocation)

Highlights:
• Best performer: INVE-B.ST (Score: 92.5)
• 8 new entries this week
• Average score improvement: +2.3 points

View full report: weekly_analysis_2025-01-17.html

Happy investing!
```

---

**End of Specification**
