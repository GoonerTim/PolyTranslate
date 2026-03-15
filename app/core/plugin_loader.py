"""Plugin loader for discovering translation services via entry points."""

from __future__ import annotations

import logging
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from app.services.base import TranslationService

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "polytranslate.services"


class PluginInfo:
    """Metadata about a loaded plugin service."""

    __slots__ = ("service_id", "display_name", "service")

    def __init__(self, service_id: str, display_name: str, service: TranslationService) -> None:
        self.service_id = service_id
        self.display_name = display_name
        self.service = service


def discover_plugins(settings: Settings) -> list[PluginInfo]:
    """Discover and load translation service plugins from entry points.

    Each entry point in the ``polytranslate.services`` group must point to a
    callable (class or factory function) that accepts a single ``Settings``
    argument and returns a ``TranslationService`` instance.

    The entry point *name* is used as the service ID (e.g. ``mymemory``).
    The loaded service's ``get_name()`` provides the display name.
    """
    plugins: list[PluginInfo] = []

    try:
        eps = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        # Python 3.9 fallback (entry_points() returns dict)
        eps = entry_points().get(ENTRY_POINT_GROUP, [])  # type: ignore[assignment]

    for ep in eps:
        service_id = ep.name
        try:
            factory = ep.load()
            service = factory(settings)

            if not isinstance(service, TranslationService):
                logger.warning(
                    "Plugin '%s' returned %s, expected TranslationService — skipped",
                    service_id,
                    type(service).__name__,
                )
                continue

            display_name = service.get_name()
            plugins.append(PluginInfo(service_id, display_name, service))
            logger.info("Loaded plugin service: %s (%s)", service_id, display_name)

        except Exception:
            logger.exception("Failed to load plugin '%s'", service_id)

    return plugins
