-- Ajouter le champ invalid_at pour marquer les cookies comme invalides au lieu de les supprimer
-- Cela permet de conserver l'historique des cookies

ALTER TABLE public.heetch_session_cookies 
ADD COLUMN IF NOT EXISTS invalid_at TIMESTAMP WITH TIME ZONE NULL;

-- Index pour filtrer les cookies valides (invalid_at IS NULL)
CREATE INDEX IF NOT EXISTS idx_heetch_session_cookies_invalid_at 
ON public.heetch_session_cookies(invalid_at) 
WHERE invalid_at IS NULL;

-- Commentaire
COMMENT ON COLUMN public.heetch_session_cookies.invalid_at IS 'Date à laquelle les cookies ont été marqués comme invalides (HTTP 307). NULL = cookies valides.';

