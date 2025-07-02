# Scanner Alignment Fix - Implementation Guide

## Overview
The **single stock analysis** (`strategy.py`) follows best practices with its weighted scoring system. The batch scanner needs to be aligned to use the same methodology.

## Best Practice Principles
1. **Weighted scoring** for technical factors (not all indicators are equally important)
2. **Consistent signal generation** across all analysis methods
3. **Single source of truth** for scoring logic (DRY principle)

## Implementation Steps

### Step 1: Update `analysis/bulk_scanner.py`

**FIND this code block (around line 340-370):**
```python
# Get tech score
tech_score = signals.get('tech_score', 0)

# Check fundamental pass
fundamental_pass = fundamental_analysis['overall'].get(
    'value_momentum_pass', False)

# Generate Value & Momentum signal
if tech_score >= 70 and fundamental_pass:
    value_momentum_signal = "BUY"
elif tech_score < 40 or not signals.get('above_ma40', False):
    value_momentum_signal = "SELL"
else:
    value_momentum_signal = "HOLD"
```

**REPLACE with:**
```python
# Calculate tech score using the strategy's weighted method
if not hasattr(self, '_strategy'):
    from analysis.strategy import ValueMomentumStrategy
    self._strategy = ValueMomentumStrategy()

tech_score = self._strategy._calculate_tech_score(signals)
signals['tech_score'] = tech_score  # Update signals with calculated score

# Check fundamental pass
fundamental_pass = fundamental_analysis['overall'].get(
    'value_momentum_pass', False)

# Generate Value & Momentum signal (using strategy's logic)
if tech_score >= 70 and fundamental_pass:
    value_momentum_signal = "BUY"
elif tech_score < 40 or not signals.get('above_ma40', False):
    value_momentum_signal = "SELL"
else:
    value_momentum_signal = "HOLD"
```

### Step 2: Update imports in `analysis/bulk_scanner.py`

**FIND the imports section at the top:**
```python
from analysis.technical import calculate_all_indicators, generate_technical_signals
from analysis.fundamental import analyze_fundamentals
```

**ADD this import:**
```python
from analysis.strategy import ValueMomentumStrategy
```

### Step 3: Fix the signal name mismatch in `analysis/technical.py`

**FIND this line (around line 275):**
```python
'breakout_up': detect_breakout(indicators),
```

**REPLACE with:**
```python
'breakout': detect_breakout(indicators),
'breakout_up': detect_breakout(indicators),  # Keep for backward compatibility
```

### Step 4: Remove tech_score calculation from `generate_technical_signals()`

**FIND this entire section in `analysis/technical.py` (around line 280-330):**
```python
# Tech factors for Value & Momentum Strategy
tech_factors = [
    signals.get('above_ma40', False),
    signals.get('above_ma4', False),
    signals.get('rsi_above_50', False),
    signals.get('higher_lows', False),
    signals.get('near_52w_high', False),
    signals.get('breakout_up', False),
    signals.get('price_above_sma_medium', False)
]

# Calculate tech score (0-100)
valid_factors = [
    factor for factor in tech_factors if factor is not None]

if not valid_factors:
    tech_score = 50
else:
    total_factors = len(valid_factors)
    positive_factors = sum(1 for factor in valid_factors if factor)
    tech_score = int((positive_factors / total_factors) * 100)

tech_score = max(1, tech_score)

# Signal Classification
if tech_score >= 70 and signals.get('above_ma40', False):
    overall_signal = "BUY"
elif tech_score < 40 or signals.get('above_ma40') is False:
    overall_signal = "SELL"
else:
    overall_signal = "HOLD"

signals['tech_score'] = tech_score
signals['overall_signal'] = overall_signal
signals['signal_strength'] = tech_score
```

**REPLACE with:**
```python
# Tech score will be calculated by the strategy class
# This ensures consistency across single and batch analysis
signals['tech_score'] = None  # Will be calculated by strategy
signals['overall_signal'] = None  # Will be determined by strategy
signals['signal_strength'] = None  # Will be set by strategy
```

### Step 5: Update `analysis/scanner.py` for consistency

**FIND this section (around line 100-120):**
```python
# Value & Momentum Strategy logic
fundamental_pass = fundamental_analysis['overall'].get(
    'value_momentum_pass', False)

if tech_score >= 70 and fundamental_pass:
    value_momentum_signal = "BUY"
elif tech_score < 40 or not signals.get('above_ma40', False):
    value_momentum_signal = "SELL"
else:
    value_momentum_signal = "HOLD"
```

**REPLACE with:**
```python
# Use strategy instance for consistent scoring
if not hasattr(self, '_strategy'):
    from analysis.strategy import ValueMomentumStrategy
    self._strategy = ValueMomentumStrategy()

# Recalculate tech score using strategy's method
tech_score = self._strategy._calculate_tech_score(signals)
signals['tech_score'] = tech_score

# Value & Momentum Strategy logic
fundamental_pass = fundamental_analysis['overall'].get(
    'value_momentum_pass', False)

if tech_score >= 70 and fundamental_pass:
    value_momentum_signal = "BUY"
elif tech_score < 40 or not signals.get('above_ma40', False):
    value_momentum_signal = "SELL"
else:
    value_momentum_signal = "HOLD"
```

## Testing the Fix

After implementation, test with ORES.ST:

1. Run single stock analysis for ORES.ST
2. Run batch analysis including ORES.ST
3. Both should show the same:
   - Tech Score
   - Signal (BUY/SELL/HOLD)
   - Technical indicators

## Expected Results

- **Consistent recommendations** across all analysis methods
- **Weighted scoring** that properly reflects indicator importance
- **Single source of truth** for scoring logic in `strategy.py`

## Why This is Best Practice

1. **DRY Principle**: One scoring method defined in one place
2. **Consistency**: Users get same results regardless of analysis method
3. **Maintainability**: Changes to scoring logic only need to be made in one place
4. **Accuracy**: Weighted scoring better reflects real trading strategies
5. **Professional**: Aligns with how institutional investors score stocks

## Additional Improvement (Optional)

Consider making `_calculate_tech_score` a public method in `strategy.py`:

**CHANGE:**
```python
def _calculate_tech_score(self, tech_analysis):
```

**TO:**
```python
def calculate_tech_score(self, tech_analysis):
```

This makes it clear that this method is intended to be used by other modules.