from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="aa_denis_fleet", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="password", alias="DB_PASSWORD")
    # Support pour connection string complète (optionnel, prioritaire si défini)
    database_url_override: Optional[str] = Field(default=None, alias="DATABASE_URL")

    @field_validator("db_host", mode="before")
    @classmethod
    def validate_db_host(cls, v: str | None) -> str:
        """Nettoyer l'URL Supabase si fournie (retirer https:// et extraire le hostname)."""
        if not v or v == "":
            return "localhost"
        # Si c'est une URL Supabase (https://xxx.supabase.co), extraire le hostname
        if v.startswith("https://"):
            # Extraire le hostname et le convertir en hostname de DB Supabase
            # https://xxx.supabase.co -> db.xxx.supabase.co
            hostname = v.replace("https://", "").replace("http://", "").split("/")[0]
            if hostname.endswith(".supabase.co"):
                # Convertir en hostname de connexion DB: xxx.supabase.co -> db.xxx.supabase.co
                project_ref = hostname.replace(".supabase.co", "")
                return f"db.{project_ref}.supabase.co"
            return hostname
        return v
    
    # Port de connection pooling Supabase (optionnel, utilise 5432 par défaut)
    db_pooling_port: Optional[int] = Field(default=None, alias="DB_POOLING_PORT")

    @field_validator("db_port", mode="before")
    @classmethod
    def validate_db_port(cls, v: str | int | None) -> int:
        """Convert empty string or None to default port."""
        if v == "" or v is None:
            return 5432
        if isinstance(v, str):
            return int(v)
        return v

    jwt_secret: str = Field(default="changeme", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    supabase_url: Optional[str] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")

    @field_validator("supabase_url", mode="before")
    @classmethod
    def validate_supabase_url(cls, v: str | None) -> str | None:
        """Convert empty string to None for optional URL."""
        if v == "":
            return None
        return v

    uber_client_id: Optional[str] = Field(default=None, alias="UBER_CLIENT_ID")
    uber_client_secret: Optional[str] = Field(default=None, alias="UBER_CLIENT_SECRET")
    uber_base_url: AnyUrl = Field(default="https://api.uber.com", alias="UBER_BASE_URL")
    uber_auth_url: AnyUrl = Field(default="https://auth.uber.com/oauth/v2/token", alias="UBER_AUTH_URL")
    uber_default_org_id: Optional[str] = Field(default=None, alias="UBER_DEFAULT_ORG_ID")

    bolt_client_id: Optional[str] = Field(default=None, alias="BOLT_CLIENT_ID")
    bolt_client_secret: Optional[str] = Field(default=None, alias="BOLT_CLIENT_SECRET")
    bolt_base_url: AnyUrl = Field(default="https://node.bolt.eu/fleet-integration-gateway", alias="BOLT_BASE_URL")
    bolt_auth_url: AnyUrl = Field(default="https://oidc.bolt.eu/token", alias="BOLT_AUTH_URL")
    bolt_default_fleet_id: Optional[str] = Field(default=None, alias="BOLT_DEFAULT_FLEET_ID")

    heetch_login: Optional[str] = Field(default=None, alias="HEETCH_LOGIN", description="Numéro de téléphone pour la connexion Heetch")
    heetch_password: Optional[str] = Field(default=None, alias="HEETCH_PASSWORD")
    heetch_2fa_code: Optional[str] = Field(default=None, alias="HEETCH_2FA_CODE")

    @property
    def database_url(self) -> str:
        """Construit l'URL de connexion à la base de données."""
        # Si une URL complète est fournie, l'utiliser directement
        if self.database_url_override:
            # S'assurer qu'elle utilise psycopg (psycopg3)
            url = self.database_url_override
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
            elif not url.startswith("postgresql+psycopg://"):
                url = f"postgresql+psycopg://{url}"
            # Ajouter sslmode=require si pas déjà présent (nécessaire pour Supabase)
            if "sslmode=" not in url:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}sslmode=require"
            return url
        
        # Sinon, construire l'URL à partir des composants
        # Utiliser le port de pooling si défini, sinon le port standard
        port = self.db_pooling_port if self.db_pooling_port else (self.db_port if self.db_port else 5432)
        # Échapper correctement le mot de passe et l'utilisateur (contient des caractères spéciaux)
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        host = self.db_host
        database = quote_plus(self.db_name) if self.db_name else "postgres"
        # Ajouter sslmode=require pour Supabase (nécessaire pour les connexions externes)
        ssl_param = "?sslmode=require"
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}{ssl_param}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

