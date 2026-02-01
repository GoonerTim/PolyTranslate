"""Tests for AI evaluator service."""

import json

import pytest

from app.services.ai_evaluator import AIEvaluator, EvaluationResult


class MockLLMService:
    """Mock LLM service for testing."""

    def __init__(self, response: str = "", configured: bool = True):
        self.response = response
        self.configured = configured
        self.call_count = 0

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        self.call_count += 1
        if not self.response:
            raise RuntimeError("Mock error")
        return self.response

    def is_configured(self) -> bool:
        return self.configured

    def get_name(self) -> str:
        return "MockLLM"


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_evaluation_result_creation(self):
        """Test creating an evaluation result."""
        result = EvaluationResult(
            service="deepl",
            score=8.5,
            explanation="Excellent translation",
            timestamp="2024-01-01 12:00:00",
        )

        assert result.service == "deepl"
        assert result.score == 8.5
        assert result.explanation == "Excellent translation"
        assert result.timestamp == "2024-01-01 12:00:00"
        assert result.strengths == []
        assert result.weaknesses == []

    def test_evaluation_result_with_strengths_weaknesses(self):
        """Test creating an evaluation result with strengths and weaknesses."""
        result = EvaluationResult(
            service="google",
            score=7.2,
            explanation="Good translation",
            timestamp="2024-01-01 12:00:00",
            strengths=["Natural flow", "Accurate"],
            weaknesses=["Minor grammar issues"],
        )

        assert result.strengths == ["Natural flow", "Accurate"]
        assert result.weaknesses == ["Minor grammar issues"]


class TestAIEvaluator:
    """Tests for AIEvaluator class."""

    def test_init(self):
        """Test AIEvaluator initialization."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        assert evaluator.llm_service == mock_service

    def test_evaluate_translations_empty_dict(self):
        """Test evaluation with empty translations dict."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        with pytest.raises(ValueError, match="No translations provided"):
            evaluator.evaluate_translations(
                original_text="Hello world",
                translations={},
                source_lang="en",
                target_lang="ru",
            )

    def test_evaluate_translations_service_not_configured(self):
        """Test evaluation with unconfigured service."""
        mock_service = MockLLMService(configured=False)
        evaluator = AIEvaluator(mock_service)

        with pytest.raises(RuntimeError, match="is not configured"):
            evaluator.evaluate_translations(
                original_text="Hello world",
                translations={"deepl": "Привет мир"},
                source_lang="en",
                target_lang="ru",
            )

    def test_evaluate_translations_success(self):
        """Test successful evaluation."""
        eval_response = json.dumps(
            {
                "evaluations": [
                    {
                        "service": "deepl",
                        "score": 8.5,
                        "explanation": "Excellent translation with natural flow",
                    },
                    {
                        "service": "yandex",
                        "score": 7.2,
                        "explanation": "Good translation with minor issues",
                    },
                ]
            }
        )

        improved_translation = "Превосходный перевод"

        mock_service = MockLLMService(response=eval_response)
        evaluator = AIEvaluator(mock_service)

        # Override second call to return improved translation
        call_count = [0]

        def mock_translate(text: str, source_lang: str, target_lang: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return eval_response
            else:
                return improved_translation

        mock_service.translate = mock_translate  # type: ignore[method-assign]

        results = evaluator.evaluate_translations(
            original_text="Hello world",
            translations={"deepl": "Привет мир", "yandex": "Здравствуй мир"},
            source_lang="en",
            target_lang="ru",
        )

        assert "deepl" in results
        assert "yandex" in results
        assert "ai_improved" in results

        assert isinstance(results["deepl"], EvaluationResult)
        assert results["deepl"].score == 8.5
        assert "Excellent" in results["deepl"].explanation

        assert isinstance(results["yandex"], EvaluationResult)
        assert results["yandex"].score == 7.2

        assert results["ai_improved"] == improved_translation

    def test_evaluate_translations_json_with_code_blocks(self):
        """Test parsing JSON response with markdown code blocks."""
        eval_response = """```json
{
  "evaluations": [
    {"service": "deepl", "score": 9.0, "explanation": "Perfect"}
  ]
}
```"""

        mock_service = MockLLMService(response=eval_response)
        evaluator = AIEvaluator(mock_service)

        # Mock second call
        call_count = [0]

        def mock_translate(text: str, source_lang: str, target_lang: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return eval_response
            else:
                return "Improved"

        mock_service.translate = mock_translate  # type: ignore[method-assign]

        results = evaluator.evaluate_translations(
            original_text="Test",
            translations={"deepl": "Тест"},
            source_lang="en",
            target_lang="ru",
        )

        assert isinstance(results["deepl"], EvaluationResult)
        assert results["deepl"].score == 9.0

    def test_evaluate_translations_score_clamping(self):
        """Test that scores are clamped to 0-10 range."""
        eval_response = json.dumps(
            {
                "evaluations": [
                    {"service": "deepl", "score": 15.0, "explanation": "Too high"},
                    {"service": "yandex", "score": -5.0, "explanation": "Too low"},
                ]
            }
        )

        mock_service = MockLLMService(response=eval_response)
        evaluator = AIEvaluator(mock_service)

        call_count = [0]

        def mock_translate(text: str, source_lang: str, target_lang: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return eval_response
            else:
                return "Improved"

        mock_service.translate = mock_translate  # type: ignore[method-assign]

        results = evaluator.evaluate_translations(
            original_text="Test",
            translations={"deepl": "Тест", "yandex": "Проверка"},
            source_lang="en",
            target_lang="ru",
        )

        assert results["deepl"].score == 10.0
        assert results["yandex"].score == 0.0

    def test_evaluate_translations_evaluation_error(self):
        """Test handling of evaluation API error."""
        mock_service = MockLLMService(response="")
        evaluator = AIEvaluator(mock_service)

        with pytest.raises(RuntimeError, match="Evaluation failed"):
            evaluator.evaluate_translations(
                original_text="Test",
                translations={"deepl": "Тест"},
                source_lang="en",
                target_lang="ru",
            )

    def test_evaluate_translations_improvement_error(self):
        """Test handling of improvement generation error."""
        eval_response = json.dumps(
            {
                "evaluations": [
                    {"service": "deepl", "score": 8.0, "explanation": "Good"},
                ]
            }
        )

        mock_service = MockLLMService(response=eval_response)
        evaluator = AIEvaluator(mock_service)

        call_count = [0]

        def mock_translate(text: str, source_lang: str, target_lang: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return eval_response
            else:
                raise RuntimeError("Improvement failed")

        mock_service.translate = mock_translate  # type: ignore[method-assign]

        results = evaluator.evaluate_translations(
            original_text="Test",
            translations={"deepl": "Тест"},
            source_lang="en",
            target_lang="ru",
        )

        # Should still return evaluations even if improvement fails
        assert "deepl" in results
        assert "ai_improved" not in results

    def test_create_evaluation_prompt(self):
        """Test evaluation prompt generation."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        prompt = evaluator._create_evaluation_prompt(
            original_text="Hello world",
            translations={"deepl": "Привет мир", "yandex": "Здравствуй мир"},
            source_lang="en",
            target_lang="ru",
        )

        assert "Hello world" in prompt
        assert "Привет мир" in prompt
        assert "Здравствуй мир" in prompt
        assert "en" in prompt
        assert "ru" in prompt
        assert "JSON" in prompt

    def test_create_improvement_prompt_no_renpy(self):
        """Test improvement prompt generation without Ren'Py."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        prompt = evaluator._create_improvement_prompt(
            original_text="Hello world",
            translations={"deepl": "Привет мир"},
            source_lang="en",
            target_lang="ru",
            is_renpy=False,
        )

        assert "Hello world" in prompt
        assert "Привет мир" in prompt
        assert "CRITICAL" not in prompt

    def test_create_improvement_prompt_with_renpy(self):
        """Test improvement prompt generation with Ren'Py."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        prompt = evaluator._create_improvement_prompt(
            original_text='    character "Hello world"',
            translations={"deepl": "Привет мир"},
            source_lang="en",
            target_lang="ru",
            is_renpy=True,
        )

        assert "CRITICAL" in prompt
        assert "Ren'Py" in prompt

    def test_parse_evaluation_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        with pytest.raises(RuntimeError, match="Failed to parse"):
            evaluator._parse_evaluation_response("invalid json", "2024-01-01")

    def test_parse_evaluation_response_missing_fields(self):
        """Test parsing response with missing fields."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        response = json.dumps(
            {
                "evaluations": [
                    {"service": "deepl"},  # Missing score and explanation
                ]
            }
        )

        results = evaluator._parse_evaluation_response(response, "2024-01-01")

        # Should handle missing fields with defaults
        assert "deepl" in results
        assert results["deepl"].score == 0.0
        assert results["deepl"].explanation == ""

    def test_preserve_renpy_structure(self):
        """Test Ren'Py structure preservation."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        original = """label start:
    character "Hello world"
    another "How are you?"
"""

        improved = """Привет мир
Как дела?"""

        result = evaluator._preserve_renpy_structure(original, improved)

        assert 'character "Привет мир"' in result
        assert 'another "Как дела?"' in result
        assert "label start:" in result
        assert result.startswith("label start:")

    def test_preserve_renpy_structure_non_renpy(self):
        """Test that non-Ren'Py text is returned unchanged."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        original = "Just plain text"
        improved = "Просто текст"

        result = evaluator._preserve_renpy_structure(original, improved)

        assert result == improved

    def test_is_renpy_dialogue(self):
        """Test Ren'Py dialogue detection."""
        mock_service = MockLLMService()
        evaluator = AIEvaluator(mock_service)

        # Test Ren'Py dialogue
        assert evaluator._is_renpy_dialogue('    character "Hello"')
        assert evaluator._is_renpy_dialogue('character "Hello"')

        # Test non-Ren'Py text
        assert not evaluator._is_renpy_dialogue("Plain text")
        assert not evaluator._is_renpy_dialogue("No dialogue here")

    def test_integration_with_mock_service(self):
        """Test integration with mocked service."""
        # Use MockLLMService instead of real OpenAI to avoid API calls
        eval_response = json.dumps(
            {
                "evaluations": [
                    {
                        "service": "deepl",
                        "score": 8.5,
                        "explanation": "Great translation",
                    }
                ]
            }
        )

        improvement_response = "Превосходный перевод"

        # Create mock service with sequential responses
        call_count = [0]

        def mock_translate(text: str, source_lang: str, target_lang: str) -> str:
            call_count[0] += 1
            if call_count[0] == 1:
                return eval_response
            else:
                return improvement_response

        mock_service = MockLLMService()
        mock_service.translate = mock_translate  # type: ignore[method-assign]

        evaluator = AIEvaluator(mock_service)

        results = evaluator.evaluate_translations(
            original_text="Hello world",
            translations={"deepl": "Привет мир"},
            source_lang="en",
            target_lang="ru",
        )

        assert "deepl" in results
        assert isinstance(results["deepl"], EvaluationResult)
        assert results["deepl"].score == 8.5
        assert "ai_improved" in results
        assert results["ai_improved"] == improvement_response
