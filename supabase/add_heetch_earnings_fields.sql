-- Ajouter les champs manquants à la table heetch_earnings
-- Migration 0006_add_missing_fields_to_heetch_earnings

-- Ajouter les nouvelles colonnes
ALTER TABLE heetch_earnings 
ADD COLUMN IF NOT EXISTS start_date DATE,
ADD COLUMN IF NOT EXISTS end_date DATE,
ADD COLUMN IF NOT EXISTS unpaid_cash_rides_refunds FLOAT,
ADD COLUMN IF NOT EXISTS debt FLOAT,
ADD COLUMN IF NOT EXISTS money_transfer_amount FLOAT;

-- Créer les index pour les nouvelles colonnes date
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_start_date ON heetch_earnings(start_date);
CREATE INDEX IF NOT EXISTS ix_heetch_earnings_end_date ON heetch_earnings(end_date);

