"""Tests for plugin loader."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.config.settings import Settings
from app.core.plugin_loader import ENTRY_POINT_GROUP, PluginInfo, discover_plugins
from app.services.base import TranslationService


class FakePlugin(TranslationService):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return f"[fake] {text}"

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Fake Service"


class AnotherPlugin(TranslationService):
    def __init__(self, settings: Settings) -> None:
        pass

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        return text

    def is_configured(self) -> bool:
        return True

    def get_name(self) -> str:
        return "Another"


def _make_ep(name: str, load_return: object) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = load_return
    return ep


class TestDiscoverPlugins:
    def test_no_plugins(self) -> None:
        with patch("app.core.plugin_loader.entry_points", return_value=[]):
            plugins = discover_plugins(Settings())
        assert plugins == []

    def test_loads_single_plugin(self) -> None:
        ep = _make_ep("fake", FakePlugin)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            plugins = discover_plugins(Settings())
        assert len(plugins) == 1
        assert plugins[0].service_id == "fake"
        assert plugins[0].display_name == "Fake Service"
        assert isinstance(plugins[0].service, FakePlugin)

    def test_loads_multiple_plugins(self) -> None:
        ep1 = _make_ep("fake", FakePlugin)
        ep2 = _make_ep("another", AnotherPlugin)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep1, ep2]):
            plugins = discover_plugins(Settings())
        assert len(plugins) == 2
        ids = {p.service_id for p in plugins}
        assert ids == {"fake", "another"}

    def test_skips_non_translation_service(self) -> None:
        def bad_factory(settings: Settings) -> str:
            return "not a service"

        ep = _make_ep("bad", bad_factory)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            plugins = discover_plugins(Settings())
        assert plugins == []

    def test_skips_plugin_that_raises(self) -> None:
        def broken_factory(settings: Settings) -> TranslationService:
            raise RuntimeError("boom")

        ep = _make_ep("broken", broken_factory)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            plugins = discover_plugins(Settings())
        assert plugins == []

    def test_good_plugin_survives_alongside_broken(self) -> None:
        def broken(settings: Settings) -> TranslationService:
            raise RuntimeError("boom")

        ep_broken = _make_ep("broken", broken)
        ep_good = _make_ep("fake", FakePlugin)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep_broken, ep_good]):
            plugins = discover_plugins(Settings())
        assert len(plugins) == 1
        assert plugins[0].service_id == "fake"

    def test_entry_point_group_constant(self) -> None:
        assert ENTRY_POINT_GROUP == "polytranslate.services"

    def test_passes_settings_to_factory(self) -> None:
        settings = Settings()
        factory = MagicMock(return_value=FakePlugin(settings))
        ep = _make_ep("test", factory)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            discover_plugins(settings)
        factory.assert_called_once_with(settings)

    def test_plugin_info_fields(self) -> None:
        svc = FakePlugin(Settings())
        info = PluginInfo("myid", "My Display", svc)
        assert info.service_id == "myid"
        assert info.display_name == "My Display"
        assert info.service is svc


class TestTranslatorPluginIntegration:
    def test_plugin_added_to_translator_services(self) -> None:
        from app.core.translator import Translator

        ep = _make_ep("fake_svc", FakePlugin)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            translator = Translator(Settings())
        assert "fake_svc" in translator.services
        assert isinstance(translator.services["fake_svc"], FakePlugin)

    def test_plugin_does_not_override_builtin(self) -> None:
        from app.core.translator import Translator

        ep = _make_ep("deepl", FakePlugin)  # conflict with built-in
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            translator = Translator(Settings())
        # deepl should remain the built-in DeepLService, not FakePlugin
        assert not isinstance(translator.services["deepl"], FakePlugin)

    def test_reload_services_reloads_plugins(self) -> None:
        from app.core.translator import Translator

        ep = _make_ep("fake_svc", FakePlugin)
        with patch("app.core.plugin_loader.entry_points", return_value=[ep]):
            translator = Translator(Settings())
            assert "fake_svc" in translator.services
            translator.reload_services()
            assert "fake_svc" in translator.services
