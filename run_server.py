#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Start the RAG Game QA API server."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

print("=" * 60)
print("  RAG Game QA System - Start Server")
print("=" * 60)

try:
    print("\n[INFO] Checking configuration...")
    from config.database import database_status
    from config.settings import settings

    print(f"[OK] APP_NAME: {settings.APP_NAME}")
    print(f"[OK] VERSION: {settings.APP_VERSION}")
    print(f"[OK] AI_PROVIDER: {settings.AI_PROVIDER}")
    print(f"[OK] HOST: {settings.API_HOST}")
    print(f"[OK] PORT: {settings.API_PORT}")
    print(f"[OK] WEB_RETRIEVAL: {settings.ENABLE_WEB_RETRIEVAL}")

    db_state = database_status()
    print(f"[OK] DB_BACKEND: {db_state.get('backend')}")
    if db_state.get("using_fallback"):
        print(f"[WARN] DB_FALLBACK: {db_state.get('init_error') or 'using sqlite fallback'}")
    else:
        print(f"[OK] DB_ACTIVE: {db_state.get('active_url')}")

    print("\n[INFO] Starting service...")
    print(f"[INFO] URL: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"[INFO] Docs: http://localhost:{settings.API_PORT}/docs")
    print(f"[INFO] Web UI: http://localhost:{settings.API_PORT}/app")
    print(f"[INFO] Health: http://localhost:{settings.API_PORT}/health")
    print(f"[INFO] Knowledge Sync: http://localhost:{settings.API_PORT}/api/v1/project/knowledge-sync")
    print("\n" + "-" * 60)
    print("[INFO] Press Ctrl+C to stop")
    print("-" * 60 + "\n")

    import uvicorn
    from api.main import app

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
except KeyboardInterrupt:
    print("\n\n[INFO] Server stopped")
    sys.exit(0)
except Exception as exc:
    print(f"\n[ERROR] Startup failed: {exc}")
    print("\n[TIPS] Check these items:")
    print("  1. pip install -r requirements.txt")
    print("  2. .env exists and DATABASE_URL is valid")
    print("  3. For PostgreSQL, install driver: pip install psycopg[binary]")
    print("\nRun diagnostics:")
    print("  python scripts/simple_test.py")

    import traceback

    print("\nDetails:")
    traceback.print_exc()
    sys.exit(1)
