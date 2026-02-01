from __future__ import annotations

import customtkinter as ctk


class ProgressBar(ctk.CTkFrame):
    """A progress bar with status text."""

    def __init__(
        self,
        master: ctk.CTk | ctk.CTkFrame,
        width: int = 400,
        height: int = 60,
        **kwargs: object,
    ) -> None:
        """
        Initialize the progress bar.

        Args:
            master: Parent widget.
            width: Widget width.
            height: Widget height.
        """
        super().__init__(master, width=width, height=height, **kwargs)

        self._progress: float = 0.0
        self._status: str = ""

        self._create_widgets()

    def _create_widgets(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=8)

        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 5))

        self.status_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_label.pack(side="left")

        self.percent_label = ctk.CTkLabel(
            header,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#2563eb", "#60a5fa"),
        )
        self.percent_label.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            container,
            width=940,
            height=20,
            corner_radius=10,
            progress_color=("#2563eb", "#1e40af"),
        )
        self.progress_bar.pack(pady=2)
        self.progress_bar.set(0)

    def set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, value))
        self.progress_bar.set(self._progress)
        self.percent_label.configure(text=f"{int(self._progress * 100)}%")

    def set_status(self, status: str) -> None:
        self._status = status
        self.status_label.configure(text=status)

    def reset(self) -> None:
        self._progress = 0.0
        self._status = ""
        self.progress_bar.set(0)
        self.status_label.configure(text="")
        self.percent_label.configure(text="0%")

    def get_progress(self) -> float:
        return self._progress

    def get_status(self) -> str:
        return self._status

    def start_indeterminate(self) -> None:
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.percent_label.configure(text="...")

    def stop_indeterminate(self) -> None:
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
