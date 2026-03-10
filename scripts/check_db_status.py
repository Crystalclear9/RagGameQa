#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check current database backend status."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import Document, Game, QueryLog, SessionLocal, database_status


def main() -> int:
    print("=" * 64)
    print("  Database Status")
    print("=" * 64)
    state = database_status()
    print(f"[INFO] Requested backend: {state.get('requested_backend')}")
    print(f"[INFO] Active backend: {state.get('backend')}")
    print(f"[INFO] Active URL: {state.get('active_url')}")
    print(f"[INFO] Using fallback: {state.get('using_fallback')}")
    if state.get("init_error"):
        print(f"[WARN] Init error: {state.get('init_error')}")

    db = SessionLocal()
    try:
        print("\n[INFO] Data counts")
        print(f"  games: {db.query(Game).count()}")
        print(f"  documents: {db.query(Document).count()}")
        print(f"  web_sync_documents: {db.query(Document).filter(Document.category == 'web_sync').count()}")
        print(f"  crawler_sync_documents: {db.query(Document).filter(Document.category == 'crawler_sync').count()}")
        print(f"  query_logs: {db.query(QueryLog).count()}")
    except Exception as exc:
        print(f"[ERROR] Read counts failed: {exc}")
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
