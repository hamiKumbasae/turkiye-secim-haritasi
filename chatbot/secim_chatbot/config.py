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


def _float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # Database (read-only user recommended, see sql/readonly_user.sql)
    db_host: str = field(default_factory=lambda: os.environ.get("DB_HOST", "192.168.1.2"))
    db_port: int = field(default_factory=lambda: _int("DB_PORT", 3306))
    db_user: str = field(default_factory=lambda: os.environ.get("DB_USER", "secim_okur"))
    db_password: str = field(default_factory=lambda: os.environ.get("DB_PASSWORD", ""))
    db_name: str = field(default_factory=lambda: os.environ.get("DB_NAME", "secim"))

    # Routing: llm | template | hybrid (template first, LLM fallback)
    mode: str = field(default_factory=lambda: os.environ.get("CHATBOT_MODE", "llm"))

    # LLM: anthropic (alias claude) | ollama | fake
    llm_provider: str = field(default_factory=lambda: os.environ.get("LLM_PROVIDER", "anthropic"))
    model: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"))
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))

    # Local models via Ollama (see README "Local models")
    ollama_model: str = field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b"))
    ollama_host: str = field(default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ollama_temperature: float = field(default_factory=lambda: _float("OLLAMA_TEMPERATURE", 0.0))
    ollama_timeout_s: float = field(default_factory=lambda: _float("OLLAMA_TIMEOUT", 120.0))
    ollama_num_ctx: int = field(default_factory=lambda: _int("OLLAMA_NUM_CTX", 8192))
    ollama_answer: str = field(default_factory=lambda: os.environ.get("OLLAMA_ANSWER", "model"))  # model | sablon
    fewshot_k: int = field(default_factory=lambda: _int("FEWSHOT_K", 4))

    # Safety limits
    max_rows: int = field(default_factory=lambda: _int("CHATBOT_MAX_ROWS", 200))
    statement_timeout_s: int = field(default_factory=lambda: _int("CHATBOT_TIMEOUT_S", 10))
    max_attempts: int = field(default_factory=lambda: _int("CHATBOT_MAX_ATTEMPTS", 2))


def get_settings() -> Settings:
    return Settings()
