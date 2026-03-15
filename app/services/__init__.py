"""Translation services."""

from app.services.agent_voting import AgentConfig, AgentVote, AgentVoting, VotingResult
from app.services.ai_evaluator import AIEvaluator, EvaluationResult
from app.services.base import TranslationService
from app.services.chatgpt_proxy import ChatGPTProxyService
from app.services.claude import ClaudeService
from app.services.deepl import DeepLService
from app.services.google import GoogleService
from app.services.groq_service import GroqService
from app.services.llm_base import LLMTranslationService
from app.services.localai import LocalAIService
from app.services.openai_service import OpenAIService
from app.services.openrouter import OpenRouterService
from app.services.yandex import YandexService

__all__ = [
    "AgentConfig",
    "AgentVote",
    "AgentVoting",
    "VotingResult",
    "AIEvaluator",
    "EvaluationResult",
    "TranslationService",
    "LLMTranslationService",
    "DeepLService",
    "YandexService",
    "GoogleService",
    "OpenAIService",
    "OpenRouterService",
    "ChatGPTProxyService",
    "GroqService",
    "ClaudeService",
    "LocalAIService",
]
