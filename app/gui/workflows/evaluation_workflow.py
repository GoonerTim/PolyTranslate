from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.renpy_context import RenpyContextExtractor
from app.services.agent_voting import AgentConfig, AgentVoting
from app.services.ai_evaluator import AIEvaluator, EvaluationResult


class EvaluationWorkflowMixin:
    def _start_evaluation(self) -> None:
        from tkinter import messagebox

        if not self._translations or not self._original_text:
            messagebox.showwarning("No Translations", "Please translate text first")
            return

        agents_config = self.settings.get("agents", [])

        if agents_config:
            self._start_agent_voting(agents_config)
        else:
            self._start_single_evaluation()

    def _start_single_evaluation(self) -> None:
        from tkinter import messagebox

        evaluator_service = self.settings.get("ai_evaluator_service", "")
        if not evaluator_service or evaluator_service not in self.translator.services:
            messagebox.showerror(
                "AI Evaluator Not Configured",
                "Please select an AI Evaluator service in Settings\n\n"
                "Go to Settings > AI Evaluation Settings and choose a service\n"
                "(OpenAI, Claude, Groq, or LocalAI)",
            )
            return

        llm_service = self.translator.services[evaluator_service]
        self._ai_evaluator = AIEvaluator(llm_service)

        self.evaluate_button.configure(state="disabled", text="\U0001f916 Evaluating...")
        self.translate_button.configure(state="disabled")
        self.compare_button.configure(state="disabled")
        self.progress.set_status("Evaluating translations...")

        is_renpy = self._current_file and self._current_file.endswith(".rpy")

        thread = threading.Thread(
            target=self._run_evaluation,
            args=(is_renpy,),
            daemon=True,
        )
        thread.start()

    def _start_agent_voting(self, agents_config: list[dict[str, Any]]) -> None:
        self._voting_result = None

        self.evaluate_button.configure(state="disabled", text="\U0001f916 Voting...")
        self.translate_button.configure(state="disabled")
        self.compare_button.configure(state="disabled")
        self.progress.set_status("Agents are voting on translations...")

        is_renpy = bool(self._current_file and self._current_file.endswith(".rpy"))

        context = ""
        renpy_folder = self.settings.get("renpy_game_folder", "")
        if is_renpy and renpy_folder:
            try:
                self._renpy_context_extractor = RenpyContextExtractor(renpy_folder)
                context = self._renpy_context_extractor.get_context_for_text(
                    self._original_text, self._current_file or ""
                )
            except Exception:
                pass

        agents = [
            AgentConfig(
                name=a.get("name", f"Agent {i}"),
                base_url=a.get("base_url", ""),
                model=a.get("model", ""),
                api_key=a.get("api_key", "not-needed"),
                agent_type=a.get("agent_type", "localai"),
                weight=a.get("weight", 1.0),
            )
            for i, a in enumerate(agents_config)
        ]

        voting = AgentVoting(agents, context=context)

        thread = threading.Thread(
            target=self._run_agent_voting,
            args=(voting, is_renpy),
            daemon=True,
        )
        thread.start()

    def _run_agent_voting(self, voting: AgentVoting, is_renpy: bool) -> None:
        try:
            source_lang = self.source_lang_var.get()
            target_lang = self.target_lang_var.get()

            result = voting.vote_on_translations(
                original_text=self._original_text,
                translations=self._translations,
                source_lang=source_lang,
                target_lang=target_lang,
                is_renpy=is_renpy,
                max_workers=self.settings.get_max_workers(),
            )

            self._voting_result = result
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self._evaluations = {}
            for service, score in result.consensus_scores.items():
                explanations = []
                for vote in result.votes:
                    if service in vote.explanations:
                        explanations.append(vote.explanations[service])
                explanation = " | ".join(explanations) if explanations else ""

                self._evaluations[service] = EvaluationResult(
                    service=service,
                    score=score,
                    explanation=explanation,
                    timestamp=timestamp,
                )

            self._ai_improved_translation = result.merged_translation
            if self._evaluations:
                self._best_service = result.consensus_best

            self.root.after(0, self._on_evaluation_complete)

        except Exception as e:
            error_msg = f"Agent voting failed: {str(e)}"
            self.root.after(0, lambda: self._on_evaluation_error(error_msg))

    def _run_evaluation(self, is_renpy: bool) -> None:
        try:
            source_lang = self.source_lang_var.get()
            target_lang = self.target_lang_var.get()

            results = self._ai_evaluator.evaluate_translations(  # type: ignore[union-attr]
                original_text=self._original_text,
                translations=self._translations,
                source_lang=source_lang,
                target_lang=target_lang,
                is_renpy=is_renpy,
            )

            self._evaluations = {
                service: result
                for service, result in results.items()
                if isinstance(result, EvaluationResult)
            }

            self._ai_improved_translation = results.get("ai_improved", "")  # type: ignore[assignment]

            if self._evaluations:
                self._best_service = max(self._evaluations.items(), key=lambda x: x[1].score)[0]

            self._voting_result = None
            self.root.after(0, self._on_evaluation_complete)

        except Exception as e:
            error_msg = f"Evaluation failed: {str(e)}"
            self.root.after(0, lambda: self._on_evaluation_error(error_msg))

    def _on_evaluation_complete(self) -> None:
        agents_config = self.settings.get("agents", [])
        button_text = "\U0001f916 Agent Vote" if agents_config else "\U0001f916 Evaluate All"
        self.evaluate_button.configure(state="normal", text=button_text)
        self.translate_button.configure(state="normal")
        self.compare_button.configure(state="normal")
        self.progress.reset()

        self._update_results()
        self._update_comparison_tab()
        self._update_ai_eval_tab()

        avg_score = sum(e.score for e in self._evaluations.values()) / len(self._evaluations)
        self._status(f"\u2705 Evaluation complete! Average score: {avg_score:.1f}/10")

        if self._ai_improved_translation:
            self._translations["ai_improved"] = self._ai_improved_translation

        self.results_tabview.set("\U0001f916 AI Evaluation")

        if self._evaluations:
            evaluations_dict = {
                service: {
                    "score": result.score,
                    "explanation": result.explanation,
                    "timestamp": result.timestamp,
                }
                for service, result in self._evaluations.items()
            }

            file_name = Path(self._current_file).name if self._current_file else ""
            self.history.add_entry(
                self._original_text,
                self._translations,
                self.source_lang_var.get(),
                self.target_lang_var.get(),
                file_name,
                evaluations=evaluations_dict,
                ai_improved=self._ai_improved_translation,
                best_service=self._best_service,
            )

    def _on_evaluation_error(self, error: str) -> None:
        from tkinter import messagebox

        agents_config = self.settings.get("agents", [])
        button_text = "\U0001f916 Agent Vote" if agents_config else "\U0001f916 Evaluate All"
        self.evaluate_button.configure(state="normal", text=button_text)
        self.translate_button.configure(state="normal")
        self.compare_button.configure(state="normal")
        self.progress.reset()
        messagebox.showerror("Evaluation Error", error)
        self._status(f"Evaluation error: {error}")
