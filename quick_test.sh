#!/bin/bash
# Quick test with random Swedish stocks

echo ""
echo "======================================================================"
echo "  QUICK STOCK ANALYSIS TEST"
echo "======================================================================"
echo ""

python3 << 'PYEOF'
from core.stock_analyzer import BatchAnalyzer
from core.settings_manager import get_settings

# Test stocks
TEST_STOCKS = ['VOLV-B.ST', 'ERIC-B.ST', 'INVE-B.ST', 'SWED-A.ST', 'ABB.ST']

print(f"Analyzing {len(TEST_STOCKS)} Swedish stocks...\n")

settings = get_settings()
analyzer = BatchAnalyzer(settings.as_dict())
results = analyzer.analyze_batch(TEST_STOCKS)

# Show results
print("\n" + "="*70)
print("ANALYSIS RESULTS")
print("="*70)

successful = [r for r in results if r.get('analysis_successful')]
print(f"Successfully analyzed: {len(successful)}/{len(TEST_STOCKS)}\n")

if successful:
    # Sort by score
    successful.sort(key=lambda x: x.get('composite_score', 0), reverse=True)

    print(f"{'Ticker':<12} {'Score':<8} {'Tech':<8} {'Fund':<8} {'Recommendation':<15}")
    print("-" * 70)

    for r in successful:
        ticker = r.get('ticker', 'N/A')
        score = r.get('composite_score', 0)
        tech = r.get('technical_score', 0)
        fund = r.get('fundamental_score', 0)
        rec = r.get('recommendation', 'N/A')

        print(f"{ticker:<12} {score:<8.1f} {tech:<8.1f} {fund:<8.1f} {rec:<15}")

    print("\n" + "="*70)
    print(f"Top Stock: {successful[0]['ticker']} (Score: {successful[0].get('composite_score', 0):.1f})")
    print("="*70)

PYEOF
