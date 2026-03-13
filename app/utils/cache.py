"""Translation cache to avoid redundant API calls."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TranslationCache:
    """In-memory + JSON-persisted translation cache with LRU eviction."""

    def __init__(
        self,
        cache_path: str | Path | None = None,
        max_size: int = 10000,
        enabled: bool = True,
    ) -> None:
        if cache_path is None:
            self.cache_path = Path("cache.json")
        else:
            self.cache_path = Path(cache_path)

        self.max_size = max_size
        self.enabled = enabled
        self._entries: dict[str, dict[str, Any]] = {}
        self._access_order: list[str] = []
        self._lock = threading.Lock()
        self._dirty = False
        self.load()

    @staticmethod
    def _make_key(text: str, source_lang: str, target_lang: str, service: str) -> str:
        raw = f"{text.strip()}|{source_lang.lower()}|{target_lang.lower()}|{service.lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, text: str, source_lang: str, target_lang: str, service: str) -> str | None:
        if not self.enabled:
            return None

        key = self._make_key(text, source_lang, target_lang, service)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            return entry["translation"]

    def put(
        self, text: str, source_lang: str, target_lang: str, service: str, translation: str
    ) -> None:
        if not self.enabled:
            return

        key = self._make_key(text, source_lang, target_lang, service)
        with self._lock:
            self._entries[key] = {
                "text": text.strip(),
                "source_lang": source_lang.lower(),
                "target_lang": target_lang.lower(),
                "service": service.lower(),
                "translation": translation,
            }
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            self._dirty = True
            self._evict()

    def _evict(self) -> None:
        while len(self._entries) > self.max_size and self._access_order:
            oldest_key = self._access_order.pop(0)
            self._entries.pop(oldest_key, None)

    def load(self) -> None:
        if not self.cache_path.exists():
            return
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "entries" in data:
                self._entries = data["entries"]
                self._access_order = data.get("access_order", list(self._entries.keys()))
            else:
                self._entries = {}
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load cache from %s: %s", self.cache_path, e)
            self._entries = {}

    def save(self) -> None:
        if not self._dirty:
            return
        try:
            with self._lock:
                data = {
                    "entries": self._entries,
                    "access_order": self._access_order,
                }
                self._dirty = False
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except OSError as e:
            logger.error("Failed to save cache to %s: %s", self.cache_path, e)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._access_order.clear()
            self._dirty = True

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: tuple[str, str, str, str]) -> bool:
        text, source_lang, target_lang, service = key
        return self.get(text, source_lang, target_lang, service) is not None
