"""Translation cache to avoid redundant API calls."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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

    def export_tmx(self, output_path: str | Path) -> Path:
        """Export cache entries to a TMX 1.4b file."""
        output_path = Path(output_path)

        root = ET.Element("tmx", version="1.4")
        header = ET.SubElement(
            root,
            "header",
            creationtool="PolyTranslate",
            creationtoolversion="3.0",
            datatype="plaintext",
            segtype="sentence",
            adminlang="en",
            srclang="*all*",
            creationdate=datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        )
        header.text = ""
        body = ET.SubElement(root, "body")

        with self._lock:
            entries = list(self._entries.values())

        for entry in entries:
            tu = ET.SubElement(body, "tu")
            tu.set("tuid", f"{entry['source_lang']}_{entry['target_lang']}_{entry['service']}")
            prop = ET.SubElement(tu, "prop", type="x-service")
            prop.text = entry["service"]

            src_tuv = ET.SubElement(tu, "tuv")
            src_tuv.set("{http://www.w3.org/XML/1998/namespace}lang", entry["source_lang"])
            src_seg = ET.SubElement(src_tuv, "seg")
            src_seg.text = entry["text"]

            tgt_tuv = ET.SubElement(tu, "tuv")
            tgt_tuv.set("{http://www.w3.org/XML/1998/namespace}lang", entry["target_lang"])
            tgt_seg = ET.SubElement(tgt_tuv, "seg")
            tgt_seg.text = entry["translation"]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(str(output_path), encoding="unicode", xml_declaration=True)

        logger.info("Exported %d cache entries to TMX: %s", len(entries), output_path)
        return output_path

    def import_tmx(self, input_path: str | Path) -> int:
        """Import translation units from a TMX file into the cache. Returns count imported."""
        input_path = Path(input_path)
        tree = ET.parse(str(input_path))  # noqa: S314
        root = tree.getroot()

        body = root.find("body")
        if body is None:
            return 0

        count = 0
        for tu in body.findall("tu"):
            service = ""
            prop = tu.find("prop[@type='x-service']")
            if prop is not None and prop.text:
                service = prop.text

            tuvs = tu.findall("tuv")
            if len(tuvs) < 2:
                continue

            src_tuv = tuvs[0]
            tgt_tuv = tuvs[1]

            src_lang = (
                src_tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
                or src_tuv.get("lang")
                or ""
            )
            tgt_lang = (
                tgt_tuv.get("{http://www.w3.org/XML/1998/namespace}lang")
                or tgt_tuv.get("lang")
                or ""
            )

            src_seg = src_tuv.find("seg")
            tgt_seg = tgt_tuv.find("seg")
            if src_seg is None or tgt_seg is None:
                continue

            text = src_seg.text or ""
            translation = tgt_seg.text or ""
            if not text or not translation:
                continue

            if not service:
                service = "imported"

            self.put(text, src_lang, tgt_lang, service, translation)
            count += 1

        logger.info("Imported %d entries from TMX: %s", count, input_path)
        return count
