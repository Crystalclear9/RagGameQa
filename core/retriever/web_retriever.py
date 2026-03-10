"""Online retriever backed by game wiki and Wikipedia APIs."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List
from urllib.parse import quote_plus

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

GAME_NAME_HINTS = {
    "wow": "World of Warcraft",
    "lol": "League of Legends",
    "genshin": "Genshin Impact",
    "minecraft": "Minecraft",
    "valorant": "Valorant",
    "apex": "Apex Legends",
}

GAME_WIKI_APIS = {
    "wow": ["https://wowpedia.fandom.com/api.php"],
    "lol": ["https://leagueoflegends.fandom.com/api.php"],
    "genshin": ["https://genshin-impact.fandom.com/api.php"],
    "minecraft": ["https://minecraft.fandom.com/api.php"],
    "valorant": ["https://valorant.fandom.com/api.php"],
    "apex": ["https://apexlegends.fandom.com/api.php"],
}


class WebRetriever:
    def __init__(self, game_id: str):
        self.game_id = game_id
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )

    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._retrieve_sync, query, top_k)

    def _retrieve_sync(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        docs: List[Dict[str, Any]] = []
        for wiki_api in GAME_WIKI_APIS.get(self.game_id, []):
            docs.extend(self._search_mediawiki_api(wiki_api, query, top_k=top_k))
            if len(docs) >= top_k:
                break

        if len(docs) < top_k:
            docs.extend(self._search_wikipedia(query, top_k=top_k - len(docs)))

        deduped = []
        seen = set()
        for item in docs:
            meta = item.get("metadata") or {}
            key = f"{meta.get('title','')}|{meta.get('source','')}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= top_k:
                break
        return deduped

    def _search_mediawiki_api(self, api_url: str, query: str, top_k: int) -> List[Dict[str, Any]]:
        timeout = max(settings.WEB_RETRIEVAL_TIMEOUT_SECONDS, 3)
        headers = {"User-Agent": self.user_agent}
        search_text = query.strip()
        if not search_text:
            return []

        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_text,
            "format": "json",
        }
        try:
            response = requests.get(api_url, params=params, timeout=timeout, headers=headers)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("Wiki search failed (%s): %s", api_url, exc)
            return []

        search_items = ((payload.get("query") or {}).get("search") or [])[:top_k]
        results: List[Dict[str, Any]] = []
        for rank, item in enumerate(search_items, start=1):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            extract = self._fetch_mediawiki_extract(api_url, title, timeout, headers=headers)
            if not extract:
                continue
            source_url = self._build_mediawiki_page_url(api_url, title)
            score = max(0.2, 0.68 - rank * 0.07)
            results.append(
                {
                    "id": f"wiki-{rank}-{self.game_id}",
                    "content": extract,
                    "metadata": {"title": title, "source": source_url},
                    "score": float(score),
                    "type": "web",
                }
            )
        return results

    def _fetch_mediawiki_extract(self, api_url: str, title: str, timeout: int, headers: Dict[str, str]) -> str:
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "exintro": "1",
            "titles": title,
            "format": "json",
        }
        try:
            response = requests.get(api_url, params=params, timeout=timeout, headers=headers)
            response.raise_for_status()
            payload = response.json()
            pages = ((payload.get("query") or {}).get("pages") or {}).values()
            for page in pages:
                text = self._clean_text(page.get("extract", ""))
                if text:
                    return text[:1200]
        except Exception:
            return ""
        return ""

    def _build_mediawiki_page_url(self, api_url: str, title: str) -> str:
        base = api_url.split("/api.php", 1)[0]
        return f"{base}/wiki/{quote_plus(title.replace(' ', '_'))}"

    def _search_wikipedia(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        timeout = max(settings.WEB_RETRIEVAL_TIMEOUT_SECONDS, 3)
        game_hint = GAME_NAME_HINTS.get(self.game_id, self.game_id)
        search_text = f"{game_hint} {query}"
        base = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_text,
            "format": "json",
        }
        try:
            response = requests.get(base, params=params, timeout=timeout, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            logger.warning("Wikipedia search failed: %s", exc)
            return []

        search_items = ((payload.get("query") or {}).get("search") or [])[:top_k]
        results: List[Dict[str, Any]] = []
        for rank, item in enumerate(search_items, start=1):
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            excerpt = self._fetch_wikipedia_extract(title, timeout)
            if not excerpt:
                continue
            page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
            score = max(0.2, 0.46 - rank * 0.05)
            results.append(
                {
                    "id": f"wikipedia-{rank}",
                    "content": excerpt,
                    "metadata": {"title": title, "source": page_url},
                    "score": float(score),
                    "type": "web",
                }
            )
        return results

    def _fetch_wikipedia_extract(self, title: str, timeout: int) -> str:
        base = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "exintro": "1",
            "titles": title,
            "format": "json",
        }
        try:
            response = requests.get(base, params=params, timeout=timeout, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
            payload = response.json()
            pages = ((payload.get("query") or {}).get("pages") or {}).values()
            for page in pages:
                text = self._clean_text(page.get("extract", ""))
                if text:
                    return text[:1200]
        except Exception:
            return ""
        return ""

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()
