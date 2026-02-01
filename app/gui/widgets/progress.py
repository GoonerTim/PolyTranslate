"""Progress bar widget with status text."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    pass


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
        """Create the widgets."""
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(pady=(5, 2), padx=10, anchor="w")

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self,
            width=380,
            height=15,
        )
        self.progress_bar.pack(pady=5, padx=10)
        self.progress_bar.set(0)

        # Percentage label
        self.percent_label = ctk.CTkLabel(
            self,
            text="0%",
            font=ctk.CTkFont(size=11),
        )
        self.percent_label.pack(pady=(0, 5))

    def set_progress(self, value: float) -> None:
        """
        Set the progress value.

        Args:
            value: Progress value between 0.0 and 1.0.
        """
        self._progress = max(0.0, min(1.0, value))
        self.progress_bar.set(self._progress)
        self.percent_label.configure(text=f"{int(self._progress * 100)}%")

    def set_status(self, status: str) -> None:
        """
        Set the status text.

        Args:
            status: Status text to display.
        """
        self._status = status
        self.status_label.configure(text=status)

    def reset(self) -> None:
        """Reset the progress bar."""
        self._progress = 0.0
        self._status = ""
        self.progress_bar.set(0)
        self.status_label.configure(text="")
        self.percent_label.configure(text="0%")

    def get_progress(self) -> float:
        """Get the current progress value."""
        return self._progress

    def get_status(self) -> str:
        """Get the current status text."""
        return self._status

    def start_indeterminate(self) -> None:
        """Start indeterminate mode (for unknown duration tasks)."""
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        self.percent_label.configure(text="...")

    def stop_indeterminate(self) -> None:
        """Stop indeterminate mode."""
        self.progress_bar.stop()
        self.progress_bar.configure(mode="determinate")
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%")
