#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bootstrap external PostgreSQL database and seed sample knowledge."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import Document, SessionLocal, create_tables, database_status, ensure_game_record
from config.settings import settings


def _print_header(title: str) -> None:
    print("\n" + "=" * 68)
    print(f"  {title}")
    print("=" * 68)


def _load_sample_data() -> dict:
    sample_path = PROJECT_ROOT / "data" / "sample_data.json"
    if not sample_path.exists():
        return {"games": [], "documents": []}
    return json.loads(sample_path.read_text(encoding="utf-8"))


def _build_embedding(text: str):
    try:
        from core.knowledge_base.embedding_service import EmbeddingService
    except Exception:
        return None
    try:
        service = EmbeddingService(settings.EMBEDDING_MODEL)
        vector = service.model.encode([text])[0]
        return vector.tolist()
    except Exception:
        return None


def main() -> int:
    _print_header("RAG External DB Bootstrap")
    state = database_status()
    print(f"[INFO] Requested backend: {state.get('requested_backend')}")
    print(f"[INFO] Active backend: {state.get('backend')}")
    print(f"[INFO] Active URL: {state.get('active_url')}")

    if state.get("requested_backend") != "postgresql":
        print("[ERROR] DATABASE_URL is not PostgreSQL. Please set DATABASE_URL first.")
        print("        Example: postgresql://postgres:password@localhost:5432/rag_game_qa")
        return 1

    if state.get("using_fallback"):
        print("[ERROR] PostgreSQL is not active, still using SQLite fallback.")
        if state.get("init_error"):
            print(f"[DETAIL] {state.get('init_error')}")
        print("[TIP] Install driver: pip install psycopg[binary]")
        print("[TIP] Ensure PostgreSQL is running and DATABASE_URL is reachable.")
        return 1

    print("[STEP] Creating tables...")
    create_tables()
    print("[OK] Tables created.")

    sample_data = _load_sample_data()
    games = sample_data.get("games", [])
    docs = sample_data.get("documents", [])

    db = SessionLocal()
    try:
        print(f"[STEP] Seeding games: {len(games)}")
        for game in games:
            ensure_game_record(db, game.get("game_id", ""), game.get("game_name"))

        print(f"[STEP] Seeding documents: {len(docs)}")
        added = 0
        skipped = 0
        for item in docs:
            game_id = str(item.get("game_id", "")).strip()
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            if not game_id or not content:
                continue

            exists = (
                db.query(Document)
                .filter(Document.game_id == game_id, Document.title == title, Document.content == content)
                .first()
            )
            if exists:
                skipped += 1
                continue

            embedding = _build_embedding(content)
            db.add(
                Document(
                    game_id=game_id,
                    title=title,
                    content=content,
                    category=str(item.get("category", "sample")),
                    source=str(item.get("source", "sample_data")),
                    doc_metadata=json.dumps({"seed": "sample_data"}, ensure_ascii=False),
                    embedding=json.dumps(embedding) if embedding is not None else None,
                )
            )
            added += 1

        db.commit()
        print(f"[OK] Seed done. Added={added}, Skipped={skipped}")
    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seed failed: {exc}")
        return 1
    finally:
        db.close()

    print("[SUCCESS] External PostgreSQL is ready for RAG.")
    print("[NEXT] Start server: python run_server.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
