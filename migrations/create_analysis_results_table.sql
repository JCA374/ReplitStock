-- Create analysis_results table to store batch analysis results
CREATE TABLE IF NOT EXISTS public.analysis_results (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    analysis_date TIMESTAMP NOT NULL,
    price FLOAT,
    tech_score INTEGER,
    signal VARCHAR(10),
    above_ma40 BOOLEAN,
    above_ma4 BOOLEAN,
    rsi_value FLOAT,
    rsi_above_50 BOOLEAN,
    near_52w_high BOOLEAN,
    pe_ratio FLOAT,
    profit_margin FLOAT,
    revenue_growth FLOAT,
    is_profitable BOOLEAN,
    data_source VARCHAR(20),
    last_updated BIGINT,
    CONSTRAINT analysis_results_unique UNIQUE (ticker, analysis_date)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_analysis_results_ticker ON public.analysis_results(ticker);
CREATE INDEX IF NOT EXISTS idx_analysis_results_date ON public.analysis_results(analysis_date);