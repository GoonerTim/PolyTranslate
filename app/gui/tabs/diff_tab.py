from __future__ import annotations

import customtkinter as ctk

from app.gui.tabs.results_tab import ResultsTabMixin
from app.gui.widgets.diff_view import DiffView


class DiffTabMixin:
    def _update_diff_tab(self) -> None:
        diff_tab = self.results_tabview.tab("\U0001f500 Diff")
        for widget in diff_tab.winfo_children():
            widget.destroy()

        if not self._translations or not self._original_text:
            self._create_empty_diff_state(diff_tab)
            return

        services = list(self._translations.keys())

        if len(services) == 1:
            service = services[0]
            diff_view = DiffView(
                diff_tab,
                on_change=lambda text, svc=service: self._on_diff_revert(svc, text),
            )
            diff_view.pack(fill="both", expand=True, padx=5, pady=5)
            diff_view.set_diff(
                self._original_text,
                self._translations[service],
                service_name=service,
                service_icon=ResultsTabMixin.SERVICE_ICONS.get(service, ""),
            )
        else:
            diff_tabview = ctk.CTkTabview(diff_tab, corner_radius=8)
            diff_tabview.pack(fill="both", expand=True, padx=5, pady=5)

            for service in services:
                icon = ResultsTabMixin.SERVICE_ICONS.get(service, "\u2022")
                tab_name = f"{icon} {service.upper()}"
                diff_tabview.add(tab_name)
                tab = diff_tabview.tab(tab_name)

                diff_view = DiffView(
                    tab,
                    on_change=lambda text, svc=service: self._on_diff_revert(svc, text),
                )
                diff_view.pack(fill="both", expand=True)
                diff_view.set_diff(
                    self._original_text,
                    self._translations[service],
                    service_name=service,
                    service_icon=icon,
                )

    def _on_diff_revert(self, service: str, text: str) -> None:
        self._translations[service] = text
