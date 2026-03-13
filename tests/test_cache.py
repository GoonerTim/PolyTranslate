"""Tests for translation cache."""

from __future__ import annotations

import json
from pathlib import Path

from app.utils.cache import TranslationCache


class TestTranslationCache:
    def test_put_and_get(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        assert cache.get("hello", "en", "ru", "deepl") == "привет"

    def test_miss_returns_none(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        assert cache.get("hello", "en", "ru", "deepl") is None

    def test_different_service_different_entry(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет1")
        cache.put("hello", "en", "ru", "google", "привет2")
        assert cache.get("hello", "en", "ru", "deepl") == "привет1"
        assert cache.get("hello", "en", "ru", "google") == "привет2"

    def test_different_lang_pair(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        cache.put("hello", "en", "de", "deepl", "hallo")
        assert cache.get("hello", "en", "ru", "deepl") == "привет"
        assert cache.get("hello", "en", "de", "deepl") == "hallo"

    def test_case_insensitive_keys(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "EN", "RU", "DeepL", "привет")
        assert cache.get("hello", "en", "ru", "deepl") == "привет"

    def test_strips_whitespace(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("  hello  ", "en", "ru", "deepl", "привет")
        assert cache.get("hello", "en", "ru", "deepl") == "привет"

    def test_save_and_load(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = TranslationCache(cache_path=path)
        cache.put("hello", "en", "ru", "deepl", "привет")
        cache.save()

        cache2 = TranslationCache(cache_path=path)
        assert cache2.get("hello", "en", "ru", "deepl") == "привет"

    def test_save_creates_file(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = TranslationCache(cache_path=path)
        cache.put("test", "en", "ru", "deepl", "тест")
        cache.save()
        assert path.exists()

    def test_save_skips_when_not_dirty(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = TranslationCache(cache_path=path)
        cache.save()
        assert not path.exists()

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "nonexistent.json")
        assert len(cache) == 0

    def test_load_corrupted_file(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        path.write_text("not json", encoding="utf-8")
        cache = TranslationCache(cache_path=path)
        assert len(cache) == 0

    def test_lru_eviction(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json", max_size=3)
        cache.put("a", "en", "ru", "deepl", "а")
        cache.put("b", "en", "ru", "deepl", "б")
        cache.put("c", "en", "ru", "deepl", "в")
        cache.put("d", "en", "ru", "deepl", "г")
        assert len(cache) == 3
        assert cache.get("a", "en", "ru", "deepl") is None
        assert cache.get("d", "en", "ru", "deepl") == "г"

    def test_lru_access_refreshes(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json", max_size=3)
        cache.put("a", "en", "ru", "deepl", "а")
        cache.put("b", "en", "ru", "deepl", "б")
        cache.put("c", "en", "ru", "deepl", "в")
        # Access "a" to refresh it
        cache.get("a", "en", "ru", "deepl")
        # Add new entry — should evict "b" (oldest unreferenced)
        cache.put("d", "en", "ru", "deepl", "г")
        assert cache.get("a", "en", "ru", "deepl") == "а"
        assert cache.get("b", "en", "ru", "deepl") is None

    def test_clear(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        cache.clear()
        assert len(cache) == 0
        assert cache.get("hello", "en", "ru", "deepl") is None

    def test_len(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        assert len(cache) == 0
        cache.put("a", "en", "ru", "deepl", "а")
        assert len(cache) == 1
        cache.put("b", "en", "ru", "deepl", "б")
        assert len(cache) == 2

    def test_contains(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        assert ("hello", "en", "ru", "deepl") in cache
        assert ("bye", "en", "ru", "deepl") not in cache

    def test_disabled_cache(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json", enabled=False)
        cache.put("hello", "en", "ru", "deepl", "привет")
        assert cache.get("hello", "en", "ru", "deepl") is None
        assert len(cache) == 0

    def test_overwrite_existing_entry(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет1")
        cache.put("hello", "en", "ru", "deepl", "привет2")
        assert cache.get("hello", "en", "ru", "deepl") == "привет2"
        assert len(cache) == 1

    def test_persistence_format(self, tmp_path: Path) -> None:
        path = tmp_path / "cache.json"
        cache = TranslationCache(cache_path=path)
        cache.put("hello", "en", "ru", "deepl", "привет")
        cache.save()

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "entries" in data
        assert "access_order" in data
        values = list(data["entries"].values())
        assert values[0]["translation"] == "привет"
