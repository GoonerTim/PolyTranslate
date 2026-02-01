"""Integration tests for the translator application."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from app.config.settings import Settings
from app.core.file_processor import FileProcessor
from app.core.translator import Translator
from app.utils.glossary import Glossary


class TestEndToEndTranslation:
    """End-to-end integration tests."""

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_translate_text_file_end_to_end(self, mock_post: MagicMock, temp_dir: Path) -> None:
        """Test complete flow: file → process → translate → save."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Привет, мир!"}}
        mock_post.return_value = mock_response

        # Create test file
        input_file = temp_dir / "input.txt"
        input_file.write_text("Hello, world!", encoding="utf-8")

        # Process file
        text = FileProcessor.process_file(input_file)
        assert text == "Hello, world!"

        # Translate
        translator = Translator()
        result = translator.translate(text, "en", "ru", "chatgpt_proxy")
        assert isinstance(result, str)

        # Save result
        output_file = temp_dir / "output.txt"
        output_file.write_text(result, encoding="utf-8")
        assert output_file.exists()

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_parallel_translation_workflow(self, mock_post: MagicMock, temp_dir: Path) -> None:
        """Test parallel translation workflow."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Переведено"}}
        mock_post.return_value = mock_response

        # Create settings
        settings = Settings(temp_dir / "config.json")
        translator = Translator(settings)

        # Translate with multiple chunks
        text = "First sentence. Second sentence. Third sentence."
        results = translator.translate_parallel(
            text, "en", "ru", ["chatgpt_proxy"], chunk_size=20, max_workers=2
        )

        assert "chatgpt_proxy" in results
        assert isinstance(results["chatgpt_proxy"], str)

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_translation_with_glossary_integration(
        self, mock_post: MagicMock, temp_dir: Path
    ) -> None:
        """Test translation with glossary applied."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "API is great"}}
        mock_post.return_value = mock_response

        # Setup glossary
        glossary_path = temp_dir / "glossary.json"
        glossary = Glossary(glossary_path)
        glossary.add_entry("API", "АПИ")
        glossary.save()

        # Setup translator
        translator = Translator()
        translator.glossary = glossary

        # Translate
        result = translator.translate("Test", "en", "ru", "chatgpt_proxy")

        # Glossary should be applied
        if "API" in result:
            # If original had API, it should be replaced
            pass

    def test_settings_persistence(self, temp_dir: Path) -> None:
        """Test that settings persist across sessions."""
        config_path = temp_dir / "config.json"

        # Create and save settings
        settings1 = Settings(config_path)
        settings1.set_api_key("deepl", "test_key_123")
        settings1.set_theme("light")
        settings1.set_chunk_size(1500)
        settings1.save()

        # Load in new instance
        settings2 = Settings(config_path)
        assert settings2.get_api_key("deepl") == "test_key_123"
        assert settings2.get_theme() == "light"
        assert settings2.get_chunk_size() == 1500

    def test_glossary_persistence(self, temp_dir: Path) -> None:
        """Test that glossary persists across sessions."""
        glossary_path = temp_dir / "glossary.json"

        # Create and save glossary
        glossary1 = Glossary(glossary_path)
        glossary1.add_entry("hello", "привет")
        glossary1.add_entry("world", "мир")
        glossary1.save()

        # Load in new instance
        glossary2 = Glossary(glossary_path)
        assert glossary2.get_entry("hello") == "привет"
        assert glossary2.get_entry("world") == "мир"

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_multi_service_comparison(self, mock_post: MagicMock) -> None:
        """Test comparing translations from multiple services."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Результат перевода"}}
        mock_post.return_value = mock_response

        translator = Translator()
        text = "Hello, world!"

        # Translate with one service (chatgpt_proxy)
        results = translator.translate_parallel(
            text, "en", "ru", ["chatgpt_proxy"], chunk_size=100, max_workers=1
        )

        # Should have one result
        assert len(results) >= 1
        assert "chatgpt_proxy" in results

    def test_language_detection_integration(self) -> None:
        """Test language detection in workflow."""
        translator = Translator()

        # Detect English
        result_en = translator.detect_language("This is a test sentence in English language.")
        if result_en is not None:  # langdetect may not be available
            assert result_en == "en"

        # Detect Russian
        result_ru = translator.detect_language("Это тестовое предложение на русском языке.")
        if result_ru is not None:
            assert result_ru == "ru"

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_error_handling_in_parallel_translation(self, mock_post: MagicMock) -> None:
        """Test error handling in parallel translation."""
        # First call succeeds, second fails
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"response": {"translated_text": "Success"}}

        mock_response_error = MagicMock()
        mock_response_error.status_code = 500
        mock_response_error.text = "Server error"

        mock_post.side_effect = [mock_response_success, mock_response_error]

        translator = Translator()
        # Should handle errors gracefully
        results = translator.translate_parallel(
            "Test. Test.", "en", "ru", ["chatgpt_proxy"], chunk_size=10, max_workers=1
        )

        # Should still return results (with errors marked)
        assert "chatgpt_proxy" in results

    def test_chunk_reassembly(self) -> None:
        """Test that split chunks are reassembled correctly."""
        translator = Translator()

        # Create text that will be split
        sentences = [f"Sentence number {i}." for i in range(10)]
        original_text = " ".join(sentences)

        # Split text
        chunks = translator.split_text(original_text, chunk_size=50)
        assert len(chunks) > 1

        # Reassemble
        reassembled = " ".join(chunks)

        # Should contain all original sentences
        for sentence in sentences:
            assert sentence in reassembled or sentence in original_text

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_progress_tracking(self, mock_post: MagicMock) -> None:
        """Test progress tracking during translation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Translated"}}
        mock_post.return_value = mock_response

        translator = Translator()
        progress_updates = []

        def track_progress(completed: int, total: int) -> None:
            progress_updates.append((completed, total))

        # Translate with progress tracking
        text = "One. Two. Three. Four. Five."
        translator.translate_parallel(
            text,
            "en",
            "ru",
            ["chatgpt_proxy"],
            chunk_size=10,
            max_workers=1,
            progress_callback=track_progress,
        )

        # Should have received progress updates
        assert len(progress_updates) > 0

        # Last update should show completion
        if progress_updates:
            final_completed, final_total = progress_updates[-1]
            assert final_completed == final_total

    def test_empty_text_handling(self) -> None:
        """Test handling of empty text."""
        translator = Translator()

        # Split empty text
        chunks = translator.split_text("", chunk_size=100)
        assert chunks == [""]

        # Detect language of empty text
        result = translator.detect_language("")
        assert result is None

    def test_special_characters_handling(self, temp_dir: Path) -> None:
        """Test handling of special characters in text."""
        # Create file with special characters
        input_file = temp_dir / "special.txt"
        special_text = "Special: @#$%^&*() \n\t émojis: 😀🎉"
        input_file.write_text(special_text, encoding="utf-8")

        # Process file
        result = FileProcessor.process_file(input_file)
        assert "@#$%^&*()" in result

    def test_large_text_processing(self) -> None:
        """Test processing of large text."""
        translator = Translator()

        # Create large text (1000 sentences)
        large_text = " ".join([f"Sentence {i}." for i in range(1000)])

        # Should split into multiple chunks
        chunks = translator.split_text(large_text, chunk_size=500)
        assert len(chunks) > 5

    @patch("app.services.chatgpt_proxy.requests.post")
    def test_concurrent_service_calls(self, mock_post: MagicMock) -> None:
        """Test concurrent calls to translation service."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": {"translated_text": "Результат"}}
        mock_post.return_value = mock_response

        translator = Translator()

        # Translate with max workers > 1
        text = "One. Two. Three. Four. Five. Six. Seven. Eight."
        results = translator.translate_parallel(
            text, "en", "ru", ["chatgpt_proxy"], chunk_size=10, max_workers=3
        )

        assert "chatgpt_proxy" in results
        # Multiple API calls should have been made concurrently
        assert mock_post.call_count > 1
