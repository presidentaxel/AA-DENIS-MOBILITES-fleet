from functools import lru_cache
from typing import Optional

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="dev", alias="APP_ENV")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="aa_denis_fleet", alias="DB_NAME")
    db_user: str = Field(default="postgres", alias="DB_USER")
    db_password: str = Field(default="password", alias="DB_PASSWORD")

    jwt_secret: str = Field(default="changeme", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    supabase_url: Optional[AnyUrl] = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_jwt_secret: Optional[str] = Field(default=None, alias="SUPABASE_JWT_SECRET")

    uber_client_id: Optional[str] = Field(default=None, alias="UBER_CLIENT_ID")
    uber_client_secret: Optional[str] = Field(default=None, alias="UBER_CLIENT_SECRET")
    uber_base_url: AnyUrl = Field(default="https://api.uber.com", alias="UBER_BASE_URL")
    uber_auth_url: AnyUrl = Field(default="https://auth.uber.com/oauth/v2/token", alias="UBER_AUTH_URL")
    uber_default_org_id: Optional[str] = Field(default=None, alias="UBER_DEFAULT_ORG_ID")

    bolt_client_id: Optional[str] = Field(default=None, alias="BOLT_CLIENT_ID")
    bolt_client_secret: Optional[str] = Field(default=None, alias="BOLT_CLIENT_SECRET")
    bolt_base_url: AnyUrl = Field(default="https://api.bolt.com", alias="BOLT_BASE_URL")
    bolt_auth_url: AnyUrl = Field(default="https://auth.bolt.com/oauth/token", alias="BOLT_AUTH_URL")
    bolt_default_fleet_id: Optional[str] = Field(default=None, alias="BOLT_DEFAULT_FLEET_ID")

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

