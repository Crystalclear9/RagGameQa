#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Export priority report to Jira or preview it locally."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from api.routes.analytics_routes import JiraExportRequest, export_priority_report_to_jira


def parse_args():
    parser = argparse.ArgumentParser(description="Export feedback priorities to Jira")
    parser.add_argument("--game-id", required=True, help="Game id")
    parser.add_argument("--limit", type=int, default=3, help="Max issues")
    parser.add_argument("--create", action="store_true", help="Actually create Jira issues")
    return parser.parse_args()


async def main_async() -> int:
    args = parse_args()
    response = await export_priority_report_to_jira(
        JiraExportRequest(
            game_id=args.game_id,
            limit=max(1, min(args.limit, 10)),
            dry_run=not args.create,
        )
    )
    print("=" * 64)
    print("  Jira Export")
    print("=" * 64)
    print(f"[INFO] configured: {response.configured}")
    print(f"[INFO] dry_run: {response.dry_run}")
    print(f"[INFO] issue_count: {response.issue_count}")
    for item in response.issues:
        suffix = f" -> {item.jira_key}" if item.jira_key else ""
        print(f"  - {item.label} | score={item.score} | {item.summary}{suffix}")
    return 0


def main() -> int:
    return asyncio.run(main_async())


if __name__ == "__main__":
    raise SystemExit(main())
