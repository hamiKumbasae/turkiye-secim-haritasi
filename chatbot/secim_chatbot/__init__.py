"""Natural-language (Turkish) question answering over the Türkiye election database."""
from .config import Settings, get_settings
from .pipeline import ChatPipeline, ChatResponse

__all__ = ["ChatPipeline", "ChatResponse", "Settings", "build_pipeline", "get_settings"]
__version__ = "0.1.0"


def build_pipeline(settings: Settings | None = None, llm=None, db=None) -> ChatPipeline:
    """Wire the real components from settings; any part can be injected (tests, demo)."""
    from .db import MariaDB
    from .llm import make_llm

    settings = settings or get_settings()
    return ChatPipeline(
        llm=llm or make_llm(settings),
        db=db or MariaDB(settings),
        max_rows=settings.max_rows,
        max_attempts=settings.max_attempts,
    )
