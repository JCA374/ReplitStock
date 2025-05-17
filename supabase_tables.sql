-- Create watchlist table
CREATE TABLE IF NOT EXISTS public.watchlist (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100),
    exchange VARCHAR(50),
    sector VARCHAR(50),
    added_date VARCHAR(20)
);

-- Create stock_data_cache table
CREATE TABLE IF NOT EXISTS public.stock_data_cache (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    period VARCHAR(10) NOT NULL,
    data TEXT,
    timestamp BIGINT,
    source VARCHAR(20),
    CONSTRAINT stock_data_cache_unique UNIQUE (ticker, timeframe, period, source)
);

-- Create fundamentals_cache table
CREATE TABLE IF NOT EXISTS public.fundamentals_cache (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL UNIQUE,
    pe_ratio FLOAT,
    profit_margin FLOAT,
    revenue_growth FLOAT,
    earnings_growth FLOAT,
    book_value FLOAT,
    market_cap FLOAT,
    dividend_yield FLOAT,
    last_updated BIGINT
);

-- Insert a test row into watchlist
INSERT INTO public.watchlist (ticker, name, exchange, sector, added_date)
VALUES ('TEST', 'Test Stock', 'TEST-EXCHANGE', 'Technology', CURRENT_DATE)
ON CONFLICT (ticker) DO NOTHING;

-- Select from watchlist to verify data
SELECT * FROM public.watchlist;