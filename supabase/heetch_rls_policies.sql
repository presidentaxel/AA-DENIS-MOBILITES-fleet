-- RLS (Row Level Security) Policies pour les tables Heetch
-- Les utilisateurs ne peuvent accéder qu'aux données de leur organisation (org_id)

-- ============================================================================
-- Activer RLS sur toutes les tables Heetch
-- ============================================================================

ALTER TABLE public.heetch_session_cookies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.heetch_earnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.heetch_drivers ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Service role: accès complet (pour le backend avec service_role)
-- ============================================================================

-- Policy pour heetch_session_cookies
DROP POLICY IF EXISTS heetch_session_cookies_service_all ON public.heetch_session_cookies;
CREATE POLICY heetch_session_cookies_service_all ON public.heetch_session_cookies
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Policy pour heetch_earnings
DROP POLICY IF EXISTS heetch_earnings_service_all ON public.heetch_earnings;
CREATE POLICY heetch_earnings_service_all ON public.heetch_earnings
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- Policy pour heetch_drivers
DROP POLICY IF EXISTS heetch_drivers_service_all ON public.heetch_drivers;
CREATE POLICY heetch_drivers_service_all ON public.heetch_drivers
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

-- ============================================================================
-- Authenticated users: accès selon org_id (extrait du JWT)
-- ============================================================================

-- Policy pour heetch_session_cookies: SELECT, INSERT, UPDATE, DELETE selon org_id
DROP POLICY IF EXISTS heetch_session_cookies_auth_select ON public.heetch_session_cookies;
CREATE POLICY heetch_session_cookies_auth_select ON public.heetch_session_cookies
    FOR SELECT
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_session_cookies_auth_insert ON public.heetch_session_cookies;
CREATE POLICY heetch_session_cookies_auth_insert ON public.heetch_session_cookies
    FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_session_cookies_auth_update ON public.heetch_session_cookies;
CREATE POLICY heetch_session_cookies_auth_update ON public.heetch_session_cookies
    FOR UPDATE
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    )
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_session_cookies_auth_delete ON public.heetch_session_cookies;
CREATE POLICY heetch_session_cookies_auth_delete ON public.heetch_session_cookies
    FOR DELETE
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

-- Policy pour heetch_earnings: SELECT, INSERT, UPDATE selon org_id
DROP POLICY IF EXISTS heetch_earnings_auth_select ON public.heetch_earnings;
CREATE POLICY heetch_earnings_auth_select ON public.heetch_earnings
    FOR SELECT
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_earnings_auth_insert ON public.heetch_earnings;
CREATE POLICY heetch_earnings_auth_insert ON public.heetch_earnings
    FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_earnings_auth_update ON public.heetch_earnings;
CREATE POLICY heetch_earnings_auth_update ON public.heetch_earnings
    FOR UPDATE
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    )
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

-- Policy pour heetch_drivers: SELECT, INSERT, UPDATE selon org_id
DROP POLICY IF EXISTS heetch_drivers_auth_select ON public.heetch_drivers;
CREATE POLICY heetch_drivers_auth_select ON public.heetch_drivers
    FOR SELECT
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_drivers_auth_insert ON public.heetch_drivers;
CREATE POLICY heetch_drivers_auth_insert ON public.heetch_drivers
    FOR INSERT
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

DROP POLICY IF EXISTS heetch_drivers_auth_update ON public.heetch_drivers;
CREATE POLICY heetch_drivers_auth_update ON public.heetch_drivers
    FOR UPDATE
    USING (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    )
    WITH CHECK (
        auth.role() = 'authenticated' 
        AND org_id = COALESCE(
            (current_setting('request.jwt.claims', true)::json->>'org_id'),
            ''
        )
    );

