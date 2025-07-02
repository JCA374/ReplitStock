I'll search your project knowledge to understand the technical specification and then investigate why you're getting different results between single vs batch analysis for ORES.ST.Now let me search for information about ORES.ST and the single vs batch analysis difference:Let me search for more specific information about the issue with ORES.ST:Based on my analysis of your project knowledge, I can see the issue clearly. You're getting different results for ORES.ST between single vs batch analysis because the **tech score calculation methods are different** between the two analysis paths.

## Problem Identification

According to your technical specification and fix documentation, you have a consistency issue where:

1. **Single stock analysis** (via `strategy.py`) uses a **weighted scoring system** with `_calculate_tech_score()` method
2. **Batch analysis** (via `bulk_scanner.py` and `scanner.py`) uses a different tech score calculation that just takes `signals.get('tech_score', 0)` directly from the technical analysis

This divergence violates the **Single Source of Truth** principle outlined in your technical spec.

## Code Changes Required

You need to make the batch analysis use the same weighted scoring system as the single analysis. Here are the exact changes:

### 1. Update `analysis/bulk_scanner.py`

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

### 2. Update `analysis/scanner.py`

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

### 3. Update `analysis/technical.py`

**FIND this section (around line 270-280):**
```python
# Tech score will be calculated by the strategy class
# This ensures consistency across single and batch analysis
signals['tech_score'] = None  # Will be calculated by strategy
signals['overall_signal'] = None  # Will be determined by strategy
signals['signal_strength'] = None  # Will be set by strategy
```

**CONFIRM this is already set to `None`** - this ensures the strategy calculates it rather than technical.py

## Why This Fixes the Issue

1. **Single Source of Truth**: All analysis paths now use the same weighted scoring method from `strategy.py`
2. **Consistency**: ORES.ST will show identical tech scores and signals regardless of analysis method
3. **Best Practice**: Follows the DRY principle outlined in your technical spec
4. **Maintainability**: Changes to scoring logic only need to be made in one place

## Testing After Implementation

1. Run single stock analysis for ORES.ST
2. Run batch analysis including ORES.ST  
3. Both should now show identical:
   - Tech Score
   - Signal (BUY/SELL/HOLD)
   - Technical indicators

This alignment ensures your application follows the technical specification's core principle of **database-first approach with consistent analysis methods** across all interfaces.