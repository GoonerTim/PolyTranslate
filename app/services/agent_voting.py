"""Multi-agent voting system for translation evaluation."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from app.services.base import TranslationService

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    name: str
    base_url: str = ""
    model: str = ""
    api_key: str = "not-needed"
    agent_type: str = "localai"
    weight: float = 1.0


@dataclass
class AgentVote:
    agent_name: str
    scores: dict[str, float] = field(default_factory=dict)
    best_service: str = ""
    explanations: dict[str, str] = field(default_factory=dict)
    merged_translation: str = ""


@dataclass
class VotingResult:
    votes: list[AgentVote] = field(default_factory=list)
    consensus_scores: dict[str, float] = field(default_factory=dict)
    consensus_best: str = ""
    merged_translation: str = ""
    agreement_ratio: float = 0.0


class AgentVoting:
    def __init__(self, agents: list[AgentConfig], context: str = "") -> None:
        self.agents = agents
        self._context = context

    def vote_on_translations(
        self,
        original_text: str,
        translations: dict[str, str],
        source_lang: str,
        target_lang: str,
        is_renpy: bool = False,
        max_workers: int = 3,
    ) -> VotingResult:
        if not translations:
            raise ValueError("No translations provided for voting")

        if not self.agents:
            raise ValueError("No agents configured for voting")

        prompt = self._create_voting_prompt(
            original_text, translations, source_lang, target_lang, is_renpy
        )

        votes: list[AgentVote] = []
        workers = min(max_workers, len(self.agents))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._query_agent, agent, prompt): agent for agent in self.agents
            }

            for future in as_completed(futures, timeout=120):
                agent = futures[future]
                try:
                    vote = future.result(timeout=60)
                    votes.append(vote)
                except Exception:
                    logger.warning("Agent %s failed, skipping", agent.name)

        if not votes:
            raise RuntimeError("All agents failed to respond")

        return self._compute_consensus(votes)

    def _create_agent_client(self, agent: AgentConfig) -> TranslationService:
        if agent.agent_type == "localai":
            from app.services.localai import LocalAIService

            return LocalAIService(
                base_url=agent.base_url,
                model=agent.model,
                api_key=agent.api_key,
            )
        elif agent.agent_type == "openai":
            from app.services.openai_service import OpenAIService

            return OpenAIService(api_key=agent.api_key, model=agent.model)
        elif agent.agent_type == "claude":
            from app.services.claude import ClaudeService

            return ClaudeService(api_key=agent.api_key, model=agent.model)
        elif agent.agent_type == "groq":
            from app.services.groq_service import GroqService

            return GroqService(api_key=agent.api_key, model=agent.model)
        else:
            raise ValueError(f"Unknown agent type: {agent.agent_type}")

    def _query_agent(self, agent: AgentConfig, prompt: str) -> AgentVote:
        client = self._create_agent_client(agent)
        response = client.translate(prompt, "en", "en")
        return self._parse_agent_response(agent.name, response)

    def _create_voting_prompt(
        self,
        original: str,
        translations: dict[str, str],
        src: str,
        tgt: str,
        is_renpy: bool,
    ) -> str:
        translations_text = "\n".join(
            f"{i + 1}. {service}: {text}" for i, (service, text) in enumerate(translations.items())
        )

        context_block = ""
        if self._context:
            context_block = f"\n{self._context}\n"

        renpy_note = ""
        if is_renpy:
            renpy_note = "\nNote: This is a Ren'Py visual novel translation. Preserve character names, dialogue markers, and indentation in the merged translation."

        prompt = f"""You are a professional translation evaluator.{context_block}

Evaluate these translations from {src} to {tgt}.

Original text:
{original}

Translations:
{translations_text}
{renpy_note}
For each translation:
- Score (0-10) based on accuracy, fluency, and naturalness
- Brief explanation (1-2 sentences)

Then create a merged/improved translation combining the best aspects.

Respond in JSON format ONLY:
{{
  "scores": {{"service_name": 8.5, ...}},
  "best": "service_name",
  "explanations": {{"service_name": "explanation", ...}},
  "merged": "the improved translation"
}}"""

        return prompt

    def _parse_agent_response(self, agent_name: str, response: str) -> AgentVote:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Agent %s returned invalid JSON, using fallback", agent_name)
            return AgentVote(agent_name=agent_name)

        scores: dict[str, float] = {}
        raw_scores = data.get("scores", {})
        for service, score in raw_scores.items():
            scores[service] = max(0.0, min(10.0, float(score)))

        best = data.get("best", "")
        if not best and scores:
            best = max(scores, key=scores.get)  # type: ignore[arg-type]

        explanations = data.get("explanations", {})
        merged = data.get("merged", "")

        return AgentVote(
            agent_name=agent_name,
            scores=scores,
            best_service=best,
            explanations=explanations,
            merged_translation=merged,
        )

    def _compute_consensus(self, votes: list[AgentVote]) -> VotingResult:
        all_services: set[str] = set()
        for vote in votes:
            all_services.update(vote.scores.keys())

        consensus_scores: dict[str, float] = {}
        total_weight = sum(
            agent.weight for agent in self.agents if any(v.agent_name == agent.name for v in votes)
        )

        if total_weight == 0:
            total_weight = 1.0

        for service in all_services:
            weighted_sum = 0.0
            service_weight = 0.0
            for vote in votes:
                if service in vote.scores:
                    agent_weight = self._get_agent_weight(vote.agent_name)
                    weighted_sum += vote.scores[service] * agent_weight
                    service_weight += agent_weight
            if service_weight > 0:
                consensus_scores[service] = weighted_sum / service_weight

        consensus_best = max(consensus_scores, key=consensus_scores.get) if consensus_scores else ""  # type: ignore[arg-type]

        # Agreement ratio: fraction of agents that agree on the best service
        if votes:
            agree_count = sum(1 for v in votes if v.best_service == consensus_best)
            agreement_ratio = agree_count / len(votes)
        else:
            agreement_ratio = 0.0

        # Pick merged translation from highest-weight agent that provided one
        merged = ""
        best_weight = 0.0
        for vote in votes:
            if vote.merged_translation:
                w = self._get_agent_weight(vote.agent_name)
                if w > best_weight:
                    best_weight = w
                    merged = vote.merged_translation

        return VotingResult(
            votes=votes,
            consensus_scores=consensus_scores,
            consensus_best=consensus_best,
            merged_translation=merged,
            agreement_ratio=agreement_ratio,
        )

    def _get_agent_weight(self, agent_name: str) -> float:
        for agent in self.agents:
            if agent.name == agent_name:
                return agent.weight
        return 1.0
