"""Environment config — mirrors the Go backend's config/viperConfig.go + model/config.go.

Loads dev.env (the "dev" profile), falling back to OS environment variables, exactly
like the Go service. Exposes a single `config` instance other modules import.
"""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load dev.env sitting next to this file (Go uses viper's "dev" profile).
# OS environment variables already set will win (K8s/Docker), matching viper.AutomaticEnv.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dev.env"))


def _bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


@dataclass(frozen=True)
class Config:
    server_address: str
    router_path: str
    jwt_secret_key: str
    verify_token: bool
    tenant: bool

    # Default / non-tenant DB (CLIENT1DB_*)
    client_db_server: str
    client_db_name: str
    client_db_user: str
    client_db_password: str
    client_db_port: str

    # Master (tenant catalog) DB (MASTER_DB_*) — the hostdb holding config_tenant
    master_db_user: str
    master_db_password: str
    master_db_host: str
    master_db_port: str
    master_db_name: str

    # AI provider (OpenRouter / OpenAI-compatible) for the report narrative
    openrouter_base_url: str
    openrouter_api_key: str
    openrouter_model: str


def load_config() -> Config:
    return Config(
        server_address=os.getenv("SERVER_ADDRESS", "0.0.0.0:8090"),
        router_path=os.getenv("ROUTER_PATH", "/api"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", ""),
        verify_token=_bool(os.getenv("VERIFY_TOKEN", "false")),
        tenant=_bool(os.getenv("TENANT", "false")),
        client_db_server=os.getenv("CLIENT1DB_SERVER", "localhost"),
        client_db_name=os.getenv("CLIENT1DB_NAME", ""),
        client_db_user=os.getenv("CLIENT1DB_USER", "root"),
        client_db_password=os.getenv("CLIENT1DB_PASSWORD", ""),
        client_db_port=os.getenv("CLIENT1DB_PORT", "3306"),
        master_db_user=os.getenv("MASTER_DB_USER", "root"),
        master_db_password=os.getenv("MASTER_DB_PASSWORD", ""),
        master_db_host=os.getenv("MASTER_DB_HOST", "localhost"),
        master_db_port=os.getenv("MASTER_DB_PORT", "3306"),
        master_db_name=os.getenv("MASTER_DB_NAME", ""),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openai/gpt-5.2"),
    )


config = load_config()
