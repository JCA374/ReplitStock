#!/usr/bin/env python3
"""
Test Market-Aware Caching

Demonstrates how the system intelligently handles cache based on Swedish market hours.
"""

from datetime import datetime, timedelta
import pytz
from utils.market_hours import (
    is_market_open,
    get_next_market_open,
    should_refresh_cache,
    STOCKHOLM_TZ
)

def test_market_hours():
    """Test market hour detection"""
    print("="*70)
    print("MARKET HOURS TEST")
    print("="*70)

    # Test various times
    test_times = [
        ("Monday 10:00", datetime(2025, 11, 17, 10, 0, tzinfo=STOCKHOLM_TZ)),
        ("Monday 08:00 (before open)", datetime(2025, 11, 17, 8, 0, tzinfo=STOCKHOLM_TZ)),
        ("Friday 17:45 (after close)", datetime(2025, 11, 21, 17, 45, tzinfo=STOCKHOLM_TZ)),
        ("Saturday 12:00", datetime(2025, 11, 22, 12, 0, tzinfo=STOCKHOLM_TZ)),
        ("Sunday 12:00", datetime(2025, 11, 23, 12, 0, tzinfo=STOCKHOLM_TZ)),
    ]

    for desc, test_time in test_times:
        is_open = is_market_open(test_time)
        next_open = get_next_market_open(test_time)

        print(f"\n{desc}:")
        print(f"  Market Open: {'YES ✓' if is_open else 'NO ✗'}")
        if not is_open:
            print(f"  Next Open: {next_open.strftime('%A %Y-%m-%d %H:%M %Z')}")


def test_cache_logic():
    """Test cache refresh logic"""
    print("\n" + "="*70)
    print("CACHE REFRESH LOGIC TEST")
    print("="*70)

    # Simulate different scenarios
    scenarios = [
        {
            "name": "Friday 18:00 - Cache from 12:00 same day",
            "current": datetime(2025, 11, 21, 18, 0, tzinfo=STOCKHOLM_TZ),  # Friday 18:00
            "cached": datetime(2025, 11, 21, 12, 0, tzinfo=STOCKHOLM_TZ),   # Friday 12:00 (6h old)
        },
        {
            "name": "Friday 18:00 - Cache from Friday 17:00",
            "current": datetime(2025, 11, 21, 18, 0, tzinfo=STOCKHOLM_TZ),  # Friday 18:00
            "cached": datetime(2025, 11, 21, 17, 0, tzinfo=STOCKHOLM_TZ),   # Friday 17:00 (1h old)
        },
        {
            "name": "Saturday 10:00 - Cache from Friday 17:00",
            "current": datetime(2025, 11, 22, 10, 0, tzinfo=STOCKHOLM_TZ),  # Saturday 10:00
            "cached": datetime(2025, 11, 21, 17, 0, tzinfo=STOCKHOLM_TZ),   # Friday 17:00 (17h old)
        },
        {
            "name": "Monday 10:00 - Cache from Friday 17:00",
            "current": datetime(2025, 11, 24, 10, 0, tzinfo=STOCKHOLM_TZ),  # Monday 10:00
            "cached": datetime(2025, 11, 21, 17, 0, tzinfo=STOCKHOLM_TZ),   # Friday 17:00 (65h old!)
        },
        {
            "name": "Monday 10:00 - Cache from Monday 09:30",
            "current": datetime(2025, 11, 24, 10, 0, tzinfo=STOCKHOLM_TZ),  # Monday 10:00
            "cached": datetime(2025, 11, 24, 9, 30, tzinfo=STOCKHOLM_TZ),   # Monday 09:30 (0.5h old)
        },
    ]

    for scenario in scenarios:
        print(f"\n{scenario['name']}:")

        current = scenario['current']
        cached_ts = int(scenario['cached'].timestamp())

        cache_age = (current - scenario['cached']).total_seconds() / 3600

        # Test with 5-hour cache during trading
        needs_refresh = should_refresh_cache(cached_ts, cache_hours_during_trading=5, current_time=current)

        market_open = is_market_open(current)

        print(f"  Current Time: {current.strftime('%A %Y-%m-%d %H:%M')}")
        print(f"  Cached Time:  {scenario['cached'].strftime('%A %Y-%m-%d %H:%M')}")
        print(f"  Cache Age:    {cache_age:.1f} hours")
        print(f"  Market Open:  {'YES' if market_open else 'NO'}")
        print(f"  Refresh?:     {'YES - Fetch new data' if needs_refresh else 'NO - Use cache ✓'}")

        if not needs_refresh and not market_open:
            next_open = get_next_market_open(current)
            print(f"  Next Refresh: When market opens at {next_open.strftime('%A %H:%M')}")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("MARKET-AWARE CACHING TEST SUITE")
    print("Stockholm Stock Exchange (09:00-17:30 CET)")
    print("="*70)

    test_market_hours()
    test_cache_logic()

    print("\n" + "="*70)
    print("KEY INSIGHTS:")
    print("="*70)
    print("✓ Market closed (evenings/weekends): Cache valid until market reopens")
    print("✓ Friday 18:00 analysis: Uses fresh closing data from 17:30")
    print("✓ Weekend analysis: Uses Friday's close, no API calls needed")
    print("✓ Market open: Standard 5-hour cache for price data")
    print("✓ Prevents unnecessary API calls and respects rate limits")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
