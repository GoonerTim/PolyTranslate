import json
import re
from dataclasses import dataclass, field
from datetime import datetime

from app.services.base import TranslationService


@dataclass
class EvaluationResult:
    service: str
    score: float
    explanation: str
    timestamp: str
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


class AIEvaluator:
    def __init__(self, llm_service: TranslationService):
        self.llm_service = llm_service

    def evaluate_translations(
        self,
        original_text: str,
        translations: dict[str, str],
        source_lang: str,
        target_lang: str,
        is_renpy: bool = False,
    ) -> dict[str, EvaluationResult | str]:
        if not translations:
            raise ValueError("No translations provided for evaluation")

        if not self.llm_service.is_configured():
            raise RuntimeError(f"LLM service {self.llm_service.get_name()} is not configured")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        evaluation_prompt = self._create_evaluation_prompt(
            original_text, translations, source_lang, target_lang
        )

        try:
            evaluation_response = self.llm_service.translate(evaluation_prompt, "en", "en")
        except Exception as e:
            raise RuntimeError(f"Evaluation failed: {str(e)}") from e

        evaluations = self._parse_evaluation_response(evaluation_response, timestamp)

        improvement_prompt = self._create_improvement_prompt(
            original_text, translations, source_lang, target_lang, is_renpy
        )

        try:
            improved_translation = self.llm_service.translate(improvement_prompt, "en", "en")
        except Exception:
            improved_translation = ""

        if is_renpy and improved_translation:
            improved_translation = self._preserve_renpy_structure(
                original_text, improved_translation
            )

        result = {**evaluations}
        if improved_translation:
            result["ai_improved"] = improved_translation

        return result

    def _create_evaluation_prompt(
        self,
        original_text: str,
        translations: dict[str, str],
        source_lang: str,
        target_lang: str,
    ) -> str:
        translations_text = "\n".join(
            [
                f"{i + 1}. {service}: {text}"
                for i, (service, text) in enumerate(translations.items())
            ]
        )

        prompt = f"""You are a professional translation quality evaluator.

Evaluate these translations of the text from {source_lang} to {target_lang}.

Original text:
{original_text}

Translations:
{translations_text}

For each translation, provide:
- Score (0-10) based on accuracy, fluency, and naturalness
- Brief explanation (1-2 sentences) highlighting strengths/weaknesses

Respond in JSON format:
{{
  "evaluations": [
    {{"service": "service_name", "score": 8.5, "explanation": "..."}},
    ...
  ]
}}

Provide ONLY the JSON response, no additional text."""

        return prompt

    def _create_improvement_prompt(
        self,
        original_text: str,
        translations: dict[str, str],
        source_lang: str,
        target_lang: str,
        is_renpy: bool,
    ) -> str:
        translations_text = "\n".join(
            [f"- {service}: {text}" for service, text in translations.items()]
        )

        renpy_instruction = ""
        if is_renpy:
            renpy_instruction = "\n- CRITICAL: Preserve all Ren'Py dialogue markers, character names, and indentation exactly"

        prompt = f"""You are a professional translator.

Based on these translations from {source_lang} to {target_lang}, create an improved version that combines the best aspects.

Original: {original_text}

Translations:
{translations_text}

Requirements:
- Preserve exact meaning
- Maximum naturalness and fluency{renpy_instruction}

Output only the improved translation, no explanations."""

        return prompt

    def _parse_evaluation_response(
        self, response: str, timestamp: str
    ) -> dict[str, EvaluationResult]:
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)

            evaluations = {}
            for eval_item in data.get("evaluations", []):
                service = eval_item.get("service", "")
                score = float(eval_item.get("score", 0))
                explanation = eval_item.get("explanation", "")

                score = max(0.0, min(10.0, score))

                evaluations[service] = EvaluationResult(
                    service=service,
                    score=score,
                    explanation=explanation,
                    timestamp=timestamp,
                    strengths=eval_item.get("strengths", []),
                    weaknesses=eval_item.get("weaknesses", []),
                )

            return evaluations

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            raise RuntimeError(f"Failed to parse evaluation response: {str(e)}") from e

    def _preserve_renpy_structure(self, original: str, improved: str) -> str:
        if not self._is_renpy_dialogue(original):
            return improved

        # Ren'Py dialogue pattern: matches lines like '    character "dialogue"'
        dialogue_pattern = re.compile(r'^(\s*)(\w+)\s*(["\'])(.*?)(["\'])(.*)$', re.MULTILINE)

        original_lines = original.split("\n")
        improved_lines = improved.split("\n")

        result_lines = []
        improved_idx = 0

        for orig_line in original_lines:
            match = dialogue_pattern.match(orig_line)
            if match:
                if improved_idx < len(improved_lines):
                    indent = match.group(1)
                    character = match.group(2)
                    start_quote = match.group(3)
                    end_quote = match.group(5)
                    rest = match.group(6)

                    new_dialogue = improved_lines[improved_idx].strip()
                    new_dialogue = new_dialogue.strip('"').strip("'")

                    result_lines.append(
                        f"{indent}{character} {start_quote}{new_dialogue}{end_quote}{rest}"
                    )
                    improved_idx += 1
                else:
                    result_lines.append(orig_line)
            else:
                result_lines.append(orig_line)

        return "\n".join(result_lines)

    def _is_renpy_dialogue(self, text: str) -> bool:
        # Ren'Py dialogue pattern: matches lines like '    character "dialogue"'
        dialogue_pattern = re.compile(r'^\s*\w+\s*["\'].*?["\']', re.MULTILINE)
        return bool(dialogue_pattern.search(text))
