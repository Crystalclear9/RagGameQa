#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create PostgreSQL database in DATABASE_URL if it does not exist."""

from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import settings


def _parse_postgres_url(url: str):
    parsed = urlparse(url)
    if not parsed.scheme.startswith("postgresql"):
        raise ValueError("DATABASE_URL is not a postgresql URL")
    db_name = (parsed.path or "/").lstrip("/")
    if not db_name:
        raise ValueError("DATABASE_URL has no database name")
    return {
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "db_name": db_name,
    }


def _run_with_psycopg(cfg: dict) -> bool:
    try:
        import psycopg
    except Exception:
        return False
    conn = psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        dbname="postgres",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg["db_name"],))
            exists = cur.fetchone() is not None
            if exists:
                print(f"[OK] Database already exists: {cfg['db_name']}")
                return True
            cur.execute(f'CREATE DATABASE "{cfg["db_name"]}"')
            print(f"[OK] Database created: {cfg['db_name']}")
            return True
    finally:
        conn.close()


def _run_with_psycopg2(cfg: dict) -> bool:
    try:
        import psycopg2
    except Exception:
        return False
    conn = psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        dbname="postgres",
    )
    conn.autocommit = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (cfg["db_name"],))
        exists = cur.fetchone() is not None
        if exists:
            print(f"[OK] Database already exists: {cfg['db_name']}")
            return True
        cur.execute(f'CREATE DATABASE "{cfg["db_name"]}"')
        print(f"[OK] Database created: {cfg['db_name']}")
        return True
    finally:
        conn.close()


def main() -> int:
    db_url = settings.get_database_url().strip()
    print(f"[INFO] DATABASE_URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    try:
        cfg = _parse_postgres_url(db_url)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    if _run_with_psycopg(cfg):
        return 0
    if _run_with_psycopg2(cfg):
        return 0

    print("[ERROR] No PostgreSQL driver found.")
    print("[TIP] Install one: pip install psycopg[binary] or pip install psycopg2-binary")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
