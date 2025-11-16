"""
Market-Aware Caching Utility for Swedish Stock Market

Implements intelligent cache expiration based on Stockholm Stock Exchange hours:
- Market hours: 09:00 - 17:30 CET
- Trading days: Monday - Friday
- Closed: Weekends and Swedish holidays

Key insight: No need to fetch new data when market is closed!
"""

from datetime import datetime, time, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)

# Swedish timezone
STOCKHOLM_TZ = pytz.timezone('Europe/Stockholm')

# Market hours (Stockholm Stock Exchange)
MARKET_OPEN = time(9, 0)    # 09:00 CET
MARKET_CLOSE = time(17, 30)  # 17:30 CET

# Swedish stock exchange holidays (2025)
# Note: Update yearly
SWEDISH_HOLIDAYS_2025 = {
    datetime(2025, 1, 1),   # New Year's Day
    datetime(2025, 1, 6),   # Epiphany
    datetime(2025, 4, 18),  # Good Friday
    datetime(2025, 4, 21),  # Easter Monday
    datetime(2025, 5, 1),   # Labour Day
    datetime(2025, 5, 29),  # Ascension Day
    datetime(2025, 6, 6),   # National Day
    datetime(2025, 6, 20),  # Midsummer Eve (half day)
    datetime(2025, 12, 24), # Christmas Eve (half day)
    datetime(2025, 12, 25), # Christmas Day
    datetime(2025, 12, 26), # Boxing Day
    datetime(2025, 12, 31), # New Year's Eve (half day)
}


def is_market_open(check_time: datetime = None) -> bool:
    """
    Check if Stockholm Stock Exchange is currently open.

    Args:
        check_time: Time to check (defaults to now in Stockholm timezone)

    Returns:
        bool: True if market is open, False otherwise
    """
    if check_time is None:
        check_time = datetime.now(STOCKHOLM_TZ)
    elif check_time.tzinfo is None:
        # Assume UTC if no timezone
        check_time = check_time.replace(tzinfo=pytz.UTC).astimezone(STOCKHOLM_TZ)

    # Check if weekend
    if check_time.weekday() >= 5:  # Saturday=5, Sunday=6
        return False

    # Check if Swedish holiday
    check_date = check_time.date()
    for holiday in SWEDISH_HOLIDAYS_2025:
        if check_date == holiday.date():
            return False

    # Check market hours
    current_time = check_time.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def get_next_market_open(from_time: datetime = None) -> datetime:
    """
    Get the next time the market opens.

    Args:
        from_time: Starting time (defaults to now in Stockholm timezone)

    Returns:
        datetime: Next market open time
    """
    if from_time is None:
        from_time = datetime.now(STOCKHOLM_TZ)
    elif from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=pytz.UTC).astimezone(STOCKHOLM_TZ)

    # Start checking from the next minute
    check_time = from_time + timedelta(minutes=1)

    # Maximum 10 days ahead (to handle long holidays)
    for _ in range(10 * 24 * 60):  # Check every minute for 10 days
        if is_market_open(check_time):
            # Set to market open time
            return check_time.replace(hour=MARKET_OPEN.hour,
                                     minute=MARKET_OPEN.minute,
                                     second=0,
                                     microsecond=0)
        check_time += timedelta(minutes=60)  # Jump by hour for efficiency

    # Fallback: return next Monday 09:00
    days_ahead = (7 - from_time.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_monday = from_time + timedelta(days=days_ahead)
    return next_monday.replace(hour=MARKET_OPEN.hour,
                              minute=MARKET_OPEN.minute,
                              second=0,
                              microsecond=0)


def should_refresh_cache(
    cached_timestamp: int,
    cache_hours_during_trading: int = 5,
    current_time: datetime = None
) -> bool:
    """
    Determine if cache should be refreshed based on market hours.

    Market-aware logic:
    - If market is CLOSED: Cache is valid until market opens
    - If market is OPEN: Use standard cache duration (default 5 hours)

    Args:
        cached_timestamp: Unix timestamp when data was cached
        cache_hours_during_trading: Cache duration during trading hours (default 5)
        current_time: Current time (defaults to now in Stockholm)

    Returns:
        bool: True if cache should be refreshed, False if still valid
    """
    if current_time is None:
        current_time = datetime.now(STOCKHOLM_TZ)
    elif current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=pytz.UTC).astimezone(STOCKHOLM_TZ)

    # Convert cached timestamp to datetime
    cached_time = datetime.fromtimestamp(cached_timestamp, tz=STOCKHOLM_TZ)

    # Calculate cache age
    cache_age_seconds = (current_time - cached_time).total_seconds()
    cache_age_hours = cache_age_seconds / 3600

    # If market is currently OPEN
    if is_market_open(current_time):
        # Use standard cache duration (e.g., 5 hours)
        should_refresh = cache_age_hours >= cache_hours_during_trading

        if should_refresh:
            logger.info(
                f"Market OPEN: Cache expired ({cache_age_hours:.1f}h > {cache_hours_during_trading}h)"
            )
        else:
            logger.info(
                f"Market OPEN: Cache valid ({cache_age_hours:.1f}h < {cache_hours_during_trading}h)"
            )

        return should_refresh

    # Market is CLOSED
    # Check if cache was created AFTER last market close
    last_close = current_time.replace(hour=MARKET_CLOSE.hour,
                                      minute=MARKET_CLOSE.minute,
                                      second=0,
                                      microsecond=0)

    # If today is past market close, that's the last close
    # If today is before market open or weekend, find yesterday's close
    if current_time.time() < MARKET_OPEN or current_time.weekday() >= 5:
        # Go back to previous trading day
        days_back = 1
        if current_time.weekday() == 6:  # Sunday
            days_back = 2
        elif current_time.weekday() == 0 and current_time.time() < MARKET_OPEN:  # Monday before open
            days_back = 3
        last_close = last_close - timedelta(days=days_back)

    # If cache was created AFTER last market close, it's still valid
    if cached_time >= last_close:
        next_open = get_next_market_open(current_time)
        time_until_open = (next_open - current_time).total_seconds() / 3600

        logger.info(
            f"Market CLOSED: Cache valid (created after last close at {last_close.strftime('%Y-%m-%d %H:%M')})"
        )
        logger.info(
            f"Next market open: {next_open.strftime('%Y-%m-%d %H:%M')} ({time_until_open:.1f}h from now)"
        )

        return False  # Don't refresh - no new data available

    # Cache was created before last close - needs refresh when market opens
    logger.info(
        f"Market CLOSED: Cache old (created {cached_time.strftime('%Y-%m-%d %H:%M')}, before last close)"
    )
    logger.info(
        f"Will refresh when market opens at {get_next_market_open(current_time).strftime('%Y-%m-%d %H:%M')}"
    )

    return False  # Don't refresh now - wait for market to open


def get_cache_expiration_time(
    cache_hours_during_trading: int = 5,
    from_time: datetime = None
) -> datetime:
    """
    Get the absolute expiration time for a cache entry.

    Args:
        cache_hours_during_trading: Cache duration during trading hours
        from_time: When the cache was created (defaults to now)

    Returns:
        datetime: When the cache should expire
    """
    if from_time is None:
        from_time = datetime.now(STOCKHOLM_TZ)
    elif from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=pytz.UTC).astimezone(STOCKHOLM_TZ)

    # If market is open, expire after N hours
    if is_market_open(from_time):
        return from_time + timedelta(hours=cache_hours_during_trading)

    # If market is closed, expire at next market open
    return get_next_market_open(from_time)


# Convenience function for the automatic analysis system
def is_stale_cache(cached_timestamp: int, data_type: str = 'price') -> bool:
    """
    Check if cached data is stale and needs refresh.

    Args:
        cached_timestamp: Unix timestamp when data was cached
        data_type: 'price' (5h cache) or 'fundamentals' (24h cache)

    Returns:
        bool: True if stale (needs refresh), False if fresh
    """
    cache_hours = 5 if data_type == 'price' else 24
    return should_refresh_cache(cached_timestamp, cache_hours)
