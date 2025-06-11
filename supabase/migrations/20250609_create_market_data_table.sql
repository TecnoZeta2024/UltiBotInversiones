-- Create market_data table optimized for time-series data storage
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(30) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open NUMERIC(24, 8) NOT NULL,
    high NUMERIC(24, 8) NOT NULL,
    low NUMERIC(24, 8) NOT NULL,
    close NUMERIC(24, 8) NOT NULL,
    volume NUMERIC(36, 8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add indexes for efficient querying
CREATE INDEX idx_market_data_symbol ON market_data(symbol);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp);
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp);

-- Add hypertable extension for efficient time-series storage
-- This requires the TimescaleDB extension to be enabled in Supabase
-- SELECT create_hypertable('market_data', 'timestamp');

-- Add comment to the table
COMMENT ON TABLE market_data IS 'Historical market data for trading and AI analysis';
