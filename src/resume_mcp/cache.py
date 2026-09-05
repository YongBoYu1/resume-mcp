"""Fetch and cache public reputation-site documents."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

RESUME_URL = "https://yongbo-yu.vercel.app/resume.json"
LLMS_TXT_URL = "https://yongbo-yu.vercel.app/llms.txt"
SITE_URL = "https://yongbo-yu.vercel.app"
ABOUT_URL = "https://yongbo-yu.vercel.app/about-yongbo-yu"
KILODOCK_URL = "https://yongbo-yu.vercel.app/projects/kilodock"
GITHUB_URL = "https://github.com/YongBoYu1"

# Re-fetch at most once per this many seconds within a process.
CACHE_TTL_SECONDS = 3600
USER_AGENT = "resume-mcp/0.1.0 (+https://github.com/YongBoYu1/resume-mcp)"


@dataclass
class PublicCache:
    """In-memory cache of public resume.json and optional llms.txt."""

    resume: dict[str, Any] | None = None
    llms_text: str | None = None
    fetched_at: float | None = None
    errors: list[str] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def ensure_loaded(self, force: bool = False) -> None:
        with self._lock:
            now = time.monotonic()
            fresh = (
                self.fetched_at is not None
                and (now - self.fetched_at) < CACHE_TTL_SECONDS
                and self.resume is not None
            )
            if fresh and not force:
                return
            self._fetch_unlocked()

    def _fetch_unlocked(self) -> None:
        errors: list[str] = []
        resume: dict[str, Any] | None = None
        llms_text: str | None = None

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/plain, */*"}
        with httpx.Client(timeout=20.0, follow_redirects=True, headers=headers) as client:
            try:
                resp = client.get(RESUME_URL)
                resp.raise_for_status()
                resume = resp.json()
                if not isinstance(resume, dict):
                    raise ValueError("resume.json root must be an object")
            except Exception as exc:  # noqa: BLE001 — surface as tool error context
                errors.append(f"Failed to fetch {RESUME_URL}: {exc}")

            try:
                resp = client.get(LLMS_TXT_URL)
                resp.raise_for_status()
                llms_text = resp.text
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Failed to fetch {LLMS_TXT_URL}: {exc}")

        self.resume = resume
        self.llms_text = llms_text
        self.errors = errors
        self.fetched_at = time.monotonic()

    def require_resume(self) -> dict[str, Any]:
        self.ensure_loaded()
        if self.resume is None:
            detail = "; ".join(self.errors) or "unknown error"
            raise RuntimeError(f"Public resume.json is unavailable: {detail}")
        return self.resume


cache = PublicCache()


def flatten_resume_text(resume: dict[str, Any]) -> str:
    """Serialize resume fields into searchable plain text."""
    return json.dumps(resume, ensure_ascii=False, indent=2)
