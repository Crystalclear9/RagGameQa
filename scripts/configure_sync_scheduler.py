#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Configure recurring knowledge sync scheduler."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.knowledge_base.sync_scheduler import knowledge_sync_scheduler


def parse_args():
    parser = argparse.ArgumentParser(description="Configure knowledge sync scheduler")
    parser.add_argument("--enable", action="store_true", help="Enable scheduler")
    parser.add_argument("--disable", action="store_true", help="Disable scheduler")
    parser.add_argument("--interval", type=int, default=60, help="Interval minutes")
    parser.add_argument("--game-id", action="append", dest="game_ids", help="Game id, can repeat")
    parser.add_argument("--top-k", type=int, default=2, help="Results per query")
    parser.add_argument("--run-now", action="store_true", help="Run one sync after configuration")
    return parser.parse_args()


async def main_async() -> int:
    args = parse_args()
    status = await knowledge_sync_scheduler.restore()
    enabled = status.get("enabled", False)
    if args.enable:
        enabled = True
    if args.disable:
        enabled = False

    status = await knowledge_sync_scheduler.configure(
        enabled=enabled,
        interval_minutes=max(5, args.interval),
        game_ids=args.game_ids or status.get("game_ids") or ["wow"],
        max_results_per_query=max(1, min(args.top_k, 5)),
    )

    print("=" * 64)
    print("  Scheduler Status")
    print("=" * 64)
    print(status)

    if args.run_now:
        result = await knowledge_sync_scheduler.run_once(args.game_ids)
        print("\n[RUN NOW]")
        print(result)
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
