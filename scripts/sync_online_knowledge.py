#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sync online knowledge into the active database backend."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.knowledge_base.knowledge_sync import KnowledgeSyncService, get_default_sync_queries


def parse_args():
    parser = argparse.ArgumentParser(description="Sync online knowledge into database")
    parser.add_argument("--game-id", required=True, help="Game id, e.g. wow / lol / genshin")
    parser.add_argument("--query", action="append", dest="queries", help="Custom query, can be repeated")
    parser.add_argument("--top-k", type=int, default=2, help="Results per query")
    return parser.parse_args()


async def main_async() -> int:
    args = parse_args()
    queries = args.queries or get_default_sync_queries(args.game_id)
    service = KnowledgeSyncService(args.game_id)
    result = await service.sync(queries=queries, max_results_per_query=max(1, min(args.top_k, 5)))
    print("=" * 64)
    print("  Knowledge Sync Result")
    print("=" * 64)
    print(f"[INFO] game_id: {result.get('game_id')}")
    print(f"[INFO] queries: {', '.join(result.get('queries', []))}")
    print(f"[INFO] fetched_docs: {result.get('fetched_docs')}")
    print(f"[INFO] stored_new_docs: {result.get('stored_new_docs')}")
    print(f"[INFO] skipped_existing_docs: {result.get('skipped_existing_docs')}")
    print(f"[INFO] last_sync_at: {result.get('last_sync_at')}")
    return 0


def main() -> int:
    try:
        return asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n[INFO] sync cancelled")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
