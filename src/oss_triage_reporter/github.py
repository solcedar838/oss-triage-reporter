from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, Iterable, List, Optional, Tuple


class GitHubError(RuntimeError):
    """Raised when GitHub API access fails."""


@dataclass(frozen=True)
class Repository:
    owner: str
    name: str

    @classmethod
    def parse(cls, value: str) -> "Repository":
        value = value.strip()
        if value.startswith("https://github.com/"):
            value = value.removeprefix("https://github.com/").strip("/")
        parts = value.split("/")
        if len(parts) < 2 or not parts[0] or not parts[1]:
            raise ValueError("Repository must be in owner/repo format")
        return cls(owner=parts[0], name=parts[1])

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


class GitHubClient:
    """Small GitHub REST API client using only the Python standard library."""

    def __init__(self, token: Optional[str] = None, api_url: str = "https://api.github.com") -> None:
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        self.api_url = api_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "oss-triage-reporter/0.1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def request_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = self._build_url(path, params)
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read().decode("utf-8")
                if not data:
                    return None
                return json.loads(data)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubError(f"GitHub API error {exc.code} for {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub API: {exc}") from exc

    def request_bytes(self, path: str, params: Optional[Dict[str, Any]] = None) -> bytes:
        url = self._build_url(path, params)
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise GitHubError(f"GitHub API error {exc.code} for {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise GitHubError(f"Could not reach GitHub API: {exc}") from exc

    def _build_url(self, path: str, params: Optional[Dict[str, Any]]) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            base = path
        else:
            base = f"{self.api_url}/{path.lstrip('/')}"
        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            return f"{base}?{query}"
        return base

    def open_issues(self, repo: Repository, limit: int = 50) -> List[Dict[str, Any]]:
        items = self.request_json(
            f"/repos/{repo.slug}/issues",
            {"state": "open", "sort": "updated", "direction": "desc", "per_page": min(limit, 100)},
        )
        return [item for item in items if "pull_request" not in item][:limit]

    def open_pulls(self, repo: Repository, limit: int = 50) -> List[Dict[str, Any]]:
        items = self.request_json(
            f"/repos/{repo.slug}/pulls",
            {"state": "open", "sort": "updated", "direction": "desc", "per_page": min(limit, 100)},
        )
        return items[:limit]

    def merged_pulls(self, repo: Repository, limit: int = 100) -> List[Dict[str, Any]]:
        items = self.request_json(
            f"/repos/{repo.slug}/pulls",
            {"state": "closed", "sort": "updated", "direction": "desc", "per_page": min(limit, 100)},
        )
        return [item for item in items if item.get("merged_at")]

    def failed_runs(self, repo: Repository, limit: int = 3) -> List[Dict[str, Any]]:
        result = self.request_json(
            f"/repos/{repo.slug}/actions/runs",
            {"status": "failure", "per_page": min(limit, 100)},
        )
        return result.get("workflow_runs", [])[:limit]

    def run_log_text(self, repo: Repository, run_id: int, max_bytes: int = 750_000) -> str:
        raw = self.request_bytes(f"/repos/{repo.slug}/actions/runs/{run_id}/logs")
        chunks: List[str] = []
        with zipfile.ZipFile(BytesIO(raw)) as zf:
            for name in zf.namelist():
                if name.endswith("/"):
                    continue
                with zf.open(name) as fp:
                    text = fp.read(max_bytes).decode("utf-8", errors="replace")
                    chunks.append(f"\n--- {name} ---\n{text}")
        return "\n".join(chunks)


def newer_than_iso(timestamp: Optional[str], days: int, now: Optional[float] = None) -> bool:
    if not timestamp:
        return False
    # GitHub timestamps are ISO 8601 UTC, for example 2026-06-05T12:34:56Z.
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$", timestamp)
    if not match:
        return False
    import datetime as _dt

    dt = _dt.datetime(
        int(match.group(1)), int(match.group(2)), int(match.group(3)),
        int(match.group(4)), int(match.group(5)), int(match.group(6)), tzinfo=_dt.timezone.utc,
    )
    now_dt = _dt.datetime.fromtimestamp(now or time.time(), tz=_dt.timezone.utc)
    return dt >= now_dt - _dt.timedelta(days=days)
