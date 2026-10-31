"""Natural-language (Turkish) question answering over the Türkiye election database."""
from .config import Settings, get_settings
from .pipeline import ChatPipeline, ChatResponse

__all__ = ["ChatPipeline", "ChatResponse", "Settings", "build_pipeline", "get_settings"]
__version__ = "0.1.0"


def build_pipeline(settings: Settings | None = None, llm=None, db=None, mode: str | None = None,
                   templates=None) -> ChatPipeline:
    """Wire the real components from settings; any part can be injected (tests, demo).

    mode: llm | template | hybrid (default: settings.mode / CHATBOT_MODE). In template mode no LLM is
    created, so no API key or Ollama is needed."""
    from .db import MariaDB
    from .llm import make_llm
    from .templates import TemplateEngine

    settings = settings or get_settings()
    mode = (mode or settings.mode or "llm").lower()
    db = db or MariaDB(settings)
    if llm is None and mode != "template":
        llm = make_llm(settings)
    return ChatPipeline(
        llm=llm,
        db=db,
        max_rows=settings.max_rows,
        max_attempts=settings.max_attempts,
        templates=templates or TemplateEngine(db=db),
        mode=mode,
    )
