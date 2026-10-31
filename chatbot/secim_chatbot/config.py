"""Runtime settings, read from environment variables (and an optional .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv is optional; plain environment variables always work
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:  # pragma: no cover
    pass


def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # Database (read-only user recommended, see sql/readonly_user.sql)
    db_host: str = field(default_factory=lambda: os.environ.get("DB_HOST", "192.168.1.2"))
    db_port: int = field(default_factory=lambda: _int("DB_PORT", 3306))
    db_user: str = field(default_factory=lambda: os.environ.get("DB_USER", "secim_okur"))
    db_password: str = field(default_factory=lambda: os.environ.get("DB_PASSWORD", ""))
    db_name: str = field(default_factory=lambda: os.environ.get("DB_NAME", "secim"))

    # LLM
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "anthropic"))
    model: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))

    # Safety limits
    max_rows: int = field(default_factory=lambda: _int("CHATBOT_MAX_ROWS", 200))
    statement_timeout_s: int = field(default_factory=lambda: _int("CHATBOT_TIMEOUT_S", 10))
    max_attempts: int = field(default_factory=lambda: _int("CHATBOT_MAX_ATTEMPTS", 2))


def get_settings() -> Settings:
    return Settings()
