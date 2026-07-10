-- =========================================================
-- Formative 1 - Task 2: Relational (MySQL) schema
-- Dataset: AAPL daily OHLCV time series
-- =========================================================

CREATE DATABASE IF NOT EXISTS stock_timeseries;
USE stock_timeseries;

-- ---------------------------------------------------------
-- 1. companies: one row per stock ticker
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
    company_id   INT AUTO_INCREMENT PRIMARY KEY,
    symbol       VARCHAR(10)  NOT NULL UNIQUE,
    company_name VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 2. daily_prices: one row per (company, trading day)
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS daily_prices (
    price_id    BIGINT AUTO_INCREMENT PRIMARY KEY,
    company_id  INT NOT NULL,
    price_date  DATE NOT NULL,
    open_price  DECIMAL(10, 4) NOT NULL,
    high_price  DECIMAL(10, 4) NOT NULL,
    low_price   DECIMAL(10, 4) NOT NULL,
    close_price DECIMAL(10, 4) NOT NULL,
    volume      BIGINT NOT NULL,
    CONSTRAINT fk_daily_prices_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE,
    CONSTRAINT uq_company_date UNIQUE (company_id, price_date)
) ENGINE=InnoDB;

CREATE INDEX idx_daily_prices_date ON daily_prices(price_date);

-- ---------------------------------------------------------
-- 3. predictions: model forecasts logged against a real date
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id   BIGINT AUTO_INCREMENT PRIMARY KEY,
    company_id      INT NOT NULL,
    price_date      DATE NOT NULL,
    predicted_close DECIMAL(10, 4) NOT NULL,
    model_name      VARCHAR(50) NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_predictions_company
        FOREIGN KEY (company_id) REFERENCES companies(company_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_predictions_date ON predictions(price_date);
