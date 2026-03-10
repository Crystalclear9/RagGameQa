"""Minimal Jira Cloud integration for feedback export."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from config.settings import settings
from utils.security import mask_secret, redact_sensitive_text

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self):
        self.base_url = (settings.JIRA_BASE_URL or "").strip().rstrip("/")
        self.email = (settings.JIRA_EMAIL or "").strip()
        self.api_token = (settings.JIRA_API_TOKEN or "").strip()
        self.project_key = (settings.JIRA_PROJECT_KEY or "").strip()
        self.issue_type = (settings.JIRA_ISSUE_TYPE or "Task").strip() or "Task"
        self.label_prefix = (settings.JIRA_PRIORITY_LABEL_PREFIX or "rag-feedback").strip() or "rag-feedback"

    def is_configured(self) -> bool:
        return all([self.base_url, self.email, self.api_token, self.project_key])

    def get_status(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "base_url": self.base_url,
            "email_masked": mask_secret(self.email),
            "api_token_configured": bool(self.api_token),
            "project_key": self.project_key,
            "issue_type": self.issue_type,
            "label_prefix": self.label_prefix,
        }

    def create_issue(
        self,
        summary: str,
        description: str,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not self.is_configured():
            raise ValueError("Jira 配置不完整，无法创建工单")

        endpoint = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary[:255],
                "issuetype": {"name": self.issue_type},
                "labels": labels or [],
                "description": self._build_adf_description(description),
            }
        }
        try:
            response = requests.post(
                endpoint,
                json=payload,
                auth=HTTPBasicAuth(self.email, self.api_token),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "id": data.get("id"),
                "key": data.get("key"),
                "url": f"{self.base_url}/browse/{data.get('key')}" if data.get("key") else None,
            }
        except requests.HTTPError as exc:
            detail = ""
            try:
                detail = exc.response.text[:400] if exc.response is not None else str(exc)
            except Exception:
                detail = str(exc)
            logger.warning("Jira issue creation failed: %s", redact_sensitive_text(detail))
            raise ValueError(f"Jira 工单创建失败: {redact_sensitive_text(detail)}") from exc
        except requests.RequestException as exc:
            logger.warning("Jira request error: %s", redact_sensitive_text(exc))
            raise ValueError("Jira 网络请求失败，请检查地址、网络或代理。") from exc

    def _build_adf_description(self, text: str) -> Dict[str, Any]:
        paragraphs = []
        for line in str(text or "").splitlines():
            content = line.strip()
            if not content:
                continue
            paragraphs.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": content[:2000]}],
                }
            )

        if not paragraphs:
            paragraphs.append(
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "No description provided."}],
                }
            )

        return {
            "version": 1,
            "type": "doc",
            "content": paragraphs,
        }
