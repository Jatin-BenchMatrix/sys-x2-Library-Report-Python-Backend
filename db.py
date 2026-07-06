"""Database connections — mirrors the Go backend's config/dbConfig.go +
controller/db.go + the tenant-connection parsing in middleware/TenantMiddleware.go.

Raw SQL via PyMySQL (no ORM), to stay close to Go's database/sql usage.
"""
import pymysql
from pymysql.cursors import DictCursor

from config import config


def _connect(host: str, port: str, user: str, password: str, database: str) -> pymysql.connections.Connection:
    return pymysql.connect(
        host=host,
        port=int(port or 3306),
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def open_default_db() -> pymysql.connections.Connection:
    """Default / non-tenant DB (CLIENT1DB_*) — mirrors config.GetDB."""
    return _connect(
        config.client_db_server,
        config.client_db_port,
        config.client_db_user,
        config.client_db_password,
        config.client_db_name,
    )


def open_master_db() -> pymysql.connections.Connection:
    """Master (tenant catalog) DB (MASTER_DB_*) — holds config_tenant."""
    return _connect(
        config.master_db_host,
        config.master_db_port,
        config.master_db_user,
        config.master_db_password,
        config.master_db_name,
    )


def parse_tenant_connection(conn_str: str) -> dict:
    """Parse a config_tenant.tenant_connection value.

    Format (same as Go): "user=...;password=...;server=...;port=...;database=..."
    """
    out: dict[str, str] = {}
    for part in conn_str.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def open_tenant_db(conn_str: str) -> pymysql.connections.Connection:
    """Open the tenant DB from a config_tenant.tenant_connection string."""
    parts = parse_tenant_connection(conn_str)
    return _connect(
        parts.get("server", "localhost"),
        parts.get("port", "3306"),
        parts.get("user", ""),
        parts.get("password", ""),
        parts.get("database", ""),
    )
