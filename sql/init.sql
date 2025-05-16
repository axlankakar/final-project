-- Create the stockdata database if it doesn't exist
CREATE DATABASE stockdata;

\c stockdata;

-- Create tables for stock data
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    volume INTEGER NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS price_stats (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    price_range DECIMAL(10,2) NOT NULL,
    volatility DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    value DECIMAL(10,2) NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX idx_stock_prices_symbol ON stock_prices(symbol);
CREATE INDEX idx_stock_prices_timestamp ON stock_prices(timestamp);
CREATE INDEX idx_price_stats_symbol ON price_stats(symbol);
CREATE INDEX idx_anomalies_symbol ON anomalies(symbol);

-- Create views for common queries
CREATE VIEW vw_latest_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    price,
    volume,
    timestamp
FROM stock_prices
ORDER BY symbol, timestamp DESC;

CREATE VIEW vw_daily_stats AS
SELECT
    symbol,
    date_trunc('day', timestamp) as date,
    MAX(price) as high,
    MIN(price) as low,
    AVG(price) as avg_price,
    SUM(volume) as total_volume
FROM stock_prices
GROUP BY symbol, date_trunc('day', timestamp);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow; 