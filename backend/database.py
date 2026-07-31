import os
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables (local .env only; Vercel uses dashboard env vars)
load_dotenv()

# Default to Docker-based PostgreSQL container on port 5434
_RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5434/banking_db",
)


def _normalize_database_url(url: str) -> str:
    """Make cloud Postgres URLs work with SQLAlchemy + psycopg2."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]

    # Prefer explicit psycopg2 driver on serverless Linux
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://") :]

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    is_local = host in ("localhost", "127.0.0.1")

    # Neon / Supabase / most hosted Postgres require SSL
    if not is_local:
        query = parse_qs(parsed.query)
        if "sslmode" not in query:
            query["sslmode"] = ["require"]
        flat = {key: values[0] for key, values in query.items()}
        parsed = parsed._replace(query=urlencode(flat))
        url = urlunparse(parsed)

    return url


DATABASE_URL = _normalize_database_url(_RAW_DATABASE_URL)

# Vercel (and other serverless) cannot keep long-lived connection pools
_is_serverless = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

_engine_kwargs: dict = {
    "echo": False,
    "pool_pre_ping": True,
}
if _is_serverless:
    _engine_kwargs["poolclass"] = NullPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for SQLAlchemy models
Base = declarative_base()


def get_db():
    """Dependency injection helper for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database() -> dict:
    """Return connectivity status for health checks / debugging."""
    host = urlparse(DATABASE_URL).hostname or "unknown"
    configured = bool(os.getenv("DATABASE_URL"))
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "ok": True,
            "host": host,
            "database_url_configured": configured,
            "serverless": _is_serverless,
        }
    except Exception as exc:
        return {
            "ok": False,
            "host": host,
            "database_url_configured": configured,
            "serverless": _is_serverless,
            "error": str(exc),
        }
