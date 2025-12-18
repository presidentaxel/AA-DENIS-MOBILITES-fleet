-- Table pour stocker les cookies de session Heetch de manière persistante
-- Permet de restaurer la session et éviter de redemander le numéro de téléphone

CREATE TABLE IF NOT EXISTS heetch_session_cookies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    cookies JSONB NOT NULL, -- Stocke les cookies au format JSON
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, phone_number)
);

-- Index pour les recherches rapides
CREATE INDEX IF NOT EXISTS idx_heetch_session_cookies_org_phone ON heetch_session_cookies(org_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_heetch_session_cookies_expires_at ON heetch_session_cookies(expires_at);

-- Fonction pour mettre à jour updated_at automatiquement
CREATE OR REPLACE FUNCTION update_heetch_session_cookies_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mettre à jour updated_at
DROP TRIGGER IF EXISTS trigger_update_heetch_session_cookies_updated_at ON heetch_session_cookies;
CREATE TRIGGER trigger_update_heetch_session_cookies_updated_at
    BEFORE UPDATE ON heetch_session_cookies
    FOR EACH ROW
    EXECUTE FUNCTION update_heetch_session_cookies_updated_at();

-- Commentaires
COMMENT ON TABLE heetch_session_cookies IS 'Stocke les cookies de session Heetch pour restaurer les sessions et éviter de redemander le numéro de téléphone';
COMMENT ON COLUMN heetch_session_cookies.cookies IS 'Cookies au format JSON (array de cookies Playwright)';
COMMENT ON COLUMN heetch_session_cookies.expires_at IS 'Date d''expiration des cookies (généralement 24h après la connexion)';

