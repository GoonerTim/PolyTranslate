"""Tests for multi-agent voting system."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from app.services.agent_voting import AgentConfig, AgentVote, AgentVoting, VotingResult


class TestAgentConfig:
    def test_creation(self) -> None:
        config = AgentConfig(
            name="Mistral 7B",
            base_url="http://localhost:1234/v1",
            model="mistral-7b",
            api_key="not-needed",
            agent_type="localai",
            weight=1.5,
        )
        assert config.name == "Mistral 7B"
        assert config.base_url == "http://localhost:1234/v1"
        assert config.model == "mistral-7b"
        assert config.weight == 1.5

    def test_defaults(self) -> None:
        config = AgentConfig(name="Test")
        assert config.base_url == ""
        assert config.api_key == "not-needed"
        assert config.agent_type == "localai"
        assert config.weight == 1.0


class TestAgentVote:
    def test_creation(self) -> None:
        vote = AgentVote(
            agent_name="Agent1",
            scores={"deepl": 8.0, "google": 7.0},
            best_service="deepl",
            explanations={"deepl": "Good", "google": "OK"},
            merged_translation="merged text",
        )
        assert vote.agent_name == "Agent1"
        assert vote.scores["deepl"] == 8.0
        assert vote.best_service == "deepl"

    def test_empty_defaults(self) -> None:
        vote = AgentVote(agent_name="Agent1")
        assert vote.scores == {}
        assert vote.best_service == ""
        assert vote.merged_translation == ""


class TestVotingResult:
    def test_creation(self) -> None:
        result = VotingResult()
        assert result.votes == []
        assert result.consensus_scores == {}
        assert result.consensus_best == ""
        assert result.agreement_ratio == 0.0


class TestAgentVoting:
    def _make_agent(self, name: str = "Agent1", weight: float = 1.0) -> AgentConfig:
        return AgentConfig(name=name, agent_type="localai", weight=weight)

    def test_vote_empty_translations(self) -> None:
        voting = AgentVoting([self._make_agent()])
        with pytest.raises(ValueError, match="No translations"):
            voting.vote_on_translations("orig", {}, "en", "ru")

    def test_vote_no_agents(self) -> None:
        voting = AgentVoting([])
        with pytest.raises(ValueError, match="No agents"):
            voting.vote_on_translations("orig", {"deepl": "text"}, "en", "ru")

    def test_vote_single_agent(self) -> None:
        agent = self._make_agent("Agent1")
        voting = AgentVoting([agent])

        with patch.object(voting, "_query_agent") as mock_query:
            mock_query.return_value = AgentVote(
                agent_name="Agent1",
                scores={"deepl": 8.5, "google": 7.0},
                best_service="deepl",
                explanations={"deepl": "Accurate", "google": "OK"},
                merged_translation="Best translation",
            )

            result = voting.vote_on_translations(
                "Hello", {"deepl": "Привет", "google": "Здравствуйте"}, "en", "ru"
            )

        assert result.consensus_best == "deepl"
        assert result.consensus_scores["deepl"] == 8.5
        assert result.agreement_ratio == 1.0
        assert result.merged_translation == "Best translation"

    def test_vote_multiple_agents(self) -> None:
        agents = [
            self._make_agent("Agent1", weight=1.0),
            self._make_agent("Agent2", weight=2.0),
        ]
        voting = AgentVoting(agents)

        votes = [
            AgentVote(
                agent_name="Agent1",
                scores={"deepl": 8.0, "google": 6.0},
                best_service="deepl",
                merged_translation="merged1",
            ),
            AgentVote(
                agent_name="Agent2",
                scores={"deepl": 7.0, "google": 9.0},
                best_service="google",
                merged_translation="merged2",
            ),
        ]

        with patch.object(voting, "_query_agent", side_effect=votes):
            result = voting.vote_on_translations(
                "Hello", {"deepl": "Привет", "google": "Здравствуйте"}, "en", "ru"
            )

        # Weighted avg: deepl = (8*1 + 7*2) / 3 = 7.33, google = (6*1 + 9*2) / 3 = 8.0
        assert result.consensus_best == "google"
        assert abs(result.consensus_scores["deepl"] - 7.333) < 0.1
        assert abs(result.consensus_scores["google"] - 8.0) < 0.1
        # Agent2 has higher weight, its merged_translation wins
        assert result.merged_translation == "merged2"

    def test_consensus_full_agreement(self) -> None:
        agents = [self._make_agent("A1"), self._make_agent("A2"), self._make_agent("A3")]
        voting = AgentVoting(agents)

        votes = [
            AgentVote(agent_name="A1", scores={"deepl": 9.0}, best_service="deepl"),
            AgentVote(agent_name="A2", scores={"deepl": 8.0}, best_service="deepl"),
            AgentVote(agent_name="A3", scores={"deepl": 8.5}, best_service="deepl"),
        ]

        with patch.object(voting, "_query_agent", side_effect=votes):
            result = voting.vote_on_translations("Hello", {"deepl": "Привет"}, "en", "ru")

        assert result.agreement_ratio == 1.0

    def test_consensus_partial(self) -> None:
        agents = [self._make_agent("A1"), self._make_agent("A2"), self._make_agent("A3")]
        voting = AgentVoting(agents)

        votes = [
            AgentVote(
                agent_name="A1",
                scores={"deepl": 9.0, "google": 7.0},
                best_service="deepl",
            ),
            AgentVote(
                agent_name="A2",
                scores={"deepl": 8.0, "google": 8.5},
                best_service="google",
            ),
            AgentVote(
                agent_name="A3",
                scores={"deepl": 8.5, "google": 7.5},
                best_service="deepl",
            ),
        ]

        with patch.object(voting, "_query_agent", side_effect=votes):
            result = voting.vote_on_translations(
                "Hello", {"deepl": "Привет", "google": "Здравствуйте"}, "en", "ru"
            )

        # consensus_best is by weighted avg score, not majority vote of best_service
        # deepl avg = (9+8+8.5)/3 = 8.5, google avg = (7+8.5+7.5)/3 = 7.67
        assert result.consensus_best == "deepl"
        # 2 out of 3 agents agree that deepl is best
        assert abs(result.agreement_ratio - 2 / 3) < 0.01

    def test_agent_failure_graceful(self) -> None:
        agents = [self._make_agent("A1"), self._make_agent("A2")]
        voting = AgentVoting(agents)

        def side_effect(agent, prompt):
            if agent.name == "A1":
                raise RuntimeError("Connection failed")
            return AgentVote(
                agent_name="A2",
                scores={"deepl": 8.0},
                best_service="deepl",
                merged_translation="result",
            )

        with patch.object(voting, "_query_agent", side_effect=side_effect):
            result = voting.vote_on_translations("Hello", {"deepl": "Привет"}, "en", "ru")

        assert len(result.votes) == 1
        assert result.votes[0].agent_name == "A2"

    def test_all_agents_fail(self) -> None:
        agents = [self._make_agent("A1")]
        voting = AgentVoting(agents)

        with (
            patch.object(voting, "_query_agent", side_effect=RuntimeError("fail")),
            pytest.raises(RuntimeError, match="All agents failed"),
        ):
            voting.vote_on_translations("Hello", {"deepl": "Привет"}, "en", "ru")

    def test_voting_prompt_contains_all_translations(self) -> None:
        voting = AgentVoting([self._make_agent()])
        translations = {"deepl": "Привет", "google": "Здравствуйте"}

        prompt = voting._create_voting_prompt("Hello", translations, "en", "ru", False)

        assert "Hello" in prompt
        assert "deepl" in prompt
        assert "google" in prompt
        assert "Привет" in prompt
        assert "Здравствуйте" in prompt

    def test_voting_prompt_with_renpy_context(self) -> None:
        voting = AgentVoting(
            [self._make_agent()],
            context="== GAME CONTEXT ==\nCharacters: e=Eileen\n== END CONTEXT ==",
        )
        translations = {"deepl": "Привет"}

        prompt = voting._create_voting_prompt("Hello", translations, "en", "ru", True)

        assert "== GAME CONTEXT ==" in prompt
        assert "e=Eileen" in prompt
        assert "Ren'Py" in prompt

    def test_parse_valid_json_response(self) -> None:
        voting = AgentVoting([self._make_agent()])

        response = json.dumps(
            {
                "scores": {"deepl": 8.5, "google": 7.0},
                "best": "deepl",
                "explanations": {"deepl": "Good", "google": "OK"},
                "merged": "Best translation",
            }
        )

        vote = voting._parse_agent_response("Agent1", response)

        assert vote.agent_name == "Agent1"
        assert vote.scores["deepl"] == 8.5
        assert vote.scores["google"] == 7.0
        assert vote.best_service == "deepl"
        assert vote.merged_translation == "Best translation"

    def test_parse_json_with_code_block(self) -> None:
        voting = AgentVoting([self._make_agent()])

        response = '```json\n{"scores": {"deepl": 8.0}, "best": "deepl", "explanations": {}, "merged": "text"}\n```'

        vote = voting._parse_agent_response("Agent1", response)
        assert vote.scores["deepl"] == 8.0

    def test_parse_invalid_json(self) -> None:
        voting = AgentVoting([self._make_agent()])

        vote = voting._parse_agent_response("Agent1", "not valid json")

        assert vote.agent_name == "Agent1"
        assert vote.scores == {}
        assert vote.best_service == ""

    def test_parse_score_clamping(self) -> None:
        voting = AgentVoting([self._make_agent()])

        response = json.dumps(
            {
                "scores": {"deepl": 15.0, "google": -2.0},
                "best": "deepl",
            }
        )

        vote = voting._parse_agent_response("Agent1", response)
        assert vote.scores["deepl"] == 10.0
        assert vote.scores["google"] == 0.0

    def test_create_agent_client_localai(self) -> None:
        voting = AgentVoting([])
        agent = AgentConfig(
            name="Local",
            base_url="http://localhost:1234/v1",
            model="mistral",
            agent_type="localai",
        )

        client = voting._create_agent_client(agent)
        assert client.get_name() == "LocalAI (mistral)"

    def test_create_agent_client_openai(self) -> None:
        voting = AgentVoting([])
        agent = AgentConfig(
            name="GPT4",
            api_key="sk-test",
            model="gpt-4",
            agent_type="openai",
        )

        client = voting._create_agent_client(agent)
        assert client.get_name() == "OpenAI (gpt-4)"

    def test_create_agent_client_claude(self) -> None:
        voting = AgentVoting([])
        agent = AgentConfig(
            name="Claude",
            api_key="sk-test",
            model="claude-3-sonnet-20240229",
            agent_type="claude",
        )

        client = voting._create_agent_client(agent)
        assert client.get_name() == "Claude (claude-3-sonnet-20240229)"

    def test_create_agent_client_groq(self) -> None:
        voting = AgentVoting([])
        agent = AgentConfig(
            name="Groq",
            api_key="gsk-test",
            model="mixtral-8x7b-32768",
            agent_type="groq",
        )

        client = voting._create_agent_client(agent)
        assert client.get_name() == "Groq (mixtral-8x7b-32768)"

    def test_create_agent_client_unknown_type(self) -> None:
        voting = AgentVoting([])
        agent = AgentConfig(name="Unknown", agent_type="unknown")

        with pytest.raises(ValueError, match="Unknown agent type"):
            voting._create_agent_client(agent)

    def test_auto_detect_best_when_missing(self) -> None:
        voting = AgentVoting([self._make_agent()])

        response = json.dumps(
            {
                "scores": {"deepl": 8.5, "google": 9.0},
                "explanations": {},
                "merged": "text",
            }
        )

        vote = voting._parse_agent_response("Agent1", response)
        assert vote.best_service == "google"  # auto-detected from highest score
