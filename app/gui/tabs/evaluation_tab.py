from __future__ import annotations

from typing import Any

import customtkinter as ctk

from app.gui.tabs.results_tab import ResultsTabMixin


class EvaluationTabMixin:
    def _update_ai_eval_tab(self) -> None:
        ai_eval_tab = self.results_tabview.tab("\U0001f916 AI Evaluation")

        for widget in ai_eval_tab.winfo_children():
            widget.destroy()

        if not self._evaluations:
            self._create_empty_ai_eval_state(ai_eval_tab)
            return

        scroll_frame = ctk.CTkScrollableFrame(ai_eval_tab)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)

        header_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header_frame,
            text="\U0001f916 AI Evaluation Report",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w")

        self._create_eval_summary(scroll_frame)

        if self._voting_result and self._voting_result.votes:
            self._create_agent_votes_section(scroll_frame)

        self._create_eval_details(scroll_frame)

        if self._ai_improved_translation:
            self._create_improved_section(scroll_frame)

    def _create_eval_summary(self, parent: ctk.CTkFrame) -> None:
        summary_card = ctk.CTkFrame(parent, corner_radius=12)
        summary_card.pack(fill="x", pady=(0, 15))

        summary_inner = ctk.CTkFrame(summary_card, fg_color="transparent")
        summary_inner.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            summary_inner,
            text="\U0001f4ca Summary Statistics",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        num_translations = len(self._evaluations)
        avg_score = sum(e.score for e in self._evaluations.values()) / num_translations
        best_service = self._best_service
        best_score = self._evaluations[best_service].score if best_service else 0

        stats_frame = ctk.CTkFrame(summary_inner, fg_color="transparent")
        stats_frame.pack(fill="x")

        stats = [
            ("Evaluated:", f"{num_translations} translations"),
            ("Best:", f"{best_service.upper()} (\u2b50 {best_score:.1f}/10)"),
            ("Average Score:", f"{avg_score:.1f}/10"),
        ]

        for label, value in stats:
            row = ctk.CTkFrame(stats_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=150,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(row, text=value, font=ctk.CTkFont(size=12), anchor="w").pack(side="left")

    def _create_agent_votes_section(self, parent: ctk.CTkFrame) -> None:
        votes_card = ctk.CTkFrame(parent, corner_radius=12)
        votes_card.pack(fill="x", pady=(0, 15))

        votes_inner = ctk.CTkFrame(votes_card, fg_color="transparent")
        votes_inner.pack(fill="x", padx=20, pady=15)

        result = self._voting_result
        if not result:
            return

        ctk.CTkLabel(
            votes_inner,
            text="\U0001f5f3\ufe0f Agent Votes",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w", pady=(0, 10))

        total = len(result.votes)
        agree = sum(1 for v in result.votes if v.best_service == result.consensus_best)
        if total == agree:
            agree_text = (
                f"\u2705 {agree}/{total} agents agree on best: {result.consensus_best.upper()}"
            )
            agree_color = ("#10b981", "#34d399")
        else:
            agree_text = (
                f"\U0001f5f3\ufe0f {agree}/{total} majority for: {result.consensus_best.upper()}"
            )
            agree_color = ("#d97706", "#f59e0b")

        ctk.CTkLabel(
            votes_inner,
            text=agree_text,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=agree_color,
        ).pack(anchor="w", pady=(0, 8))

        for vote in result.votes:
            row = ctk.CTkFrame(votes_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=vote.agent_name,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=120,
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                row,
                text=f"Best: {vote.best_service}",
                font=ctk.CTkFont(size=12),
                width=120,
                anchor="w",
            ).pack(side="left", padx=5)

            scores_text = " | ".join(
                f"{s}: {sc:.1f}" for s, sc in sorted(vote.scores.items(), key=lambda x: -x[1])
            )
            ctk.CTkLabel(
                row,
                text=scores_text,
                font=ctk.CTkFont(size=11),
                anchor="w",
            ).pack(side="left", padx=5)

    def _create_eval_details(self, parent: ctk.CTkFrame) -> None:
        details_header = ctk.CTkFrame(parent, fg_color="transparent")
        details_header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            details_header,
            text="\U0001f4dd Detailed Evaluations",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w")

        sorted_evals = sorted(self._evaluations.items(), key=lambda x: x[1].score, reverse=True)

        for service, eval_result in sorted_evals:
            eval_card = ctk.CTkFrame(
                parent,
                corner_radius=10,
                fg_color=self._get_rating_color(eval_result.score),
            )
            eval_card.pack(fill="x", pady=5)

            eval_inner = ctk.CTkFrame(eval_card, fg_color="transparent")
            eval_inner.pack(fill="x", padx=15, pady=12)

            header = ctk.CTkFrame(eval_inner, fg_color="transparent")
            header.pack(fill="x", pady=(0, 8))

            icon = ResultsTabMixin.SERVICE_ICONS.get(service, "\u2022")
            title_text = f"{icon} {service.upper()}"
            if service == self._best_service:
                title_text += " \U0001f3c6"

            ctk.CTkLabel(
                header,
                text=title_text,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=f"\u2b50 {eval_result.score:.1f}/10",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self._get_score_text_color(eval_result.score),
            ).pack(side="right")

            ctk.CTkLabel(
                eval_inner,
                text=eval_result.explanation,
                font=ctk.CTkFont(size=12),
                wraplength=700,
                anchor="w",
                justify="left",
            ).pack(fill="x")

    def _create_improved_section(self, parent: ctk.CTkFrame) -> None:
        improved_header = ctk.CTkFrame(parent, fg_color="transparent")
        improved_header.pack(fill="x", pady=(15, 10))

        ctk.CTkLabel(
            improved_header,
            text="\u2728 AI Improved Translation",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(anchor="w")

        improved_card = ctk.CTkFrame(parent, corner_radius=12)
        improved_card.pack(fill="x", pady=(0, 15))

        text_box = ctk.CTkTextbox(
            improved_card,
            wrap="word",
            height=200,
            font=ctk.CTkFont(size=13),
            activate_scrollbars=True,
        )
        text_box.pack(fill="both", expand=True, padx=15, pady=15)
        text_box.insert("1.0", self._ai_improved_translation)
        text_box.configure(state="normal")

        def on_text_change(event: Any = None) -> None:
            self._ai_improved_translation = text_box.get("1.0", "end-1c")
            if "ai_improved" in self._translations:
                self._translations["ai_improved"] = self._ai_improved_translation

        text_box._textbox.bind(
            "<<Modified>>",
            lambda e: (  # type: ignore[attr-defined]
                on_text_change() if text_box._textbox.edit_modified() else None,  # type: ignore[attr-defined]
                text_box._textbox.edit_modified(False),  # type: ignore[attr-defined]
            ),
        )

        button_frame = ctk.CTkFrame(improved_card, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            button_frame,
            text="\U0001f4cb Copy",
            command=lambda: self._copy_to_clipboard(text_box.get("1.0", "end-1c")),
            width=120,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="\U0001f4be Save to File",
            command=lambda: self._save_translation(text_box.get("1.0", "end-1c"), "ai_improved"),
            width=120,
            height=35,
            corner_radius=8,
            font=ctk.CTkFont(size=12),
        ).pack(side="left", padx=5)

    def _get_rating_color(self, score: float) -> tuple[str, str]:
        if score < 5.0:
            return ("#fee2e2", "#991b1b")
        elif score < 7.0:
            return ("#fef3c7", "#92400e")
        else:
            return ("#d1fae5", "#065f46")

    def _get_score_text_color(self, score: float) -> tuple[str, str]:
        if score < 5.0:
            return ("#dc2626", "#ef4444")
        elif score < 7.0:
            return ("#d97706", "#f59e0b")
        else:
            return ("#10b981", "#34d399")
