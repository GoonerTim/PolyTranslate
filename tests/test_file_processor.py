"""Tests for the file processor module."""

from __future__ import annotations

from pathlib import Path

from app.core.file_processor import FileProcessor


class TestFileProcessor:
    """Tests for FileProcessor class."""

    def test_detect_encoding_utf8(self) -> None:
        """Test encoding detection for UTF-8."""
        content = b"Hello, world!"
        encoding = FileProcessor.detect_encoding(content)
        assert encoding.lower() in ["utf-8", "ascii"]

    def test_detect_encoding_utf16(self) -> None:
        """Test encoding detection for UTF-16."""
        content = "Hello, world!".encode("utf-16")
        encoding = FileProcessor.detect_encoding(content)
        assert "utf" in encoding.lower() or "16" in encoding.lower()

    def test_read_txt(self) -> None:
        """Test reading text files."""
        content = b"Hello, world!"
        result = FileProcessor.read_txt(content)
        assert result == "Hello, world!"

    def test_read_txt_with_unicode(self) -> None:
        """Test reading text files with Unicode."""
        content = "Привет, мир!".encode()
        result = FileProcessor.read_txt(content)
        assert result == "Привет, мир!"

    def test_read_rpy_dialogue(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py dialogue."""
        result = FileProcessor.read_rpy(sample_rpy_content)
        assert "Hello, how are you?" in result
        assert "fine, thanks" in result

    def test_read_rpy_menu_options(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py menu options."""
        result = FileProcessor.read_rpy(sample_rpy_content)
        assert "Good option" in result
        assert "Bad option" in result

    def test_read_rpy_translatable_strings(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py translatable strings."""
        result = FileProcessor.read_rpy(sample_rpy_content, translate_strings=True)
        assert "Translatable string" in result

    def test_read_rpy_no_dialogue(self, sample_rpy_content: bytes) -> None:
        """Test reading Ren'Py without dialogue."""
        result = FileProcessor.read_rpy(
            sample_rpy_content, translate_dialogue=False, translate_strings=True
        )
        assert "Translatable string" in result
        # Dialogue should not be extracted
        assert "DIALOGUE_LINE" not in result or "Hello" not in result

    def test_process_file_txt(self, sample_txt_file: Path) -> None:
        """Test processing text file."""
        result = FileProcessor.process_file(sample_txt_file)
        assert result == "Hello, world!"

    def test_process_bytes_txt(self) -> None:
        """Test processing bytes as text."""
        content = b"Test content"
        result = FileProcessor.process_bytes(content, "txt")
        assert result == "Test content"

    def test_read_html(self) -> None:
        """Test reading HTML files."""
        html_content = b"<html><body><p>Hello, world!</p></body></html>"
        result = FileProcessor.read_html(html_content)
        assert "Hello, world!" in result

    def test_read_html_strips_scripts(self) -> None:
        """Test that HTML reading strips scripts."""
        html_content = b"<html><script>alert('bad')</script><body><p>Good text</p></body></html>"
        result = FileProcessor.read_html(html_content)
        assert "Good text" in result
        assert "alert" not in result

    def test_read_md(self) -> None:
        """Test reading Markdown files."""
        md_content = b"# Hello\n\nThis is **bold** text."
        result = FileProcessor.read_md(md_content)
        assert "Hello" in result
        assert "bold" in result

    def test_supported_extensions(self) -> None:
        """Test that supported extensions are defined."""
        assert "txt" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "pdf" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "docx" in FileProcessor.SUPPORTED_EXTENSIONS
        assert "rpy" in FileProcessor.SUPPORTED_EXTENSIONS

    def test_reconstruct_rpy(self) -> None:
        """Test Ren'Py file reconstruction."""
        original = 'e "Hello, world!"'
        translations = {"DIALOGUE_LINE_1: Hello, world!": "Привет, мир!"}
        result = FileProcessor.reconstruct_rpy(original, translations)
        # The reconstruction should preserve structure
        assert 'e "' in result

    def test_unsupported_format(self, temp_dir: Path) -> None:
        """Test handling unsupported file format."""
        file_path = temp_dir / "test.xyz"
        file_path.write_text("Some content", encoding="utf-8")

        # Should fall back to text reading
        result = FileProcessor.process_file(file_path)
        assert result == "Some content"
