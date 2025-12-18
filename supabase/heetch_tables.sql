-- Tables Heetch pour le scraping des données driver.heetch.com

-- Table des drivers Heetch
CREATE TABLE IF NOT EXISTS heetch_drivers (
    id VARCHAR NOT NULL PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    first_name VARCHAR NOT NULL DEFAULT '',
    last_name VARCHAR NOT NULL DEFAULT '',
    email VARCHAR NOT NULL,
    image_url VARCHAR,
    active BOOLEAN DEFAULT TRUE
);

-- Index pour heetch_drivers
CREATE INDEX IF NOT EXISTS ix_heetch_drivers_id ON heetch_drivers(id);
CREATE INDEX IF NOT EXISTS ix_heetch_drivers_org_id ON heetch_drivers(org_id);
CREATE INDEX IF NOT EXISTS ix_heetch_drivers_email ON heetch_drivers(email);

-- Table des earnings Heetch
CREATE TABLE IF NOT EXISTS heetch_earnings (
    id VARCHAR NOT NULL PRIMARY KEY,
    org_id VARCHAR NOT NULL,
    driver_id VARCHAR NOT NULL,
    date DATE NOT NULL,
    period VARCHAR NOT NULL,
    gross_earnings FLOAT DEFAULT 0,
    net_earnings FLOAT DEFAULT 0,
    cash_collected FLOAT DEFAULT 0,
    card_gross_earnings FLOAT DEFAULT 0,
    cash_commission_fees FLOAT DEFAULT 0,
    card_commission_fees FLOAT DEFAULT 0,
    cancellation_fees FLOAT DEFAULT 0,
    cancellation_fee_adjustments FLOAT DEFAULT 0,
    bonuses FLOAT DEFAULT 0,
    terminated_rides INTEGER DEFAULT 0,
    cancelled_rides INTEGER DEFAULT 0,
    cash_discount FLOAT DEFAULT 0,
    currency VARCHAR DEFAULT 'EUR'
);

-- Index pour heetch_earnings
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_id ON heetch_earnings(id);
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_org_id ON heetch_earnings(org_id);
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_driver_id ON heetch_earnings(driver_id);
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_date ON heetch_earnings(date);
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_period ON heetch_earnings(period);

-- Commentaires pour documentation
COMMENT ON TABLE heetch_drivers IS 'Drivers Heetch extraits depuis les données earnings';
COMMENT ON TABLE heetch_earnings IS 'Earnings Heetch par driver, date et période (weekly/monthly)';
COMMENT ON COLUMN heetch_earnings.id IS 'ID composite: driver_id_date_period';
COMMENT ON COLUMN heetch_earnings.terminated_rides IS 'Nombre de courses terminées';
COMMENT ON COLUMN heetch_earnings.cancelled_rides IS 'Nombre de courses annulées';

