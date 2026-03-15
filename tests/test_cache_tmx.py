"""Tests for TMX export/import in TranslationCache."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from app.utils.cache import TranslationCache


class TestExportTmx:
    def test_export_creates_file(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        output = tmp_path / "export.tmx"
        result = cache.export_tmx(output)
        assert result == output
        assert output.exists()

    def test_export_valid_xml(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        output = tmp_path / "export.tmx"
        cache.export_tmx(output)

        tree = ET.parse(str(output))
        root = tree.getroot()
        assert root.tag == "tmx"
        assert root.attrib["version"] == "1.4"

    def test_export_header(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        output = tmp_path / "export.tmx"
        cache.export_tmx(output)

        tree = ET.parse(str(output))
        header = tree.getroot().find("header")
        assert header is not None
        assert header.attrib["creationtool"] == "PolyTranslate"
        assert header.attrib["datatype"] == "plaintext"
        assert header.attrib["segtype"] == "sentence"

    def test_export_tu_structure(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        output = tmp_path / "export.tmx"
        cache.export_tmx(output)

        tree = ET.parse(str(output))
        body = tree.getroot().find("body")
        assert body is not None
        tus = body.findall("tu")
        assert len(tus) == 1

        tu = tus[0]
        prop = tu.find("prop[@type='x-service']")
        assert prop is not None
        assert prop.text == "deepl"

        tuvs = tu.findall("tuv")
        assert len(tuvs) == 2

        xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
        assert tuvs[0].attrib[xml_lang] == "en"
        assert tuvs[0].find("seg").text == "hello"
        assert tuvs[1].attrib[xml_lang] == "ru"
        assert tuvs[1].find("seg").text == "привет"

    def test_export_multiple_entries(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        cache.put("world", "en", "de", "google", "Welt")
        output = tmp_path / "export.tmx"
        cache.export_tmx(output)

        tree = ET.parse(str(output))
        body = tree.getroot().find("body")
        tus = body.findall("tu")
        assert len(tus) == 2

    def test_export_creates_parent_dirs(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("hello", "en", "ru", "deepl", "привет")
        output = tmp_path / "sub" / "dir" / "export.tmx"
        result = cache.export_tmx(output)
        assert result.exists()

    def test_export_empty_cache(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        output = tmp_path / "export.tmx"
        cache.export_tmx(output)

        tree = ET.parse(str(output))
        body = tree.getroot().find("body")
        assert body is not None
        assert len(body.findall("tu")) == 0


class TestImportTmx:
    def _make_tmx(self, path: Path, entries: list[dict]) -> None:
        root = ET.Element("tmx", version="1.4")
        ET.SubElement(root, "header", creationtool="test", datatype="plaintext", srclang="en")
        body = ET.SubElement(root, "body")
        for e in entries:
            tu = ET.SubElement(body, "tu")
            if "service" in e:
                prop = ET.SubElement(tu, "prop", type="x-service")
                prop.text = e["service"]
            src_tuv = ET.SubElement(tu, "tuv")
            src_tuv.set("{http://www.w3.org/XML/1998/namespace}lang", e["src_lang"])
            src_seg = ET.SubElement(src_tuv, "seg")
            src_seg.text = e["text"]
            tgt_tuv = ET.SubElement(tu, "tuv")
            tgt_tuv.set("{http://www.w3.org/XML/1998/namespace}lang", e["tgt_lang"])
            tgt_seg = ET.SubElement(tgt_tuv, "seg")
            tgt_seg.text = e["translation"]
        tree = ET.ElementTree(root)
        tree.write(str(path), encoding="unicode", xml_declaration=True)

    def test_import_basic(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {
                    "text": "hello",
                    "src_lang": "en",
                    "tgt_lang": "ru",
                    "translation": "привет",
                    "service": "deepl",
                },
            ],
        )

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 1
        assert cache.get("hello", "en", "ru", "deepl") == "привет"

    def test_import_multiple(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {
                    "text": "hello",
                    "src_lang": "en",
                    "tgt_lang": "ru",
                    "translation": "привет",
                    "service": "deepl",
                },
                {
                    "text": "world",
                    "src_lang": "en",
                    "tgt_lang": "de",
                    "translation": "Welt",
                    "service": "google",
                },
            ],
        )

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 2
        assert cache.get("hello", "en", "ru", "deepl") == "привет"
        assert cache.get("world", "en", "de", "google") == "Welt"

    def test_import_no_service_defaults_to_imported(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {"text": "hello", "src_lang": "en", "tgt_lang": "ru", "translation": "привет"},
            ],
        )

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 1
        assert cache.get("hello", "en", "ru", "imported") == "привет"

    def test_import_skips_empty_text(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {
                    "text": "",
                    "src_lang": "en",
                    "tgt_lang": "ru",
                    "translation": "привет",
                    "service": "deepl",
                },
            ],
        )

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 0

    def test_import_skips_empty_translation(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {
                    "text": "hello",
                    "src_lang": "en",
                    "tgt_lang": "ru",
                    "translation": "",
                    "service": "deepl",
                },
            ],
        )

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 0

    def test_import_empty_body(self, tmp_path: Path) -> None:
        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(tmx_path, [])

        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        count = cache.import_tmx(tmx_path)
        assert count == 0

    def test_import_merges_with_existing(self, tmp_path: Path) -> None:
        cache = TranslationCache(cache_path=tmp_path / "cache.json")
        cache.put("existing", "en", "ru", "deepl", "существующий")

        tmx_path = tmp_path / "import.tmx"
        self._make_tmx(
            tmx_path,
            [
                {
                    "text": "hello",
                    "src_lang": "en",
                    "tgt_lang": "ru",
                    "translation": "привет",
                    "service": "google",
                },
            ],
        )

        count = cache.import_tmx(tmx_path)
        assert count == 1
        assert cache.get("existing", "en", "ru", "deepl") == "существующий"
        assert cache.get("hello", "en", "ru", "google") == "привет"


class TestRoundTrip:
    def test_export_then_import(self, tmp_path: Path) -> None:
        cache1 = TranslationCache(cache_path=tmp_path / "cache1.json")
        cache1.put("hello", "en", "ru", "deepl", "привет")
        cache1.put("world", "en", "de", "google", "Welt")
        cache1.put("cat", "en", "fr", "yandex", "chat")

        tmx_path = tmp_path / "roundtrip.tmx"
        cache1.export_tmx(tmx_path)

        cache2 = TranslationCache(cache_path=tmp_path / "cache2.json")
        count = cache2.import_tmx(tmx_path)
        assert count == 3
        assert cache2.get("hello", "en", "ru", "deepl") == "привет"
        assert cache2.get("world", "en", "de", "google") == "Welt"
        assert cache2.get("cat", "en", "fr", "yandex") == "chat"

    def test_roundtrip_unicode(self, tmp_path: Path) -> None:
        cache1 = TranslationCache(cache_path=tmp_path / "cache1.json")
        cache1.put("日本語テスト", "ja", "en", "deepl", "Japanese test")
        cache1.put("Ñoño", "es", "en", "google", "Kiddo")

        tmx_path = tmp_path / "unicode.tmx"
        cache1.export_tmx(tmx_path)

        cache2 = TranslationCache(cache_path=tmp_path / "cache2.json")
        count = cache2.import_tmx(tmx_path)
        assert count == 2
        assert cache2.get("日本語テスト", "ja", "en", "deepl") == "Japanese test"
        assert cache2.get("Ñoño", "es", "en", "google") == "Kiddo"

    def test_roundtrip_preserves_service(self, tmp_path: Path) -> None:
        cache1 = TranslationCache(cache_path=tmp_path / "cache1.json")
        cache1.put("hello", "en", "ru", "deepl", "привет")
        cache1.put("hello", "en", "ru", "google", "здравствуйте")

        tmx_path = tmp_path / "services.tmx"
        cache1.export_tmx(tmx_path)

        cache2 = TranslationCache(cache_path=tmp_path / "cache2.json")
        cache2.import_tmx(tmx_path)
        assert cache2.get("hello", "en", "ru", "deepl") == "привет"
        assert cache2.get("hello", "en", "ru", "google") == "здравствуйте"
