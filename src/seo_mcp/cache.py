"""Signature cache for Ahrefs free backlink requests."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from seo_mcp.config import get_settings


@dataclass(frozen=True)
class SignatureRecord:
    """Cached signed input data for a domain."""

    signature: str
    valid_until: str
    overview_data: dict[str, Any] | None


def iso_to_timestamp(iso_date_string: str) -> float:
    """Convert an ISO 8601 datetime string to a timestamp."""

    normalized = iso_date_string
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized).timestamp()


class SignatureCache:
    """JSON-backed signature cache outside the repository by default."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or get_settings().cache_dir
        self.path = self.cache_dir / "signature_cache.json"

    def _read(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data: dict[str, dict[str, Any]]) -> bool:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with self.path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=True)
        except OSError:
            return False
        else:
            return True

    def load(self, domain: str) -> SignatureRecord | None:
        """Load a valid cache record for a domain."""

        domain_cache = self._read().get(domain)
        if not isinstance(domain_cache, dict):
            return None

        valid_until = domain_cache.get("valid_until")
        signature = domain_cache.get("signature")
        if not isinstance(valid_until, str) or not isinstance(signature, str):
            return None

        try:
            if time.time() >= iso_to_timestamp(valid_until):
                return None
        except (TypeError, ValueError):
            return None

        overview_data = domain_cache.get("overview_data")
        if overview_data is not None and not isinstance(overview_data, dict):
            overview_data = None
        return SignatureRecord(signature, valid_until, overview_data)

    def save(
        self,
        domain: str,
        signature: str,
        valid_until: str,
        overview_data: dict[str, Any] | None,
    ) -> bool:
        """Save a cache record for a domain."""

        data = self._read()
        data[domain] = {
            "signature": signature,
            "valid_until": valid_until,
            "overview_data": overview_data,
            "timestamp": time.time(),
        }
        return self._write(data)


def get_signature_cache() -> SignatureCache:
    """Return a default cache instance."""

    return SignatureCache()
