"""Regenerate secim_chatbot/data/varliklar.json (entity lexicon snapshot) from the database.

    DB_HOST=127.0.0.1 DB_USER=secim_okur DB_PASSWORD=... python scripts/build_varliklar.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from secim_chatbot import get_settings  # noqa: E402
from secim_chatbot.db import MariaDB  # noqa: E402
from secim_chatbot.entities import SNAPSHOT, EntityIndex  # noqa: E402


def main() -> int:
    db = MariaDB(get_settings())
    if not db.ping():
        print("Veritabanına bağlanılamadı.", file=sys.stderr)
        return 2
    idx = EntityIndex.from_db(db)
    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(json.dumps(idx.to_snapshot(), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(idx.elections)} seçim, {len(idx.iller)} il, {len(idx.ilceler)} ilçe adı, "
          f"{len(idx.all_parties)} parti, {len(idx.candidates)} aday -> {SNAPSHOT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
