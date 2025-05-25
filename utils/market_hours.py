import pytz
from datetime import datetime, time, timedelta
import holidays

class MarketHoursChecker:
    """Check if various stock markets are open"""
    
    def __init__(self):
        # Define market hours for different exchanges
        self.market_hours = {
            'NYSE': {
                'timezone': pytz.timezone('America/New_York'),
                'open_time': time(9, 30),
                'close_time': time(16, 0),
                'holidays': holidays.NYSE()
            },
            'NASDAQ': {
                'timezone': pytz.timezone('America/New_York'),
                'open_time': time(9, 30),
                'close_time': time(16, 0),
                'holidays': holidays.NYSE()  # Same as NYSE
            },
            'STOCKHOLM': {
                'timezone': pytz.timezone('Europe/Stockholm'),
                'open_time': time(9, 0),
                'close_time': time(17, 30),
                'holidays': holidays.Sweden()
            }
        }
    
    def is_market_open(self, exchange='NYSE'):
        """Check if a specific market is currently open"""
        if exchange not in self.market_hours:
            exchange = 'NYSE'  # Default
            
        market = self.market_hours[exchange]
        tz = market['timezone']
        now = datetime.now(tz)
        
        # Check if weekend
        if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False
            
        # Check if holiday
        if now.date() in market['holidays']:
            return False
            
        # Check if within market hours
        current_time = now.time()
        return market['open_time'] <= current_time <= market['close_time']
    
    def get_last_market_close(self, exchange='NYSE'):
        """Get the last time the market closed"""
        market = self.market_hours.get(exchange, self.market_hours['NYSE'])
        tz = market['timezone']
        now = datetime.now(tz)
        
        # Start from today
        check_date = now.date()
        
        # Go back until we find a trading day
        for i in range(7):  # Check up to a week back
            if check_date.weekday() < 5 and check_date not in market['holidays']:
                # This was a trading day
                return tz.localize(datetime.combine(check_date, market['close_time']))
            check_date = check_date - timedelta(days=1)
            
        # Fallback
        return now - timedelta(days=1)
    
    def should_use_cached_data(self, data_timestamp, exchange='NYSE'):
        """Determine if we should use cached data instead of fetching new"""
        if not self.is_market_open(exchange):
            # Market is closed - check when it last closed
            last_close = self.get_last_market_close(exchange)
            
            # If data is from after the last market close, it's fresh enough
            if data_timestamp and data_timestamp > last_close.timestamp():
                return True
                
        return False
    
    def get_market_status_text(self, exchange='NYSE'):
        """Get human-readable market status"""
        if self.is_market_open(exchange):
            return f"{exchange} Market Open"
        else:
            market = self.market_hours.get(exchange, self.market_hours['NYSE'])
            tz = market['timezone']
            now = datetime.now(tz)
            
            if now.weekday() >= 5:
                return f"{exchange} Market Closed (Weekend)"
            elif now.date() in market['holidays']:
                return f"{exchange} Market Closed (Holiday)"
            else:
                return f"{exchange} Market Closed (After Hours)"